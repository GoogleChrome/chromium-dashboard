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

import json
import os.path
from datetime import datetime

import flask
from google.cloud import ndb  # type: ignore

from api import verification_api
from internals.core_models import FeatureEntry

test_app = flask.Flask(__name__)


def make_feature(
  name: str,
  accurate_as_of: datetime,
  outstanding_notifications: int,
) -> FeatureEntry:
  fe = FeatureEntry(
    name=name,
    category=1,
    summary='Summary',
    accurate_as_of=accurate_as_of,
    outstanding_notifications=outstanding_notifications,
  )
  fe.put()
  return fe


class VerificationAPITest(testing_config.CustomTestCase):
  maxDiff = None

  def setUp(self):
    self.handler = verification_api.VerificationAPI()
    self.request_path = '/api/v0/verification'

  def tearDown(self):
    kinds: list[ndb.Model] = [FeatureEntry]
    for kind in kinds:
      for entity in kind.query():
        entity.key.delete()

  def test_no_notifications(self):
    """When no notifications have been sent, the result is empty."""
    make_feature('Feature one', datetime(2023, 11, 3, 11, 52, 1), 0)

    actual = self.handler.do_get()
    self.assertEqual([], actual)

  def test_one_pending_verification(self):
    """Basic success case."""
    fe = make_feature('Feature one', datetime(2023, 11, 3, 11, 52), 1)

    result = self.handler.do_get()
    self.assertEqual(
      [
        dict(
          feature=dict(id=fe.key.id(), name='Feature one'),
          accurate_as_of='2023-11-03T11:52:00',
        )
      ],
      result,
    )

  def test_several_pending_verifications(self):
    """Generates data to share with the Playwright test."""
    fe1 = make_feature('Feature one', datetime(2023, 11, 3, 11, 52), 1)
    fe2 = make_feature('Feature two', datetime(2024, 11, 9, 16, 31, 2), 1)
    fe3 = make_feature('Feature three', datetime(2024, 5, 7, 3, 12), 1)

    result = self.handler.do_get()

    # This test expectation is saved to a JSON file so the
    # Playwright tests can use it as a mock API response. Because the real feature IDs are
    # dynamically generated, we have to slot them into the right places here.
    with open(
      os.path.join(
        os.path.dirname(__file__),
        '../packages/playwright/tests/verification_api_result.json',
      )
    ) as f:
      expected_result = json.load(f)
    expected_result[0]['feature']['id'] = fe1.key.id()
    expected_result[1]['feature']['id'] = fe3.key.id()
    expected_result[2]['feature']['id'] = fe2.key.id()

    self.assertEqual(expected_result, result)
