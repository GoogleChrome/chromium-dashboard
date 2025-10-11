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

from datetime import datetime
from typing import TypedDict

from framework import basehandlers
from internals import feature_helpers


class StaleFeatureInfo(TypedDict):
  id: int
  name: str
  owner_emails: list[str]
  milestone: int
  milestone_field: str
  outstanding_notifications: int
  accurate_as_of: str


class GetStaleFeaturesResponse(TypedDict):
  stale_features: list[StaleFeatureInfo]
  

class StaleFeaturesAPI(basehandlers.EntitiesAPIHandler):
  """Endpoint for obtaining information on stale features."""

  def do_get(self, **kwargs):
    """Get all stale features."""
    stale_features = feature_helpers.get_stale_features()
    stale_features_info: list[StaleFeatureInfo] = []
    for feature, mstone, mstone_field in stale_features:
      stale_features_info.append({
        'id': feature.key.integer_id(),
        'name': feature.name,
        'owner_emails': feature.owner_emails,
        'milestone': mstone,
        'milestone_field': mstone_field,
        'outstanding_notifications': feature.outstanding_notifications,
        'accurate_as_of': datetime.strftime(feature.accurate_as_of,
                                            '%Y-%m-%dT%H:%M:%S')
      })
    return {
        'stale_features': stale_features_info
    }
