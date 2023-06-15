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

from internals import core_enums
from internals import stage_helpers
from internals.core_models import FeatureEntry, Stage


class StageHelpersTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_entry_1 = FeatureEntry(id=1, name='fe one',
        summary='summary', category=1, impl_status_chrome=1, feature_type=1,
        standard_maturity=1, web_dev_views=1)
    self.feature_entry_1.put()
    stage_types = [core_enums.STAGE_DEP_PLAN, core_enums.STAGE_DEP_DEV_TRIAL,
        core_enums.STAGE_DEP_DEPRECATION_TRIAL, core_enums.STAGE_DEP_SHIPPING,
        core_enums.STAGE_DEP_REMOVE_CODE]
    self.feature_id = self.feature_entry_1.key.integer_id()
    self.feature_type = self.feature_entry_1.feature_type
    for stage_type in stage_types:
      stage = Stage(feature_id=self.feature_id, stage_type=stage_type)
      stage.put()

  def tearDown(self):
    self.feature_entry_1.key.delete()
    for stage in Stage.query().fetch():
      stage.key.delete()
  
  def test_get_feature_stages(self):
    """A dictionary with stages relevant to the feature should be present."""
    stage_dict = stage_helpers.get_feature_stages(self.feature_id)
    list_stages = stage_dict.items()
    expected_stage_types = {410, 430, 450, 460, 470}
    # Extension stage type was not created, so it should not appear.
    self.assertIsNone(stage_dict.get(451, None))
    self.assertEqual(len(list_stages), 5)
    for stage_type, stages_list in stage_dict.items():
      self.assertTrue(stage_type in expected_stage_types)
      self.assertEqual(stages_list[0].stage_type, stage_type)
      expected_stage_types.remove(stage_type)
  
  def test_create_feature_stage(self):
    """A dictionary with stages relevant to the feature should be present."""
    stage_dict = stage_helpers.get_feature_stages(self.feature_id)
    list_stages = stage_dict.items()
    expected_stage_types = {410, 430, 450, 460, 470}
    self.assertEqual(len(list_stages), 5)
    for stage_type, stages_list in stage_dict.items():
      self.assertTrue(stage_type in expected_stage_types)
      self.assertEqual(stages_list[0].stage_type, stage_type)
      expected_stage_types.remove(stage_type)

    stage_helpers.create_feature_stage(
      self.feature_id,
      self.feature_type,
      core_enums.STAGE_ENT_ROLLOUT)
    stage_helpers.create_feature_stage(
      self.feature_id,
      self.feature_type,
      core_enums.STAGE_ENT_SHIPPED)
    stage_dict = stage_helpers.get_feature_stages(self.feature_id)
    list_stages = stage_dict.items()
    expected_stage_types = {410, 430, 450, 460, 470, 1061, 1070}
    self.assertEqual(len(list_stages), 7)
    for stage_type, stages_list in stage_dict.items():
      self.assertTrue(stage_type in expected_stage_types)
      self.assertEqual(stages_list[0].stage_type, stage_type)
      expected_stage_types.remove(stage_type)

