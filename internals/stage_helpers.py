# -*- coding: utf-8 -*-
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

from collections import defaultdict

from internals.core_models import Stage

def get_feature_stages(feature_id: int) -> dict[int, Stage]:
  """Return a dictionary of stages associated with a given feature."""
  stage_dict = defaultdict(list)
  for stage in Stage.query(Stage.feature_id == feature_id):
    stage_dict[stage.stage_type].append(stage)
  return stage_dict

def get_feature_stage_ids(feature_id: int) -> dict[int, list[int]]:
  stage_dict = defaultdict(list)
  for stage in Stage.query(Stage.feature_id == feature_id):
    stage_dict[stage.stage_type].append(stage.key.integer_id())
  return stage_dict
