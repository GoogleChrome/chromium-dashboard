# Copyright 2020 Google Inc.
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
import unittest
import testing_config  # Must be imported before the module under test.

import mock
import webapp2
from webob import exc

from google.appengine.ext import db
from google.appengine.api import mail
from google.appengine.api import users

import models
import notifier
import settings


class EmailFormattingTest(unittest.TestCase):

  def setUp(self):
    self.feature_1 = models.Feature(
        name='feature one', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1,
        created_by=users.User('creator@example.com'),
        updated_by=users.User('editor@example.com'),
        blink_components=['Blink'])
    self.feature_1.put()
    self.component_1 = models.BlinkComponent(name='Blink')
    self.component_1.put()
    self.owner_1 = models.FeatureOwner(
        name='owner_1', email='owner_1@example.com',
        primary_blink_components=[self.component_1.key()])
    self.owner_1.put()
    self.watcher_1 = models.FeatureOwner(
        name='watcher_1', email='watcher_1@example.com',
        watching_all_features=True)
    self.watcher_1.put()
    self.changes = [dict(prop_name='test_prop', new_val='test new value',
                    old_val='test old value')]
    self.feature_2 = models.Feature(
        name='feature two', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1,
        created_by=users.User('creator@example.com'),
        updated_by=users.User('editor@example.com'),
        blink_components=['Blink'])
    self.feature_2.put()

  def test_format_email_body__new(self):
    """We generate an email body for new features."""
    body_html = notifier.format_email_body(
        False, self.feature_1, [])
    self.assertIn('Blink', body_html)
    self.assertIn('creator@example.com added', body_html)
    self.assertIn('www.chromestatus.com/feature/%d' % self.feature_1.key().id(),
                  body_html)
    self.assertNotIn('watcher_1,', body_html)

  def test_format_email_body__update_no_changes(self):
    """We don't crash if the change list is emtpy."""
    body_html = notifier.format_email_body(
        True, self.feature_1, [])
    self.assertIn('Blink', body_html)
    self.assertIn('editor@example.com updated', body_html)
    self.assertNotIn('watcher_1,', body_html)

  def test_format_email_body__update_with_changes(self):
    """We generate an email body for an updated feature."""
    body_html = notifier.format_email_body(
        True, self.feature_1, self.changes)
    self.assertIn('test_prop', body_html)
    self.assertIn('www.chromestatus.com/feature/%d' % self.feature_1.key().id(),
                  body_html)
    self.assertIn('test old value', body_html)
    self.assertIn('test new value', body_html)

  def test_accumulate_reasons(self):
    """We can accumulate lists of reasons why we sent a message to a user."""
    addr_reasons = collections.defaultdict(list)
    notifier.accumulate_reasons(addr_reasons, [], 'a reason')
    self.assertEqual({}, addr_reasons)

    notifier.accumulate_reasons(addr_reasons, [self.owner_1], 'a reason')
    self.assertEqual(
        {'owner_1@example.com': ['a reason']},
        addr_reasons)

    notifier.accumulate_reasons(
        addr_reasons, [self.owner_1, self.watcher_1], 'another reason')
    self.assertEqual(
        {'owner_1@example.com': ['a reason', 'another reason'],
         'watcher_1@example.com': ['another reason'],
        },
        addr_reasons)

  def test_convert_reasons_to_task__no_reasons(self):
    with self.assertRaises(AssertionError):
      notifier.convert_reasons_to_task('addr', [], 'html', 'subject')

  def test_convert_reasons_to_task__normal(self):
    actual = notifier.convert_reasons_to_task(
        'addr', ['reason 1', 'reason 2'], 'html', 'subject')
    self.assertItemsEqual(
        ['to', 'subject', 'html'],
        actual.keys())
    self.assertEqual('addr', actual['to'])
    self.assertEqual('subject', actual['subject'])
    self.assertIn('html', actual['html'])
    self.assertIn('reason 1', actual['html'])
    self.assertIn('reason 2', actual['html'])

  @mock.patch('notifier.format_email_body')
  def test_make_email_tasks__new(self, mock_f_e_b):
    """We send email to component owners and subscribers for new features."""
    mock_f_e_b.return_value = 'mock body html'
    actual_tasks = notifier.make_email_tasks(
        self.feature_1, is_update=False, changes=[])
    self.assertEqual(2, len(actual_tasks))
    owner_task, watcher_task = actual_tasks
    self.assertEqual('new feature: feature one', owner_task['subject'])
    self.assertIn('mock body html', owner_task['html'])
    self.assertEqual('owner_1@example.com', owner_task['to'])
    self.assertEqual('new feature: feature one', watcher_task['subject'])
    self.assertIn('mock body html', watcher_task['html'])
    self.assertEqual('watcher_1@example.com', watcher_task['to'])
    mock_f_e_b.assert_called_once_with(
        False, self.feature_1, [])

  @mock.patch('notifier.format_email_body')
  def test_make_email_tasks__update(self, mock_f_e_b):
    """We send email to component owners and subscribers for edits."""
    mock_f_e_b.return_value = 'mock body html'
    actual_tasks = notifier.make_email_tasks(
        self.feature_1, True, self.changes)
    self.assertEqual(2, len(actual_tasks))
    owner_task, watcher_task = actual_tasks
    self.assertEqual('updated feature: feature one', owner_task['subject'])
    self.assertIn('mock body html', owner_task['html'])
    self.assertEqual('owner_1@example.com', owner_task['to'])
    self.assertEqual('updated feature: feature one', watcher_task['subject'])
    self.assertIn('mock body html', watcher_task['html'])
    self.assertEqual('watcher_1@example.com', watcher_task['to'])
    mock_f_e_b.assert_called_once_with(
        True, self.feature_1, self.changes)

  @mock.patch('notifier.format_email_body')
  def test_make_email_tasks__starrer(self, mock_f_e_b):
    """We send email to users who starred the feature."""
    mock_f_e_b.return_value = 'mock body html'
    notifier.FeatureStar.set_star(
        'starrer_1@example.com', self.feature_1.key().id())
    actual_tasks = notifier.make_email_tasks(
        self.feature_1, True, self.changes)
    self.assertEqual(3, len(actual_tasks))
    owner_task, starrer_task, watcher_task = actual_tasks
    self.assertEqual('updated feature: feature one', owner_task['subject'])
    self.assertIn('mock body html', owner_task['html'])
    self.assertEqual('owner_1@example.com', owner_task['to'])
    self.assertEqual('starrer_1@example.com', starrer_task['to'])
    self.assertEqual('updated feature: feature one', watcher_task['subject'])
    self.assertIn('mock body html', watcher_task['html'])
    self.assertEqual('watcher_1@example.com', watcher_task['to'])
    mock_f_e_b.assert_called_once_with(
        True, self.feature_1, self.changes)


  @mock.patch('notifier.format_email_body')
  def test_make_email_tasks__starrer_unsubscribed(self, mock_f_e_b):
    """We don't email users who starred the feature but opted out."""
    mock_f_e_b.return_value = 'mock body html'
    starrer_2_pref = models.UserPref(
        email='starrer_2@example.com',
        notify_as_starrer=False)
    starrer_2_pref.put()
    notifier.FeatureStar.set_star(
        'starrer_2@example.com', self.feature_2.key().id())
    actual_tasks = notifier.make_email_tasks(
        self.feature_2, True, self.changes)
    self.assertEqual(2, len(actual_tasks))
    # Note: There is no starrer_task.
    owner_task, watcher_task = actual_tasks
    self.assertEqual('owner_1@example.com', owner_task['to'])
    self.assertEqual('watcher_1@example.com', watcher_task['to'])
    mock_f_e_b.assert_called_once_with(
        True, self.feature_2, self.changes)


class FeatureStarTest(unittest.TestCase):

  def setUp(self):
    self.feature_1 = models.Feature(
        name='feature one', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1)
    self.feature_1.put()
    self.feature_2 = models.Feature(
        name='feature two', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1)
    self.feature_2.put()

  def test_get_star__no_existing(self):
    """User has never starred the given feature."""
    email = 'user1@example.com'
    feature_id = self.feature_1.key().id()
    actual = notifier.FeatureStar.get_star(email, feature_id)
    self.assertEqual(None, actual)

  def test_get_and_set_star(self):
    """User can star and unstar a feature."""
    email = 'user2@example.com'
    feature_id = self.feature_1.key().id()
    notifier.FeatureStar.set_star(email, feature_id)
    actual = notifier.FeatureStar.get_star(email, feature_id)
    self.assertEqual(email, actual.email)
    self.assertEqual(feature_id, actual.feature_id)
    self.assertTrue(actual.starred)
    updated_feature = models.Feature.get_by_id(feature_id)
    self.assertEqual(1, updated_feature.star_count)

    notifier.FeatureStar.set_star(email, feature_id, starred=False)
    actual = notifier.FeatureStar.get_star(email, feature_id)
    self.assertEqual(email, actual.email)
    self.assertEqual(feature_id, actual.feature_id)
    self.assertFalse(actual.starred)
    updated_feature = models.Feature.get_by_id(feature_id)
    self.assertEqual(0, updated_feature.star_count)

  def test_get_user_stars__no_stars(self):
    """User has never starred any features."""
    email = 'user4@example.com'
    actual = notifier.FeatureStar.get_user_stars(email)
    self.assertEqual([], actual)

  def test_get_user_stars__some_stars(self):
    """User has starred two features."""
    email = 'user5@example.com'
    feature_1_id = self.feature_1.key().id()
    feature_2_id = self.feature_2.key().id()
    notifier.FeatureStar.set_star(email, feature_1_id)
    notifier.FeatureStar.set_star(email, feature_2_id)

    actual = notifier.FeatureStar.get_user_stars(email)
    self.assertItemsEqual(
        [feature_1_id, feature_2_id],
        actual)

  def test_get_feature_starrers__no_stars(self):
    """No user has starred the given feature."""
    feature_1_id = self.feature_1.key().id()
    actual = notifier.FeatureStar.get_feature_starrers(feature_1_id)
    self.assertEqual([], actual)

  def test_get_feature_starrers__some_starrers(self):
    """Two users have starred the given feature."""
    app_user_1 = models.AppUser(email='user16@example.com')
    app_user_1.put()
    app_user_2 = models.AppUser(email='user17@example.com')
    app_user_2.put()
    feature_1_id = self.feature_1.key().id()
    notifier.FeatureStar.set_star(app_user_1.email, feature_1_id)
    notifier.FeatureStar.set_star(app_user_2.email, feature_1_id)

    actual = notifier.FeatureStar.get_feature_starrers(feature_1_id)
    self.assertItemsEqual(
        [app_user_1.email, app_user_2.email],
        [au.email for au in actual])


class OutboundEmailHandlerTest(unittest.TestCase):

  def setUp(self):
    self.handler = notifier.OutboundEmailHandler()
    self.handler.request = webapp2.Request.blank('/tasks/outbound-email')
    self.handler.response = webapp2.Response()

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
    self.handler.request.body = json.dumps({
        'to': self.to,
        'subject': self.subject,
        'html': self.html,
        })
    self.handler.post()
    mock_emailmessage_constructor.assert_called_once_with(
        sender=self.sender, to=self.to, subject=self.subject,
        html=self.html)
    mock_message = mock_emailmessage_constructor.return_value
    mock_message.check_initialized.assert_called_once_with()
    mock_message.send.assert_called_once_with()

  @mock.patch('settings.SEND_EMAIL', True)
  @mock.patch('google.appengine.api.mail.EmailMessage')
  def test_post__staging(self, mock_emailmessage_constructor):
    """On cr-status-staging, we send emails to an archive."""
    self.handler.request.body = json.dumps({
        'to': self.to,
        'subject': self.subject,
        'html': self.html,
        })
    self.handler.post()
    expected_to = 'cr-status-staging-emails+user+example.com@google.com'
    mock_emailmessage_constructor.assert_called_once_with(
        sender=self.sender, to=expected_to, subject=self.subject,
        html=self.html)
    mock_message = mock_emailmessage_constructor.return_value
    mock_message.check_initialized.assert_called_once_with()
    mock_message.send.assert_called_once_with()

  @mock.patch('settings.SEND_EMAIL', False)
  @mock.patch('google.appengine.api.mail.EmailMessage')
  def test_post__local(self, mock_emailmessage_constructor):
    """When running locally, we don't actually send emails."""
    self.handler.request.body = json.dumps({
        'to': self.to,
        'subject': self.subject,
        'html': self.html,
        })
    self.handler.post()
    expected_to = 'cr-status-staging-emails+user+example.com@google.com'
    mock_emailmessage_constructor.assert_called_once_with(
        sender=self.sender, to=expected_to, subject=self.subject,
        html=self.html)
    mock_message = mock_emailmessage_constructor.return_value
    mock_message.check_initialized.assert_called_once_with()
    mock_message.send.assert_not_called()


class SetStarHandlerTest(unittest.TestCase):

  def setUp(self):
    self.feature_1 = models.Feature(
        name='feature one', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1)
    self.feature_1.put()
    self.handler = notifier.SetStarHandler()
    self.handler.request = webapp2.Request.blank('/features/star/set')
    self.handler.response = webapp2.Response()

  def test_post__invalid_feature_id(self):
    """We reject star requests that don't have an int featureId."""
    self.handler.request.body = '{}'
    with self.assertRaises(exc.HTTPClientError):
      self.handler.post()

    self.handler.request.body = '{"featureId":"not an int"}'
    with self.assertRaises(exc.HTTPClientError):
      self.handler.post()

  def test_post__feature_id_not_found(self):
    """We reject star requests for features that don't exist."""
    self.handler.request.body = '{"featureId": 999}'
    with self.assertRaises(exc.HTTPClientError):
      self.handler.post()

  def test_post__anon(self):
    """We reject anon star requests."""
    feature_id = self.feature_1.key().id()
    self.handler.request.body = '{"featureId": %d}' % feature_id
    testing_config.ourTestbed.setup_env(
            user_email='', user_id='', overwrite=True)
    with self.assertRaises(exc.HTTPClientError):
      self.handler.post()

  def test_post__duplicate(self):
    """User sends a duplicate request, which should be a no-op."""
    testing_config.ourTestbed.setup_env(
            user_email='user7@example.com',
            user_id='123567890',
            overwrite=True)

    feature_id = self.feature_1.key().id()
    self.handler.request.body = '{"featureId": %d}' % feature_id
    self.handler.post()  # Original request
    updated_feature = models.Feature.get_by_id(feature_id)
    self.assertEqual(1, updated_feature.star_count)
    self.handler.post()  # Duplicate request
    updated_feature = models.Feature.get_by_id(feature_id)
    self.assertEqual(1, updated_feature.star_count)  # Still 1, not 2.

    self.handler.request.body = (
        '{"featureId": %d, "starred": false}' % feature_id)
    self.handler.post()  # Original request
    updated_feature = models.Feature.get_by_id(feature_id)
    self.assertEqual(0, updated_feature.star_count)
    self.handler.post()  # Duplicate request
    updated_feature = models.Feature.get_by_id(feature_id)
    self.assertEqual(0, updated_feature.star_count)  # Still 0, not negative.

  def test_post__unmatched_unstar(self):
    """User tries to unstar feature that they never starred: no-op."""
    testing_config.ourTestbed.setup_env(
            user_email='user8@example.com',
            user_id='123567890',
            overwrite=True)

    feature_id = self.feature_1.key().id()
    # User never stars the feature in the first place.

    self.handler.request.body = (
        '{"featureId": %d, "starred": false}' % feature_id)
    self.handler.post()  # Out-of-step request
    updated_feature = models.Feature.get_by_id(feature_id)
    self.assertEqual(0, updated_feature.star_count)  # Still 0, not negative.

  def test_post__normal(self):
    """User can star and unstar."""
    testing_config.ourTestbed.setup_env(
            user_email='user6@example.com',
            user_id='123567890',
            overwrite=True)

    feature_id = self.feature_1.key().id()
    self.handler.request.body = '{"featureId": %d}' % feature_id
    self.handler.post()
    updated_feature = models.Feature.get_by_id(feature_id)
    self.assertEqual(1, updated_feature.star_count)

    self.handler.request.body = (
        '{"featureId": %d, "starred": false}' % feature_id)
    self.handler.post()
    updated_feature = models.Feature.get_by_id(feature_id)
    self.assertEqual(0, updated_feature.star_count)


class GetUserStarsHandlerTest(unittest.TestCase):

  def setUp(self):
    self.feature_1 = models.Feature(
        name='feature one', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1)
    self.feature_1.put()
    self.handler = notifier.GetUserStarsHandler()
    self.handler.request = webapp2.Request.blank('/features/star/list')
    self.handler.response = webapp2.Response()

  def test_post__anon(self):
    """Anon should always have an empty list of stars."""
    testing_config.ourTestbed.setup_env(
            user_email='', user_id='', overwrite=True)
    self.handler.post()
    self.assertEqual(
        '{"featureIds":[]}',
        self.handler.response.body)

  def test_post__no_stars(self):
    """User has not starred any features."""
    testing_config.ourTestbed.setup_env(
            user_email='user7@example.com',
            user_id='123567890',
            overwrite=True)
    self.handler.post()
    self.assertEqual(
        '{"featureIds":[]}',
        self.handler.response.body)

  def test_post__some_stars(self):
    """User has starred some features."""
    email = 'user8@example.com'
    feature_1_id = self.feature_1.key().id()
    testing_config.ourTestbed.setup_env(
            user_email=email,
            user_id='123567890',
            overwrite=True)
    notifier.FeatureStar.set_star(email, feature_1_id)
    self.handler.post()
    self.assertEqual(
        '{"featureIds":[%d]}' % feature_1_id,
        self.handler.response.body)


class BouncedEmailHandlerTest(unittest.TestCase):

  def setUp(self):
    self.handler = notifier.BouncedEmailHandler()
    self.sender = ('Chromestatus <admin@%s.appspotmail.com>' %
                   settings.APP_ID)
    self.expected_to = settings.BOUNCE_ESCALATION_ADDR
    self.expected_html = 'See subject.  Check logs.'

  @mock.patch('settings.SEND_EMAIL', True)
  @mock.patch('google.appengine.api.mail.EmailMessage')
  def test_receive__user_has_prefs(self, mock_emailmessage_constructor):
    """When we get a bounce, we update the UserPrefs for that user."""
    starrer_3_pref = models.UserPref(
        email='starrer_3@example.com',
        notify_as_starrer=False)
    starrer_3_pref.put()

    bounce_message = testing_config.Blank(
        original=testing_config.Blank(
            get=lambda header: 'starrer_3@example.com'))

    self.handler.receive(bounce_message)

    updated_pref = models.UserPref.get_by_id(starrer_3_pref.key().id())
    self.assertEqual('starrer_3@example.com', updated_pref.email)
    self.assertTrue(updated_pref.bounced)
    self.assertFalse(updated_pref.notify_as_starrer)
    expected_subject = "Mail to 'starrer_3@example.com' bounced"
    mock_emailmessage_constructor.assert_called_once_with(
        sender=self.sender, to=self.expected_to, subject=expected_subject,
        html=self.expected_html)
    mock_message = mock_emailmessage_constructor.return_value
    mock_message.check_initialized.assert_called_once_with()
    mock_message.send.assert_called()

  @mock.patch('settings.SEND_EMAIL', True)
  @mock.patch('google.appengine.api.mail.EmailMessage')
  def test_receive__create_prefs(self, mock_emailmessage_constructor):
    """When we get a bounce, we create the UserPrefs for that user."""
    # Note, no existing UserPref for starrer_4.

    bounce_message = testing_config.Blank(
        original=testing_config.Blank(
            get=lambda header: 'starrer_4@example.com'))

    self.handler.receive(bounce_message)

    prefs_list = models.UserPref.get_prefs_for_emails(
        ['starrer_4@example.com'])
    updated_pref = prefs_list[0]
    self.assertEqual('starrer_4@example.com', updated_pref.email)
    self.assertTrue(updated_pref.bounced)
    self.assertTrue(updated_pref.notify_as_starrer)
    expected_subject = "Mail to 'starrer_4@example.com' bounced"
    mock_emailmessage_constructor.assert_called_once_with(
        sender=self.sender, to=self.expected_to, subject=expected_subject,
        html=self.expected_html)
    mock_message = mock_emailmessage_constructor.return_value
    mock_message.check_initialized.assert_called_once_with()
    mock_message.send.assert_called()
