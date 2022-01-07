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

import email
import collections
import json
import testing_config_py2  # Must be imported before the module under test.
import mock
import unittest

from google.appengine.api import mail
from google.appengine.api import urlfetch

import settings
import sendemail

class OutboundEmailHandlerTest(unittest.TestCase):

  def setUp(self):
    self.request_path = '/tasks/outbound-email'

    self.to = 'user@example.com'
    self.subject = 'test subject'
    self.html = '<b>body</b>'
    self.sender = ('Chromestatus <admin@%s.appspotmail.com>' %
                   settings.APP_ID)
    self.refs = 'fake-message-id-of-previous-message'

  @mock.patch('settings.SEND_EMAIL', True)
  @mock.patch('settings.SEND_ALL_EMAIL_TO', None)
  @mock.patch('google.appengine.api.mail.EmailMessage')
  def test_post__prod(self, mock_emailmessage_constructor):
    """On cr-status, we send emails to real users."""
    params = {
        'to': self.to,
        'subject': self.subject,
        'html': self.html,
        'references': self.refs,
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
    self.assertEqual(self.refs, mock_message.headers['References'])

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

  @mock.patch('sendemail.receive')
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


class FunctionTest(unittest.TestCase):

  def test_extract_addrs(self):
    """We can parse email From: lines."""
    header_val = ''
    self.assertEqual(
        [], sendemail._extract_addrs(header_val))

    header_val = 'J. Robbins <a@b.com>, c@d.com,\n Nick "Name" Dude <e@f.com>'
    self.assertEqual(
        ['a@b.com', 'c@d.com', 'e@f.com'],
        sendemail._extract_addrs(header_val))

    header_val = ('hot: J. O\'Robbins <a@b.com>; '
                  'cool: "friendly" <e.g-h@i-j.k-L.com>')
    self.assertEqual(
        ['a@b.com', 'e.g-h@i-j.k-L.com'],
        sendemail._extract_addrs(header_val))

  @mock.patch('google.appengine.api.urlfetch.fetch')
  def test_call_py3_task_handler(self, mock_fetch):
    """Our py2 code can make a request to our py3 code."""
    mock_response = testing_config_py2.Blank(
        status_code=200, content='mock content')
    mock_fetch.return_value = mock_response

    actual = sendemail.call_py3_task_handler('/path', {'a': 1})

    self.assertEqual(mock_response, actual)
    mock_fetch.assert_called_once_with(
        url='http://localhost:8080/path', method=urlfetch.POST,
        payload=b'{"a": 1}', follow_redirects=False)


def MakeMessage(header_list, body):
  """Convenience function to make an email.message.Message."""
  msg = email.message.Message()
  for key, value in header_list:
    msg[key] = value
  msg.set_payload(body)
  return msg


HEADER_LINES = [
    ('X-Original-From', 'user@example.com'),
    ('From', 'mailing-list@example.com'),
    ('To', settings.INBOUND_EMAIL_ADDR),
    ('Cc', 'other@chromium.org'),
    ('Subject', 'Intent to Ship: Featurename'),
    ('In-Reply-To', 'fake message id'),
    ]


class InboundEmailHandlerTest(unittest.TestCase):

  def test_handle_incoming_mail__wrong_to_addr(self):
    """Reject the email if the app was not on the To: line."""
    with sendemail.app.test_request_context('/_ah/mail/other@example.com'):
      actual = sendemail.handle_incoming_mail('other@example.com')

    self.assertEqual(
        {'message': 'Wrong address'},
        actual)

  def test_handle_incoming_mail__too_big(self):
    """Reject the incoming email if it is huge."""
    data = b'x' * sendemail.MAX_BODY_SIZE + b' is too big'

    with sendemail.app.test_request_context(
        '/_ah/mail/%s' % settings.INBOUND_EMAIL_ADDR, data=data):
      actual = sendemail.handle_incoming_mail(settings.INBOUND_EMAIL_ADDR)

    self.assertEqual(
        {'message': 'Too big'},
        actual)

  @mock.patch('sendemail.get_incoming_message')
  def test_handle_incoming_mail__junk_mail(self, mock_get_incoming_message):
    """Reject the incoming email if it has the wrong precedence header."""
    for precedence in ['Bulk', 'Junk']:
      msg = MakeMessage(
          HEADER_LINES + [('Precedence', precedence)],
          'I am on vacation!')
      mock_get_incoming_message.return_value = msg

      with sendemail.app.test_request_context(
          '/_ah/mail/%s' % settings.INBOUND_EMAIL_ADDR):
        actual = sendemail.handle_incoming_mail(settings.INBOUND_EMAIL_ADDR)

      self.assertEqual(
          {'message': 'Wrong precedence'},
          actual)

  @mock.patch('sendemail.get_incoming_message')
  def test_handle_incoming_mail__unclear_from(self, mock_get_incoming_message):
    """Reject the incoming email if it we cannot parse the From: line."""
    msg = MakeMessage([], 'Guess who this is')
    mock_get_incoming_message.return_value = msg

    with sendemail.app.test_request_context(
        '/_ah/mail/%s' % settings.INBOUND_EMAIL_ADDR):
      actual = sendemail.handle_incoming_mail(settings.INBOUND_EMAIL_ADDR)

    self.assertEqual(
        {'message': 'Missing From'},
        actual)

  @mock.patch('sendemail.call_py3_task_handler')
  @mock.patch('sendemail.get_incoming_message')
  def test_handle_incoming_mail__normal(
      self, mock_get_incoming_message, mock_call_py3):
    """A valid incoming email is handed off to py3 code."""
    msg = MakeMessage(HEADER_LINES, 'Please review')
    mock_get_incoming_message.return_value = msg
    mock_call_py3.return_value = testing_config_py2.Blank(status_code=200)

    with sendemail.app.test_request_context(
        '/_ah/mail/%s' % settings.INBOUND_EMAIL_ADDR):
      actual = sendemail.handle_incoming_mail(settings.INBOUND_EMAIL_ADDR)

    self.assertEqual({'message': 'Done'}, actual)
    expected_task_dict = {
      'to_addr': settings.INBOUND_EMAIL_ADDR,
      'from_addr': 'user@example.com',
      'subject': 'Intent to Ship: Featurename',
      'in_reply_to': 'fake message id',
      'body': 'Please review',
    }
    mock_call_py3.assert_called_once_with(
        '/tasks/detect-intent', expected_task_dict)

  @mock.patch('sendemail.call_py3_task_handler')
  @mock.patch('sendemail.get_incoming_message')
  def test_handle_incoming_mail__fallback_to_mailing_list(
      self, mock_get_incoming_message, mock_call_py3):
    """If there is no personal X-Original-From, use the mailing list From:."""
    msg = MakeMessage(HEADER_LINES, 'Please review')
    del msg['X-Original-From']
    mock_get_incoming_message.return_value = msg
    mock_call_py3.return_value = testing_config_py2.Blank(status_code=200)

    with sendemail.app.test_request_context(
        '/_ah/mail/%s' % settings.INBOUND_EMAIL_ADDR):
      actual = sendemail.handle_incoming_mail(settings.INBOUND_EMAIL_ADDR)

    self.assertEqual({'message': 'Done'}, actual)
    expected_task_dict = {
      'to_addr': settings.INBOUND_EMAIL_ADDR,
      'from_addr': 'mailing-list@example.com',
      'subject': 'Intent to Ship: Featurename',
      'in_reply_to': 'fake message id',
      'body': 'Please review',
    }
    mock_call_py3.assert_called_once_with(
        '/tasks/detect-intent', expected_task_dict)
