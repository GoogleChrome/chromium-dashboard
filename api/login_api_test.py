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

from api import login_api
from framework import xsrf

test_app = flask.Flask(__name__)
test_app.secret_key = 'testing secret'


class LoginAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.handler = login_api.LoginAPI()
    self.request_path = '/api/v0/login'

  def test_get(self):
    """We reject all GETs to this endpoint."""
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.MethodNotAllowed):
        self.handler.do_get()

  def test_post__missing_credential_token(self):
    """We reject login requests that don't have any credential_token."""
    params = {}
    with test_app.test_request_context(self.request_path, json=params):
      session.clear()
      session['something else'] = 'some other aspect of the session'
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post()
      self.assertEqual(1, len(session))

  def test_post__invalid_credential_token(self):
    """We reject login requests that have an invalid credential_token."""
    params = {'credential': 'fake bad token'}
    with test_app.test_request_context(self.request_path, json=params):
      session.clear()
      actual_response = self.handler.do_post()
      self.assertEqual({'message': 'Invalid token'}, actual_response)
      self.assertNotIn('signed_user_info', session)

  @mock.patch('google.oauth2.id_token.verify_oauth2_token')
  def test_post__normal(self, mock_verify):
    """We log in the user if they provide a good credential_token."""
    mock_verify.return_value = {'email': 'user@example.com'}
    params = {'credential': 'fake good token'}
    with test_app.test_request_context(self.request_path, json=params):
      session.clear()
      actual_response = self.handler.do_post()
      self.assertEqual({'message': 'Done'}, actual_response)
      self.assertIn('signed_user_info', session)
