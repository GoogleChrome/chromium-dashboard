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
from typing import TypedDict

from api import converters
from internals.core_enums import (
    INTENT_NONE,
    INTENT_STAGES_BY_STAGE_TYPE,
    STAGE_TYPES_PROTOTYPE,
    STAGE_TYPES_DEV_TRIAL,
    STAGE_TYPES_ORIGIN_TRIAL,
    STAGE_TYPES_EXTEND_ORIGIN_TRIAL,
    STAGE_TYPES_SHIPPING)
from internals.core_models import FeatureEntry, MilestoneSet, Stage


# Type return value of get_stage_info_for_templates()
class StageTemplateInfo(TypedDict):
  proto_stages: list[Stage]
  dt_stages: list[Stage]
  ot_stages: list[Stage]
  extension_stages: list[Stage]
  ship_stages: list[Stage]
  should_render_mstone_table: bool
  should_render_intents: bool


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


def get_stage_info_for_templates(
    fe: FeatureEntry) -> StageTemplateInfo:
  """Gather the information needed to display the estimated milestones table."""
  # Only milestones from DevTrial, OT, or shipping stages are displayed.
  id = fe.key.integer_id()
  f_type = fe.feature_type or 0
  proto_stage_type = STAGE_TYPES_PROTOTYPE[f_type]
  dt_stage_type = STAGE_TYPES_DEV_TRIAL[f_type]
  ot_stage_type = STAGE_TYPES_ORIGIN_TRIAL[f_type]
  extension_stage_type = STAGE_TYPES_EXTEND_ORIGIN_TRIAL[f_type]
  ship_stage_type = STAGE_TYPES_SHIPPING[f_type]

  stage_info: StageTemplateInfo = {
    'proto_stages': [],
    'dt_stages': [],
    'ot_stages': [],
    'extension_stages': [],
    'ship_stages': [],
    # Note if any milestones that can be displayed are seen while organizing.
    # This is used to check if rendering the milestone table is needed.
    'should_render_mstone_table': False,
    # Note if any intent URLs are seen while organizing.
    # This is used to check if rendering the table is needed.
    'should_render_intents': False,
  }

  for s in Stage.query(Stage.feature_id == id):
    # Stage info is not needed if it's not the correct stage type.
    if (s.stage_type != proto_stage_type and
        s.stage_type != dt_stage_type and
        s.stage_type != ot_stage_type and
        s.stage_type != extension_stage_type and
        s.stage_type != ship_stage_type):
      continue

    # If an intent thread is present in any stage,
    # we should render the intents template.
    if s.intent_thread_url is not None:
      stage_info['should_render_intents'] = True

    # Add stages to their respective lists.
    if s.stage_type == proto_stage_type: 
      stage_info['proto_stages'].append(s)

    # Make sure a MilestoneSet entity is referenced to avoid errors. 
    if s.milestones is None:
      s.milestones = MilestoneSet()

    m: MilestoneSet = s.milestones
    if s.stage_type == dt_stage_type:
      # Dev trial's announcement URL is rendered in templates like an intent.
      if s.announcement_url is not None:
        stage_info['should_render_intents'] = True
      stage_info['dt_stages'].append(s)
      if m.desktop_first or m.android_first or m.ios_first:
        stage_info['should_render_mstone_table'] = True
    
    if s.stage_type == ot_stage_type:
      stage_info['ot_stages'].append(s)
      if (m.desktop_first or m.android_first or m.webview_first or
          m.desktop_last or m.android_last or m.webview_last):
        stage_info['should_render_mstone_table'] = True
    
    if s.stage_type == extension_stage_type:
     stage_info['extension_stages'].append(s)
      # Extension stages are not rendered
      # in the milestones table; only for intents.

    if s.stage_type == ship_stage_type:
      stage_info['ship_stages'].append(s)
      if m.desktop_first or m.android_first or m.webview_first or m.ios_first:
        stage_info['should_render_mstone_table'] = True
  
  # Returns a dictionary of stages needed for rendering info, as well as
  # a boolean value representing whether or not the estimated milestones
  # table will need to be rendered.
  return stage_info
