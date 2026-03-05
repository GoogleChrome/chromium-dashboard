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

import json5
from typing import TypedDict
from google.cloud import ndb

from framework import basehandlers, utils
from internals import feature_helpers
from internals.core_enums import (
  CONTENT_FEATURES_FILE,
  ENABLED_FEATURES_FILE_URL,
  STAGE_TYPES_SHIPPING
)
from internals.core_models import Stage


class GetShippingFeaturesResponse(TypedDict):
  complete_features: list[feature_helpers.ShippingFeatureInfo]
  incomplete_features: list[tuple[feature_helpers.ShippingFeatureInfo, list[str]]]


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

    if len(shipping_stages) == 0:
      return {
        'complete_features': [],
        'incomplete_features': [],
      }

    enabled_features_file = utils.get_chromium_file(ENABLED_FEATURES_FILE_URL)
    enabled_features_json = json5.loads(enabled_features_file)
    content_features_file = utils.get_chromium_file(CONTENT_FEATURES_FILE)

    url_root = f'{self.request.scheme}://{self.request.host}'

    complete_features, incomplete_features = (
      feature_helpers.aggregate_shipping_features(
        shipping_stages,
        enabled_features_json,
        content_features_file,
    ))

    return {
      'complete_features': complete_features,
      'incomplete_features': incomplete_features
    }
