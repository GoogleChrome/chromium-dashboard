# -*- coding: utf-8 -*-
# Copyright 2021 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License")
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import flask
import json
import logging
import re
import urllib
import requests
import rfc822

from google.appengine.api import mail
from google.appengine.ext.webapp.mail_handlers import BounceNotification

import settings

app = flask.Flask(__name__)

# Parsing very large messages could cause out-of-memory errors.
MAX_BODY_SIZE = 100 * 1024


def require_task_header():
  """Abort if this is not a Google Cloud Tasks request."""
  if settings.UNIT_TEST_MODE or settings.DEV_MODE:
    return
  if 'X-AppEngine-QueueName' not in flask.request.headers:
    flask.abort(403, msg='Lacking X-AppEngine-QueueName header')


def get_param(request, name):
  """Get the specified JSON parameter."""
  json_body = request.get_json(force=True)
  val = json_body.get(name)
  if not val:
    flask.abort(400, msg='Missing parameter %r' % name)
  return val


@app.route('/tasks/outbound-email', methods=['POST'])
def handle_outbound_mail_task():
  """Task to send a notification email to one recipient."""
  require_task_header()

  to = get_param(flask.request, 'to')
  subject = get_param(flask.request, 'subject')
  email_html = get_param(flask.request, 'html')

  if settings.SEND_ALL_EMAIL_TO:
    to_user, to_domain = to.split('@')
    to = settings.SEND_ALL_EMAIL_TO % {'user': to_user, 'domain': to_domain}

  message = mail.EmailMessage(
      sender='Chromestatus <admin@%s.appspotmail.com>' % settings.APP_ID,
      to=to, subject=subject, html=email_html)
  message.check_initialized()

  logging.info('Will send the following email:\n')
  logging.info('To: %s', message.to)
  logging.info('Subject: %s', message.subject)
  logging.info('Body:\n%s', message.html)
  if settings.SEND_EMAIL:
    message.send()
    logging.info('Email sent')
  else:
    logging.info('Email not sent because of settings.SEND_EMAIL')

  return {'message': 'Done'}


BAD_WRAP_RE = re.compile('=\r\n')
BAD_EQ_RE = re.compile('=3D')
IS_INTERNAL_HANDLER = True

# For docs on AppEngine's bounce email handling, see:
# https://cloud.google.com/appengine/docs/python/mail/bounce
# Source code is in file:
# google_appengine/google/appengine/ext/webapp/mail_handlers.py

@app.route('/_ah/bounce', methods=['POST'])
def handle_bounce():
  """Handler to notice when email to given user is bouncing."""
  receive(BounceNotification(flask.request.form))
  return {'message': 'Done'}

def receive(bounce_message):
  email_addr = bounce_message.original.get('to')
  subject = 'Mail to %r bounced' % email_addr
  logging.info(subject)

  # TODO(jrobbins): Re-implement this without depending on models.
  # Instead create a task and then have that processed in py3.
  # pref_list = models.UserPref.get_prefs_for_emails([email_addr])
  # user_pref = pref_list[0]
  # user_pref.bounced = True
  # user_pref.put()

  # Escalate to someone who might do something about it, e.g.
  # find a new owner for a component.
  body = ('The following message bounced.\n'
          '=================\n'
          'From: {from}\n'
          'To: {to}\n'
          'Subject: {subject}\n\n'
          '{text}\n'.format(**bounce_message.original))
  logging.info(body)
  message = mail.EmailMessage(
      sender='Chromestatus <admin@%s.appspotmail.com>' % settings.APP_ID,
      to=settings.BOUNCE_ESCALATION_ADDR, subject=subject, body=body)
  message.check_initialized()
  if settings.SEND_EMAIL:
    message.send()


def _extract_addrs(header_value):
  """Given a message header value, return email address found there."""
  friendly_addr_pairs = list(rfc822.AddressList(header_value))
  return [addr for _friendly, addr in friendly_addr_pairs]


def call_py3_task_handler(handler_path, task_dict):
  """Request that our py3 code handle the rest of the work."""
  handler_host = 'http://localhost:8080'
  if settings.APP_ID == 'cr-status':
    handler_host = 'https://chromestatus.com'
  if settings.APP_ID == 'cr-status-staging':
    handler_host = 'https://cr-status-staging.appspot.com'
  handler_url = handler_host + handler_path

  request_body = json.dumps(task_dict).encode()
  logging.info('request_body is %r', request_body)

  # AppEngine automatically sets header X-Appengine-Inbound-Appid,
  # and that header is stripped from external requests.  So,
  # require_task_header() can check for it to authenticate.
  handler_response = requests.request(
      'POST', handler_url, data=request_body, allow_redirects=False)

  logging.info('request_response is %r', handler_response)
  return handler_response


def get_incoming_message():
  """Get an email message object from the request data."""
  data = flask.request.get_data(as_text=True)
  msg = mail.InboundEmailMessage(data).original
  return msg


@app.route('/_ah/mail/<string:addr>', methods=['POST'])
def handle_incoming_mail(addr=None):
  """Handle an incoming email by making a task to examine it.

  This code checks some basic properties of the incoming message
  to make sure that it is worth examining.  Then it puts all the
  relevent fields into a dict and makes a new Cloud Task which
  is futher processed in python 3 code.
  """
  logging.info('Request Headers: %r', flask.request.headers)

  logging.info('\n\n\nPOST for InboundEmail and addr is %r', addr)
  if addr != settings.INBOUND_EMAIL_ADDR:
    logging.info('Message not sent directly to our address')
    return {'message': 'Wrong address'}

  if flask.request.content_length > MAX_BODY_SIZE:
    logging.info('Message too big, ignoring')
    return {'message': 'Too big'}

  msg = get_incoming_message()

  precedence = msg.get('precedence', '')
  if precedence.lower() in ['bulk', 'junk']:
    logging.info('Precedence: %r indicates an autoresponder', precedence)
    return {'message': 'Wrong precedence'}
  from_addrs = _extract_addrs(msg.get('from', ''))
  if from_addrs:
    from_addr = from_addrs[0]
  else:
    logging.info('could not parse from addr')
    return {'message': 'Missing From'}
  in_reply_to = msg.get('in-reply-to', '')

  body = u''
  for part in msg.walk():
    # We only process plain text emails.
    if part.get_content_type() == 'text/plain':
      body = part.get_payload(decode=True)
      if not isinstance(body, unicode):
        body = body.decode('utf-8')
      break  # Only consider the first text part.

  to_addr = urllib.unquote(addr)
  subject = msg.get('subject', '')
  task_dict = {
      'to_addr': to_addr,
      'from_addr': from_addr,
      'subject': subject,
      'in_reply_to': in_reply_to,
      'body': body,
      }
  call_py3_task_handler('/tasks/detect-intent', task_dict)

  return {'message': 'Done'}
