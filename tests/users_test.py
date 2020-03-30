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

import mock
import unittest
import testing_config  # Must be imported before the module under test.

import webapp2
from webob import exc

import models
import users


class SettingsHandlerTests(unittest.TestCase):

  def setUp(self):
    request = webapp2.Request.blank('/settings')
    response = webapp2.Response()
    self.handler = users.SettingsHandler(request, response)

  @mock.patch('users.SettingsHandler.redirect')
  @mock.patch('models.UserPref.get_signed_in_user_pref')
  def test_get__anon(self, mock_gsiup, mock_redirect):
    mock_gsiup.return_value = None

    actual = self.handler.get()

    mock_redirect.assert_called_once()

  @mock.patch('users.SettingsHandler.render')
  @mock.patch('models.UserPref.get_signed_in_user_pref')
  def test_get__signed_in(self, mock_gsiup, mock_render):
    mock_gsiup.return_value = models.UserPref(
        email='user@example.com')

    actual = self.handler.get()

    mock_render.assert_called_once()
