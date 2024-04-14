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
from unittest import mock

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

    self.mock_usecounters_file = """
enum WebFeature {
  kSomeFeature = 1,
  kValidFeature = 2,
  kNoThirdParty = 3
  kSample = 4,
  kNoCriticalTrial = 5,
};
"""

    self.mock_features_file = """
{
  "data": [
    {
      "name": "ValidFeaturePart1",
      "origin_trial_feature_name": "ValidFeature",
      "origin_trial_allows_third_party": true
    },
    {
      "name": "ValidFeaturePart2",
      "origin_trial_feature_name": "ValidFeature",
      "origin_trial_allows_third_party": true
    },
    {
      "name": "InvalidFeaturePart1",
      "origin_trial_feature_name": "InvalidFeature"
    },
    {
      "name": "NoThirdParty",
      "origin_trial_feature_name": "NoThirdParty"
    },
    {
      "name": "NoCriticalTrialEntry",
      "origin_trial_feature_name": "NoCriticalTrial"
    }
  ]
}
"""

    self.mock_grace_period_file = """
bool FeatureHasExpiryGracePeriod(blink::mojom::OriginTrialFeature feature) {
  static blink::mojom::OriginTrialFeature const kHasExpiryGracePeriod[] = {
      // Production grace period trials start here:
      blink::mojom::OriginTrialFeature::kSomeFeature,
      blink::mojom::OriginTrialFeature::kValidFeature,
      blink::mojom::OriginTrialFeature::kInvalidFeature,
  };
  return base::Contains(kHasExpiryGracePeriod, feature);
}
"""

    self.existing_origin_trials = [
      {
        'origin_trial_feature_name': 'ExistingFeature',
      }
    ]

  def tearDown(self):
    for kind in [FeatureEntry, Stage]:
      for entity in kind.query():
        entity.key.delete()

  @mock.patch('api.origin_trials_api.get_chromium_file')
  def test_validate_creation_args__valid(self, mock_get_chromium_file):
    mock_get_chromium_file.side_effect = [
      self.mock_features_file,
      self.mock_usecounters_file,
      self.mock_grace_period_file]

    body = {
      'ot_chromium_trial_name': 'ValidFeature',
      'ot_webfeature_use_counter': 'kValidFeature',
      'ot_is_critical_trial': True,
      'ot_is_deprecation_trial': False,
      'ot_has_third_party_support': True,
    }
    # No exception should be raised.
    with test_app.test_request_context(self.request_path):
      self.handler._validate_creation_args(body)

  @mock.patch('api.origin_trials_api.get_chromium_file')
  def test_validate_creation_args__invalid_webfeature_use_counter(
      self, mock_get_chromium_file):
    mock_get_chromium_file.side_effect = [
      self.mock_features_file,
      self.mock_usecounters_file,
      self.mock_grace_period_file]
    body = {
      'ot_chromium_trial_name': 'ValidFeature',
      'ot_webfeature_use_counter': 'kBadUseCounter',
      'ot_is_critical_trial': False,
      'ot_is_deprecation_trial': False,
      'ot_has_third_party_support': False,
    }
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler._validate_creation_args(body)

  @mock.patch('api.origin_trials_api.get_chromium_file')
  def test_validate_creation_args__invalid_chromium_trial_name(
      self, mock_get_chromium_file):
    mock_get_chromium_file.side_effect = [
      self.mock_features_file,
      self.mock_usecounters_file,
      self.mock_grace_period_file]
    body = {
      'ot_chromium_trial_name': 'NonexistantFeature',
      'ot_webfeature_use_counter': 'kValidFeature',
      'ot_is_critical_trial': False,
      'ot_is_deprecation_trial': False,
      'ot_has_third_party_support': False,
    }
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler._validate_creation_args(body)

  @mock.patch('api.origin_trials_api.get_chromium_file')
  def test_validate_creation_args__invalid_third_party_trial(
      self, mock_get_chromium_file):
    mock_get_chromium_file.side_effect = [
      self.mock_features_file,
      self.mock_usecounters_file,
      self.mock_grace_period_file]
    body = {
      'ot_chromium_trial_name': 'NoThirdParty',
      'ot_webfeature_use_counter': 'kNoThirdParty',
      'ot_is_critical_trial': False,
      'ot_is_deprecation_trial': False,
      'ot_has_third_party_support': True,
    }
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler._validate_creation_args(body)

  @mock.patch('api.origin_trials_api.get_chromium_file')
  def test_validate_creation_args__invalid_critical_trial(
      self, mock_get_chromium_file):
    mock_get_chromium_file.side_effect = [
      self.mock_features_file,
      self.mock_usecounters_file,
      self.mock_grace_period_file]
    body = {
      'ot_chromium_trial_name': 'NoCriticalTrial',
      'ot_webfeature_use_counter': 'kNoCriticalTrial',
      'ot_is_critical_trial': True,
      'ot_is_deprecation_trial': False,
      'ot_has_third_party_support': False,
    }
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler._validate_creation_args(body)

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
