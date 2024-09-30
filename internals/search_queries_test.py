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
from internals import search_fulltext
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
    search_fulltext.index_feature(self.feature_1)

    self.stage_1_ship = Stage(
      feature_id=self.feature_1_id,
      stage_type=core_enums.STAGE_BLINK_SHIPPING,
      milestones=MilestoneSet(desktop_first=99, android_first=100),
    )
    self.stage_1_ship.put()

    self.feature_2 = FeatureEntry(
      name='feature b',
      summary='summary of editor stuff',
      owner_emails=['owner@example.com'],
      category=1,
      impl_status_chrome=3,
      accurate_as_of=datetime.datetime(2023, 6, 1),
    )
    self.feature_2.put()
    search_fulltext.index_feature(self.feature_1)
    self.feature_2_id = self.feature_2.key.integer_id()
    self.stage_2_ot = Stage(
      feature_id=self.feature_2_id,
      stage_type=core_enums.STAGE_BLINK_ORIGIN_TRIAL,
      milestones=MilestoneSet(desktop_first=89, desktop_last=95, webview_first=100),
    )
    self.stage_2_ot.put()

    self.feature_3 = FeatureEntry(
      name='feature c',
      summary='sum',
      owner_emails=['random@example.com'],
      category=1,
      impl_status_chrome=4,
      accurate_as_of=datetime.datetime(2024, 6, 1),
    )
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
    for kind in [
        FeatureEntry, search_fulltext.FeatureWords, Stage, Gate, Vote]:
      for entry in kind.query():
        entry.key.delete()

  def test_single_field_query_async__normal(self):
    """We get a promise to run the DB query, which produces results."""
    actual_promise = search_queries.single_field_query_async(
        'owner', '=', ['owner@example.com'])
    actual = actual_promise.get_result()
    self.assertCountEqual(
        [self.feature_1_id, self.feature_2_id],
        [key.integer_id() for key in actual])

    actual_promise = search_queries.single_field_query_async(
        'unlisted', '=', [True])
    actual = actual_promise.get_result()
    self.assertCountEqual([], actual)

    actual_promise = search_queries.single_field_query_async(
        'deleted', '=', [True])
    actual = actual_promise.get_result()
    self.assertCountEqual([], actual)

  def test_single_field_query_async__multiple_vals(self):
    """We get a promise to run the DB query with multiple values."""
    actual_promise = search_queries.single_field_query_async(
        'owner', '=', ['owner@example.com', 'random@example.com'])
    actual = actual_promise.get_result()
    self.assertCountEqual(
        [self.feature_1_id, self.feature_2_id, self.feature_3_id],
        [key.integer_id() for key in actual])

  def test_single_field_query_async__inequality_nulls_first(self):
    """accurate_as_of treats None as before any comparison value."""
    actual_promise = search_queries.single_field_query_async(
      'accurate_as_of', '<', [datetime.datetime(2024, 1, 1)]
    )
    actual = actual_promise.get_result()
    self.assertCountEqual(
      [self.feature_1_id, self.feature_2_id], [key.integer_id() for key in actual]
    )

    actual_promise = search_queries.single_field_query_async(
      'accurate_as_of', '>', [datetime.datetime(2024, 1, 1)]
    )
    actual = actual_promise.get_result()
    self.assertCountEqual([self.feature_3_id], [key.integer_id() for key in actual])

  def test_single_field_query_async__any_start_milestone(self):
    actual = search_queries.single_field_query_async(
      'any_start_milestone', '=', [100]
    ).get_result()
    self.assertEqual(
      set([self.feature_1_id, self.feature_2_id]),
      set(proj.feature_id for proj in actual),
      'Finds across multiple milestones.',
    )

    actual = search_queries.single_field_query_async(
      'any_start_milestone', '=', [95]
    ).get_result()
    self.assertEqual(
      set(), set(proj.feature_id for proj in actual), 'Does not find "last" milestones.'
    )

    actual = search_queries.single_field_query_async(
      'any_start_milestone', '=', [search_queries.Interval(97, 99)]
    ).get_result()
    self.assertCountEqual(
      set([self.feature_1_id]),
      set(proj.feature_id for proj in actual),
      'Intervals are constrained to a single milestone.',
    )

  def check_wrong_type(self, field_name, bad_values):
    with self.assertRaises(ValueError) as cm:
      search_queries.single_field_query_async(
          field_name, '=', bad_values)
    self.assertEqual(
        cm.exception.args[0], 'Query value does not match field type')

  def test_single_field_query_async__wrong_types(self):
    """We reject requests with values that parse to the wrong type."""
    # Feature entry fields
    self.check_wrong_type('owner', [True])
    self.check_wrong_type('owner', [123])
    self.check_wrong_type('deleted', ['not a boolean'])
    self.check_wrong_type('shipping_year', ['not an integer'])
    self.check_wrong_type('star_count', ['not an integer'])
    self.check_wrong_type('created.when', ['not a date'])
    self.check_wrong_type('owner', ['ok@example.com', True])

    # Stage fields
    self.check_wrong_type('browsers.chrome.android', ['not an integer'])
    self.check_wrong_type('finch_url', [123])
    self.check_wrong_type('finch_url', [True])

  def test_single_field_query_async__normal_stage_field(self):
    """We can find a FeatureEntry based on values in an associated Stage."""
    actual_promise = search_queries.single_field_query_async(
        'browsers.chrome.desktop', '=', [99])
    actual = actual_promise.get_result()
    self.assertCountEqual(
        [self.feature_1_id],
        [projection.feature_id for projection in actual])

  def test_single_field_query_async__other_stage_field(self):
    """We only consider the appropriate Stage."""
    actual_promise = search_queries.single_field_query_async(
        'browsers.chrome.ot.desktop.start', '=', [99])
    actual = actual_promise.get_result()
    self.assertCountEqual([], actual)

  def test_single_field_query_async__zero_results(self):
    """When there are no matching results, we get back a promise for []."""
    actual_promise = search_queries.single_field_query_async(
        'owner', '=', ['nope'])
    actual = actual_promise.get_result()
    self.assertCountEqual([], actual)

  def test_single_field_query_async__fulltext_in_field(self):
    """We can search for words within a field."""
    actual = search_queries.single_field_query_async(
        'editor', ':', ['editor'])
    self.assertCountEqual([self.feature_1_id], actual)

    actual = search_queries.single_field_query_async(
        'editor', ':', ['wrongword'])
    self.assertCountEqual([], actual)

    actual = search_queries.single_field_query_async(
        'owner', ':', ['editor'])
    self.assertCountEqual([], actual)

  @mock.patch('logging.warning')
  def test_single_field_query_async__bad_field(self, mock_warn):
    """An unknown field imediately gives zero results."""
    actual = search_queries.single_field_query_async('zodiac', '=', ['leo'])
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
    future = search_queries.total_order_query_async('gate.requested_on')
    actual = search._resolve_promise_to_id_list(future)
    self.assertEqual(
        [self.feature_2_id],
        actual)

  def test_total_order_query_async__reviewed_on(self):
    """We can get feature IDs sorted by gate resolution times."""
    future = search_queries.total_order_query_async('gate.reviewed_on')
    actual = search._resolve_promise_to_id_list(future)
    self.assertEqual(
        [self.feature_1_id, self.feature_2_id],
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
