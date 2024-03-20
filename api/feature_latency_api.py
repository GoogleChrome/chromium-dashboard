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

from datetime import datetime
import logging

from chromestatus_openapi.models.feature_link import FeatureLink
from chromestatus_openapi.models.feature_latency import FeatureLatency

from api import channels_api
from framework import basehandlers
from internals import stage_helpers
from internals.core_enums import *
from internals.core_models import FeatureEntry, Stage


class FeatureLatencyAPI(basehandlers.APIHandler):
  """Implements the OpenAPI /feature_latency path."""

  def get_date_range(
      self, request_args: dict[str, str]
  ) -> tuple[datetime|None, datetime|None]:
    """Parse start and end dates from query-string params."""
    start_param: str | None = request_args.get('startDate', None)
    start_date: datetime | None = None
    if start_param is not None:
      try:
        start_date = datetime.fromisoformat(start_param)
      except ValueError:
        self.abort(400, f'invalid ?startDate parameter {start_param}')

    end_param: str | None = request_args.get('endDate', None)
    end_date: datetime | None = None
    if end_param is not None:
      try:
        end_date = datetime.fromisoformat(end_param)
      except ValueError:
        self.abort(400, f'invalid ?endDate parameter {end_param}')

    return start_date, end_date

  def do_get(self, **kwargs):
    """Calculate feature latency for features in a date range.

    Returns:
      A list of FeatureLatency objects for each matching feature.
    """
    start_date, end_date = self.get_date_range(self.request.args)
    logging.info('range %r %r', start_date, end_date)

    # 1. Get all shipped feature entries that were created before end date.
    fe_query = FeatureEntry.query().order(FeatureEntry.created)
    fe_query = fe_query.filter(FeatureEntry.created < end_date)
    features = fe_query.fetch(None)
    logging.info('features %r', [fe.name for fe in features])
    features = [
        fe for fe in features
        if (not fe.deleted and
            fe.impl_status_chrome in [ENABLED_BY_DEFAULT, DEPRECATED, REMOVED])]

    # 2. Get all the ship Stages for those features to find shipping milestones.
    feature_ids = {fe.key.integer_id() for fe in features}
    logging.info('feature_ids %r', feature_ids)
    if not feature_ids:
      return []
    stage_query = Stage.query()
    stage_query = stage_query.filter(Stage.feature_id.IN(feature_ids))
    stage_query = stage_query.filter(Stage.stage_type.IN([
        STAGE_BLINK_SHIPPING, STAGE_PSA_SHIPPING,
        STAGE_FAST_SHIPPING, STAGE_DEP_SHIPPING, STAGE_ENT_ROLLOUT]))
    stages = stage_query.fetch(None)
    stages = [s for s in stages if not s.archived]
    if not stages:
      return []
    stages_by_fid = stage_helpers.organize_all_stages_by_feature(stages)
    ship_milestone_by_fid = {
        f_id: min(s.milestones.desktop_first for s in feature_stages)
        for f_id, feature_stages in stages_by_fid.items()}

    # 3. Get all the milestone details, including branch date.
    milestone_details = channels_api.construct_specified_milestones_details(
        min(ship_milestone_by_fid.values()),
        max(ship_milestone_by_fid.values()))
    for m in milestone_details:
      logging.info('M%d: branch_point %r', m,
                   milestone_details[m]['branch_point'])

    # 4. Use only features that shipped in milestones that branched
    # between start_date and end_date.
    start_date_iso = start_date.isoformat()
    end_date_iso = end_date.isoformat()
    lowest_milestone_in_range = min(
      m for m in milestone_details
      if milestone_details[m]['branch_point'] >= start_date_iso)
    highest_milestone_in_range = max(
      m for m in milestone_details
      if milestone_details[m]['branch_point'] <= end_date_iso)
    logging.info('highest_milestone_in_range: %r', highest_milestone_in_range)
    features = [
        fe for fe in features
        if (lowest_milestone_in_range <=
            ship_milestone_by_fid[fe.key.integer_id()] <=
            highest_milestone_in_range)]

    # 5. Stuff results into OpenAPI objects and convert to python dicts.
    result = []
    for fe in features:
      m = ship_milestone_by_fid[fe.key.integer_id()]
      result.append(FeatureLatency(
          FeatureLink(fe.key.integer_id(), fe.name),
          fe.created.isoformat(),
          m,
          milestone_details[m]['branch_point'],
          fe.owner_emails).to_dict())

    return result
