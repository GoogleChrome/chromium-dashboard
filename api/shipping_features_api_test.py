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

import flask
import werkzeug.exceptions
from unittest import mock

import testing_config
from api import shipping_features_api
from internals import core_enums
from internals.core_models import Stage, MilestoneSet

test_app = flask.Flask(__name__)

# Minimal mock data to ensure json5.loads works in the handler.
MOCK_ENABLED_FEATURES_JSON5 = '{ \"data\": [] }'
MOCK_CONTENT_FEATURES_CC = 'BASE_FEATURE...'


class ShippingFeaturesAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.handler = shipping_features_api.ShippingFeaturesAPI()
    self.milestone = 120

    # Stages 1 & 2: Matches Milestone 120 (Various platforms)
    self.stage_1 = Stage(id=101, feature_id=1, stage_type=160,
        milestones=MilestoneSet(desktop_first=self.milestone))
    self.stage_1.put()

    self.stage_2 = Stage(id=102, feature_id=2, stage_type=160,
        milestones=MilestoneSet(android_first=self.milestone))
    self.stage_2.put()

    # Stage 3: Wrong Milestone (Should be ignored)
    self.stage_3 = Stage(id=106, feature_id=6, stage_type=160,
        milestones=MilestoneSet(desktop_first=self.milestone + 1))
    self.stage_3.put()

    # Stage 4: Wrong Stage Type (Dev trial, should be ignored)
    self.stage_4 = Stage(id=107, feature_id=7, stage_type=110,
        milestones=MilestoneSet(desktop_first=self.milestone))
    self.stage_4.put()

  def tearDown(self):
    for entity in Stage.query():
      entity.key.delete()

  def test_get_shipping_stages__success(self):
    """Should retrieve only stages with the correct milestone and type."""
    shipping_stages = self.handler._get_shipping_stages(self.milestone)

    # Should match stage_1 and stage_2 only.
    self.assertEqual(len(shipping_stages), 2)
    stage_ids = {s.key.integer_id() for s in shipping_stages}
    self.assertEqual(stage_ids, {101, 102})

  @mock.patch('internals.feature_helpers.aggregate_shipping_features')
  @mock.patch('api.shipping_features_api.utils.get_chromium_file')
  def test_do_get__success(self, mock_get_chromium_file, mock_aggregate):
    """Handler should fetch files and delegate logic to the helper function."""
    def mock_get_file(url):
      if url == core_enums.ENABLED_FEATURES_FILE_URL:
        return MOCK_ENABLED_FEATURES_JSON5
      if url == core_enums.CONTENT_FEATURES_FILE:
        return MOCK_CONTENT_FEATURES_CC
      return ''
    mock_get_chromium_file.side_effect = mock_get_file

    # Define the expected return from the helper
    mock_response_data = {
        'complete_features': [{'name': 'Feature 1'}],
        'incomplete_features': []
    }
    mock_aggregate.return_value = (
        mock_response_data['complete_features'],
        mock_response_data['incomplete_features']
    )

    with test_app.test_request_context(
        f'/api/v0/features/shipping?mstone={self.milestone}'):
      response = self.handler.do_get(mstone=self.milestone)

    self.assertEqual(response, mock_response_data)

    # Ensure the helper was called with the stages found in DB and the files fetched
    mock_aggregate.assert_called_once()
    call_args = mock_aggregate.call_args[0]

    # List of stages (Order matches query result)
    passed_stages = call_args[0]
    passed_stage_ids = sorted([s.key.integer_id() for s in passed_stages])
    self.assertEqual(passed_stage_ids, [101, 102])

    self.assertEqual(call_args[1], {'data': []})

    self.assertEqual(call_args[2], MOCK_CONTENT_FEATURES_CC)

    # URL root (constructed from request context)
    self.assertEqual(call_args[3], 'http://localhost')

  def test_do_get__no_features_found(self):
    """API returns empty lists immediately if no features match the milestone."""
    unmatched_milestone = 999
    with test_app.test_request_context(
        f'/api/v0/features/shipping?mstone={unmatched_milestone}'):
      response = self.handler.do_get(mstone=unmatched_milestone)

    self.assertEqual(response['complete_features'], [])
    self.assertEqual(response['incomplete_features'], [])

  def test_do_get__no_milestone(self):
    """API aborts with 400 if the milestone parameter is missing."""
    with test_app.test_request_context('/api/v0/features/shipping'):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_get()
