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

from api import logout_api

test_app = flask.Flask(__name__)
test_app.secret_key = 'testing secret'


class LogoutAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.handler = logout_api.LogoutAPI()
    self.request_path = '/api/v0/logout'

  def test_get(self):
    """We reject all GETs to this endpoint."""
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.MethodNotAllowed):
        self.handler.do_get()

  def test_post__normal(self):
    """We log out the user whenever they request that."""
    params = {}
    with test_app.test_request_context(self.request_path, json=params):
      session['signed_user_info'] = {'email': 'x'}, 'fake signature'
      session['something else'] = 'some other aspect of the session'
      actual_response = self.handler.do_post()
      self.assertEqual({'message': 'Done'}, actual_response)
      self.assertEqual(0, len(session))
