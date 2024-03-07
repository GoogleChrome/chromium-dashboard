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
from internals.core_models import FeatureEntry, MilestoneSet, Stage
from internals.review_models import Gate, Vote

test_app = flask.Flask(__name__)


class OriginTrialsAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = FeatureEntry(
        feature_type=1, name='feature one', summary='sum', category=1)
    self.feature_1.put()
    self.feature_1_id = self.feature_1.key.integer_id()
    self.ot_stage_1 = Stage(
        feature_id=self.feature_1_id, stage_type=150,
        origin_trial_id='-1234567890')
    self.ot_stage_1.put()

    self.extension_stage_1 = Stage(
        feature_id=self.feature_1_id, stage_type=151, 
        ot_stage_id=self.ot_stage_1.key.integer_id(),
        milestones=MilestoneSet(desktop_last=153),
        intent_thread_url='https://example.com/intent')
    self.extension_stage_1.put()
    self.extension_gate_1 = Gate(feature_id=self.feature_1_id,
                stage_id=self.extension_stage_1.key.integer_id(),
                gate_type=3, state=Vote.APPROVED)
    self.extension_gate_1.put()

    self.feature_2 = FeatureEntry(
        feature_type=1, name='feature two', summary='sum', category=1)
    self.feature_2.put()
    self.ot_stage_2 = Stage(
        feature_id=self.feature_2.key.integer_id(), stage_type=150,
        origin_trial_id='9876543210')
    self.ot_stage_2.put()
    self.handler = origin_trials_api.OriginTrialsAPI()
    self.request_path = (
        '/api/v0/origintrials/'
        f'{self.feature_1_id}/{self.extension_stage_1.key.integer_id()}/extend')

  def tearDown(self):
    for kind in [FeatureEntry, Stage]:
      for entity in kind.query():
        entity.key.delete()

  def test_validate_extension_args__valid(self):
    # No exception should be raised.
    with test_app.test_request_context(self.request_path):
      self.handler._validate_extension_args(
          self.feature_1_id, self.ot_stage_1, self.extension_stage_1)

  def test_validate_extension_args__missing_ot_id(self):
    self.ot_stage_1.origin_trial_id = None
    self.ot_stage_1.put()
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler._validate_extension_args(
            self.feature_1_id, self.ot_stage_1, self.extension_stage_1)

  def test_validate_extension_args__missing_end_milestone(self):
    self.extension_stage_1.milestones.desktop_last = None
    self.extension_stage_1.put()
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler._validate_extension_args(
            self.feature_1_id, self.ot_stage_1, self.extension_stage_1)

  def test_validate_extension_args__invalid_intent_url(self):
    self.extension_stage_1.intent_thread_url = 'This can\'t be right.'
    self.extension_stage_1.put()
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler._validate_extension_args(
            self.feature_1_id, self.ot_stage_1, self.extension_stage_1)

  def test_validate_extension_args__missing_intent_url(self):
    self.extension_stage_1.intent_thread_url = None
    self.extension_stage_1.put()
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler._validate_extension_args(
            self.feature_1_id, self.ot_stage_1, self.extension_stage_1)

  def test_validate_extension_args__not_approved(self):
    self.extension_gate_1.state = Vote.NA
    self.extension_gate_1.put()
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler._validate_extension_args(
            self.feature_1_id, self.ot_stage_1, self.extension_stage_1)
