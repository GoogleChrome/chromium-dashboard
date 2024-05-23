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


from chromestatus_openapi.models.feature_link import FeatureLink
from chromestatus_openapi.models.pending_verification import PendingVerification

from framework import basehandlers
from internals.core_models import FeatureEntry


class VerificationAPI(basehandlers.APIHandler):
  """Implements the OpenAPI /verification path."""

  def do_get(self, **kwargs):
    """Get a list of features that need their accuracy verified."""

    features = FeatureEntry.query(
      FeatureEntry.deleted == False,  # noqa: E712
      FeatureEntry.outstanding_notifications > 0,
    ).fetch()

    # Build the response objects.
    verifications = [
      PendingVerification(
        feature=FeatureLink(id=feature.key.id(), name=feature.name),
        accurate_as_of=feature.accurate_as_of.isoformat(),
      )
      for feature in features
    ]
    verifications.sort(key=lambda feature: feature.accurate_as_of)
    return [v.to_dict() for v in verifications]
