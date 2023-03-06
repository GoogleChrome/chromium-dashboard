# Copyright 2020 Google Inc.
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

import testing_config  # Must be imported before the module under test.

import datetime
from unittest import mock

from internals import core_enums
from internals.core_models import FeatureEntry, MilestoneSet, Stage
from internals.review_models import Gate, Vote
from internals import search
from internals import search_queries


class SearchFeaturesTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = FeatureEntry(
        name='feature a', summary='sum',
        category=1, impl_status_chrome=3)
    self.feature_1.owner_emails = ['owner@example.com']
    self.feature_1.editor_emails = ['editor@example.com']
    self.feature_1.cc_emails = ['cc@example.com']
    self.feature_1.put()
    self.feature_1_id = self.feature_1.key.integer_id()

    self.stage_1_ship = Stage(
        feature_id=self.feature_1_id,
        stage_type=core_enums.STAGE_BLINK_SHIPPING,
        milestones=MilestoneSet(desktop_first=99))
    self.stage_1_ship.put()

    self.feature_2 = FeatureEntry(
        name='feature b', summary='sum', owner_emails=['owner@example.com'],
        category=1, impl_status_chrome=3)
    self.feature_2.put()
    self.feature_2_id = self.feature_2.key.integer_id()

    self.feature_3 = FeatureEntry(
        name='feature c', summary='sum', owner_emails=['random@example.com'],
        category=1, impl_status_chrome=4)
    self.feature_3.put()
    self.feature_3_id = self.feature_3.key.integer_id()

    self.gate_1 = Gate(
        feature_id=self.feature_1_id, stage_id=1,
        gate_type=core_enums.GATE_API_PROTOTYPE,
        state=Vote.APPROVED,
        requested_on=datetime.datetime(2022, 7, 1))
    self.gate_1.put()
    self.gate_1_id = self.gate_1.key.integer_id()

    self.vote_1_1 = Vote(
        feature_id=self.feature_1_id, gate_type=core_enums.GATE_API_PROTOTYPE,
        gate_id=self.gate_1_id,
        state=Vote.REVIEW_REQUESTED,
        set_on=datetime.datetime(2022, 7, 1),
        set_by='feature_owner@example.com')
    self.vote_1_1.put()

    self.vote_1_2 = Vote(
        feature_id=self.feature_1_id, gate_type=core_enums.GATE_API_PROTOTYPE,
        gate_id=self.gate_1_id,
        state=Vote.APPROVED,
        set_on=datetime.datetime(2022, 7, 2),
        set_by='reviewer@example.com')
    self.vote_1_2.put()

    self.gate_2 = Gate(
        feature_id=self.feature_2_id, stage_id=1,
        gate_type=core_enums.GATE_API_SHIP,
        state=Vote.REVIEW_REQUESTED,
        requested_on=datetime.datetime(2022, 8, 1))
    self.gate_2.put()
    self.gate_2_id = self.gate_2.key.integer_id()

    self.vote_2_1 = Vote(
        feature_id=self.feature_2_id, gate_type=core_enums.GATE_API_SHIP,
        gate_id=self.gate_2_id,
        state=Vote.REVIEW_REQUESTED,
        set_on=datetime.datetime(2022, 8, 1),
        set_by='feature_owner@example.com')
    self.vote_2_1.put()

    self.vote_2_2 = Vote(
        feature_id=self.feature_2_id, gate_type=core_enums.GATE_API_SHIP,
        gate_id=self.gate_2_id,
        state=Vote.APPROVED,
        set_on=datetime.datetime(2022, 8, 2),
        set_by='reviewer@example.com')
    self.vote_2_2.put()

  def tearDown(self):
    self.feature_1.key.delete()
    self.feature_2.key.delete()
    self.feature_3.key.delete()
    self.stage_1_ship.key.delete()
    for gate in Gate.query():
      gate.key.delete()
    for vote in Vote.query():
      vote.key.delete()

  def test_single_field_query_async__normal(self):
    """We get a promise to run the DB query, which produces results."""
    actual_promise = search_queries.single_field_query_async(
        'owner', '=', 'owner@example.com')
    actual = actual_promise.get_result()
    self.assertCountEqual(
        [self.feature_1_id, self.feature_2_id],
        [key.integer_id() for key in actual])

    actual_promise = search_queries.single_field_query_async(
        'unlisted', '=', True)
    actual = actual_promise.get_result()
    self.assertCountEqual([], actual)

    actual_promise = search_queries.single_field_query_async(
        'deleted', '=', True)
    actual = actual_promise.get_result()
    self.assertCountEqual([], actual)

  def test_single_field_query_async__multiple_vals(self):
    """We get a promise to run the DB query with multiple values."""
    actual_promise = search_queries.single_field_query_async(
        'owner', '=', 'owner@example.com,random@example.com')
    actual = actual_promise.get_result()
    self.assertCountEqual(
        [self.feature_1_id, self.feature_2_id, self.feature_3_id],
        [key.integer_id() for key in actual])

  def test_single_field_query_async__normal_stage_field(self):
    """We can find a FeatureEntry based on values in an associated Stage."""
    actual_promise = search_queries.single_field_query_async(
        'browsers.chrome.desktop', '=', 99)
    actual = actual_promise.get_result()
    self.assertCountEqual(
        [self.feature_1_id],
        [projection.feature_id for projection in actual])

  def test_single_field_query_async__other_stage_field(self):
    """We only consider the appropriate Stage."""
    actual_promise = search_queries.single_field_query_async(
        'browsers.chrome.ot.desktop.start', '=', 99)
    actual = actual_promise.get_result()
    self.assertCountEqual([], actual)

  def test_single_field_query_async__zero_results(self):
    """When there are no matching results, we get back a promise for []."""
    actual_promise = search_queries.single_field_query_async(
        'owner', '=', 'nope')
    actual = actual_promise.get_result()
    self.assertCountEqual([], actual)

  @mock.patch('logging.warning')
  def test_single_field_query_async__bad_field(self, mock_warn):
    """An unknown field imediately gives zero results."""
    actual = search_queries.single_field_query_async('zodiac', '=', 'leo')
    self.assertCountEqual([], actual)

  def test_handle_me_query_async__owner_anon(self):
    """We can return a list of features owned by the user."""
    testing_config.sign_in('visitor@example.com', 111)
    future = search_queries.handle_me_query_async('owner')
    actual = search._resolve_promise_to_id_list(future)
    self.assertEqual(actual, [])

  def test_handle_me_query__owner_some(self):
    """We can return a list of features owned by the user."""
    testing_config.sign_in('owner@example.com', 111)
    future = search_queries.handle_me_query_async('owner')
    actual = search._resolve_promise_to_id_list(future)
    self.assertEqual(
        [self.feature_1_id, self.feature_2_id], actual)

  def test_handle_me_query__editor_none(self):
    """We can return a list of features the user can edit."""
    testing_config.sign_in('visitor@example.com', 111)
    future = search_queries.handle_me_query_async('editor')
    actual = search._resolve_promise_to_id_list(future)
    self.assertEqual([], actual)

  def test_handle_me_query__editor_some(self):
    """We can return a list of features the user can edit."""
    testing_config.sign_in('editor@example.com', 111)
    future = search_queries.handle_me_query_async('editor')
    actual = search._resolve_promise_to_id_list(future)
    self.assertEqual([self.feature_1_id], actual)

  def test_handle_me_query__cc_none(self):
    """We can return a list of features the user is CC'd on."""
    testing_config.sign_in('visitor@example.com', 111)
    future = search_queries.handle_me_query_async('cc')
    actual = search._resolve_promise_to_id_list(future)
    self.assertEqual(actual, [])

  def test_handle_me_query__cc_some(self):
    """We can return a list of features the user is CC'd on."""
    testing_config.sign_in('cc@example.com', 111)
    future = search_queries.handle_me_query_async('cc')
    actual = search._resolve_promise_to_id_list(future)
    self.assertEqual([self.feature_1_id], actual)

  def test_handle_can_edit_me_query_async__anon(self):
    """Anon cannot edit any features."""
    testing_config.sign_out()
    future = search_queries.handle_can_edit_me_query_async()
    actual = search._resolve_promise_to_id_list(future)
    self.assertEqual([], actual)

  def test_handle_can_edit_me_query_async__visitor(self):
    """Visitor cannot edit any features."""
    testing_config.sign_in('visitor@example.com', 111)
    future = search_queries.handle_can_edit_me_query_async()
    actual = search._resolve_promise_to_id_list(future)
    self.assertEqual([], actual)

  def test_handle_can_edit_me_query_async__owner(self):
    """A feature owner can edit those features."""
    testing_config.sign_in('owner@example.com', 111)
    future = search_queries.handle_can_edit_me_query_async()
    actual = search._resolve_promise_to_id_list(future)
    self.assertEqual(
        [self.feature_1_id, self.feature_2_id], actual)

  def test_handle_can_edit_me_query_async__editor(self):
    """A feature editor can edit those features."""
    testing_config.sign_in('editor@example.com', 111)
    future = search_queries.handle_can_edit_me_query_async()
    actual = search._resolve_promise_to_id_list(future)
    self.assertEqual([self.feature_1_id], actual)

  def test_total_order_query_async__field_asc(self):
    """We can get keys used to sort features in ascending order."""
    future = search_queries.total_order_query_async('name')
    actual = search._resolve_promise_to_id_list(future)
    self.assertEqual(
        [self.feature_1_id, self.feature_2_id, self.feature_3_id], actual)

  def test_total_order_query_async__field_desc(self):
    """We can get keys used to sort features in descending order."""
    future = search_queries.total_order_query_async('-name')
    actual = search._resolve_promise_to_id_list(future)
    self.assertEqual(
        [self.feature_3_id, self.feature_2_id, self.feature_1_id], actual)

  def test_total_order_query_async__requested_on(self):
    """We can get feature IDs sorted by gate review requests."""
    actual = search_queries.total_order_query_async('gate.requested_on')
    self.assertEqual(
        [self.feature_2_id],
        actual)

  def test_total_order_query_async__reviewed_on(self):
    """We can get feature IDs sorted by gate resolution times."""
    actual = search_queries.total_order_query_async('gate.reviewed_on')
    self.assertEqual(
        [self.feature_1_id],
        actual)

  def test_stage_fields_have_join_conditions(self):
    """Every STAGE_QUERIABLE_FIELDS has a STAGE_TYPES_BY_QUERY_FIELD entry."""
    self.assertCountEqual(
        search_queries.STAGE_QUERIABLE_FIELDS.keys(),
        search_queries.STAGE_TYPES_BY_QUERY_FIELD.keys())

  def test_negate_operator(self):
    """We can get correct negated operators"""
    actual = search_queries.negate_operator('=')
    self.assertEqual('!=', actual)

    actual = search_queries.negate_operator('!=')
    self.assertEqual('=', actual)

    actual = search_queries.negate_operator('<')
    self.assertEqual('>=', actual)

    actual = search_queries.negate_operator('<=')
    self.assertEqual('>', actual)

    actual = search_queries.negate_operator('>')
    self.assertEqual('<=', actual)

    actual = search_queries.negate_operator('>=')
    self.assertEqual('<', actual)
