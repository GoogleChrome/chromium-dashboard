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

import testing_config  # Must be imported first

import flask
import werkzeug

from internals import models
from internals import detect_intent

test_app = flask.Flask(__name__)


class IntentEmailHandlerTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = models.Feature(
        name='feature one', summary='detailed sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1,
        intent_stage=models.INTENT_IMPLEMENT)
    self.feature_1.put()
    self.feature_id = self.feature_1.key.integer_id()

    self.request_path = '/tasks/detect-intent'
    self.json_data = {
        'from_addr': 'user@example.com',
        'subject': 'Intent to Ship: Featurename',
        'body': 'Please review',
        }
    self.handler = detect_intent.IntentEmailHandler()

  def tearDown(self):
    self.feature_1.key.delete()

  def test_process_post_data__normal(self):
    """When everything is perfect, we record the intent thread."""
    with test_app.test_request_context(
        self.request_path, json=self.json_data):
      actual = self.handler.process_post_data()

    # TODO(jrobbins): Add checks after detect_intent is written.

    self.assertEqual(actual, {'message': 'Done'})
