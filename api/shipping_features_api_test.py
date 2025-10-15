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
import json5
import werkzeug.exceptions
from unittest import mock

import testing_config
from api import shipping_features_api
from internals import core_enums
from internals.core_models import FeatureEntry, Stage, MilestoneSet
from internals.review_models import Gate, Vote

test_app = flask.Flask(__name__)

# Mock data representing the content of Chromium source files.
MOCK_ENABLED_FEATURES_JSON5 = """
{
  "data": [
    // For feature_1: A complete feature that is stable.
    { "name": "featureOneFinch", "status": "stable" },
    // For feature_7: An incomplete feature that is not stable.
    { "name": "feature7-unstable", "status": "experimental" }
  ]
}
"""

MOCK_CONTENT_FEATURES_CC = """
// Some C++ code here...
// For feature_8: A complete feature, enabled by default.
BASE_FEATURE(kFeature8Enabled,
             // Some rogue comment.
             base::FEATURE_ENABLED_BY_DEFAULT);
// More C++ code...
// For feature_9: An incomplete feature, disabled by default.
BASE_FEATURE(kFeature9Disabled, base::FEATURE_DISABLED_BY_DEFAULT);
// Even more C++ code...
"""


class ShippingFeaturesAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.handler = shipping_features_api.ShippingFeaturesAPI()
    self.milestone = 120

    # Feature 1: Complete - Should be in `complete_features`.
    # Finch name 'featureOneFinch' is in MOCK_ENABLED_FEATURES_JSON5 as "stable".
    self.feature_1 = FeatureEntry(
        id=1, name='Feature 1 (Complete)', summary='sum', category=1,
        feature_type=core_enums.FEATURE_TYPE_INCUBATE_ID,
        finch_name='featureOneFinch', owner_emails=['owner@example.com'])
    self.feature_1.put()
    stage_1 = Stage(
        id=101, feature_id=1, stage_type=160,  # Shipping stage
        intent_thread_url='https://example.com/intent1',
        milestones=MilestoneSet(desktop_first=self.milestone))
    stage_1.put()
    Gate(id=1001, feature_id=1, stage_id=101, gate_type=core_enums.GATE_API_SHIP,
         state=Vote.APPROVED).put()

    # Feature 2: Incomplete (Missing LGTM) - Should be in `incomplete_features`.
    self.feature_2 = FeatureEntry(
        id=2, name='Feature 2 (No LGTM)', summary='sum', category=1,
        feature_type=core_enums.FEATURE_TYPE_INCUBATE_ID,
        finch_name='feature2-finch')
    self.feature_2.put()
    stage_2 = Stage(
        id=102, feature_id=2, stage_type=160,
        intent_thread_url='https://example.com/intent2',
        milestones=MilestoneSet(android_first=self.milestone))
    stage_2.put()
    Gate(id=1002, feature_id=2, stage_id=102, gate_type=core_enums.GATE_API_SHIP,
         state=Vote.NA).put()  # Not approved

    # Feature 3: Incomplete (Missing Intent to Ship).
    self.feature_3 = FeatureEntry(
        id=3, name='Feature 3 (No I2S)', summary='sum', category=1,
        feature_type=core_enums.FEATURE_TYPE_INCUBATE_ID,
        finch_name='feature3-finch')
    self.feature_3.put()
    stage_3 = Stage(
        id=103, feature_id=3, stage_type=160,
        intent_thread_url=None,  # Missing intent
        milestones=MilestoneSet(webview_first=self.milestone))
    stage_3.put()
    Gate(id=1003, feature_id=3, stage_id=103, gate_type=core_enums.GATE_API_SHIP,
         state=Vote.APPROVED).put()
    Gate(id=1010, feature_id=3, stage_id=103,
         gate_type=core_enums.GATE_DEBUGGABILITY_SHIP, # Not an API owners gate.
         state=Vote.APPROVED).put()

    # Feature 4: Incomplete (Missing Finch name and justification).
    self.feature_4 = FeatureEntry(
        id=4, name='Feature 4 (No Finch)', summary='sum', category=1,
        feature_type=core_enums.FEATURE_TYPE_INCUBATE_ID,
        finch_name=None, non_finch_justification=None)  # Both missing
    self.feature_4.put()
    stage_4 = Stage(
        id=104, feature_id=4, stage_type=160,
        intent_thread_url='https://example.com/intent4',
        milestones=MilestoneSet(desktop_first=self.milestone))
    stage_4.put()
    Gate(id=1004, feature_id=4, stage_id=104, gate_type=core_enums.GATE_API_SHIP,
         state=Vote.APPROVED).put()

    # Feature 5: Complete (PSA/Code Change) - Bypasses checks.
    self.feature_5 = FeatureEntry(
        id=5, name='Feature 5 (PSA)', summary='sum', category=1,
        feature_type=core_enums.FEATURE_TYPE_CODE_CHANGE_ID) # PSA type
    self.feature_5.put()
    stage_5 = Stage(
        id=105, feature_id=5, stage_type=360,
        milestones=MilestoneSet(desktop_first=self.milestone))
    stage_5.put()

    # Feature 6: Wrong Milestone - Should be excluded entirely.
    self.feature_6 = FeatureEntry(
        id=6, name='Feature 6 (Wrong Mstone)', summary='sum', category=1,
        feature_type=core_enums.FEATURE_TYPE_INCUBATE_ID,
        finch_name='feature6-finch')
    self.feature_6.put()
    stage_6 = Stage(
        id=106, feature_id=6, stage_type=160,
        intent_thread_url='https://example.com/intent6',
        milestones=MilestoneSet(desktop_first=self.milestone + 1))  # Future mstone
    stage_6.put()
    Gate(id=1006, feature_id=6, stage_id=106, gate_type=core_enums.GATE_API_SHIP,
         state=Vote.APPROVED).put()

    # Feature 7: Incomplete (Not stable in runtime_enabled_features.json5).
    self.feature_7 = FeatureEntry(
        id=7, name='F7 Unstable', summary='sum', category=1,
        feature_type=core_enums.FEATURE_TYPE_INCUBATE_ID,
        finch_name='feature7-unstable')
    self.feature_7.put()
    stage_7 = Stage(
        id=107, feature_id=7, stage_type=160,
        intent_thread_url='https://example.com/intent7',
        milestones=MilestoneSet(desktop_first=self.milestone))
    stage_7.put()
    Gate(id=1007, feature_id=7, stage_id=107, gate_type=core_enums.GATE_API_SHIP,
         state=Vote.APPROVED).put()

    # Feature 8: Complete (Enabled in content_features.cc).
    self.feature_8 = FeatureEntry(
        id=8, name='F8 Enabled', summary='sum', category=1,
        feature_type=core_enums.FEATURE_TYPE_INCUBATE_ID,
        finch_name='Feature8Enabled')
    self.feature_8.put()
    stage_8 = Stage(
        id=108, feature_id=8, stage_type=160,
        intent_thread_url='https://example.com/intent8',
        milestones=MilestoneSet(desktop_first=self.milestone))
    stage_8.put()
    Gate(id=1008, feature_id=8, stage_id=108, gate_type=core_enums.GATE_API_SHIP,
         state=Vote.APPROVED).put()

    # Feature 9: Incomplete (Disabled in content_features.cc).
    self.feature_9 = FeatureEntry(
        id=9, name='F9 Disabled', summary='sum', category=1,
        feature_type=core_enums.FEATURE_TYPE_INCUBATE_ID,
        finch_name='Feature9Disabled')
    self.feature_9.put()
    stage_9 = Stage(
        id=109, feature_id=9, stage_type=160,
        intent_thread_url='https://example.com/intent9',
        milestones=MilestoneSet(desktop_first=self.milestone))
    stage_9.put()
    Gate(id=1009, feature_id=9, stage_id=109, gate_type=core_enums.GATE_API_SHIP,
         state=Vote.APPROVED).put()

    # Feature 10: Incomplete (Not found in Chromium files).
    self.feature_10 = FeatureEntry(
        id=10, name='F10 Not Found', summary='sum', category=1,
        feature_type=core_enums.FEATURE_TYPE_INCUBATE_ID,
        finch_name='non-existent-feature')
    self.feature_10.put()
    stage_10 = Stage(
        id=110, feature_id=10, stage_type=160,
        intent_thread_url='https://example.com/intent10',
        milestones=MilestoneSet(desktop_first=self.milestone))
    stage_10.put()
    Gate(id=1010, feature_id=10, stage_id=110, gate_type=core_enums.GATE_API_SHIP,
         state=Vote.APPROVED).put()


    # Stage for a feature that doesn't exist - Should be logged and ignored.
    self.stage_deleted_feature = Stage(
        id=999, feature_id=999, stage_type=160,
        milestones=MilestoneSet(desktop_first=self.milestone))
    self.stage_deleted_feature.put()

  def tearDown(self):
    for kind in [FeatureEntry, Stage, Gate]:
      for entity in kind.query():
        entity.key.delete()

  def test_get_shipping_stages__success(self):
    """Should retrieve only stages with the correct milestone and type."""
    shipping_stages = self.handler._get_shipping_stages(self.milestone)
    # 10 stages are in the target milestone (stages for features 1-5, 7-10,
    # and the deleted feature 999).
    self.assertEqual(len(shipping_stages), 10)

    feature_ids = {s.feature_id for s in shipping_stages}
    expected_ids = {1, 2, 3, 4, 5, 7, 8, 9, 10, 999}
    self.assertEqual(feature_ids, expected_ids)

  def test_validate_feature_in_chromium__all_cases(self):
    """Tests the validation logic against mock Chromium file content."""
    handler = shipping_features_api.ShippingFeaturesAPI()
    enabled_features_json = json5.loads(MOCK_ENABLED_FEATURES_JSON5)
    content_features_file = MOCK_CONTENT_FEATURES_CC

    # Case 1: Found in JSON and stable -> No missing criteria.
    result = handler._validate_feature_in_chromium(
        'featureOneFinch', enabled_features_json, content_features_file)
    self.assertEqual(result, [])

    # Case 2: Found in JSON but not stable.
    result = handler._validate_feature_in_chromium(
        'feature7-unstable', enabled_features_json, content_features_file)
    self.assertEqual(result,
        [shipping_features_api.Criteria.RUNTIME_FEATURE_NOT_STABLE])

    # Case 3: Found in .cc file and enabled.
    result = handler._validate_feature_in_chromium(
        'Feature8Enabled', enabled_features_json, content_features_file)
    self.assertEqual(result, [])

    # Case 4: Found in .cc file but disabled.
    result = handler._validate_feature_in_chromium(
        'Feature9Disabled', enabled_features_json, content_features_file)
    self.assertEqual(result,
        [shipping_features_api.Criteria.CONTENT_FEATURE_NOT_ENABLED])

    # Case 5: Not found in either file.
    result = handler._validate_feature_in_chromium(
        'not-a-real-feature', enabled_features_json, content_features_file)
    self.assertEqual(result,
        [shipping_features_api.Criteria.CHROMIUM_FEATURE_NOT_FOUND])


  @mock.patch('logging.warning')
  @mock.patch('api.shipping_features_api.utils.get_chromium_file')
  def test_do_get__success(self, mock_get_chromium_file, mock_logging):
    """Correctly categorizes features into complete and incomplete lists."""
    def mock_get_file(url):
      if url == core_enums.ENABLED_FEATURES_FILE_URL:
        return MOCK_ENABLED_FEATURES_JSON5
      if url == core_enums.CONTENT_FEATURES_FILE:
        return MOCK_CONTENT_FEATURES_CC
      return ''
    mock_get_chromium_file.side_effect = mock_get_file

    with test_app.test_request_context(
        f'/api/v0/features/shipping?mstone={self.milestone}'):
      response = self.handler.do_get(mstone=self.milestone)

    # Verify Complete Features
    complete_features = response['complete_features']
    self.assertEqual(len(complete_features), 3)
    # feature_1 is complete.
    # feature_5 is a PSA that bypasses checks.
    # feature_8 is enabled in the mock .cc file.
    expected_complete_urls = {
        'http://localhost/feature/1',
        'http://localhost/feature/5',
        'http://localhost/feature/8'
    }
    self.assertEqual(set(complete_features), expected_complete_urls)

    # Verify Incomplete Features
    incomplete_features = response['incomplete_features']
    self.assertEqual(len(incomplete_features), 6)

    incomplete_map = {
        int(url.split('/')[-1]): reasons
        for url, reasons in incomplete_features
    }
    # Feature 2: Missing LGTM
    self.assertIn(self.feature_2.key.id(), incomplete_map)
    self.assertEqual(incomplete_map[self.feature_2.key.id()],
                     ['lgtms', 'chromium_feature_not_found'])
    # Feature 3: Missing Intent to Ship
    self.assertIn(self.feature_3.key.id(), incomplete_map)
    self.assertEqual(incomplete_map[self.feature_3.key.id()],
                     ['i2s', 'chromium_feature_not_found'])
    # Feature 4: Missing Finch name
    self.assertIn(self.feature_4.key.id(), incomplete_map)
    self.assertEqual(incomplete_map[self.feature_4.key.id()], ['finch_name'])
    # Feature 7: Not stable in JSON
    self.assertIn(self.feature_7.key.id(), incomplete_map)
    self.assertEqual(
        incomplete_map[self.feature_7.key.id()], ['runtime_feature_not_stable'])
    # Feature 9: Not enabled in .cc file
    self.assertIn(self.feature_9.key.id(), incomplete_map)
    self.assertEqual(
        incomplete_map[self.feature_9.key.id()], ['content_feature_not_enabled'])
    # Feature 10: Not found in Chromium files
    self.assertIn(self.feature_10.key.id(), incomplete_map)
    self.assertEqual(
        incomplete_map[self.feature_10.key.id()], ['chromium_feature_not_found'])

    # Verify that the missing feature was logged
    mock_logging.assert_called_once_with('Feature 999 not found.')

  def test_do_get__no_features_found(self):
    """API returns empty lists when no features match the milestone."""
    unmatched_milestone = 99
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
