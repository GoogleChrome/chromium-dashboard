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

from api import converters
from internals.core_enums import INTENT_NONE
from internals.core_models import Stage
from internals.core_models import INTENT_STAGES_BY_STAGE_TYPE


def get_feature_stages(feature_id: int) -> dict[int, list[Stage]]:
  """Return a dictionary of stages associated with a given feature."""
  # key = stage type, value = list of stages with that stage type.
  stage_dict = defaultdict(list)
  for stage in Stage.query(Stage.feature_id == feature_id):
    stage_dict[stage.stage_type].append(stage)
  return stage_dict


def get_feature_stage_ids(feature_id: int) -> dict[int, list[int]]:
  """Return a dictionary of stage IDs associated with the given feature."""
  # key = stage type, value = list of stages with that stage type.
  stage_dict = defaultdict(list)
  for stage in Stage.query(Stage.feature_id == feature_id):
    stage_dict[stage.stage_type].append(stage.key.integer_id())
  return stage_dict


def organize_all_stages_by_feature(stages: list[Stage]):
  """Return a dict with feature IDs as keys and feature's stages as values."""
  stages_by_feature = defaultdict(list)
  for stage in stages:
    stages_by_feature[stage.feature_id].append(stage)
  return stages_by_feature


def get_feature_stage_ids_list(feature_id: int) -> list[dict[str, int]]:
  """Return a list of stage types and IDs associated with a given feature."""
  q = Stage.query(Stage.feature_id == feature_id)
  q = q.order(Stage.stage_type)
  return [
    {
      'stage_id': s.key.integer_id(),
      'stage_type': s.stage_type,
      'intent_stage': INTENT_STAGES_BY_STAGE_TYPE.get(s.stage_type, INTENT_NONE)
    } for s in q]

def get_ot_stage_extensions(ot_stage_id: int):
  """Return a list of extension stages associated with a stage in JSON format"""
  q = Stage.query(Stage.ot_stage_id == ot_stage_id)
  return [converters.stage_to_json_dict(stage) for stage in q]
