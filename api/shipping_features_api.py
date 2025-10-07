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

import logging
from typing import TypedDict
from google.cloud import ndb

from api import converters
from framework import basehandlers
from internals.core_enums import (
  FEATURE_TYPE_CODE_CHANGE_ID,
  GATE_API_SHIP,
  STAGE_TYPES_SHIPPING
)
from internals.core_models import FeatureEntry, Stage
from internals.review_models import Gate, Vote
from internals.data_types import VerboseFeatureDict


class GetShippingFeaturesResponse(TypedDict):
  complete_features: list[VerboseFeatureDict]
  incomplete_features: list[tuple[VerboseFeatureDict, list[str]]]
  

class ShippingFeaturesAPI(basehandlers.EntitiesAPIHandler):
  """Endpoints involving the tracking of shipping features."""

  def _get_shipping_stages(self, milestone: int) -> list[Stage]:
    shipping_stage_types = [st for st in STAGE_TYPES_SHIPPING.values() if st]
    shipping_stages: list[Stage] = Stage.query(
      Stage.stage_type.IN(shipping_stage_types),
      ndb.OR(
        Stage.milestones.desktop_first == milestone,
        Stage.milestones.android_first == milestone,
        Stage.milestones.ios_first == milestone,
        Stage.milestones.webview_first  == milestone,
      )
    ).fetch()

    return shipping_stages

  def do_get(self, **kwargs) -> GetShippingFeaturesResponse:
    """Get all features that have met all conditions to ship for a given milestone"""
    milestone = self.get_int_arg('mstone')

    if milestone is None:
      self.abort(400, msg='No milestone provided.')

    shipping_stages = self._get_shipping_stages(milestone)

    complete_features: list[VerboseFeatureDict] = []
    incomplete_features: list[tuple[VerboseFeatureDict, list[str]]] = []
    for stage in shipping_stages:
      criteria_missing: list[str] = []
      feature = FeatureEntry.get_by_id(stage.feature_id)
      if feature is None:
        logging.warning(f'Feature {stage.feature_id} not found.')
        continue

      if feature.feature_type == FEATURE_TYPE_CODE_CHANGE_ID:
        # PSA features do not require intents or approvals.
        feature_dict = converters.feature_entry_to_json_verbose(feature)
        complete_features.append(feature_dict)
        continue

      api_owner_gate: Gate | None = Gate.query(
          Gate.stage_id == stage.key.integer_id(),
          Gate.gate_type == GATE_API_SHIP).get()
      if api_owner_gate is None or api_owner_gate.state != Vote.APPROVED:
        criteria_missing.append('lgtms')
      if not stage.intent_thread_url:
        criteria_missing.append('i2s')
      if not feature.finch_name and not feature.non_finch_justification:
        criteria_missing.append('finch_name')

      feature_dict = converters.feature_entry_to_json_verbose(feature)
      if criteria_missing:
        incomplete_features.append((feature_dict, criteria_missing))
      else:
        complete_features.append(feature_dict)

    return {
      'complete_features': complete_features,
      'incomplete_features': incomplete_features
    }
