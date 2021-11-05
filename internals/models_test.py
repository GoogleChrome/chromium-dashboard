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

import testing_config  # Must be imported before the module under test.

import datetime
import mock
from framework import ramcache
# from google.appengine.api import users
from framework import users

from internals import models


class MockQuery(object):

  def __init__(self, result_list):
    self.result_list = result_list

  def fetch(self, *args, **kw):
    return self.result_list


class ModelsFunctionsTest(testing_config.CustomTestCase):

  def test_convert_enum_int_to_string__not_an_enum(self):
    """If the property is not an enum, just use the property value."""
    actual = models.convert_enum_int_to_string(
        'name', 'not an int')
    self.assertEqual('not an int', actual)

    actual = models.convert_enum_int_to_string(
        'unknown property', 'something')
    self.assertEqual('something', actual)

  def test_convert_enum_int_to_string__not_an_int(self):
    """We don't crash or convert when given non-numeric values."""
    actual = models.convert_enum_int_to_string(
        'impl_status_chrome', {'something': 'non-numeric'})
    self.assertEqual(
        {'something': 'non-numeric'},
        actual)

  def test_convert_enum_int_to_string__enum_found(self):
    """We use the human-reable string if it is defined."""
    actual = models.convert_enum_int_to_string(
        'impl_status_chrome', models.NO_ACTIVE_DEV)
    self.assertEqual(
        models.IMPLEMENTATION_STATUS[models.NO_ACTIVE_DEV],
        actual)

  def test_convert_enum_int_to_string__enum_not_found(self):
    """If we somehow don't have an emum string, use the ordinal."""
    actual = models.convert_enum_int_to_string(
        'impl_status_chrome', 99)
    self.assertEqual(99, actual)


  def test_del_none(self):
    d = {}
    self.assertEqual(
        {},
        models.del_none(d))

    d = {1: 'one', 2: None, 3: {33: None}, 4:{44: 44, 45: None}}
    self.assertEqual(
        {1: 'one', 3: {}, 4: {44: 44}},
        models.del_none(d))


class FeatureTest(testing_config.CustomTestCase):

  def setUp(self):
    ramcache.SharedInvalidate.check_for_distributed_invalidation()
    self.feature_2 = models.Feature(
        name='feature b', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=3)
    self.feature_2.put()

    self.feature_1 = models.Feature(
        name='feature a', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=3)
    self.feature_1.put()

    self.feature_4 = models.Feature(
        name='feature d', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=2)
    self.feature_4.put()

    self.feature_3 = models.Feature(
        name='feature c', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=2)
    self.feature_3.put()

  def tearDown(self):
    self.feature_1.key.delete()
    self.feature_2.key.delete()
    self.feature_3.key.delete()
    self.feature_4.key.delete()
    ramcache.flush_all()

  def test_get_all__normal(self):
    """We can retrieve a list of all features with no filter."""
    actual = models.Feature.get_all(update_cache=True)
    names = [f['name'] for f in actual]
    self.assertEqual(
        ['feature c', 'feature d', 'feature a', 'feature b'],
        names)

    self.feature_1.summary = 'revised summary'
    self.feature_1.put()  # Changes updated field.
    actual = models.Feature.get_all(update_cache=True)
    names = [f['name'] for f in actual]
    self.assertEqual(
        ['feature a', 'feature c', 'feature d', 'feature b'],
        names)

  def test_get_all__category(self):
    """We can retrieve a list of all features of a given category."""
    actual = models.Feature.get_all(
        filterby=('category', models.CSS), update_cache=True)
    names = [f['name'] for f in actual]
    self.assertEqual(
        [],
        names)

    self.feature_1.category = models.CSS
    self.feature_1.put()  # Changes updated field.
    actual = models.Feature.get_all(
        filterby=('category', models.CSS), update_cache=True)
    names = [f['name'] for f in actual]
    self.assertEqual(
        ['feature a'],
        names)

  def test_get_all__owner(self):
    """We can retrieve a list of all features with a given owner."""
    actual = models.Feature.get_all(
        filterby=('owner', 'owner@example.com'), update_cache=True)
    names = [f['name'] for f in actual]
    self.assertEqual(
        [],
        names)

    self.feature_1.owner = ['owner@example.com']
    self.feature_1.put()  # Changes updated field.
    actual = models.Feature.get_all(
        filterby=('owner', 'owner@example.com'), update_cache=True)
    names = [f['name'] for f in actual]
    self.assertEqual(
        ['feature a'],
        names)

  def test_get_by_ids__empty(self):
    """A request to load zero features returns zero results."""
    actual = models.Feature.get_by_ids([])
    self.assertEqual([], actual)

  def test_get_by_ids__cache_miss(self):
    """We can load features from datastore."""
    ramcache.global_cache.clear()

    actual = models.Feature.get_by_ids([self.feature_1.key.integer_id()])

    self.assertEqual(1, len(actual))
    self.assertEqual('feature a', actual[0]['name'])

  def test_get_by_ids__cache_hit(self):
    """We can load features from ramcache."""
    ramcache.global_cache.clear()
    cache_key = '%s|%s' % (
        models.Feature.DEFAULT_CACHE_KEY, self.feature_1.key.integer_id())
    ramcache.set(cache_key, 'fake cached feature')

    actual = models.Feature.get_by_ids([self.feature_1.key.integer_id()])

    self.assertEqual(1, len(actual))
    self.assertEqual('fake cached feature', actual[0])

  def test_get_by_ids__batch_order(self):
    """Features are returned in the order of the given IDs."""
    actual = models.Feature.get_by_ids([
        self.feature_4.key.integer_id(),
        self.feature_1.key.integer_id(),
        self.feature_3.key.integer_id(),
        self.feature_2.key.integer_id(),
    ])

    self.assertEqual(4, len(actual))
    self.assertEqual('feature d', actual[0]['name'])
    self.assertEqual('feature a', actual[1]['name'])
    self.assertEqual('feature c', actual[2]['name'])
    self.assertEqual('feature b', actual[3]['name'])

  def test_get_chronological__normal(self):
    """We can retrieve a list of features."""
    actual = models.Feature.get_chronological()
    names = [f['name'] for f in actual]
    self.assertEqual(
        ['feature c', 'feature d', 'feature a', 'feature b'],
        names)
    self.assertEqual(True, actual[0]['first_of_milestone'])
    self.assertEqual(False, hasattr(actual[1], 'first_of_milestone'))
    self.assertEqual(True, actual[2]['first_of_milestone'])
    self.assertEqual(False, hasattr(actual[3], 'first_of_milestone'))

  def test_get_chronological__unlisted(self):
    """Unlisted features are not included in the list."""
    self.feature_2.unlisted = True
    self.feature_2.put()
    actual = models.Feature.get_chronological()
    names = [f['name'] for f in actual]
    self.assertEqual(
        ['feature c', 'feature d', 'feature a'],
        names)

  def test_get_chronological__unlisted_shown(self):
    """Unlisted features are included for users with edit access."""
    self.feature_2.unlisted = True
    self.feature_2.put()
    actual = models.Feature.get_chronological(show_unlisted=True)
    names = [f['name'] for f in actual]
    self.assertEqual(
        ['feature c', 'feature d', 'feature a', 'feature b'],
        names)

  def test_get_in_milestone__normal(self):
    """We can retrieve a list of features."""
    self.feature_2.impl_status_chrome = 7
    self.feature_2.shipped_milestone = 1
    self.feature_2.put()

    self.feature_1.impl_status_chrome = 5
    self.feature_1.shipped_milestone = 1
    self.feature_1.put()

    self.feature_3.impl_status_chrome = 5
    self.feature_3.shipped_milestone = 1
    self.feature_3.put()

    self.feature_4.impl_status_chrome = 7
    self.feature_4.shipped_milestone = 2
    self.feature_4.put()

    actual = models.Feature.get_in_milestone(milestone=1)
    removed = [f['name'] for f in actual['Removed']]
    enabled_by_default = [f['name'] for f in actual['Enabled by default']]
    self.assertEqual(
        ['feature b'],
        removed)
    self.assertEqual(
        ['feature a', 'feature c'],
        enabled_by_default)
    self.assertEqual(6, len(actual))

    cache_key = '%s|%s|%s|%s' % (
        models.Feature.DEFAULT_CACHE_KEY, 'milestone', False, 1)
    cached_result = ramcache.get(cache_key)
    self.assertEqual(cached_result, actual)


  def test_get_in_milestone__unlisted(self):
    """Unlisted features should not be listed for users who can't edit."""
    self.feature_2.unlisted = True
    self.feature_2.impl_status_chrome = 7
    self.feature_2.shipped_milestone = 1
    self.feature_2.put()

    self.feature_1.impl_status_chrome = 5
    self.feature_1.shipped_milestone = 1
    self.feature_1.put()

    self.feature_3.impl_status_chrome = 5
    self.feature_3.shipped_milestone = 1
    self.feature_3.put()

    self.feature_4.impl_status_chrome = 7
    self.feature_4.shipped_milestone = 2
    self.feature_4.put()

    actual = models.Feature.get_in_milestone(milestone=1)
    self.assertEqual(
        0,
        len(actual['Removed']))

  def test_get_in_milestone__unlisted_shown(self):
    """Unlisted features should be listed for users who can edit."""
    self.feature_2.unlisted = True
    self.feature_2.impl_status_chrome = 7
    self.feature_2.shipped_milestone = 1
    self.feature_2.put()

    self.feature_1.impl_status_chrome = 5
    self.feature_1.shipped_milestone = 1
    self.feature_1.put()

    self.feature_3.impl_status_chrome = 5
    self.feature_3.shipped_milestone = 1
    self.feature_3.put()

    self.feature_4.impl_status_chrome = 7
    self.feature_4.shipped_milestone = 2
    self.feature_4.put()

    actual = models.Feature.get_in_milestone(milestone=1, show_unlisted=True)
    self.assertEqual(
        1,
        len(actual['Removed']))

  def test_get_in_milestone__cached(self):
    """If there is something in the cache, we use it."""
    cache_key = '%s|%s|%s|%s' % (
        models.Feature.DEFAULT_CACHE_KEY, 'milestone', False, 1)
    ramcache.set(cache_key, 'fake feature dict')

    actual = models.Feature.get_in_milestone(milestone=1)
    self.assertEqual(
        'fake feature dict',
        actual)


class ApprovalTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = models.Feature(
        name='feature a', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=3)
    self.feature_1.put()
    self.feature_1_id = self.feature_1.key.integer_id()
    self.appr_1 = models.Approval(
        feature_id=self.feature_1_id, field_id=1,
        state=models.Approval.REVIEW_STARTED,
        set_on=datetime.datetime.now(),
        set_by='one@example.com')
    self.appr_1.put()

  def tearDown(self):
    self.feature_1.key.delete()
    for appr in models.Approval.query().fetch(None):
      appr.key.delete()

  def test_get_approvals(self):
    """We can retrieve Approval entities."""
    actual = models.Approval.get_approvals(feature_id=self.feature_1_id)
    self.assertEqual(1, len(actual))
    self.assertEqual(self.feature_1_id, actual[0].feature_id)

    actual = models.Approval.get_approvals(field_id=1)
    self.assertEqual(1, len(actual))

    actual = models.Approval.get_approvals(
        states={models.Approval.REVIEW_STARTED, models.Approval.NEED_INFO})
    self.assertEqual(1, len(actual))

    actual = models.Approval.get_approvals(set_by='one@example.com')
    self.assertEqual(1, len(actual))

  def test_is_valid_state(self):
    """We know what approval states are valid."""
    self.assertTrue(
        models.Approval.is_valid_state(models.Approval.REVIEW_REQUESTED))
    self.assertFalse(models.Approval.is_valid_state(None))
    self.assertFalse(models.Approval.is_valid_state('not an int'))
    self.assertFalse(models.Approval.is_valid_state(999))

  def test_set_approval(self):
    """We can set an Approval entity."""
    models.Approval.set_approval(
        self.feature_1_id, 2, models.Approval.REVIEW_REQUESTED,
        'owner@example.com')
    self.assertEqual(
        2,
        len(models.Approval.query().fetch(None)))

  def test_clear_request(self):
    """We can clear a review request so that it is no longer pending."""
    self.appr_1.state = models.Approval.NEEDS_REVIEW
    self.appr_1.put()

    models.Approval.clear_request(self.feature_1_id, 1)

    remaining_apprs = models.Approval.get_approvals(
        feature_id=self.feature_1_id, field_id=1,
        states=[models.Approval.NEEDS_REVIEW])
    self.assertEqual([], remaining_apprs)


class CommentTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = models.Feature(
        name='feature a', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=3)
    self.feature_1.put()
    self.feature_1_id = self.feature_1.key.integer_id()
    self.comment_1_1 = models.Comment(
        feature_id=self.feature_1_id, field_id=1,
        author='one@example.com',
        content='some text')
    self.comment_1_1.put()
    self.comment_1_2 = models.Comment(
        feature_id=self.feature_1_id, field_id=2,
        author='one@example.com',
        content='some other text')
    self.comment_1_2.put()

    self.feature_2 = models.Feature(
        name='feature b', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=3)
    self.feature_2.put()
    self.feature_2_id = self.feature_2.key.integer_id()

  def tearDown(self):
    self.feature_1.key.delete()
    self.feature_2.key.delete()
    for comm in models.Comment.query().fetch(None):
      comm.key.delete()

  def test_get_comments__none(self):
    """We get [] if feature has no review comments."""
    actual = models.Comment.get_comments(self.feature_2_id)
    self.assertEqual([], actual)

  def test_get_comments__some(self):
    """We get review comments if the feature has some."""
    actual = models.Comment.get_comments(self.feature_1_id)
    self.assertEqual(2, len(actual))
    self.assertEqual(
        ['some text', 'some other text'],
        [c.content for c in actual])

  def test_get_comments__specific_fields(self):
    """We get review comments for specific approval fields if requested."""
    actual_1 = models.Comment.get_comments(self.feature_1_id, 1)
    self.assertEqual(1, len(actual_1))
    self.assertEqual('some text', actual_1[0].content)

    actual_2 = models.Comment.get_comments(self.feature_1_id, 2)
    self.assertEqual(1, len(actual_2))
    self.assertEqual('some other text', actual_2[0].content)

    actual_3 = models.Comment.get_comments(self.feature_1_id, 3)
    self.assertEqual([], actual_3)


class UserPrefTest(testing_config.CustomTestCase):

  def setUp(self):
    self.user_pref_1 = models.UserPref(email='one@example.com')
    self.user_pref_1.notify_as_starrer = False
    self.user_pref_1.put()

    self.user_pref_2 = models.UserPref(email='two@example.com')
    self.user_pref_2.put()

  def tearDown(self):
    self.user_pref_1.key.delete()
    self.user_pref_2.key.delete()

  # @mock.patch('google.appengine.api.users.get_current_user')
  @mock.patch('framework.users.get_current_user')
  def test_get_signed_in_user_pref__anon(self, mock_get_current_user):
    mock_get_current_user.return_value = None
    actual = models.UserPref.get_signed_in_user_pref()
    self.assertIsNone(actual)

  # @mock.patch('google.appengine.api.users.get_current_user')
  @mock.patch('framework.users.get_current_user')
  def test_get_signed_in_user_pref__first_time(self, mock_get_current_user):
    mock_get_current_user.return_value = testing_config.Blank(
        email=lambda: 'user1@example.com')

    actual = models.UserPref.get_signed_in_user_pref()

    self.assertEqual('user1@example.com', actual.email)
    self.assertEqual(True, actual.notify_as_starrer)
    self.assertEqual(False, actual.bounced)

  # @mock.patch('google.appengine.api.users.get_current_user')
  @mock.patch('framework.users.get_current_user')
  def test_get_signed_in_user_pref__had_pref(self, mock_get_current_user):
    mock_get_current_user.return_value = testing_config.Blank(
        email=lambda: 'user2@example.com')
    user_pref = models.UserPref(
        email='user2@example.com', notify_as_starrer=False, bounced=True)
    user_pref.put()

    actual = models.UserPref.get_signed_in_user_pref()

    self.assertEqual('user2@example.com', actual.email)
    self.assertEqual(False, actual.notify_as_starrer)
    self.assertEqual(True, actual.bounced)

  # @mock.patch('google.appengine.api.users.get_current_user')
  @mock.patch('framework.users.get_current_user')
  def test_dismiss_cue(self, mock_get_current_user):
    """We store the fact that a user has dismissed a cue card."""
    mock_get_current_user.return_value = testing_config.Blank(
        email=lambda: 'one@example.com')

    models.UserPref.dismiss_cue('welcome-message')

    revised_user_pref = models.UserPref.get_signed_in_user_pref()
    self.assertEqual('one@example.com', revised_user_pref.email)
    self.assertEqual(['welcome-message'], revised_user_pref.dismissed_cues)

  # @mock.patch('google.appengine.api.users.get_current_user')
  @mock.patch('framework.users.get_current_user')
  def test_dismiss_cue__double(self, mock_get_current_user):
    """We ignore the same user dismissing the same cue multiple times."""
    mock_get_current_user.return_value = testing_config.Blank(
        email=lambda: 'one@example.com')

    models.UserPref.dismiss_cue('welcome-message')
    models.UserPref.dismiss_cue('welcome-message')

    revised_user_pref = models.UserPref.get_signed_in_user_pref()
    self.assertEqual('one@example.com', revised_user_pref.email)
    self.assertEqual(['welcome-message'], revised_user_pref.dismissed_cues)

  def test_get_prefs_for_emails__some_found(self):
    emails = ['one@example.com', 'two@example.com', 'huh@example.com']
    user_prefs = models.UserPref.get_prefs_for_emails(emails)
    self.assertEqual(3, len(user_prefs))
    one, two, huh = user_prefs
    self.assertEqual('one@example.com', one.email)
    self.assertFalse(one.notify_as_starrer)
    self.assertEqual('two@example.com', two.email)
    self.assertTrue(two.notify_as_starrer)
    # This one is automatically created:
    self.assertEqual('huh@example.com', huh.email)
    self.assertTrue(huh.notify_as_starrer)

  def test_get_prefs_for_emails__long_list(self):
    emails = ['user_%d@example.com' % i
              for i in range(100)]
    user_prefs = models.UserPref.get_prefs_for_emails(emails)
    self.assertEqual(100, len(user_prefs))
    self.assertEqual('user_0@example.com', user_prefs[0].email)
