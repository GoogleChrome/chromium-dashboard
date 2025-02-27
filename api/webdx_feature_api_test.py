# Copyright 2025 Google Inc.
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

import testing_config
from collections import OrderedDict

import flask

from api.webdx_feature_api import WebdxFeatureAPI
from internals.metrics_models import WebDXFeatureObserver

test_app = flask.Flask(__name__)

class WebdxFeatureAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.webdx_observer = WebDXFeatureObserver(bucket_id=3, property_name='css')
    self.webdx_observer.put()

    self.handler = WebdxFeatureAPI()
    self.request_path = '/api/v0/webdxfeatures'

  def tearDown(self):
    for entity in WebDXFeatureObserver.query():
      entity.key.delete()

  def test_do_get__success(self):
    testing_config.sign_out()

    with test_app.test_request_context(self.request_path):
      actual = self.handler.do_get()

    expected = OrderedDict(
      [
        ('Missing feature', ['Missing feature', 'Missing feature']),
        ('TBD', ['TBD', 'TBD']),
        ('css', ['css', '3']),
      ]
    )
    self.assertEqual(actual, expected)

  def test_do_get__empty_data(self):
    testing_config.sign_out()
    self.webdx_observer.key.delete()

    with test_app.test_request_context(self.request_path):
      actual = self.handler.do_get()

    self.assertEqual(actual, {})
