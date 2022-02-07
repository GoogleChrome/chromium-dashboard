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

import testing_config  # Must be imported first

import flask
from unittest import mock
import werkzeug

import settings
from framework import ramcache
from internals import models
from pages import myfeatures

test_app = flask.Flask(__name__)


class MyFeaturesHandlerTest(testing_config.CustomTestCase):

  def setUp(self):
    self.request_path = '/myfeatures'
    self.handler = myfeatures.MyFeaturesHandler()

  @mock.patch('flask.redirect')
  @mock.patch('internals.models.UserPref.get_signed_in_user_pref')
  def test_get_template_data__anon(self, mock_gsiup, mock_redirect):
    mock_gsiup.return_value = None
    mock_redirect.return_value = 'mock redirect response'

    with test_app.test_request_context(self.request_path):
      actual = self.handler.get_template_data()

    mock_redirect.assert_called_once_with(settings.LOGIN_PAGE_URL)
    self.assertEqual('mock redirect response', actual)

  @mock.patch('internals.models.UserPref.get_signed_in_user_pref')
  def test_get_template_data(self, mock_gsiup):
    """User can get a 'my feature' page."""
    mock_gsiup.return_value = models.UserPref(
        email='user@example.com')
    with test_app.test_request_context(self.request_path):
      template_data = self.handler.get_template_data()

    # Everything is done in JS, so there is no template_data
    self.assertEqual({}, template_data)
