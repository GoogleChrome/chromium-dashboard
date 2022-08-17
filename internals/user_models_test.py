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

from unittest import mock
from framework import ramcache
from framework import users

from internals import user_models


class UserPrefTest(testing_config.CustomTestCase):

  def setUp(self):
    self.user_pref_1 = user_models.UserPref(email='one@example.com')
    self.user_pref_1.notify_as_starrer = False
    self.user_pref_1.put()

    self.user_pref_2 = user_models.UserPref(email='two@example.com')
    self.user_pref_2.put()

  def tearDown(self):
    self.user_pref_1.key.delete()
    self.user_pref_2.key.delete()

  @mock.patch('framework.users.get_current_user')
  def test_get_signed_in_user_pref__anon(self, mock_get_current_user):
    mock_get_current_user.return_value = None
    actual = user_models.UserPref.get_signed_in_user_pref()
    self.assertIsNone(actual)

  @mock.patch('framework.users.get_current_user')
  def test_get_signed_in_user_pref__first_time(self, mock_get_current_user):
    mock_get_current_user.return_value = testing_config.Blank(
        email=lambda: 'user1@example.com')

    actual = user_models.UserPref.get_signed_in_user_pref()

    self.assertEqual('user1@example.com', actual.email)
    self.assertEqual(True, actual.notify_as_starrer)
    self.assertEqual(False, actual.bounced)

  @mock.patch('framework.users.get_current_user')
  def test_get_signed_in_user_pref__had_pref(self, mock_get_current_user):
    mock_get_current_user.return_value = testing_config.Blank(
        email=lambda: 'user2@example.com')
    user_pref = user_models.UserPref(
        email='user2@example.com', notify_as_starrer=False, bounced=True)
    user_pref.put()

    actual = user_models.UserPref.get_signed_in_user_pref()

    self.assertEqual('user2@example.com', actual.email)
    self.assertEqual(False, actual.notify_as_starrer)
    self.assertEqual(True, actual.bounced)

  @mock.patch('framework.users.get_current_user')
  def test_dismiss_cue(self, mock_get_current_user):
    """We store the fact that a user has dismissed a cue card."""
    mock_get_current_user.return_value = testing_config.Blank(
        email=lambda: 'one@example.com')

    user_models.UserPref.dismiss_cue('welcome-message')

    revised_user_pref = user_models.UserPref.get_signed_in_user_pref()
    self.assertEqual('one@example.com', revised_user_pref.email)
    self.assertEqual(['welcome-message'], revised_user_pref.dismissed_cues)

  @mock.patch('framework.users.get_current_user')
  def test_dismiss_cue__double(self, mock_get_current_user):
    """We ignore the same user dismissing the same cue multiple times."""
    mock_get_current_user.return_value = testing_config.Blank(
        email=lambda: 'one@example.com')

    user_models.UserPref.dismiss_cue('welcome-message')
    user_models.UserPref.dismiss_cue('welcome-message')

    revised_user_pref = user_models.UserPref.get_signed_in_user_pref()
    self.assertEqual('one@example.com', revised_user_pref.email)
    self.assertEqual(['welcome-message'], revised_user_pref.dismissed_cues)

  def test_get_prefs_for_emails__some_found(self):
    emails = ['one@example.com', 'two@example.com', 'huh@example.com']
    user_prefs = user_models.UserPref.get_prefs_for_emails(emails)
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
    user_prefs = user_models.UserPref.get_prefs_for_emails(emails)
    self.assertEqual(100, len(user_prefs))
    self.assertEqual('user_0@example.com', user_prefs[0].email)
