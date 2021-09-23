


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
import testing_config  # Must be imported before the module under test.

import flask
import mock
import werkzeug.exceptions  # Flask HTTP stuff.
from google.cloud import ndb

from framework import users

from internals import models
from internals import notifier
import settings


class EmailFormattingTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = models.Feature(
        name='feature one', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1,
        created_by=ndb.User(
            email='creator@example.com', _auth_domain='gmail.com'),
        updated_by=ndb.User(
            email='editor@example.com', _auth_domain='gmail.com'),
        blink_components=['Blink'])
    self.feature_1.put()
    self.component_1 = models.BlinkComponent(name='Blink')
    self.component_1.put()
    self.owner_1 = models.FeatureOwner(
        name='owner_1', email='owner_1@example.com',
        primary_blink_components=[self.component_1.key])
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
        created_by=ndb.User(
            email='creator@example.com', _auth_domain='gmail.com'),
        updated_by=ndb.User(
            email='editor@example.com', _auth_domain='gmail.com'),
        blink_components=['Blink'])
    self.feature_2.put()

  def tearDown(self):
    self.feature_1.key.delete()
    self.feature_2.key.delete()

  def test_format_email_body__new(self):
    """We generate an email body for new features."""
    body_html = notifier.format_email_body(
        False, self.feature_1, [])
    self.assertIn('Blink', body_html)
    self.assertIn('creator@example.com added', body_html)
    self.assertIn('www.chromestatus.com/feature/%d' % self.feature_1.key.integer_id(),
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
    self.assertIn('www.chromestatus.com/feature/%d' % self.feature_1.key.integer_id(),
                  body_html)
    self.assertIn('test old value', body_html)
    self.assertIn('test new value', body_html)

  def test_accumulate_reasons(self):
    """We can accumulate lists of reasons why we sent a message to a user."""
    addr_reasons = collections.defaultdict(list)

    # Adding an empty list of users
    notifier.accumulate_reasons(addr_reasons, [], 'a reason')
    self.assertEqual({}, addr_reasons)

    # Adding some users builds up a bigger reason dictionary.
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

    # We can also add email addresses that are not users.
    notifier.accumulate_reasons(
        addr_reasons, ['mailing-list@example.com'], 'third reason')
    self.assertEqual(
        {'owner_1@example.com': ['a reason', 'another reason'],
         'watcher_1@example.com': ['another reason'],
         'mailing-list@example.com': ['third reason'],
        },
        addr_reasons)

  def test_convert_reasons_to_task__no_reasons(self):
    with self.assertRaises(AssertionError):
      notifier.convert_reasons_to_task('addr', [], 'html', 'subject')

  def test_convert_reasons_to_task__normal(self):
    actual = notifier.convert_reasons_to_task(
        'addr', ['reason 1', 'reason 2'], 'html', 'subject')
    self.assertCountEqual(
        ['to', 'subject', 'html'],
        list(actual.keys()))
    self.assertEqual('addr', actual['to'])
    self.assertEqual('subject', actual['subject'])
    self.assertIn('html', actual['html'])
    self.assertIn('reason 1', actual['html'])
    self.assertIn('reason 2', actual['html'])

  def test_apply_subscription_rules__relevant_match(self):
    """When a feature and change match a rule, a reason is returned."""
    self.feature_1.shipped_android_milestone = 88
    changes = [{'prop_name': 'shipped_android_milestone'}]

    actual = notifier.apply_subscription_rules(self.feature_1, changes)

    self.assertEqual(
        {notifier.WEBVIEW_RULE_REASON: notifier.WEBVIEW_RULE_ADDRS},
        actual)

  def test_apply_subscription_rules__irrelevant_match(self):
    """When a feature matches, but the change is not relevant => skip."""
    self.feature_1.shipped_android_milestone = 88
    changes = [{'prop_name': 'some_other_field'}]  # irrelevant changesa

    actual = notifier.apply_subscription_rules(self.feature_1, changes)

    self.assertEqual({}, actual)

  def test_apply_subscription_rules__non_match(self):
    """When a feature is not a match => skip."""
    changes = [{'prop_name': 'shipped_android_milestone'}]

    # No milestones of any kind set.
    actual = notifier.apply_subscription_rules(self.feature_1, changes)
    self.assertEqual({}, actual)

    # Webview is also set
    self.feature_1.shipped_android_milestone = 88
    self.feature_1.shipped_webview_milestone = 89
    actual = notifier.apply_subscription_rules(self.feature_1, changes)
    self.assertEqual({}, actual)

  @mock.patch('internals.notifier.format_email_body')
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

  @mock.patch('internals.notifier.format_email_body')
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

  @mock.patch('internals.notifier.format_email_body')
  def test_make_email_tasks__starrer(self, mock_f_e_b):
    """We send email to users who starred the feature."""
    mock_f_e_b.return_value = 'mock body html'
    notifier.FeatureStar.set_star(
        'starrer_1@example.com', self.feature_1.key.integer_id())
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


  @mock.patch('internals.notifier.format_email_body')
  def test_make_email_tasks__starrer_unsubscribed(self, mock_f_e_b):
    """We don't email users who starred the feature but opted out."""
    mock_f_e_b.return_value = 'mock body html'
    starrer_2_pref = models.UserPref(
        email='starrer_2@example.com',
        notify_as_starrer=False)
    starrer_2_pref.put()
    notifier.FeatureStar.set_star(
        'starrer_2@example.com', self.feature_2.key.integer_id())
    actual_tasks = notifier.make_email_tasks(
        self.feature_2, True, self.changes)
    self.assertEqual(2, len(actual_tasks))
    # Note: There is no starrer_task.
    owner_task, watcher_task = actual_tasks
    self.assertEqual('owner_1@example.com', owner_task['to'])
    self.assertEqual('watcher_1@example.com', watcher_task['to'])
    mock_f_e_b.assert_called_once_with(
        True, self.feature_2, self.changes)


class FeatureStarTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = models.Feature(
        name='feature one', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1)
    self.feature_1.put()
    self.feature_2 = models.Feature(
        name='feature two', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1)
    self.feature_2.put()
    self.feature_3 = models.Feature(
        name='feature three', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1)
    self.feature_3.put()

  def tearDown(self):
    self.feature_1.key.delete()
    self.feature_2.key.delete()
    self.feature_3.key.delete()

  def test_get_star__no_existing(self):
    """User has never starred the given feature."""
    email = 'user1@example.com'
    feature_id = self.feature_1.key.integer_id()
    actual = notifier.FeatureStar.get_star(email, feature_id)
    self.assertEqual(None, actual)

  def test_get_and_set_star(self):
    """User can star and unstar a feature."""
    email = 'user2@example.com'
    feature_id = self.feature_1.key.integer_id()
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
    """User has starred three features."""
    email = 'user5@example.com'
    feature_1_id = self.feature_1.key.integer_id()
    feature_2_id = self.feature_2.key.integer_id()
    feature_3_id = self.feature_3.key.integer_id()
    # Note intermixed order
    notifier.FeatureStar.set_star(email, feature_1_id)
    notifier.FeatureStar.set_star(email, feature_3_id)
    notifier.FeatureStar.set_star(email, feature_2_id)

    actual = notifier.FeatureStar.get_user_stars(email)
    self.assertEqual(
        sorted([feature_1_id, feature_2_id, feature_3_id],
                      reverse=True),
        actual)

  def test_get_feature_starrers__no_stars(self):
    """No user has starred the given feature."""
    feature_1_id = self.feature_1.key.integer_id()
    actual = notifier.FeatureStar.get_feature_starrers(feature_1_id)
    self.assertEqual([], actual)

  def test_get_feature_starrers__some_starrers(self):
    """Two users have starred the given feature."""
    app_user_1 = models.AppUser(email='user16@example.com')
    app_user_1.put()
    app_user_2 = models.AppUser(email='user17@example.com')
    app_user_2.put()
    feature_1_id = self.feature_1.key.integer_id()
    notifier.FeatureStar.set_star(app_user_1.email, feature_1_id)
    notifier.FeatureStar.set_star(app_user_2.email, feature_1_id)

    actual = notifier.FeatureStar.get_feature_starrers(feature_1_id)
    self.assertCountEqual(
        [app_user_1.email, app_user_2.email],
        [au.email for au in actual])
