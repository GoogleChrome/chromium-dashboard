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
from datetime import datetime
from google.cloud import ndb  # type: ignore
from typing import TypedDict

from api import converters
from framework import utils
from internals.core_enums import (
    INTENT_NONE,
    INTENT_STAGES_BY_STAGE_TYPE,
    STAGE_TYPES_PROTOTYPE,
    STAGE_TYPES_DEV_TRIAL,
    STAGE_TYPES_ORIGIN_TRIAL,
    STAGE_TYPES_EXTEND_ORIGIN_TRIAL,
    STAGE_TYPES_SHIPPING,
    GATE_API_SHIP,
    GATE_API_EXTEND_ORIGIN_TRIAL,
    GATE_API_ORIGIN_TRIAL,
    GATE_API_PROTOTYPE)
from internals.core_models import FeatureEntry, MilestoneSet, Stage
from internals import fetchchannels
from internals.review_models import Gate


# Type return value of get_stage_info_for_templates()
class StageTemplateInfo(TypedDict):
  proto_stages: list[Stage]
  dt_stages: list[Stage]
  ot_stages: list[Stage]
  extension_stages: list[Stage]
  ship_stages: list[Stage]
  should_render_mstone_table: bool
  should_render_intents: bool

def create_feature_stage(feature_id: int, feature_type: int, stage_type: int) -> Stage:
  # Create the stage.
  stage = Stage(feature_id=feature_id, stage_type=stage_type)
  stage.put()

  # If we should create a gate and this is a stage that requires a gate,
  # create it.
  gate_type = get_gate_for_stage(feature_type, stage_type)
  if gate_type is not None:
    gate = Gate(feature_id=feature_id, stage_id=stage.key.id(), gate_type=gate_type,
        state=Gate.PREPARING)
    gate.put()

  return stage

def get_gate_for_stage(feature_type, s_type) -> int | None:
  # Update type-specific fields.
  if s_type == STAGE_TYPES_DEV_TRIAL[feature_type]: # pragma: no cover
    return GATE_API_PROTOTYPE

  if s_type == STAGE_TYPES_ORIGIN_TRIAL[feature_type]:
    return GATE_API_ORIGIN_TRIAL

  if s_type == STAGE_TYPES_EXTEND_ORIGIN_TRIAL[feature_type]:
    return GATE_API_EXTEND_ORIGIN_TRIAL

  if s_type == STAGE_TYPES_SHIPPING[feature_type]: # pragma: no cover
    return GATE_API_SHIP
  return None


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
  extension_stages =  [converters.stage_to_json_dict(stage) for stage in q]
  return sorted(extension_stages, key=lambda s: (s['created']))


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


LAST_MILESTONE_TO_YEAR: dict[int, int] = {
    # last shipped milestone of the year: calendar year
    3: 2009,
    8: 2010,
    16: 2011,
    24: 2012,
    31: 2013,
    39: 2014,
    47: 2015,
    55: 2016,
    63: 2017,
    71: 2018,
    79: 2019,
    87: 2020,
    96: 2021,
    108: 2022,
    120: 2023,
    132: 2024,
    # Later milestones are determined by chromiumdash.appspot.com.
    }


def look_up_year(milestone: int) -> int:
  """Return the calendar year in which a feature shipped."""
  for (last_milestone_of_year, year) in LAST_MILESTONE_TO_YEAR.items():
    if milestone <= last_milestone_of_year:
      return year

  release_info = fetchchannels.fetch_chrome_release_info(milestone)
  if release_info and 'final_beta' in release_info:
    shipping_date_str = release_info['final_beta']
    shipping_date = datetime.strptime(
        shipping_date_str, utils.CHROMIUM_SCHEDULE_DATE_FORMAT).date()
    shipping_year = shipping_date.year
  return shipping_year


def find_earliest_milestone(stages: list[Stage]) -> int|None:
  """Find the earliest milestone in a list of stages."""
  m_list: list[int] = []
  for stage in stages:
    if stage.milestones is None:
      continue
    m_list.append(stage.milestones.desktop_first)
    m_list.append(stage.milestones.android_first)
    m_list.append(stage.milestones.ios_first)
    m_list.append(stage.milestones.webview_first)
  m_list = [m for m in m_list if m]
  if m_list:
    return min(m_list)
  return None


def get_all_shipping_stages_with_milestones(
    feature_id: int | None = None) -> list[Stage]:
  """Return shipping stages for the specified feature or all features."""
  shipping_stage_types = [st for st in STAGE_TYPES_SHIPPING.values() if st]
  shipping_query: ndb.Query = Stage.query(
      Stage.stage_type.IN(shipping_stage_types))
  if feature_id:
    shipping_query = shipping_query.filter(
        Stage.feature_id == feature_id)
  shipping_stages: list[Stage] = shipping_query.fetch()
  shipping_stages_with_milestones = [
      stage for stage in shipping_stages
      if (stage.milestones and
          (stage.milestones.desktop_first or
           stage.milestones.android_first or
           stage.milestones.ios_first or
           stage.milestones.webview_first))]
  return shipping_stages_with_milestones
