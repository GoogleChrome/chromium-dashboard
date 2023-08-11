# Copyright 2021 Google Inc.
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
from internals.core_models import FeatureEntry
from internals.review_models import Gate, Vote
from internals import notifier
from internals import search


class SearchRETest(testing_config.CustomTestCase):
  # Note: User queries will always have a space appended before parsing.

  def test_empty_query(self):
    """An empty user query string should yield zero serach terms."""
    self.assertEqual([], search.TERM_RE.findall(''))
    self.assertEqual([], search.TERM_RE.findall('   '))

  def test_structured_query_terms(self):
    """We can parse operator terms."""
    self.assertEqual(
        [('', 'field', '=', 'value', '')],
        search.TERM_RE.findall('field=value '))
    self.assertEqual(
        [('', 'field', '>', 'value', '')],
        search.TERM_RE.findall('field>value '))
    self.assertEqual(
        [('', 'flag_name', '=', 'version', '')],
        search.TERM_RE.findall('flag_name=version '))
    self.assertEqual(
        [('', 'flag_name', '=', 'enable-super-stuff', '')],
        search.TERM_RE.findall('flag_name=enable-super-stuff '))
    self.assertEqual(
        [('', 'flag_name', '=', '"enable super stuff"', '')],
        search.TERM_RE.findall('flag_name="enable super stuff" '))

  def test_structured_query_terms__complex(self):
    """We can parse complex operator terms."""
    self.assertEqual(
        [('-', 'field', '=', 'value', '')],
        search.TERM_RE.findall('-field=value '))
    self.assertEqual(
        [('OR ', 'field', '>', 'value', '')],
        search.TERM_RE.findall('OR field>value '))
    self.assertEqual(
        [('-', 'flag_name', '=', 'version', '')],
        search.TERM_RE.findall('-flag_name=version '))
    self.assertEqual(
        [('OR ', 'flag_name', '=', 'enable-super-stuff', '')],
        search.TERM_RE.findall('OR flag_name=enable-super-stuff '))

  def test_text_terms(self):
    """We can parse text terms."""
    self.assertEqual(
        [('', '', '', '', 'hello')],
        search.TERM_RE.findall('hello '))
    self.assertEqual(
        [('', '', '', '', '"hello there people"')],
        search.TERM_RE.findall('"hello there people" '))
    self.assertEqual(
        [('', '', '', '', '"memory location $0x25"')],
        search.TERM_RE.findall('"memory location $0x25" '))

  def test_text_terms__complex(self):
    """We can parse complex text terms."""
    self.assertEqual(
        [('-', '', '', '', 'hello')],
        search.TERM_RE.findall('-hello '))
    self.assertEqual(
        [('-', '', '', '', '"hello there people"')],
        search.TERM_RE.findall('-"hello there people" '))
    self.assertEqual(
        [('OR ', '', '', '', '"memory location $0x25"')],
        search.TERM_RE.findall('OR "memory location $0x25" '))

  def test_malformed(self):
    """Malformed queries are treated like full text, junk ignored."""
    self.assertEqual(
        [],
        search.TERM_RE.findall(':: = == := > >> >>> '))
    self.assertEqual(
        [('', '', '', '', 'word')],
        search.TERM_RE.findall('=word '))


class SearchFunctionsTest(testing_config.CustomTestCase):

  def setUp(self):
    self.featureentry_1 = FeatureEntry(
        name='feature 1', summary='sum', category=1, web_dev_views=1,
        impl_status_chrome=3)
    self.featureentry_1.owner_emails = ['owner@example.com']
    self.featureentry_1.editor_emails = ['editor@example.com']
    self.featureentry_1.cc_emailss = ['cc@example.com']
    self.featureentry_1.put()
    self.featureentry_2 = FeatureEntry(
        name='feature 2', summary='sum', category=2, web_dev_views=1,
        impl_status_chrome=3)
    self.featureentry_2.owner_emails = ['owner@example.com']
    self.featureentry_2.put()
    notifier.FeatureStar.set_star(
        'starrer@example.com', self.featureentry_1.key.integer_id())
    self.featureentry_3 = FeatureEntry(
        name='feature 3', summary='sum', category=3, web_dev_views=1,
        impl_status_chrome=3, unlisted=True)
    self.featureentry_3.owner_emails = ['owner@example.com']
    self.featureentry_3.put()
    self.featureentry_4 = FeatureEntry(
        name='feature 4', summary='sum', category=4, web_dev_views=1,
        impl_status_chrome=4,
        feature_type=core_enums.FEATURE_TYPE_ENTERPRISE_ID)
    self.featureentry_4.owner_emails = ['owner@example.com']
    self.featureentry_4.put()

  def tearDown(self):
    notifier.FeatureStar.set_star(
        'starrer@example.com', self.featureentry_1.key.integer_id(),
        starred=False)
    self.featureentry_1.key.delete()
    self.featureentry_2.key.delete()
    self.featureentry_3.key.delete()
    self.featureentry_4.key.delete()
    for kind in [Gate, FeatureEntry]:
      for entity in kind.query():
        entity.key.delete()

  @mock.patch('internals.approval_defs.fields_approvable_by')
  def test_process_pending_approval_me_query__none(
      self, mock_approvable_by):
    """Nothing is pending."""
    testing_config.sign_in('oner@example.com', 111)
    now = datetime.datetime.now()
    mock_approvable_by.return_value = set([1, 2, 3])

    future = search.process_pending_approval_me_query()
    feature_ids = search._resolve_promise_to_id_list(future)

    self.assertEqual(0, len(feature_ids))

  @mock.patch('internals.approval_defs.fields_approvable_by')
  def test_process_pending_approval_me_query__some__nonapprover(
      self, mock_approvable_by):
    """It's not a pending approval for you."""
    testing_config.sign_in('visitor@example.com', 111)
    now = datetime.datetime.now()
    mock_approvable_by.return_value = set()
    Gate(
        feature_id=self.featureentry_1.key.integer_id(), stage_id=1,
        gate_type=1, state=Vote.REVIEW_REQUESTED,
        requested_on=now).put()

    future = search.process_pending_approval_me_query()
    feature_ids = search._resolve_promise_to_id_list(future)

    self.assertEqual(0, len(feature_ids))

  @mock.patch('internals.approval_defs.fields_approvable_by')
  def test_process_pending_approval_me_query__some__approver(
      self, mock_approvable_by):
    """We can return a list of features pending approval."""
    testing_config.sign_in('owner@example.com', 111)
    time_1 = datetime.datetime.now() - datetime.timedelta(days=4)
    time_2 = datetime.datetime.now()
    mock_approvable_by.return_value = set([1, 2, 3])
    Gate(
        feature_id=self.featureentry_2.key.integer_id(), stage_id=1,
        gate_type=1, state=Vote.REVIEW_REQUESTED,
        requested_on=time_1).put()
    Gate(
        feature_id=self.featureentry_1.key.integer_id(), stage_id=1,
        gate_type=1, state=Vote.REVIEW_REQUESTED,
        requested_on=time_2).put()

    future = search.process_pending_approval_me_query()
    feature_ids = search._resolve_promise_to_id_list(future)
    self.assertEqual(2, len(feature_ids))
    # Results are not sorted.
    self.assertCountEqual(
        [self.featureentry_2.key.integer_id(),
         self.featureentry_1.key.integer_id()],
        feature_ids)

  @mock.patch('internals.approval_defs.fields_approvable_by')
  def test_process_pending_approval_me_query__mixed__approver(
      self, mock_approvable_by):
    """We can find gates that are pending approval."""
    testing_config.sign_in('owner@example.com', 111)
    time_1 = datetime.datetime.now() - datetime.timedelta(days=4)
    time_2 = datetime.datetime.now()
    mock_approvable_by.return_value = set([1, 2, 3])
    Gate(
        feature_id=self.featureentry_2.key.integer_id(), stage_id=1,
        gate_type=1, state=Vote.REVIEW_REQUESTED,
        requested_on=time_1).put()
    Gate(
        feature_id=self.featureentry_1.key.integer_id(), stage_id=1,
        gate_type=1, state=Vote.APPROVED,
        requested_on=time_2).put()

    future = search.process_pending_approval_me_query()
    feature_ids = search._resolve_promise_to_id_list(future)
    self.assertEqual(1, len(feature_ids))
    # Results are not sorted.
    self.assertEqual(
        [self.featureentry_2.key.integer_id()],
        feature_ids)

  def test_process_starred_me_query__anon(self):
    """Anon always has an empty list of starred features."""
    testing_config.sign_out()
    actual = search.process_starred_me_query()
    self.assertEqual(actual, [])

  def test_process_starred_me_query__none(self):
    """We can return a list of features starred by the user."""
    testing_config.sign_in('visitor@example.com', 111)
    actual = search.process_starred_me_query()
    self.assertEqual(actual, [])

  def test_process_starred_me_query__some(self):
    """We can return a list of features starred by the user."""
    testing_config.sign_in('starrer@example.com', 111)
    actual = search.process_starred_me_query()
    self.assertEqual(len(actual), 1)
    self.assertEqual(actual[0], self.featureentry_1.key.integer_id())

  @mock.patch('internals.approval_defs.fields_approvable_by')
  def test_process_recent_reviews_query__none(
      self, mock_approvable_by):
    """Nothing has been reviewed recently."""
    mock_approvable_by.return_value = set({1, 2, 3})

    future = search.process_recent_reviews_query()
    feature_ids = search._resolve_promise_to_id_list(future)

    self.assertEqual(0, len(feature_ids))

  @mock.patch('internals.approval_defs.fields_approvable_by')
  def test_process_recent_reviews_query__some(
      self, mock_approvable_by):
    """Some features have been reviewed recently."""
    mock_approvable_by.return_value = set({1, 2, 3})
    time_1 = datetime.datetime.now() - datetime.timedelta(days=4)
    time_2 = datetime.datetime.now()
    Gate(
        feature_id=self.featureentry_1.key.integer_id(), stage_id=1,
        gate_type=1, state=Vote.NA,
        requested_on=time_2).put()
    Gate(
        feature_id=self.featureentry_2.key.integer_id(), stage_id=1,
        gate_type=1, state=Vote.APPROVED,
        requested_on=time_1).put()

    future = search.process_recent_reviews_query()
    feature_ids = search._resolve_promise_to_id_list(future)

    self.assertEqual(2, len(feature_ids))
    self.assertEqual(
        feature_ids[0], self.featureentry_1.key.integer_id())  # Most recent
    self.assertEqual(
        feature_ids[1], self.featureentry_2.key.integer_id())

  def test_sort_by_total_order__empty(self):
    """Sorting an empty list works."""
    feature_ids = []
    total_order_ids = []
    actual = search._sort_by_total_order(feature_ids, total_order_ids)
    self.assertEqual([], actual)

    total_order_ids = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    actual = search._sort_by_total_order(feature_ids, total_order_ids)
    self.assertEqual([], actual)

  def test_sort_by_total_order__normal(self):
    """We can sort the results according to the total order."""
    feature_ids = [10, 1, 9, 4]
    total_order_ids = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    actual = search._sort_by_total_order(feature_ids, total_order_ids)
    self.assertEqual([10, 9, 4, 1], actual)

  def test_sort_by_total_order__unordered_at_end(self):
    """If the results include features not present in the total order,
    they are put at the end of the list in ID order."""
    feature_ids = [999, 10, 998, 1, 9, 997, 4]
    total_order_ids = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    actual = search._sort_by_total_order(feature_ids, total_order_ids)
    self.assertEqual([10, 9, 4, 1, 997, 998, 999], actual)

  @mock.patch('internals.search.process_pending_approval_me_query')
  @mock.patch('internals.search.process_starred_me_query')
  @mock.patch('internals.search_queries.handle_me_query_async')
  @mock.patch('internals.search.process_recent_reviews_query')
  def test_process_query__predefined(
      self, mock_recent, mock_own_me, mock_star_me, mock_pend_me):
    """We can match predefined queries."""
    mock_recent.return_value = [self.featureentry_1.key.integer_id()]
    mock_own_me.return_value = [self.featureentry_2.key.integer_id()]
    mock_star_me.return_value = [self.featureentry_1.key.integer_id()]
    mock_pend_me.return_value = [self.featureentry_2.key.integer_id()]

    actual_pending, tc = search.process_query('pending-approval-by:me')
    self.assertEqual(actual_pending[0]['name'], 'feature 2')

    actual_star_me, tc = search.process_query('starred-by:me')
    self.assertEqual(actual_star_me[0]['name'], 'feature 1')

    actual_own_me, tc = search.process_query('owner:me')
    self.assertEqual(actual_own_me[0]['name'], 'feature 2')

    actual_recent, tc = search.process_query('is:recently-reviewed')
    self.assertEqual(actual_recent[0]['name'],'feature 1')

  @mock.patch('internals.search.process_pending_approval_me_query')
  @mock.patch('internals.search.process_starred_me_query')
  @mock.patch('internals.search_queries.handle_me_query_async')
  @mock.patch('internals.search.process_recent_reviews_query')
  def test_process_query__negated_predefined(
      self, mock_recent, mock_own_me, mock_star_me, mock_pend_me):
    """We can match predefined queries."""
    mock_recent.return_value = [self.featureentry_1.key.integer_id()]
    mock_own_me.return_value = [self.featureentry_2.key.integer_id()]
    mock_star_me.return_value = [self.featureentry_1.key.integer_id()]
    mock_pend_me.return_value = [self.featureentry_2.key.integer_id()]

    actual_pending, tc = search.process_query('-pending-approval-by:me')
    self.assertEqual(actual_pending[0]['name'], 'feature 1')

    actual_star_me, tc = search.process_query('-starred-by:me')
    self.assertEqual(actual_star_me[0]['name'], 'feature 2')

    actual_own_me, tc = search.process_query('-owner:me')
    self.assertEqual(actual_own_me[0]['name'], 'feature 1')

    actual_recent, tc = search.process_query('-is:recently-reviewed')
    self.assertEqual(actual_recent[0]['name'],'feature 2')

  def test_process_query__single_field(self):
    """We can run single-field queries."""
    actual, tc = search.process_query('')
    self.assertEqual(2, len(actual))
    self.assertCountEqual(
        [f['name'] for f in actual],
        ['feature 1', 'feature 2'])

    actual, tc = search.process_query('category="Web Components"')
    self.assertEqual(1, len(actual))
    self.assertEqual(actual[0]['name'], 'feature 1')

    actual, tc = search.process_query('category=Miscellaneous')
    self.assertEqual(1, len(actual))
    self.assertEqual(actual[0]['name'], 'feature 2')

    actual, tc = search.process_query('category="Miscellaneous"')
    self.assertEqual(1, len(actual))
    self.assertEqual(actual[0]['name'], 'feature 2')

    actual, tc = search.process_query('name="feature 2"')
    self.assertEqual(1, len(actual))
    self.assertEqual(actual[0]['name'], 'feature 2')

    actual, tc = search.process_query('browsers.webdev.view="Strongly positive"')
    self.assertEqual(2, len(actual))
    self.assertCountEqual(
        [f['name'] for f in actual],
        ['feature 1', 'feature 2'])

  def test_process_query__show_deleted_unlisted(self):
    """We can run queries without deleted/unlisted features."""
    actual, tc = search.process_query('', show_deleted=True)
    self.assertEqual(2, len(actual))
    self.assertCountEqual(
        [f['name'] for f in actual],
        ['feature 1', 'feature 2'])

    actual, tc = search.process_query('', show_unlisted=True)
    self.assertEqual(3, len(actual))
    self.assertCountEqual(
        [f['name'] for f in actual],
        ['feature 1', 'feature 2', 'feature 3'])

    actual, tc = search.process_query(
        '', show_unlisted=True, show_deleted=True)
    self.assertEqual(3, len(actual))
    self.assertCountEqual(
        [f['name'] for f in actual],
        ['feature 1', 'feature 2', 'feature 3'])

    actual, tc = search.process_query(
        'category="Web Components" category=Security', show_unlisted=True)
    self.assertEqual([], actual)

    actual, tc = search.process_query(
        'category="Web Components" OR category=Security', show_unlisted=True)
    self.assertEqual(2, len(actual))
    self.assertCountEqual(
        [f['name'] for f in actual],
        ['feature 1', 'feature 3'])

    actual, tc = search.process_query(
        'category="Web Components" OR category=Security', show_deleted=True)
    self.assertEqual(1, len(actual))
    self.assertCountEqual(
        [f['name'] for f in actual],
        ['feature 1'])

  def test_process_query__show_enterprise(self):
    """We can run queries without or without enterprise features."""
    actual, tc = search.process_query('')
    self.assertEqual(2, len(actual))
    self.assertCountEqual(
        [f['name'] for f in actual],
        ['feature 1', 'feature 2'])

    actual, tc = search.process_query('', show_enterprise=True)
    self.assertEqual(3, len(actual))
    self.assertCountEqual(
        [f['name'] for f in actual],
        ['feature 1', 'feature 2', 'feature 4'])


  def test_process_query__negated_single_field(self):
    """We can run single-field queries."""

    actual, tc = search.process_query('-category="Web Components"')
    self.assertEqual(1, len(actual))
    self.assertEqual(actual[0]['name'], 'feature 2')

    actual, tc = search.process_query('-category=Miscellaneous')
    self.assertEqual(1, len(actual))
    self.assertEqual(actual[0]['name'], 'feature 1')

    actual, tc = search.process_query('-category="Miscellaneous"')
    self.assertEqual(1, len(actual))
    self.assertEqual(actual[0]['name'], 'feature 1')

    actual, tc = search.process_query('-name="feature 2"')
    self.assertEqual(1, len(actual))
    self.assertEqual(actual[0]['name'], 'feature 1')

    actual, tc = search.process_query('-browsers.webdev.view="Strongly positive"')
    self.assertEqual(0, len(actual))

  def test_process_query__multiple_fields(self):
    """We can run multi-field queries."""

    actual, tc = search.process_query(
        'category="Web Components" category=Miscellaneous')
    self.assertEqual([], actual)

    actual, tc = search.process_query(
        'category="Web Components" OR category=Miscellaneous')
    self.assertEqual(2, len(actual))
    self.assertCountEqual(
        [f['name'] for f in actual],
        ['feature 1', 'feature 2'])

    actual, tc = search.process_query(
        'category="Web Components" -category=Miscellaneous')
    self.assertEqual(1, len(actual))
    self.assertEqual(actual[0]['name'], 'feature 1')

    actual, tc = search.process_query(
        'browsers.webdev.view="Strongly positive" -category=Miscellaneous')
    self.assertEqual(1, len(actual))
    self.assertEqual(actual[0]['name'], 'feature 1')

    actual, tc = search.process_query(
        'browsers.webdev.view="Strongly positive" '
        '-category=Miscellaneous OR category=Miscellaneous')
    self.assertEqual(2, len(actual))
    self.assertCountEqual(
        [f['name'] for f in actual],
        ['feature 1', 'feature 2'])

    actual, tc = search.process_query(
        'browsers.webdev.view="Strongly positive" -category=Miscellaneous '
        'OR category="Web Components" -category=Miscellaneous')
    self.assertEqual(1, len(actual))
    self.assertEqual(actual[0]['name'], 'feature 1')

  @mock.patch('logging.warning')
  def test_process_query__bad(self, mock_warn):
    """Query terms that are not valid, give warnings."""
    self.assertEqual(
        search.process_query('any:thing e=lse'),
        ([], 0))
    self.assertEqual(2, len(mock_warn.mock_calls))
