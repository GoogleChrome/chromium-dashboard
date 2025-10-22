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

import re
import json5
import logging
from enum import Enum
from typing import TypedDict
from google.cloud import ndb

from framework import basehandlers, utils
from internals.core_enums import (
  CONTENT_FEATURES_FILE,
  ENABLED_FEATURES_FILE_URL,
  FEATURE_TYPE_CODE_CHANGE_ID,
  GATE_API_SHIP,
  STAGE_TYPES_SHIPPING
)
from internals.core_models import FeatureEntry, Stage
from internals.review_models import Gate, Vote


class GetShippingFeaturesResponse(TypedDict):
  complete_features: list[str]
  incomplete_features: list[tuple[str, list[str]]]

class Criteria(str, Enum):
  # Intent to Ship thread URL is missing.
  INTENT_TO_SHIP_MISSING = 'i2s'
  # API Owner approvals have not been obtained on the ship gate.
  API_OWNER_LGTMS_MISSING = 'lgtms'
  # Both the finch name and the non-finch justification fields are missing.
  FINCH_NAME_MISSING = 'finch_name'
  # The feature exists in runtime_enabled_features.json5, but is not marked as 'status: "stable"'.
  RUNTIME_FEATURE_NOT_STABLE = 'runtime_feature_not_stable'
  # The feature exists in content_features.cc, but is not marked as enabled.
  CONTENT_FEATURE_NOT_ENABLED = 'content_feature_not_enabled'
  CHROMIUM_FEATURE_NOT_FOUND = 'chromium_feature_not_found'

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

  def _validate_feature_in_chromium(
    self,
    name: str,
    enabled_features_json: dict,
    content_features_file: str
  ) -> list[Criteria]:
    """Verify required info exists in Chromium files. Return a list of missing criteria"""
    criteria_missing = []
    feature_found = False
    feature_info = next(
      (finfo for finfo in enabled_features_json['data']
       if finfo['name'] == name),
      None)
    if feature_info:
      feature_found = True
      # The status of a feature can be represented as a string (meaning the same
      # status for all platforms), or an object mapping the status of each
      # platform individually.
      if isinstance(feature_info.get('status', None), dict):
        # If we're checking by platform, we just check if at least one platform
        # is designated as stable.
        if not any(s for s in feature_info['status'].values() if s == 'stable'):
          criteria_missing.append(Criteria.RUNTIME_FEATURE_NOT_STABLE)
      elif feature_info.get('status', None) != 'stable':
        criteria_missing.append(Criteria.RUNTIME_FEATURE_NOT_STABLE)
    else:
      # Search for the feature and determine if it is enabled.
      pattern = re.compile(
        rf"BASE_FEATURE\(\s*k{name}\s*,"
        r"(?:(?:\s|//.*))*"
        r"base::FEATURE_(\w+)_BY_DEFAULT"
        r"\s*\);",
        re.MULTILINE
      )
      match = re.search(pattern, content_features_file)
      if match:
        feature_found = True
        status = match.group(1)
        if status != 'ENABLED':
          criteria_missing.append(Criteria.CONTENT_FEATURE_NOT_ENABLED)

    if not feature_found:
      criteria_missing.append(Criteria.CHROMIUM_FEATURE_NOT_FOUND)

    return criteria_missing


  def do_get(self, **kwargs) -> GetShippingFeaturesResponse:
    """Get all features that have met all conditions to ship for a given milestone"""
    milestone = self.get_int_arg('mstone')

    if milestone is None:
      self.abort(400, msg='No milestone provided.')

    shipping_stages = self._get_shipping_stages(milestone)

    if len(shipping_stages) == 0:
      return {
        'complete_features': [],
        'incomplete_features': [],
      }

    # Fetch chromium code to search for feature name within contents.
    # A shipping feature should be named in one of these two files.
    enabled_features_file = utils.get_chromium_file(ENABLED_FEATURES_FILE_URL)
    enabled_features_json = json5.loads(enabled_features_file)
    content_features_file = utils.get_chromium_file(CONTENT_FEATURES_FILE)

    complete_features: list[str] = []
    incomplete_features: list[tuple[str, list[str]]] = []
    for stage in shipping_stages:
      criteria_missing: list[Criteria] = []
      feature: FeatureEntry | None = FeatureEntry.get_by_id(stage.feature_id)
      if feature is None:
        logging.warning(f'Feature {stage.feature_id} not found.')
        continue

      chromestatus_url = (f'{self.request.scheme}://{self.request.host}'
                          f'/feature/{feature.key.integer_id()}')

      if feature.feature_type == FEATURE_TYPE_CODE_CHANGE_ID:
        # PSA features do not require intents or approvals.
        complete_features.append(chromestatus_url)
        continue

      api_owner_gate: Gate | None = Gate.query(
          Gate.stage_id == stage.key.integer_id(),
          Gate.gate_type == GATE_API_SHIP).get()
      if api_owner_gate is None or api_owner_gate.state != Vote.APPROVED:
        criteria_missing.append(Criteria.API_OWNER_LGTMS_MISSING)
      if not stage.intent_thread_url:
        criteria_missing.append(Criteria.INTENT_TO_SHIP_MISSING)
      if not feature.finch_name and not feature.non_finch_justification:
        criteria_missing.append(Criteria.FINCH_NAME_MISSING)
      if feature.finch_name:
        criteria_missing.extend(self._validate_feature_in_chromium(
          feature.finch_name,
          enabled_features_json,
          content_features_file
        ))

      if criteria_missing:
        incomplete_features.append((chromestatus_url,
                                    [c.value for c in criteria_missing]))
      else:
        complete_features.append(chromestatus_url)

    return {
      'complete_features': complete_features,
      'incomplete_features': incomplete_features
    }
