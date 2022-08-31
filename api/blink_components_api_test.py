# -*- coding: utf-8 -*-
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

from api import blink_components_api
from internals import user_models

test_app = flask.Flask(__name__)


class BlinkComponentsAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.handler = blink_components_api.BlinkComponentsAPI()
    self.request_path = '/api/v0/blinkcomponents'

  def test_get__anon(self):
    """We can get blink components as an anonymous."""
    testing_config.sign_out()
    with test_app.test_request_context(self.request_path):
      actual = self.handler.do_get()
    self.assertEqual(user_models.BlinkComponent.fetch_all_components(), list(actual))

  def test_get__signed_in(self):
    """We can get blink components as a signed-in user."""
    testing_config.sign_in('one@example.com', 123567890)
    with test_app.test_request_context(self.request_path):
      actual = self.handler.do_get()
    self.assertEqual(user_models.BlinkComponent.fetch_all_components(), list(actual))
