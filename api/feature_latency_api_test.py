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

import flask
from unittest import mock
import werkzeug.exceptions  # Flask HTTP stuff.
from google.cloud import ndb  # type: ignore

from api import feature_latency_api
from internals.core_enums import *
from internals.core_models import FeatureEntry, Stage, MilestoneSet
from internals import user_models


test_app = flask.Flask(__name__)


def make_feature(name, created_tuple, status, shipped):
  fe = FeatureEntry(
      name=name, summary='sum', category=1, created=datetime(*created_tuple),
      impl_status_chrome=status)
  fe.put()
  if shipped:
    s = Stage(
        feature_id=fe.key.integer_id(), stage_type=STAGE_BLINK_SHIPPING,
        milestones=MilestoneSet(desktop_first=shipped))
    s.put()
  return fe, fe.key.integer_id()


class FeatureLatencyAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.app_admin = user_models.AppUser(email='admin@example.com')
    self.app_admin.is_admin = True
    self.app_admin.put()

    self.handler = feature_latency_api.FeatureLatencyAPI()
    self.request_path = '/api/v0/feature-latency'

    self.fe_1a, self.fe_1a_id = make_feature(
        'has no milestone', (2023, 2, 18), ENABLED_BY_DEFAULT, None)
    self.fe_1b, self.fe_1b_id = make_feature(
        'not a launch status', (2023, 2, 18), NO_ACTIVE_DEV, 119)
    self.fe_2, self.fe_2_id = make_feature(
        'launched before start', (2022, 8, 19), ENABLED_BY_DEFAULT, 108)
    self.fe_3, self.fe_3_id = make_feature(
        'launched in timeframe', (2023, 2, 18), ENABLED_BY_DEFAULT, 119)
    self.fe_4, self.fe_4_id = make_feature(
        'deleted feature', (2023, 2, 18), ENABLED_BY_DEFAULT, 119)
    self.fe_4.deleted = True
    self.fe_4.put()
    self.fe_5, self.fe_5_id = make_feature(
        'launched after end', (2023, 9, 29), ENABLED_BY_DEFAULT, 125)

  def tearDown(self):
    testing_config.sign_out()
    self.app_admin.key.delete()
    kinds: list[ndb.Model] = [FeatureEntry, Stage]
    for kind in kinds:
      for entity in kind.query():
        entity.key.delete()

  def test_get_date_range__unspecified(self):
    """If query string params were not set, it rejects."""
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.get_date_range({})

  def test_get_date_range__specified(self):
    """It parses dates from query-string params."""
    actual = self.handler.get_date_range({
        'startAt': '2023-01-15',
        'endAt': '2023-12-24'})
    self.assertEqual(
        (datetime(2023, 1, 15),
         datetime(2023, 12, 24)),
        actual)

  def test_do_get__anon(self):
    """Only users who can create features can view reports."""
    testing_config.sign_out()
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_get()

  def test_do_get__rando(self):
    """Only users who can create features can view reports."""
    testing_config.sign_in('someone@example.com', 1232345)
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_get()

  def test_do_get__normal(self):
    """It finds some feature launches to include and excludes others."""
    testing_config.sign_in('admin@example.com', 123567890)
    path = self.request_path + '?startAt=2023-01-01&endAt=2024-01-01'
    with test_app.test_request_context(path):
      actual = self.handler.do_get()

    self.assertEqual(1, len(actual))
    actual_1 = actual[0]
    self.assertEqual(
        {'name': 'launched in timeframe', 'id': self.fe_3_id},
        actual_1['feature'])
    self.assertTrue(actual_1['entry_created_date'].startswith('2023-02-18'))
    self.assertEqual(119, actual_1['shipped_milestone'])
    self.assertTrue(actual_1['shipped_date'].startswith('2023-10-02'))
    self.assertEqual([], actual_1['owner_emails'])

  def test_do_get__zero_results(self):
    """There were no test launches in this range."""
    testing_config.sign_in('admin@example.com', 123567890)
    path = self.request_path + '?startAt=2020-01-01&endAt=2020-03-01'
    with test_app.test_request_context(path):
      actual = self.handler.do_get()

    self.assertEqual(0, len(actual))
