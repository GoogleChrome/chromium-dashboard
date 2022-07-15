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
from flask import testing

import main



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
