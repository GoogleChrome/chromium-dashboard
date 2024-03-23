# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import testing_config  # isort: split

from datetime import datetime

from unittest import mock
from google.cloud import ndb  # type: ignore

from api import review_latency_api
from internals.core_enums import *
from internals.core_models import FeatureEntry
from internals.review_models import Gate


def make_feature_and_gates(name):
  fe = FeatureEntry(name=name, summary='sum', category=1)
  fe.put()
  fe_id = fe.key.integer_id()
  g_1 = Gate(feature_id=fe_id, gate_type=1, stage_id=1, state=Gate.PREPARING)
  g_1.put()
  g_2 = Gate(feature_id=fe_id, gate_type=2, stage_id=1, state=Gate.PREPARING)
  g_2.put()
  g_3 = Gate(feature_id=fe_id, gate_type=3, stage_id=1, state=Gate.PREPARING)
  g_3.put()
  return fe, fe_id, g_1, g_2, g_3


class ReviewLatencyAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.handler = review_latency_api.ReviewLatencyAPI()
    self.request_path = '/api/v0/review-latency'

    self.fe_1, self.fe_1_id, self.g_1_1, self.g_1_2, self.g_1_3 = (
        make_feature_and_gates('Feature one'))
    self.fe_2, self.fe_2_id, self.g_2_1, self.g_2_2, self.g_2_3 = (
        make_feature_and_gates('Feature two'))
    self.today = datetime(2024, 3, 22)
    self.yesterday = datetime(2024, 3, 21)
    self.last_week = datetime(2024, 3, 15)

  def tearDown(self):
    kinds: list[ndb.Model] = [FeatureEntry, Gate]
    for kind in kinds:
      for entity in kind.query():
        entity.key.delete()

  def test_do_get__nothing_requested(self):
    """When no reviews have been started, the result is empty."""
    actual = self.handler.do_get()
    self.assertEqual([], actual)

  def test_do_get__normal(self):
    """It produces a report of review latency."""
    self.g_1_1.requested_on = self.last_week
    self.g_1_1.responded_on = self.today
    self.g_1_1.put()
    self.g_1_2.requested_on = self.last_week
    self.g_1_2.put()

    actual = self.handler.do_get()

    expected = [
        { 'feature': {'name': 'Feature one', 'id': self.fe_1_id},
          'gate_reviews': [
              {'gate_type': 1,
               'latency_days': 5},
              {'gate_type': 2,
               'latency_days': review_latency_api.PENDING_LATENCY},
              {'gate_type': 3,
               'latency_days': review_latency_api.NOT_STARTED_LATENCY},
          ],
         }]
    self.assertEqual(expected, actual)

  def test_do_get__sorting(self):
    """Multiple results are sorted by earlest review request."""
    self.g_1_1.requested_on = self.yesterday
    self.g_1_1.responded_on = self.today
    self.g_1_1.put()
    self.g_1_2.requested_on = self.today
    self.g_1_2.responded_on = self.today
    self.g_1_2.put()

    self.g_2_1.requested_on = self.last_week
    self.g_2_1.responded_on = self.yesterday
    self.g_2_1.put()

    actual = self.handler.do_get()

    expected = [
        { 'feature': {'name': 'Feature two', 'id': self.fe_2_id},
          'gate_reviews': [
              {'gate_type': 1,
               'latency_days': 4},
              {'gate_type': 2,
               'latency_days': review_latency_api.NOT_STARTED_LATENCY},
              {'gate_type': 3,
               'latency_days': review_latency_api.NOT_STARTED_LATENCY},
          ],
         },
        { 'feature': {'name': 'Feature one', 'id': self.fe_1_id},
          'gate_reviews': [
              {'gate_type': 1,
               'latency_days': 1},
              {'gate_type': 2,
               'latency_days': 0},
              {'gate_type': 3,
               'latency_days': review_latency_api.NOT_STARTED_LATENCY},
          ],
         },
    ]
    self.assertEqual(expected, actual)
