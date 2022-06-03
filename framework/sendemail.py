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
from email import utils

from google.appengine.api import mail

import settings
from framework import cloud_tasks_helpers


# Parsing very large messages could cause out-of-memory errors.
MAX_BODY_SIZE = 20 * 1024 * 1024  # 20 MB


def require_task_header():
  """Abort if this is not a Google Cloud Tasks request."""
  if settings.UNIT_TEST_MODE or settings.DEV_MODE:
    return
  if 'X-AppEngine-QueueName' not in flask.request.headers:
    flask.abort(403, msg='Lacking X-AppEngine-QueueName header')


def get_param(request, name, required=True):
  """Get the specified JSON parameter."""
  json_body = request.get_json(force=True)
  val = json_body.get(name)
  if required and not val:
    flask.abort(400, msg='Missing parameter %r' % name)
  return val


def py2_health_check():
  """Prove that this GAE module is responding."""
  return {'message': 'OK py2'}


def handle_outbound_mail_task():
  """Task to send a notification email to one recipient."""
  require_task_header()

  to = get_param(flask.request, 'to')
  from_user = get_param(flask.request, 'from_user', required=False)
  subject = get_param(flask.request, 'subject')
  email_html = get_param(flask.request, 'html')
  references = get_param(flask.request, 'references', required=False)

  if settings.SEND_ALL_EMAIL_TO and to != settings.REVIEW_COMMENT_MAILING_LIST:
    to_user, to_domain = to.split('@')
    to = settings.SEND_ALL_EMAIL_TO % {'user': to_user, 'domain': to_domain}

  sender = 'Chromestatus <admin@%s.appspotmail.com>' % settings.APP_ID
  if from_user:
    sender = '%s via Chromestatus <admin+%s@%s.appspotmail.com>' % (
        from_user, from_user, settings.APP_ID)

  message = mail.EmailMessage(
      sender=sender, to=to, subject=subject, html=email_html)
  message.check_initialized()

  if references:
    message.headers = {
        'References': references,
        'In-Reply-To': references,
    }

  logging.info('Will send the following email:\n')
  logging.info('Sender: %s', message.sender)
  logging.info('To: %s', message.to)
  logging.info('Subject: %s', message.subject)
  logging.info('References: %s', references or '(not included)')
  logging.info('In-Reply-To: %s', references or '(not included)')
  logging.info('Body:\n%s', message.html[:settings.MAX_LOG_LINE])
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

def handle_bounce():
  """Handler to notice when email to given user is bouncing."""
  receive(mail.BounceNotification(flask.request.form))
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
  friendly_addr_pairs = utils.getaddresses(header_value)
  return [addr for _friendly, addr in friendly_addr_pairs]


def get_incoming_message():
  """Get an email message object from the request data."""
  data = flask.request.get_data(as_text=True)
  msg = mail.InboundEmailMessage(data).original
  return msg


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
  from_addrs = (_extract_addrs(msg.get_all('x-original-from', [])) or
                _extract_addrs(msg.get_all('from', [])))
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
      #if not isinstance(body, unicode):
      #  body = body.decode('utf-8')
      break  # Only consider the first text part.

  to_addr = urllib.parse.unquote(addr)
  subject = msg.get('subject', '')
  task_dict = {
      'to_addr': to_addr,
      'from_addr': from_addr,
      'subject': subject,
      'in_reply_to': in_reply_to,
      'body': body,
      }
  logging.info('task_dict is %r', task_dict)
  cloud_tasks_helpers.enqueue_task(
      '/tasks/detect-intent', task_dict)

  return {'message': 'Done'}


def add_routes(app):
  """Xxx"""
  app.add_url_rule('/py2', view_func=py2_health_check)
  app.add_url_rule(
      '/tasks/outbound-email', view_func=handle_outbound_mail_task,
      methods=['POST'])
  app.add_url_rule('/_ah/bounce', view_func=handle_bounce, methods=['POST'])
  app.add_url_rule(
      '/_ah/mail/<string:addr>', view_func=handle_incoming_mail, methods=['POST'])
