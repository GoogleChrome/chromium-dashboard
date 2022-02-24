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

from pages import metrics

test_app = flask.Flask(__name__)


class CssPopularityTemplateTest(testing_config.CustomTestCase):

  HANDLER_CLASS = metrics.CssPopularityHandler

  def setUp(self):        

    self.request_path = self.HANDLER_CLASS.TEMPLATE_PATH
    self.handler = self.HANDLER_CLASS()

    with test_app.test_request_context(self.request_path):
      self.template_data = self.handler.get_template_data()
    self.full_template_path = self.handler.get_template_path(self.template_data)

  def test_html_rendering(self):
    """We can render the template with valid html."""
    template_text = self.handler.render(
        self.template_data, self.full_template_path)
    parser = html5lib.HTMLParser(strict=True)
    document = parser.parse(template_text)


class CssAnimatedTemplateTest(testing_config.CustomTestCase):

  HANDLER_CLASS = metrics.CssAnimatedHandler

  def setUp(self):        

    self.request_path = self.HANDLER_CLASS.TEMPLATE_PATH
    self.handler = self.HANDLER_CLASS()

    with test_app.test_request_context(self.request_path):
      self.template_data = self.handler.get_template_data()
    self.full_template_path = self.handler.get_template_path(self.template_data)

  def test_html_rendering(self):
    """We can render the template with valid html."""
    template_text = self.handler.render(
        self.template_data, self.full_template_path)
    parser = html5lib.HTMLParser(strict=True)
    document = parser.parse(template_text)


class FeaturePopularityTemplateTest(testing_config.CustomTestCase):

  HANDLER_CLASS = metrics.FeaturePopularityHandler

  def setUp(self):        

    self.request_path = self.HANDLER_CLASS.TEMPLATE_PATH
    self.handler = self.HANDLER_CLASS()

    with test_app.test_request_context(self.request_path):
      self.template_data = self.handler.get_template_data()
    self.full_template_path = self.handler.get_template_path(self.template_data)

  def test_html_rendering(self):
    """We can render the template with valid html."""
    template_text = self.handler.render(
        self.template_data, self.full_template_path)
    parser = html5lib.HTMLParser(strict=True)
    document = parser.parse(template_text)
