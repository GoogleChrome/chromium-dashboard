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

import flask
from flask import session
from unittest import mock
import werkzeug.exceptions  # Flask HTTP stuff.

from api import token_refresh_api
from framework import xsrf

test_app = flask.Flask(__name__)
test_app.secret_key = 'testing secret'


class TokenRefreshAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.handler = token_refresh_api.TokenRefreshAPI()
    self.request_path = '/api/v0/currentuser/token'

  @mock.patch('framework.xsrf.validate_token')
  def test_validate_token(self, mock_xsrf_validate_token):
    """This handler validates tokens with a a longer timeout."""
    self.handler.validate_token('test token', 'user@example.com')
    mock_xsrf_validate_token.assert_called_once_with(
        'test token', 'user@example.com',
        timeout=xsrf.REFRESH_TOKEN_TIMEOUT_SEC)

  def test_do_get(self):
    """This handler does not respond to GET requests."""
    self.assertFalse(hasattr(self.handler, 'do_get'))

  def test_post__anon(self):
    """We reject token requests from signed out users."""
    testing_config.sign_out()
    params = {}
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.post()

  def test_post__missing(self):
    """We reject token requests that do not include a previous token."""
    testing_config.sign_in('user@example.com', 111)
    params = {}
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.post()

  @mock.patch('api.token_refresh_api.TokenRefreshAPI.validate_token')
  def test_post__bad(self, mock_validate_token):
    """We reject token requests that have a bad token."""
    testing_config.sign_in('user@example.com', 111)
    mock_validate_token.side_effect = xsrf.TokenIncorrect()
    params = {'token': 'bad'}
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.post()
    mock_validate_token.assert_called_once()

  def test_do_post__OK(self):
    """If the request is accepted, we return a new token."""
    params = {'token': 'checked in base class'}
    with test_app.test_request_context(self.request_path, json=params):
      session.clear()
      testing_config.sign_in('user@example.com', 111)
      actual = self.handler.do_post()

      self.assertIn('signed_user_info', session)
      self.assertIn('token', actual)
      self.assertIn('token_expires_sec', actual)
