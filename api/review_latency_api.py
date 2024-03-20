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

from chromestatus_openapi.models.feature_link import FeatureLink
from chromestatus_openapi.models.gate_latency import GateLatency
from chromestatus_openapi.models.review_latency import ReviewLatency

from framework import basehandlers
from internals.core_enums import *
from internals.core_models import FeatureEntry


class ReviewLatencyAPI(basehandlers.APIHandler):
  """Implements the OpenAPI /spec_mentors path."""

  def do_get(self, **kwargs):
    """Get a list of matching spec mentors.

    Returns:
      A list of data on all public origin trials.
    """
    return [
        ReviewLatency(
            FeatureLink(12345, 'Some feature'),
            [GateLatency(GATE_API_PROTOTYPE, 2),
             GateLatency(GATE_API_ORIGIN_TRIAL, 2),
             GateLatency(GATE_API_EXTEND_ORIGIN_TRIAL, 2),
             GateLatency(GATE_API_SHIP, 2),
             GateLatency(GATE_PRIVACY_ORIGIN_TRIAL, 2),
             GateLatency(GATE_SECURITY_ORIGIN_TRIAL, 2),
             GateLatency(GATE_SECURITY_SHIP, 4),
             GateLatency(GATE_ENTERPRISE_SHIP, 3),
             GateLatency(GATE_DEBUGGABILITY_ORIGIN_TRIAL, 2),
             ]
        ).to_dict(),
        ReviewLatency(
            FeatureLink(1299345, 'Another feature'),
            [GateLatency(GATE_API_PROTOTYPE, 3),
             GateLatency(GATE_API_ORIGIN_TRIAL, 2),
             GateLatency(GATE_API_EXTEND_ORIGIN_TRIAL, 5),
             GateLatency(GATE_API_SHIP, 2),
             GateLatency(GATE_PRIVACY_ORIGIN_TRIAL, 3),
             GateLatency(GATE_SECURITY_ORIGIN_TRIAL, 1),
             GateLatency(GATE_ENTERPRISE_SHIP, 8),
             GateLatency(GATE_DEBUGGABILITY_ORIGIN_TRIAL, 12),
             ]
        ).to_dict(),
    ]
