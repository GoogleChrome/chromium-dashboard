from __future__ import division
from __future__ import print_function

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

import collections
import json
import testing_config_py2  # Must be imported before the module under test.
import mock
import unittest

from google.appengine.api import mail

import settings
from internals import sendemail

class OutboundEmailHandlerTest(unittest.TestCase):

  def setUp(self):
    self.request_path = '/tasks/outbound-email'

    self.to = 'user@example.com'
    self.subject = 'test subject'
    self.html = '<b>body</b>'
    self.sender = ('Chromestatus <admin@%s.appspotmail.com>' %
                   settings.APP_ID)

  @mock.patch('settings.SEND_EMAIL', True)
  @mock.patch('settings.SEND_ALL_EMAIL_TO', None)
  @mock.patch('google.appengine.api.mail.EmailMessage')
  def test_post__prod(self, mock_emailmessage_constructor):
    """On cr-status, we send emails to real users."""
    params = {
        'to': self.to,
        'subject': self.subject,
        'html': self.html,
        }
    with sendemail.app.test_request_context(self.request_path, json=params):
      actual_response = sendemail.handle_outbound_mail_task()

    mock_emailmessage_constructor.assert_called_once_with(
        sender=self.sender, to=self.to, subject=self.subject,
        html=self.html)
    mock_message = mock_emailmessage_constructor.return_value
    mock_message.check_initialized.assert_called_once_with()
    mock_message.send.assert_called_once_with()
    self.assertEqual({'message': 'Done'}, actual_response)

  @mock.patch('settings.SEND_EMAIL', True)
  @mock.patch('google.appengine.api.mail.EmailMessage')
  def test_post__staging(self, mock_emailmessage_constructor):
    """On cr-status-staging, we send emails to an archive."""
    params = {
        'to': self.to,
        'subject': self.subject,
        'html': self.html,
        }
    with sendemail.app.test_request_context(self.request_path, json=params):
      actual_response = sendemail.handle_outbound_mail_task()

    expected_to = 'cr-status-staging-emails+user+example.com@google.com'
    mock_emailmessage_constructor.assert_called_once_with(
        sender=self.sender, to=expected_to, subject=self.subject,
        html=self.html)
    mock_message = mock_emailmessage_constructor.return_value
    mock_message.check_initialized.assert_called_once_with()
    mock_message.send.assert_called_once_with()
    self.assertEqual({'message': 'Done'}, actual_response)

  @mock.patch('settings.SEND_EMAIL', False)
  @mock.patch('google.appengine.api.mail.EmailMessage')
  def test_post__local(self, mock_emailmessage_constructor):
    """When running locally, we don't actually send emails."""
    params = {
        'to': self.to,
        'subject': self.subject,
        'html': self.html,
        }
    with sendemail.app.test_request_context(self.request_path, json=params):
      actual_response = sendemail.handle_outbound_mail_task()

    expected_to = 'cr-status-staging-emails+user+example.com@google.com'
    mock_emailmessage_constructor.assert_called_once_with(
        sender=self.sender, to=expected_to, subject=self.subject,
        html=self.html)
    mock_message = mock_emailmessage_constructor.return_value
    mock_message.check_initialized.assert_called_once_with()
    mock_message.send.assert_not_called()
    self.assertEqual({'message': 'Done'}, actual_response)


class BouncedEmailHandlerTest(unittest.TestCase):

  def setUp(self):
    self.sender = ('Chromestatus <admin@%s.appspotmail.com>' %
                   settings.APP_ID)
    self.expected_to = settings.BOUNCE_ESCALATION_ADDR

  @mock.patch('internals.sendemail.receive')
  def test_process_post_data(self, mock_receive):
    with sendemail.app.test_request_context('/_ah/bounce'):
      actual_json = sendemail.handle_bounce()

    self.assertEqual({'message': 'Done'}, actual_json)
    mock_receive.assert_called_once()


  @mock.patch('settings.SEND_EMAIL', True)
  @mock.patch('google.appengine.api.mail.EmailMessage')
  def test_receive__user_has_prefs(self, mock_emailmessage_constructor):
    """When we get a bounce, we update the UserPrefs for that user."""
    #starrer_3_pref = models.UserPref(
    #    email='starrer_3@example.com',
    #    notify_as_starrer=False)
    #starrer_3_pref.put()

    bounce_message = testing_config_py2.Blank(
        original={'to': 'starrer_3@example.com',
                  'from': 'sender',
                  'subject': 'subject',
                  'text': 'body'})

    sendemail.receive(bounce_message)

    # TODO(jrobbins): Redo this testing after this aspect of the code is
    # re-implemented.
    # updated_pref = models.UserPref.get_by_id(starrer_3_pref.key.integer_id())
    # self.assertEqual('starrer_3@example.com', updated_pref.email)
    # self.assertTrue(updated_pref.bounced)
    # self.assertFalse(updated_pref.notify_as_starrer)

    expected_subject = "Mail to 'starrer_3@example.com' bounced"
    mock_emailmessage_constructor.assert_called_once_with(
        sender=self.sender, to=self.expected_to, subject=expected_subject,
        body=mock.ANY)
    mock_message = mock_emailmessage_constructor.return_value
    mock_message.check_initialized.assert_called_once_with()
    mock_message.send.assert_called()

  @mock.patch('settings.SEND_EMAIL', True)
  @mock.patch('google.appengine.api.mail.EmailMessage')
  def test_receive__create_prefs(self, mock_emailmessage_constructor):
    """When we get a bounce, we create the UserPrefs for that user."""
    # Note, no existing UserPref for starrer_4.

    bounce_message = testing_config_py2.Blank(
        original={'to': 'starrer_4@example.com',
                  'from': 'sender',
                  'subject': 'subject',
                  'text': 'body'})

    sendemail.receive(bounce_message)

    # TODO(jrobbins): Redo this testing after this aspect of the code is
    # re-implemented.
    # prefs_list = models.UserPref.get_prefs_for_emails(
    #     ['starrer_4@example.com'])
    # updated_pref = prefs_list[0]
    # self.assertEqual('starrer_4@example.com', updated_pref.email)
    # self.assertTrue(updated_pref.bounced)
    # self.assertTrue(updated_pref.notify_as_starrer)

    expected_subject = "Mail to 'starrer_4@example.com' bounced"
    mock_emailmessage_constructor.assert_called_once_with(
        sender=self.sender, to=self.expected_to, subject=expected_subject,
        body=mock.ANY)
    mock_message = mock_emailmessage_constructor.return_value
    mock_message.check_initialized.assert_called_once_with()
    mock_message.send.assert_called()
