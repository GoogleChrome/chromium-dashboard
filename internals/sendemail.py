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

from __future__ import division
from __future__ import print_function

import logging
import re

from google.appengine.api import mail
from google.appengine.ext.webapp.mail_handlers import BounceNotification

# TODO(jrobbins): For now, these files and files that they import must
# remain compatible with both py2 and py3.  We could split those files too.
import settings
from framework import basehandlers
from internals import models


class OutboundEmailHandler(basehandlers.FlaskHandler):
  """Task to send a notification email to one recipient."""

  IS_INTERNAL_HANDLER = True

  def process_post_data(self):
    self.require_task_header()

    to = self.get_param('to', required=True)
    subject = self.get_param('subject', required=True)
    email_html = self.get_param('html', required=True)

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


class BouncedEmailHandler(basehandlers.FlaskHandler):
  BAD_WRAP_RE = re.compile('=\r\n')
  BAD_EQ_RE = re.compile('=3D')
  IS_INTERNAL_HANDLER = True

  """Handler to notice when email to given user is bouncing."""
  # For docs on AppEngine's bounce email handling, see:
  # https://cloud.google.com/appengine/docs/python/mail/bounce
  # Source code is in file:
  # google_appengine/google/appengine/ext/webapp/mail_handlers.py
  def process_post_data(self):
    self.receive(BounceNotification(self.form))
    return {'message': 'Done'}

  def receive(self, bounce_message):
    email_addr = bounce_message.original.get('to')
    subject = 'Mail to %r bounced' % email_addr
    logging.info(subject)
    pref_list = models.UserPref.get_prefs_for_emails([email_addr])
    user_pref = pref_list[0]
    user_pref.bounced = True
    user_pref.put()

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


app = basehandlers.FlaskApplication([
  ('/tasks/outbound-email', OutboundEmailHandler),
  ('/_ah/bounce', BouncedEmailHandler),
], debug=settings.DEBUG)
