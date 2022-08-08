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
from unittest import mock
import werkzeug.exceptions  # Flask HTTP stuff.
from google.cloud import ndb

from framework import users

from internals import approval_defs
from internals import models
from internals import notifier
import settings


class EmailFormattingTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = models.Feature(
        name='feature one', summary='sum', owner=['feature_owner@example.com'],
        ot_milestone_desktop_start=100,
        editors=['feature_editor@example.com', 'owner_1@example.com'],
        category=1, visibility=1, standardization=1, web_dev_views=1,
        impl_status_chrome=1, created_by=ndb.User(
            email='creator1@gmail.com', _auth_domain='gmail.com'),
        updated_by=ndb.User(
            email='editor1@gmail.com', _auth_domain='gmail.com'),
        blink_components=['Blink'])
    self.feature_1.put()
    self.component_1 = models.BlinkComponent(name='Blink')
    self.component_1.put()
    self.component_owner_1 = models.FeatureOwner(
        name='owner_1', email='owner_1@example.com',
        primary_blink_components=[self.component_1.key])
    self.component_owner_1.put()
    self.watcher_1 = models.FeatureOwner(
        name='watcher_1', email='watcher_1@example.com',
        watching_all_features=True)
    self.watcher_1.put()
    self.changes = [dict(prop_name='test_prop', new_val='test new value',
                    old_val='test old value')]
    self.feature_2 = models.Feature(
        name='feature two', summary='sum', owner=['feature_owner@example.com'],
        editors=['feature_editor@example.com', 'owner_1@example.com'],
        category=1, visibility=1, standardization=1, web_dev_views=1,
        impl_status_chrome=1, created_by=ndb.User(
            email='creator2@example.com', _auth_domain='gmail.com'),
        updated_by=ndb.User(
            email='editor2@example.com', _auth_domain='gmail.com'),
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
    self.assertIn('creator1@gmail.com added', body_html)
    self.assertIn('chromestatus.com/feature/%d' %
                  self.feature_1.key.integer_id(),
                  body_html)
    self.assertNotIn('watcher_1,', body_html)

  def test_format_email_body__update_no_changes(self):
    """We don't crash if the change list is emtpy."""
    body_html = notifier.format_email_body(
        True, self.feature_1, [])
    self.assertIn('Blink', body_html)
    self.assertIn('editor1@gmail.com updated', body_html)
    self.assertNotIn('watcher_1,', body_html)

  def test_format_email_body__update_with_changes(self):
    """We generate an email body for an updated feature."""
    body_html = notifier.format_email_body(
        True, self.feature_1, self.changes)
    self.assertIn('test_prop', body_html)
    self.assertIn('chromestatus.com/feature/%d' %
                  self.feature_1.key.integer_id(),
                  body_html)
    self.assertIn('test old value', body_html)
    self.assertIn('test new value', body_html)

  def test_format_email_body__mozdev_links(self):
    """We generate an email body with links to developer.mozilla.org."""
    self.feature_1.doc_links = ['https://developer.mozilla.org/look-here']
    body_html = notifier.format_email_body(
        True, self.feature_1, self.changes)
    self.assertIn('look-here', body_html)

    self.feature_1.doc_links = [
        'https://hacker-site.org/developer.mozilla.org/look-here']
    body_html = notifier.format_email_body(
        True, self.feature_1, self.changes)
    self.assertNotIn('look-here', body_html)

  def test_accumulate_reasons(self):
    """We can accumulate lists of reasons why we sent a message to a user."""
    addr_reasons = collections.defaultdict(list)

    # Adding an empty list of users
    notifier.accumulate_reasons(addr_reasons, [], 'a reason')
    self.assertEqual({}, addr_reasons)

    # Adding some users builds up a bigger reason dictionary.
    notifier.accumulate_reasons(addr_reasons, [self.component_owner_1],
                                'a reason')
    self.assertEqual(
        {'owner_1@example.com': ['a reason']},
        addr_reasons)

    notifier.accumulate_reasons(
        addr_reasons, [self.component_owner_1, self.watcher_1], 'another reason')
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
      notifier.convert_reasons_to_task(
          'addr', [], 'html', 'subject', 'triggerer')

  def test_convert_reasons_to_task__normal(self):
    actual = notifier.convert_reasons_to_task(
        'addr', ['reason 1', 'reason 2'], 'html', 'subject',
        'triggerer@example.com')
    self.assertCountEqual(
        ['to', 'subject', 'html', 'reply_to'],
        list(actual.keys()))
    self.assertEqual('addr', actual['to'])
    self.assertEqual('subject', actual['subject'])
    self.assertEqual(None, actual['reply_to'])  # Lacks perm to reply.
    self.assertIn('html', actual['html'])
    self.assertIn('reason 1', actual['html'])
    self.assertIn('reason 2', actual['html'])

  def test_convert_reasons_to_task__can_reply(self):
    """If the user is allowed to reply, set reply_to to the triggerer."""
    actual = notifier.convert_reasons_to_task(
        'user@chromium.org', ['reason 1', 'reason 2'], 'html', 'subject',
        'triggerer@example.com')
    self.assertCountEqual(
        ['to', 'subject', 'html', 'reply_to'],
        list(actual.keys()))
    self.assertEqual('user@chromium.org', actual['to'])
    self.assertEqual('subject', actual['subject'])
    self.assertEqual('triggerer@example.com', actual['reply_to'])

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
    self.assertEqual(4, len(actual_tasks))
    (feature_editor_task, feature_owner_task, component_owner_task,
     watcher_task) = actual_tasks

    # Notification to feature owner.
    self.assertEqual('feature_owner@example.com', feature_owner_task['to'])
    self.assertEqual('new feature: feature one', feature_owner_task['subject'])
    self.assertIn('mock body html', feature_owner_task['html'])
    self.assertIn('<li>You are listed as an owner of this feature</li>',
      feature_owner_task['html'])

    # Notification to feature editor.
    self.assertEqual('new feature: feature one', feature_editor_task['subject'])
    self.assertIn('mock body html', feature_editor_task['html'])
    self.assertIn('<li>You are listed as an editor of this feature</li>',
      feature_editor_task['html'])
    self.assertEqual('feature_editor@example.com', feature_editor_task['to'])

    # Notification to component owner.
    self.assertEqual('new feature: feature one', component_owner_task['subject'])
    self.assertIn('mock body html', component_owner_task['html'])
    # Component owner is also a feature editor and should have both reasons.
    self.assertIn('<li>You are an owner of this feature\'s component</li>\n'
                  '<li>You are listed as an editor of this feature</li>',
      component_owner_task['html'])
    self.assertEqual('owner_1@example.com', component_owner_task['to'])

    # Notification to feature change watcher.
    self.assertEqual('new feature: feature one', watcher_task['subject'])
    self.assertIn('mock body html', watcher_task['html'])
    self.assertIn('<li>You are watching all feature changes</li>',
      watcher_task['html'])
    self.assertEqual('watcher_1@example.com', watcher_task['to'])

    mock_f_e_b.assert_called_once_with(
        False, self.feature_1, [])

  @mock.patch('internals.notifier.format_email_body')
  def test_make_email_tasks__update(self, mock_f_e_b):
    """We send email to component owners and subscribers for edits."""
    mock_f_e_b.return_value = 'mock body html'
    actual_tasks = notifier.make_email_tasks(
        self.feature_1, True, self.changes)
    self.assertEqual(4, len(actual_tasks))
    (feature_editor_task, feature_owner_task, component_owner_task,
     watcher_task) = actual_tasks

    # Notification to feature owner.
    self.assertEqual('feature_owner@example.com', feature_owner_task['to'])
    self.assertEqual('updated feature: feature one',
      feature_owner_task['subject'])
    self.assertIn('mock body html', feature_owner_task['html'])
    self.assertIn('<li>You are listed as an owner of this feature</li>',
      feature_owner_task['html'])

    # Notification to feature editor.
    self.assertEqual('updated feature: feature one',
      feature_editor_task['subject'])
    self.assertIn('mock body html', feature_editor_task['html'])
    self.assertIn('<li>You are listed as an editor of this feature</li>',
      feature_editor_task['html'])
    self.assertEqual('feature_editor@example.com', feature_editor_task['to'])

    # Notification to component owner.
    self.assertEqual('updated feature: feature one',
      component_owner_task['subject'])
    self.assertIn('mock body html', component_owner_task['html'])
    # Component owner is also a feature editor and should have both reasons.
    self.assertIn('<li>You are an owner of this feature\'s component</li>\n'
                  '<li>You are listed as an editor of this feature</li>',
      component_owner_task['html'])
    self.assertEqual('owner_1@example.com', component_owner_task['to'])

    # Notification to feature change watcher.
    self.assertEqual('updated feature: feature one', watcher_task['subject'])
    self.assertIn('mock body html', watcher_task['html'])
    self.assertIn('<li>You are watching all feature changes</li>',
      watcher_task['html'])
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
    self.assertEqual(5, len(actual_tasks))
    (feature_editor_task, feature_owner_task, component_owner_task,
     starrer_task, watcher_task) = actual_tasks

    # Notification to feature owner.
    self.assertEqual('feature_owner@example.com', feature_owner_task['to'])
    self.assertEqual('updated feature: feature one',
      feature_owner_task['subject'])
    self.assertIn('mock body html', feature_owner_task['html'])
    self.assertIn('<li>You are listed as an owner of this feature</li>',
      feature_owner_task['html'])

    # Notification to feature editor.
    self.assertEqual('updated feature: feature one',
      feature_editor_task['subject'])
    self.assertIn('mock body html', feature_editor_task['html'])
    self.assertIn('<li>You are listed as an editor of this feature</li>',
      feature_editor_task['html'])
    self.assertEqual('feature_editor@example.com', feature_editor_task['to'])

    # Notification to component owner.
    self.assertEqual('updated feature: feature one',
      component_owner_task['subject'])
    self.assertIn('mock body html', component_owner_task['html'])
    # Component owner is also a feature editor and should have both reasons.
    self.assertIn('<li>You are an owner of this feature\'s component</li>\n'
                  '<li>You are listed as an editor of this feature</li>',
      component_owner_task['html'])
    self.assertEqual('owner_1@example.com', component_owner_task['to'])

    # Notification to feature starrer.
    self.assertEqual('updated feature: feature one', starrer_task['subject'])
    self.assertIn('mock body html', starrer_task['html'])
    self.assertIn('<li>You starred this feature</li>',
      starrer_task['html'])
    self.assertEqual('starrer_1@example.com', starrer_task['to'])

    # Notification to feature change watcher.
    self.assertEqual('updated feature: feature one', watcher_task['subject'])
    self.assertIn('mock body html', watcher_task['html'])
    self.assertIn('<li>You are watching all feature changes</li>',
      watcher_task['html'])
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
    self.assertEqual(4, len(actual_tasks))
    # Note: There is no starrer_task.
    (feature_editor_task, feature_owner_task, component_owner_task,
     watcher_task) = actual_tasks
    self.assertEqual('feature_editor@example.com', feature_editor_task['to'])
    self.assertEqual('feature_owner@example.com', feature_owner_task['to'])
    self.assertEqual('owner_1@example.com', component_owner_task['to'])
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


class MockResponse:
  """Creates a fake response object for testing."""
  def __init__(self, status_code=200, text='{}'):
    self.status_code = status_code
    self.text = text


class FeatureAccuracyHandlerTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = models.Feature(
        name='feature one', summary='sum', owner=['feature_owner@example.com'],
        category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1,
        ot_milestone_desktop_start=100)
    self.feature_1.put()
    self.feature_2 = models.Feature(
        name='feature two', summary='sum',
        owner=['owner_1@example.com', 'owner_2@example.com'],
        category=1, visibility=1, standardization=1,
        web_dev_views=1, impl_status_chrome=1, shipped_milestone=150)
    self.feature_2.put()
    self.feature_3 = models.Feature(
        name='feature three', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1)
    self.feature_3.put()
  
  def tearDown(self):
    self.feature_1.key.delete()
    self.feature_2.key.delete()
    self.feature_3.key.delete()

  @mock.patch('requests.get')
  def test_determine_features_to_notify__no_features(self, mock_get):
    mock_return = MockResponse(text='{"mstones":[{"mstone": "40"}]}')
    mock_get.return_value = mock_return
    accuracy_notifier = notifier.FeatureAccuracyHandler()
    result = accuracy_notifier.get_template_data()
    expected = {'message': '0 email(s) sent or logged.'}
    self.assertEqual(result, expected)
  
  @mock.patch('requests.get')
  def test_determine_features_to_notify__valid_features(self, mock_get):
    mock_return = MockResponse(text='{"mstones":[{"mstone": "100"}]}')
    mock_get.return_value = mock_return
    accuracy_notifier = notifier.FeatureAccuracyHandler()
    result = accuracy_notifier.get_template_data()
    expected = {'message': '1 email(s) sent or logged.'}
    self.assertEqual(result, expected)

  @mock.patch('requests.get')
  def test_determine_features_to_notify__multiple_owners(self, mock_get):
    mock_return = MockResponse(text='{"mstones":[{"mstone": "148"}]}')
    mock_get.return_value = mock_return
    accuracy_notifier = notifier.FeatureAccuracyHandler()
    result = accuracy_notifier.get_template_data()
    expected = {'message': '2 email(s) sent or logged.'}
    self.assertEqual(result, expected)


class FunctionsTest(testing_config.CustomTestCase):

  def setUp(self):
    quoted_msg_id = 'xxx%3Dyyy%40mail.gmail.com'
    impl_url = notifier.BLINK_DEV_ARCHIVE_URL_PREFIX + '123' + quoted_msg_id
    expr_url = notifier.TEST_ARCHIVE_URL_PREFIX + '456' + quoted_msg_id
    self.feature_1 = models.Feature(
        name='feature one', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1,
        intent_to_implement_url=impl_url,
        intent_to_experiment_url=expr_url)
    # Note: There is no need to put() it in the datastore.

  def test_get_thread_id__normal(self):
    """We can select the correct approval thread field of a feature."""
    self.assertEqual(
        '123xxx=yyy@mail.gmail.com',
        notifier.get_thread_id(
            self.feature_1, approval_defs.PrototypeApproval))
    self.assertEqual(
        '456xxx=yyy@mail.gmail.com',
        notifier.get_thread_id(
            self.feature_1, approval_defs.ExperimentApproval))
    self.assertEqual(
        None,
        notifier.get_thread_id(
            self.feature_1, approval_defs.ShipApproval))

  def test_get_existing_thread_subject__none(self):
    """If a feature does not store an existing thread subject, use None."""
    self.assertIsNone(notifier.get_existing_thread_subject(
        self.feature_1, approval_defs.PrototypeApproval))

  def test_get_existing_thread_subject__found(self):
    """If a feature does not store an existing thread subject, use it."""
    self.feature_1.intent_to_ship_subject_line = (
        'Intent to really ship: feature one')
    actual = notifier.get_existing_thread_subject(
        self.feature_1, approval_defs.ShipApproval)
    self.assertEqual('Intent to really ship: feature one', actual)

  def test_get_existing_thread_subject__unknown(self):
    """Raise ValueError if called with an unknown approval field."""
    PivotApproval = approval_defs.ApprovalFieldDef(
        'Intent to Pivot',
        'One API Owner must approve your intent',
        99, approval_defs.ONE_LGTM, [])
    with self.assertRaises(ValueError):
      notifier.get_existing_thread_subject(
          self.feature_1, PivotApproval)

  def test_generate_thread_subject__normal(self):
    """Most intents just use the name of the intent."""
    self.assertEqual(
        'Intent to Prototype: feature one',
        notifier.generate_thread_subject(
            self.feature_1, approval_defs.PrototypeApproval))
    self.assertEqual(
        'Intent to Experiment: feature one',
        notifier.generate_thread_subject(
            self.feature_1, approval_defs.ExperimentApproval))
    self.assertEqual(
        'Intent to Extend Experiment: feature one',
        notifier.generate_thread_subject(
            self.feature_1, approval_defs.ExtendExperimentApproval))
    self.assertEqual(
        'Intent to Ship: feature one',
        notifier.generate_thread_subject(
            self.feature_1, approval_defs.ShipApproval))

  def test_generate_thread_subject__deprecation(self):
    """Deprecation intents use different subjects for most intents."""
    self.feature_1.feature_type = models.FEATURE_TYPE_DEPRECATION_ID
    self.assertEqual(
        'Intent to Deprecate and Remove: feature one',
        notifier.generate_thread_subject(
            self.feature_1, approval_defs.PrototypeApproval))
    self.assertEqual(
        'Request for Deprecation Trial: feature one',
        notifier.generate_thread_subject(
            self.feature_1, approval_defs.ExperimentApproval))
    self.assertEqual(
        'Intent to Extend Deprecation Trial: feature one',
        notifier.generate_thread_subject(
            self.feature_1, approval_defs.ExtendExperimentApproval))
    self.assertEqual(
        'Intent to Ship: feature one',
        notifier.generate_thread_subject(
            self.feature_1, approval_defs.ShipApproval))


  def test_get_thread_id__trailing_junk(self):
    """We can select the correct approval thread field of a feature."""
    self.feature_1.intent_to_implement_url += '?param=val#anchor'
    self.assertEqual(
        '123xxx=yyy@mail.gmail.com',
        notifier.get_thread_id(
            self.feature_1, approval_defs.PrototypeApproval))
