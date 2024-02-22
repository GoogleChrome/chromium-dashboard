# Copyright 2024 Google Inc.
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
import werkzeug.exceptions  # Flask HTTP stuff.

from api import origin_trials_api
from internals.core_models import FeatureEntry, Stage

test_app = flask.Flask(__name__)


class OriginTrialsAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = FeatureEntry(
        feature_type=1, name='feature one', summary='sum', category=1)
    self.feature_1.put()
    self.feature_1_id = self.feature_1.key.integer_id()
    self.ot_stage_1 = Stage(
        feature_id=self.feature_1_id, stage_type=151,
        origin_trial_id='-1234567890')
    self.ot_stage_1.put()
    self.feature_2 = FeatureEntry(
        feature_type=1, name='feature two', summary='sum', category=1)
    self.feature_2.put()
    self.ot_stage_2 = Stage(
        feature_id=self.feature_2.key.integer_id(), stage_type=151,
        origin_trial_id='9876543210')
    self.ot_stage_2.put()
    self.handler = origin_trials_api.OriginTrialsAPI()
    self.request_path = (
        '/api/v0/origintrials/'
        f'{self.feature_1_id}/{self.ot_stage_1.key.integer_id()}/extend')

  def tearDown(self):
    for kind in [FeatureEntry, Stage]:
      for entity in kind.query():
        entity.key.delete()

  def test_validate_extension_args__valid(self):
    body = {
      'origin_trial_id': '-1234567890',
      'end_milestone': '150',
      'intent_thread_url': 'https://example.com/intent',
    }
    # No exception should be raised.
    with test_app.test_request_context(self.request_path):
      self.handler._validate_extension_args(
          self.feature_1_id, self.ot_stage_1, body)
  
  def test_validate_extension_args__mismatched_stage(self):
    body = {
      'origin_trial_id': '-1234567890',
      'end_milestone': '150',
      'intent_thread_url': 'https://example.com/intent',
    }
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        # Stage doesn't belong to feature.
        self.handler._validate_extension_args(
            self.feature_1_id, self.ot_stage_2, body)
  
  def test_validate_extension_args__invalid_ot_id(self):
    body = {
      # Invalid trial ID.
      'origin_trial_id': '1111111111',
      'end_milestone': '150',
      'intent_thread_url': 'https://example.com/intent',
    }
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler._validate_extension_args(
            self.feature_1_id, self.ot_stage_1, body)

  def test_validate_extension_args__missing_ot_id(self):
    body = {
      # Missing trial ID.
      'end_milestone': '150',
      'intent_thread_url': 'https://example.com/intent',
    }
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler._validate_extension_args(
            self.feature_1_id, self.ot_stage_1, body)

  def test_validate_extension_args__invalid_end_milestone(self):
    body = {
      'origin_trial_id': '-1234567890',
      # Invalid end milestone.
      'end_milestone': 'abc',
      'intent_thread_url': 'https://example.com/intent',
    }
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler._validate_extension_args(
            self.feature_1_id, self.ot_stage_1, body)

  def test_validate_extension_args__missing_end_milestone(self):
    body = {
      'origin_trial_id': '-1234567890',
      # Missing end milestone.
      'intent_thread_url': 'https://example.com/intent',
    }
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler._validate_extension_args(
            self.feature_1_id, self.ot_stage_1, body)

  def test_validate_extension_args__invalid_intent_url(self):
    body = {
      'origin_trial_id': '-1234567890',
      'end_milestone': '150',
      # Invalid intent thread URL.
      'intent_thread_url': 'This can\'t be right.',
    }
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler._validate_extension_args(
            self.feature_1_id, self.ot_stage_1, body)

  def test_validate_extension_args__missing_intent_url(self):
    body = {
      'origin_trial_id': '-1234567890',
      'end_milestone': '150',
      # Missing intent thread URL.
    }
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler._validate_extension_args(
            self.feature_1_id, self.ot_stage_1, body)

