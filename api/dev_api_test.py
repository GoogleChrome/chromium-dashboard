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

import testing_config

from google.cloud import ndb  # type: ignore

from api import dev_api
from internals import stage_helpers
from internals.core_models import FeatureEntry, Stage
from internals.legacy_models import Feature
from internals.review_models import Gate

class DevAPITest(testing_config.CustomTestCase):

  def tearDown(self):
    for kind in [Feature, FeatureEntry, Stage, Gate]:
      for entity in kind.query():
        entity.key.delete()

  def test_write_dev_data(self):
    """Dev data script writes accurate data."""
    handler_class = dev_api.WriteDevData()
    handler_class.do_get()

    fes: list[FeatureEntry] = FeatureEntry.query().fetch()
    self.assertTrue(len(fes) > 0)
    for fe in fes:
      stages = stage_helpers.get_feature_stages(fe.key.integer_id())
      # At least 1 stage should be created for each possible stage
      # a feature could have.
      for stages_of_type in stages.values():
        self.assertTrue(len(stages_of_type) > 0)
    
    gates: list[Gate] = Gate.query().fetch()
    for gate in gates:
      # Each gate should have a stage ID that matches an existing stage.
      stage = Stage.get_by_id(gate.stage_id)
      self.assertIsNotNone(stage)

  def test_clear_entities(self):
    """Script successfully deletes most major entities."""
    f_1 = Feature(id=1, name='feature one', summary='summary',
        category=1, impl_status_chrome=1)
    fe_1 = FeatureEntry(id=1, name='feature one', summary='summary',
        category=1, impl_status_chrome=1)
    stage = Stage(id=2, feature_id=1, stage_type=160)
    gate = Gate(id=3, feature_id=1, stage_id=2, gate_type=4, state=1)
    f_1.put()
    fe_1.put()
    stage.put()
    gate.put()

    handler_class = dev_api.ClearEntities()
    handler_class.do_get()

    kinds: list[ndb.Model] = [Feature, FeatureEntry, Stage, Gate]
    for kind in kinds:
      self.assertTrue(len(kind.query().fetch()) == 0)
