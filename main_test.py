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

import testing_config  # Must be imported before the module under test.

from unittest import mock
import flask
from flask import testing
import html5lib

from framework import basehandlers
import main

test_app = flask.Flask(__name__)



class MainTest(testing_config.CustomTestCase):
  """Set of unit tests for our page route registration and other setup."""

  def test_app_exists(self):
    """Just test that this file parses and creates an app object."""
    self.assertIsNotNone(main.app)

  def test_redirects(self):
    """Redirect are working."""
    main.app.wsgi_app = main.app.original_wsgi_app
    test_client = testing.FlaskClient(main.app)

    response = test_client.get('/')
    self.assertEqual(302, response.status_code)
    self.assertEqual('/roadmap', response.location)

    response = test_client.get('/metrics')
    self.assertEqual(302, response.status_code)
    self.assertEqual('/metrics/css/popularity', response.location)

    response = test_client.get('/metrics/css')
    self.assertEqual(302, response.status_code)
    self.assertEqual('/metrics/css/popularity', response.location)


class ConstTemplateTest(testing_config.CustomTestCase):

  def check_template(self, route):
    request_path, handler_class, defaults = route
    handler = handler_class()

    with test_app.test_request_context(request_path):
      template_data = handler.get_template_data(**defaults)
    full_template_path = handler.get_template_path(template_data)

    template_text = handler.render(template_data, full_template_path)
    parser = html5lib.HTMLParser(strict=True)
    document = parser.parse(template_text)

  def test_const_templates(self):
    """All the ConstHandler instances render valid HTML."""
    for route in main.page_routes:
      if (route[1] == basehandlers.ConstHandler and
          not route[0].endswith('.xml')):
        with self.subTest(path=route[0]):
          self.check_template(route)
