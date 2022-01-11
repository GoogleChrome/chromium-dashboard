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

import testing_config  # Must be imported first
from unittest import mock
import unittest

import flask

from internals import models
from pages import users

test_app = flask.Flask(__name__)


class SettingsHandlerTests(unittest.TestCase):

  def setUp(self):
    self.handler = users.SettingsHandler()

  @mock.patch('flask.redirect')
  @mock.patch('internals.models.UserPref.get_signed_in_user_pref')
  def test_get__anon(self, mock_gsiup, mock_redirect):
    mock_gsiup.return_value = None
    mock_redirect.return_value = 'mock redirect response'

    with test_app.test_request_context('/settings'):
      actual = self.handler.get_template_data()

    mock_redirect.assert_called_once()
    self.assertEqual('mock redirect response', actual)

  @mock.patch('internals.models.UserPref.get_signed_in_user_pref')
  def test_get__signed_in(self, mock_gsiup):
    mock_gsiup.return_value = models.UserPref(
        email='user@example.com')

    actual = self.handler.get_template_data()

    self.assertIsInstance(actual, dict)
    self.assertIn('user_pref', actual)
    self.assertIn('user_pref_form', actual)
