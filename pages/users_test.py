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

import flask
import html5lib
import os

from google.cloud import ndb
from pathlib import Path
from unittest import mock

from internals import user_models
from pages import users

test_app = flask.Flask(__name__)


# Load testdata to be used across all of the CustomTestCases
TESTDATA = testing_config.Testdata(__file__)

class UsersListTemplateTest(testing_config.CustomTestCase):

  def setUp(self):
    self.handler = users.UserListHandler()

    self.app_admin = user_models.AppUser(email='admin@example.com')
    self.app_admin.is_admin = True
    self.app_admin.key = ndb.Key('AppUser', 1)
    self.app_admin.put()
    testing_config.sign_in('admin@example.com', 123567890)

    with test_app.test_request_context('/request_path'):
      self.template_data = self.handler.get_template_data()
      self.template_data.update(self.handler.get_common_data())
      self.template_data['nonce'] = 'fake nonce'
      self.template_data['xsrf_token'] = ''
      self.template_data['xsrf_token_expires'] = 0
    self.full_template_path = self.handler.get_template_path(self.template_data)
    self.maxDiff = None

  def tearDown(self):
    self.app_admin.key.delete()
    testing_config.sign_out()

  def test_html_rendering(self):
    """We can render the template with valid html."""
    template_text = self.handler.render(
        self.template_data, self.full_template_path)
    parser = html5lib.HTMLParser(strict=True)
    document = parser.parse(template_text)
    # TESTDATA.make_golden(template_text, 'test_html_rendering.html')
    self.assertMultiLineEqual(
      TESTDATA['test_html_rendering.html'], template_text)
