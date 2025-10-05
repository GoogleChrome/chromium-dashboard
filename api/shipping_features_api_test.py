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
from internals.core_models import FeatureEntry, Stage, MilestoneSet
from internals.review_models import Gate, Vote

test_app = flask.Flask(__name__)


class ShippingFeaturesAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.handler = shipping_features_api.ShippingFeaturesAPI()
    self.milestone = 120

    # Feature 1: Complete - Should be in `complete_features`.
    self.feature_1 = FeatureEntry(
        id=1, name='Feature 1 (Complete)', summary='sum', category=1,
        feature_type=core_enums.FEATURE_TYPE_INCUBATE_ID,
        finch_name='feature1-finch', owner_emails=['owner@example.com'])
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
        milestones=MilestoneSet(desktop_first=self.milestone + 1)) # Future mstone
    stage_6.put()
    Gate(id=1006, feature_id=6, stage_id=106, gate_type=core_enums.GATE_API_SHIP,
         state=Vote.APPROVED).put()

    # Stage for a feature that doesn't exist - Should be logged and ignored.
    self.stage_deleted_feature = Stage(
        id=107, feature_id=999, stage_type=160,
        milestones=MilestoneSet(desktop_first=self.milestone))
    self.stage_deleted_feature.put()

  def tearDown(self):
    for kind in [FeatureEntry, Stage, Gate]:
      for entity in kind.query():
        entity.key.delete()

  def test_get_shipping_stages__success(self):
    """Should retrieve only stages with the correct milestone and type."""
    shipping_stages = self.handler._get_shipping_stages(self.milestone)
    self.assertEqual(len(shipping_stages), 6)
    
    feature_ids = {s.feature_id for s in shipping_stages}
    expected_ids = {1, 2, 3, 4, 5, 999} # Excludes feature 6 (wrong milestone)
    self.assertEqual(feature_ids, expected_ids)

  @mock.patch('logging.warning')
  def test_do_get__success(self, mock_logging):
    """Correctly categorizes features into complete and incomplete lists."""
    with test_app.test_request_context(f'/api/v0/features/shipping?mstone={self.milestone}'):
      response = self.handler.do_get(mstone=self.milestone)

    # Verify Complete Features
    complete_features = response['complete_features']
    self.assertEqual(len(complete_features), 2)
    complete_ids = {f['id'] for f in complete_features}
    # Feature 1 is complete, Feature 5 is a PSA that bypasses checks.
    self.assertEqual(complete_ids, {self.feature_1.key.integer_id(), self.feature_5.key.integer_id()})

    # Verify Incomplete Features
    incomplete_features = response['incomplete_features']
    self.assertEqual(len(incomplete_features), 3)

    # Use a dictionary for easy, order-independent lookup and assertion.
    incomplete_map = {
        item[0]['id']: item[1] for item in incomplete_features
    }
    self.assertIn(self.feature_2.key.integer_id(), incomplete_map)
    self.assertEqual(incomplete_map[self.feature_2.key.integer_id()], ['lgtms'])

    self.assertIn(self.feature_3.key.integer_id(), incomplete_map)
    self.assertEqual(incomplete_map[self.feature_3.key.integer_id()], ['i2s'])

    self.assertIn(self.feature_4.key.integer_id(), incomplete_map)
    self.assertEqual(incomplete_map[self.feature_4.key.integer_id()], ['finch_name'])

    # Verify that the missing feature was logged
    mock_logging.assert_called_once_with('Feature 999 not found.')


  def test_do_get__invalid_milestone(self):
    """API aborts with a 400 error for invalid milestone values."""
    with test_app.test_request_context('/api/v0/features/shipping?mstone=abc'):
      with self.assertRaisesRegex(werkzeug.exceptions.BadRequest, 'Invalid milestone'):
        self.handler.do_get(mstone='abc')

    with test_app.test_request_context('/api/v0/features/shipping'):
      with self.assertRaisesRegex(werkzeug.exceptions.BadRequest, 'No milestone provided'):
        self.handler.do_get(mstone=None)

  def test_do_get__no_features_found(self):
    """API returns empty lists when no features match the milestone."""
    unmatched_milestone = 99
    with test_app.test_request_context(f'/api/v0/features/shipping?mstone={unmatched_milestone}'):
      response = self.handler.do_get(mstone=unmatched_milestone)
    
    self.assertEqual(response['complete_features'], [])
    self.assertEqual(response['incomplete_features'], [])
