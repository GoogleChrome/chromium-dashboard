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

from framework import basehandlers
from internals.core_models import FeatureEntry


class FeatureLatencyAPI(basehandlers.APIHandler):
  """Implements the OpenAPI /spec_mentors path."""

  def do_get(self, **kwargs):
    """Get a list of matching spec mentors.

    Returns:
      A list of data on all public origin trials.
    """
    start_param: str | None = self.request.args.get('startDate', None)
    start_date: datetime | None = None
    if start_param is not None:
      try:
        start_date = datetime.fromisoformat(start_param)
      except ValueError:
        self.abort(400, f'invalid ?startDate parameter {start_param}')

    end_param: str | None = self.request.args.get('endDate', None)
    end_date: datetime | None = None
    if end_param is not None:
      try:
        end_date = datetime.fromisoformat(end_param)
      except ValueError:
        self.abort(400, f'invalid ?endDate parameter {end_param}')

    # TODO(jrobbins): Replace fake data with queries and calculations.
    result = [
        FeatureLatency(
            'Some feature', 12345, datetime(2023,1,8).isoformat(),
            122, datetime(2023, 3, 15).isoformat(),
            'owner@example.com').to_dict(),
        FeatureLatency(
            'Another feature', 128391, datetime(2023,3,18).isoformat(),
            123, datetime(2023, 5, 25).isoformat(),
            'owner@example.com').to_dict(),
    ]
    return result
