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

from unittest import mock

import os
import flask
import werkzeug
import html5lib
from pathlib import Path

from pages import blink_handler
from internals import user_models

test_app = flask.Flask(__name__)

# Load testdata to be used across all of the CustomTestCases
TESTDATA = testing_config.Testdata(
  os.path.abspath(os.path.dirname(__file__)),
  Path(__file__).stem)

class BlinkTemplateTest(testing_config.CustomTestCase):

  HANDLER_CLASS = blink_handler.BlinkHandler

  def setUp(self):

    self.request_path = self.HANDLER_CLASS.TEMPLATE_PATH
    self.handler = self.HANDLER_CLASS()

    self.app_admin = user_models.AppUser(email='admin@example.com')
    self.app_admin.is_admin = True
    self.app_admin.put()
    testing_config.sign_in('admin@example.com', 123567890)

    with test_app.test_request_context(self.request_path):
      self.template_data = self.handler.get_template_data()
    self.full_template_path = self.handler.get_template_path(self.template_data)

    self.maxDiff = None

  def test_html_rendering(self):
    """We can render the template with valid html."""
    template_text = self.handler.render(
        self.template_data, self.full_template_path)
    parser = html5lib.HTMLParser(strict=True)
    document = parser.parse(template_text)
    # TESTDATA.make_golden(template_text, 'BlinkTemplateTest_test_html_rendering.html')
    self.assertMultiLineEqual(
      TESTDATA['BlinkTemplateTest_test_html_rendering.html'], template_text)


class SubscribersTemplateTest(testing_config.CustomTestCase):

  HANDLER_CLASS = blink_handler.SubscribersHandler

  def setUp(self):

    self.request_path = self.HANDLER_CLASS.TEMPLATE_PATH
    self.handler = self.HANDLER_CLASS()

    self.app_admin = user_models.AppUser(email='admin@example.com')
    self.app_admin.is_admin = True
    self.app_admin.put()

    testing_config.sign_in('admin@example.com', 123567890)

    with test_app.test_request_context(self.request_path):
      self.template_data = self.handler.get_template_data()
    self.full_template_path = self.handler.get_template_path(self.template_data)

    self.maxDiff = None

  def test_html_rendering(self):
    """We can render the template with valid html."""
    template_text = self.handler.render(
        self.template_data, self.full_template_path)
    parser = html5lib.HTMLParser(strict=True)
    document = parser.parse(template_text)
    # TESTDATA.make_golden(template_text, 'SubscribersTemplateTest_test_html_rendering.html')
    self.assertMultiLineEqual(
      TESTDATA['SubscribersTemplateTest_test_html_rendering.html'], template_text)
