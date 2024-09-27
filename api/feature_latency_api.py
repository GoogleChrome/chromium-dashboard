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

from datetime import datetime, timedelta
import logging
from typing import Any

from chromestatus_openapi.models.feature_link import FeatureLink
from chromestatus_openapi.models.feature_latency import FeatureLatency

from api import channels_api
from framework import basehandlers
from framework import permissions
from internals import stage_helpers
from internals.core_enums import *
from internals.core_models import FeatureEntry, Stage


class FeatureLatencyAPI(basehandlers.APIHandler):
  """Implements the OpenAPI /feature_latency path."""

  def get_date_range(
      self, request_args: dict[str, str]
  ) -> tuple[datetime, datetime]:
    """Parse start and end dates from query-string params."""
    start_param: str | None = request_args.get('startAt')
    if start_param:
      try:
        start_date = datetime.fromisoformat(start_param)
      except ValueError:
        self.abort(400, f'invalid ?startAt parameter {start_param}')
    else:
      self.abort(400, 'missing ?startAt parameter')

    end_param: str | None = request_args.get('endAt')
    if end_param:
      try:
        end_date = datetime.fromisoformat(end_param)
      except ValueError:
        self.abort(400, f'invalid ?endAt parameter {end_param}')
    else:
      self.abort(400, 'missing ?endAt parameter')

    return start_date, end_date

  @permissions.require_create_feature
  def do_get(self, **kwargs):
    """Calculate feature latency for features in a date range.

    Returns:
      A list of FeatureLatency objects for each matching feature.
    """
    start_date, end_date = self.get_date_range(self.request.args)
    logging.info('range %r %r', start_date, end_date)
    features = self.get_features_to_consider(start_date, end_date)
    ship_milestone_by_fid = self.get_shipped_milestones(features)
    milestone_details = self.get_milestone_details(ship_milestone_by_fid)
    matching_features = self.filter_out_unshipped_features(
        features, ship_milestone_by_fid, start_date, end_date,
        milestone_details)
    result = self.convert_to_result_format(
        matching_features, ship_milestone_by_fid, milestone_details)
    return result

  def get_features_to_consider(
      self, start_date: datetime, end_date: datetime) -> list[FeatureEntry]:
    """Get all shipped feature entries that were created before end date."""
    fe_query = FeatureEntry.query().order(FeatureEntry.created)
    fe_query = fe_query.filter(
        FeatureEntry.created > start_date - timedelta(days=2*365))
    fe_query = fe_query.filter(FeatureEntry.created < end_date)
    features = fe_query.fetch(None)
    logging.info('features %r', [fe.name for fe in features])
    features = [
        fe for fe in features
        if (not fe.deleted and
            fe.impl_status_chrome in [ENABLED_BY_DEFAULT, DEPRECATED, REMOVED])]
    return features

  def get_shipped_milestones(
      self, features: list[FeatureEntry]
  ) -> dict[int, int]:
    """Get all the ship Stages for those features to find shipping milestones."""
    feature_ids = {fe.key.integer_id() for fe in features}
    logging.info('feature_ids %r', feature_ids)
    if not feature_ids:
      return {}
    stage_query = Stage.query()
    stage_query = stage_query.filter(Stage.feature_id.IN(feature_ids))
    stage_query = stage_query.filter(Stage.stage_type.IN([
        STAGE_BLINK_SHIPPING, STAGE_PSA_SHIPPING,
        STAGE_FAST_SHIPPING, STAGE_DEP_SHIPPING, STAGE_ENT_ROLLOUT]))
    stages = stage_query.fetch(None)
    stages = [s for s in stages if not s.archived]
    if not stages:
      return {}
    stages_by_fid = stage_helpers.organize_all_stages_by_feature(stages)

    ship_milestone_by_fid: dict[int, int] = {}
    for f_id, feature_stages in stages_by_fid.items():
      for s in feature_stages:
        if not s or not s.milestones:
          continue
        if s.milestones.desktop_first:
          if (ship_milestone_by_fid.get(f_id, 9999) >
              s.milestones.desktop_first):
            ship_milestone_by_fid[f_id] = s.milestones.desktop_first
        if s.milestones.android_first:
          if (ship_milestone_by_fid.get(f_id, 9999) >
              s.milestones.android_first):
            ship_milestone_by_fid[f_id] = s.milestones.android_first

    return ship_milestone_by_fid

  def get_milestone_details(
      self, ship_milestone_by_fid: dict[int, int]
  )-> dict[int, dict[str, Any]] :
    """Get all the milestone details, including branch date."""
    if not ship_milestone_by_fid:
      return {}
    milestone_details = channels_api.construct_specified_milestones_details(
        min(ship_milestone_by_fid.values()),
        max(ship_milestone_by_fid.values()))
    for m in milestone_details:
      logging.info(
          'M%d: branch_point %r', m, milestone_details[m].get('branch_point'))

    return milestone_details

  def filter_out_unshipped_features(
      self, features: list[FeatureEntry],
      ship_milestone_by_fid: dict[int, int],
      start_date: datetime,
      end_date: datetime,
      milestone_details: dict[int, dict[str, Any]]
  ) -> list[FeatureEntry]:
    """Return only features that shipped in milestones that branched
       between start_date and end_date."""
    if not milestone_details:
      return []
    start_date_iso = start_date.isoformat()
    end_date_iso = end_date.isoformat()
    lowest_milestone_in_range = min(
      m for m in milestone_details
      if milestone_details[m].get('branch_point', '0') >= start_date_iso)
    highest_milestone_in_range = max(
      m for m in milestone_details
      if milestone_details[m].get('branch_point', '9') <= end_date_iso)
    logging.info('highest_milestone_in_range: %r', highest_milestone_in_range)
    matching_features = [
        fe for fe in features
        if (ship_milestone_by_fid.get(fe.key.integer_id()) and
            lowest_milestone_in_range <=
            ship_milestone_by_fid[fe.key.integer_id()] <=
            highest_milestone_in_range)]
    return matching_features

  def convert_to_result_format(
      self, matching_features: list[FeatureEntry],
      ship_milestone_by_fid: dict[int, int],
      milestone_details: dict[int, dict[str, Any]]
  ) -> list[dict[str, Any]]:
    """Stuff results into OpenAPI objects and convert to python dicts."""
    result = []
    for fe in matching_features:
      m = ship_milestone_by_fid.get(fe.key.integer_id())
      if m and milestone_details[m].get('branch_point'):
        result.append(FeatureLatency(
            feature=FeatureLink(id=fe.key.integer_id(), name=fe.name),
            entry_created_date=fe.created.isoformat(),
            shipped_milestone=m,
            shipped_date=milestone_details[m]['branch_point'],
            owner_emails=fe.owner_emails).to_dict())

    return result
