# Copyright 2022 Google Inc.
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

import flask
from flask import session
from unittest import mock
import werkzeug.exceptions  # Flask HTTP stuff.

from framework import users
from framework import xsrf

test_app = flask.Flask(__name__)
test_app.secret_key = 'testing secret'


class UsersTest(testing_config.CustomTestCase):

  def test_get_current_user__unittest_signed_in(self):
    """For unit tests, we know when the user is signed in."""
    testing_config.sign_in('user_111@example.com', 111)
    actual_user = users.get_current_user()
    self.assertEqual('user_111@example.com', actual_user.email())

  def test_get_current_user__unittest_signed_out(self):
    """For unit tests, we know when the user is signed out."""
    testing_config.sign_out()
    actual_user = users.get_current_user()
    self.assertIsNone(actual_user)

  @mock.patch('settings.UNIT_TEST_MODE', False)
  @mock.patch('framework.xsrf.validate_token')
  def test_get_current_user__signed_in_sui(self, mock_validate):
    """A valid signed user_info means the user is signed in."""
    with test_app.test_request_context('/any-path'):
      session.clear()
      session['signed_user_info'] = {'email': 'user_333@example.com'}, 'good'
      actual_user = users.get_current_user()
      self.assertEqual('user_333@example.com', actual_user.email())
      mock_validate.assert_called_once()

  @mock.patch('settings.UNIT_TEST_MODE', False)
  @mock.patch('framework.xsrf.validate_token')
  def test_get_current_user__bad_sui(self, mock_validate):
    """We reject bad signed user_info and clear the session."""
    mock_validate.side_effect = xsrf.TokenIncorrect()
    with test_app.test_request_context('/any-path'):
      session.clear()
      session['signed_user_info'] = {'email': 'anything'}, 'bad signature'
      actual_user = users.get_current_user()
      self.assertIsNone(actual_user)
      self.assertEqual(0, len(session))

  @mock.patch('settings.UNIT_TEST_MODE', False)
  def test_get_current_user__signed_out(self):
    """When there is no jwt or user info in the session, user is signed out."""
    with test_app.test_request_context('/any-path'):
      session.clear()
      actual_user = users.get_current_user()
      self.assertIsNone(actual_user)

  def test_is_currnet_user_admin(self):
    """We never consider a user an admin based on old GAE auth info."""
    actual = users.is_current_user_admin()
    self.assertFalse(actual)

  def test_add_signed_user_info_to_session(self):
    """We log in the user by adding a signed user_info to the session."""
    with test_app.test_request_context('/any/path'):
      session.clear()
      session['something else'] = 'some other aspect of the session'
      users.add_signed_user_info_to_session('user@example.com')
      self.assertEqual(2, len(session))
      user_info, signature = session['signed_user_info']
      self.assertEqual({'email': 'user@example.com'}, user_info)
      xsrf.validate_token(
          signature,
          str(user_info),
          timeout=xsrf.REFRESH_TOKEN_TIMEOUT_SEC)
