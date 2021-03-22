from __future__ import division
from __future__ import print_function

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

import unittest
import testing_config  # Must be imported before the module under test.

import mock
from framework import ramcache
from google.appengine.api import users

import models


class MockQuery(object):

  def __init__(self, result_list):
    self.result_list = result_list

  def fetch(self, *args, **kw):
    return self.result_list


class ModelsFunctionsTest(unittest.TestCase):

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


class FeatureTest(unittest.TestCase):

  def setUp(self):
    ramcache.SharedInvalidate.check_for_distributed_invalidation()
    self.feature_1 = models.Feature(
        name='feature one', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1)
    self.feature_1.put()

    self.feature_2 = models.Feature(
        name='feature two', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1)
    self.feature_2.put()

  def tearDown(self):
    self.feature_1.delete()
    self.feature_2.delete()
    ramcache.flush_all()

  def test_get_chronological__normal(self):
    """We can retrieve a list of features."""
    actual = models.Feature.get_chronological()
    names = [f['name'] for f in actual]
    self.assertEqual(
        ['feature one', 'feature two'],
        names)

  def test_get_chronological__unlisted(self):
    """Unlisted features are not included in the list."""
    self.feature_2.unlisted = True
    self.feature_2.put()
    actual = models.Feature.get_chronological()
    names = [f['name'] for f in actual]
    self.assertEqual(
        ['feature one'],
        names)

  def test_get_chronological__unlisted_shown(self):
    """Unlisted features are included for users with edit access."""
    self.feature_2.unlisted = True
    self.feature_2.put()
    actual = models.Feature.get_chronological(show_unlisted=True)
    names = [f['name'] for f in actual]
    self.assertEqual(
        ['feature one', 'feature two'],
        names)


class UserPrefTest(unittest.TestCase):

  def setUp(self):
    self.user_pref_1 = models.UserPref(email='one@example.com')
    self.user_pref_1.notify_as_starrer = False
    self.user_pref_1.put()

    self.user_pref_2 = models.UserPref(email='two@example.com')
    self.user_pref_2.put()

  def tearDown(self):
    self.user_pref_1.delete()
    self.user_pref_2.delete()

  @mock.patch('google.appengine.api.users.get_current_user')
  def test_get_signed_in_user_pref__anon(self, mock_get_current_user):
    mock_get_current_user.return_value = None
    actual = models.UserPref.get_signed_in_user_pref()
    self.assertIsNone(actual)

  @mock.patch('google.appengine.api.users.get_current_user')
  def test_get_signed_in_user_pref__first_time(self, mock_get_current_user):
    mock_get_current_user.return_value = testing_config.Blank(
        email=lambda: 'user1@example.com')

    actual = models.UserPref.get_signed_in_user_pref()

    self.assertEqual('user1@example.com', actual.email)
    self.assertEqual(True, actual.notify_as_starrer)
    self.assertEqual(False, actual.bounced)

  @mock.patch('google.appengine.api.users.get_current_user')
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

  @mock.patch('google.appengine.api.users.get_current_user')
  def test_dismiss_cue(self, mock_get_current_user):
    """We store the fact that a user has dismissed a cue card."""
    mock_get_current_user.return_value = testing_config.Blank(
        email=lambda: 'one@example.com')

    models.UserPref.dismiss_cue('welcome-message')

    revised_user_pref = models.UserPref.get_signed_in_user_pref()
    self.assertEqual('one@example.com', revised_user_pref.email)
    self.assertEqual(['welcome-message'], revised_user_pref.dismissed_cues)

  @mock.patch('google.appengine.api.users.get_current_user')
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
