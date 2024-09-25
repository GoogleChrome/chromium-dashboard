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

import collections
import logging
from datetime import datetime, timedelta
from typing import Any, Iterable

from chromestatus_openapi.models.feature_link import FeatureLink
from chromestatus_openapi.models.gate_latency import GateLatency
from chromestatus_openapi.models.review_latency import ReviewLatency
from google.cloud import ndb  # type: ignore

from framework import basehandlers
from framework import permissions
from internals import slo
from internals.core_enums import *
from internals.core_models import FeatureEntry
from internals.review_models import Gate

DEFAULT_RECENT_DAYS = 90
# This means that the feature team has not yet requested this review.
NOT_STARTED_LATENCY = -1
# This means that the feature team is still waiting for an initial response.
PENDING_LATENCY = -2


class ReviewLatencyAPI(basehandlers.APIHandler):
  """Implements the OpenAPI /spec_mentors path."""

  @permissions.require_create_feature
  def do_get(self, **kwargs):
    """Get a list of matching spec mentors.

    Returns:
      A list of data on all public origin trials.
    """
    today = kwargs.get('today')
    gates = self.get_recently_reviewed_gates(DEFAULT_RECENT_DAYS, today=today)
    gates_by_fid = self.organize_gates_by_feature_id(gates)
    for fid, feature_gates in gates_by_fid.items():
      logging.info('feautre %r:', fid)
      for fg in feature_gates:
        logging.info('  %r', fg)
    features = self.get_features_by_id(gates_by_fid.keys())
    features = self.sort_features_by_request(features, gates_by_fid)
    latencies_by_fid = {
        fid: self.latencies_for_feature(feature_gates)
        for fid, feature_gates in gates_by_fid.items()}
    result = self.convert_to_result_format(
        latencies_by_fid, features)
    return result

  def get_recently_reviewed_gates(
      self, days:int, today:datetime|None = None
  ) -> list[Gate]:
    """Retrieve a list of Gates responded to in recent days."""
    today = today or datetime.today()
    start_date = today - timedelta(days=90)
    gates_in_range = Gate.query(
        Gate.requested_on >= start_date).fetch()
    feature_ids = {g.feature_id for g in gates_in_range}
    if not feature_ids:
      return []
    gates_on_those_features = Gate.query(
        Gate.feature_id.IN(feature_ids)).fetch()
    return gates_on_those_features

  def organize_gates_by_feature_id(
      self, gates: list[Gate]
  ) -> dict[int, list[Gate]]:
    """Return a dict of feature IDs and a list of gates for each feature."""
    gates_by_fid: dict[int, list[Gate]] = collections.defaultdict(list)
    for g in gates:
      gates_by_fid[g.feature_id].append(g)
    return gates_by_fid

  def get_features_by_id(
      self, feature_ids: Iterable[int]) -> dict[int, FeatureEntry]:
    """Retrieve features by ID and return them in a dict."""
    if not feature_ids:
      return {}  # We cannot pass an empty list to IN().
    query = FeatureEntry.query(FeatureEntry.key.IN(
        [ndb.Key('FeatureEntry', id) for id in feature_ids]))
    features = query.fetch()
    return features

  def earliest_request(self, feature_gates: list[Gate]) -> datetime:
    """Return the time of the earliest reivew request among the given gates."""
    if not feature_gates:
      raise ValueError('There should be some gates for every feature')
    request_dates = [
        g.requested_on for g in feature_gates
        if g.requested_on]
    return min(request_dates, default=datetime(2000, 1, 1))

  def sort_features_by_request(self, features, gates_by_fid):
    """Return the same features sorted by the earliest review request of each."""
    sorted_features = sorted(
        features,
        key=lambda fe: self.earliest_request(gates_by_fid[fe.key.integer_id()]))
    return sorted_features

  def latency(self, gate: Gate) -> int:
    """Return the number of weekdays that the review was pending."""
    if not gate.requested_on:
      return NOT_STARTED_LATENCY
    if not gate.responded_on:
      return PENDING_LATENCY
    return slo.weekdays_between(gate.requested_on, gate.responded_on)

  def latencies_for_feature(
      self, feature_gates: list[Gate]) -> list[tuple[int, int]]:
    """Compute the review latency for each gate on a feature."""
    pairs = [(g.gate_type, self.latency(g)) for g in feature_gates]
    pairs = sorted(pairs)  # Sort by gate_type for non-flaky testing.
    return pairs

  def convert_to_result_format(
      self, latencies_by_fid: dict[int, list[tuple[int, int]]],
      sorted_features: list[FeatureEntry]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for fe in sorted_features:
      latencies = latencies_by_fid[fe.key.integer_id()]
      review_latency = ReviewLatency.model_construct(feature=
          FeatureLink.model_construct(id=fe.key.integer_id(), name=fe.name),
          gate_reviews=
          [GateLatency.model_construct(gate_type=gate_type, latency_days=days)
           for (gate_type, days) in latencies]
        )
      result.append(review_latency.to_dict())

    return result
