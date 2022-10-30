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

from internals import core_models
from internals import notifier
from internals import review_models
from internals import search


class SearchRETest(testing_config.CustomTestCase):
  # Note: User queries will always have a space appended before parsing.

  def test_empty_query(self):
    """An empty user query string should yield zero serach terms."""
    self.assertEqual([], search.TERM_RE.findall(''))
    self.assertEqual([], search.TERM_RE.findall('   '))

  def test_operator_terms(self):
    """We can parse operator terms."""
    self.assertEqual(
        [('field', '=', 'value', '')],
        search.TERM_RE.findall('field=value '))
    self.assertEqual(
        [('field', '>', 'value', '')],
        search.TERM_RE.findall('field>value '))
    self.assertEqual(
        [('flag_name', '=', 'version', '')],
        search.TERM_RE.findall('flag_name=version '))
    self.assertEqual(
        [('flag_name', '=', 'enable-super-stuff', '')],
        search.TERM_RE.findall('flag_name=enable-super-stuff '))
    self.assertEqual(
        [('flag_name', '=', '"enable super stuff"', '')],
        search.TERM_RE.findall('flag_name="enable super stuff" '))

  def test_text_terms(self):
    """We can parse text terms."""
    self.assertEqual(
        [('', '', '', 'hello')],
        search.TERM_RE.findall('hello '))
    self.assertEqual(
        [('', '', '', '"hello there people"')],
        search.TERM_RE.findall('"hello there people" '))
    self.assertEqual(
        [('', '', '', '"memory location $0x25"')],
        search.TERM_RE.findall('"memory location $0x25" '))

  def test_malformed(self):
    """Malformed queries are treated like full text, junk ignored."""
    self.assertEqual(
        [],
        search.TERM_RE.findall(':: = == := > >> >>> '))
    self.assertEqual(
        [('', '', '', 'word')],
        search.TERM_RE.findall('=word '))


class SearchFunctionsTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = core_models.Feature(
        name='feature 1', summary='sum', category=1, web_dev_views=1,
        impl_status_chrome=3)
    self.feature_1.put()
    self.featureentry_1 = core_models.FeatureEntry(
        id=self.feature_1.key.integer_id(),
        name='feature 1', summary='sum', category=1, web_dev_views=1,
        impl_status_chrome=3)
    self.featureentry_1.owner_emails = ['owner@example.com']
    self.featureentry_1.editor_emails = ['editor@example.com']
    self.featureentry_1.cc_emailss = ['cc@example.com']
    self.featureentry_1.put()
    self.feature_2 = core_models.Feature(
        name='feature 2', summary='sum', category=2, web_dev_views=1,
        impl_status_chrome=3)
    self.feature_2.put()
    self.featureentry_2 = core_models.FeatureEntry(
        id=self.feature_2.key.integer_id(),
        name='feature 2', summary='sum', category=2, web_dev_views=1,
        impl_status_chrome=3)
    self.featureentry_2.owner_emails = ['owner@example.com']
    self.featureentry_2.put()
    notifier.FeatureStar.set_star(
        'starrer@example.com', self.feature_1.key.integer_id())

  def tearDown(self):
    notifier.FeatureStar.set_star(
        'starrer@example.com', self.feature_1.key.integer_id(),
        starred=False)
    self.feature_1.key.delete()
    self.feature_2.key.delete()
    self.featureentry_1.key.delete()
    self.featureentry_2.key.delete()
    for appr in review_models.Approval.query():
      appr.key.delete()

  @mock.patch('internals.approval_defs.fields_approvable_by')
  def test_process_pending_approval_me_query__none(
      self, mock_approvable_by):
    """Nothing is pending."""
    testing_config.sign_in('oner@example.com', 111)
    now = datetime.datetime.now()
    mock_approvable_by.return_value = set()

    feature_ids = search.process_pending_approval_me_query()

    self.assertEqual(0, len(feature_ids))

  @mock.patch('internals.approval_defs.fields_approvable_by')
  def test_process_pending_approval_me_query__some__nonapprover(
      self, mock_approvable_by):
    """It's not a pending approval for you."""
    testing_config.sign_in('visitor@example.com', 111)
    now = datetime.datetime.now()
    mock_approvable_by.return_value = set()
    review_models.Approval(
        feature_id=self.feature_1.key.integer_id(),
        field_id=1, state=review_models.Approval.REVIEW_REQUESTED,
        set_by='feature_owner@example.com', set_on=now).put()

    feature_ids = search.process_pending_approval_me_query()

    self.assertEqual(0, len(feature_ids))

  @mock.patch('internals.approval_defs.fields_approvable_by')
  def test_process_pending_approval_me_query__some__approver(
      self, mock_approvable_by):
    """We can return a list of features pending approval."""
    testing_config.sign_in('owner@example.com', 111)
    time_1 = datetime.datetime.now() - datetime.timedelta(days=4)
    time_2 = datetime.datetime.now()
    mock_approvable_by.return_value = set([1, 2, 3])
    review_models.Approval(
        feature_id=self.feature_2.key.integer_id(),
        field_id=1, state=review_models.Approval.REVIEW_REQUESTED,
        set_by='feature_owner@example', set_on=time_1).put()
    review_models.Approval(
        feature_id=self.feature_1.key.integer_id(),
        field_id=1, state=review_models.Approval.REVIEW_REQUESTED,
        set_by='feature_owner@example.com', set_on=time_2).put()

    feature_ids = search.process_pending_approval_me_query()
    self.assertEqual(2, len(feature_ids))
    # Results are sorted by set_on timestamp.
    self.assertEqual(
        [self.feature_2.key.integer_id(),
         self.feature_1.key.integer_id()],
        feature_ids)

  @mock.patch('internals.approval_defs.fields_approvable_by')
  def test_process_pending_approval_me_query__mixed__approver(
      self, mock_approvable_by):
    """Only REVIEW_REQUESTED is considered a pending approval."""
    testing_config.sign_in('owner@example.com', 111)
    time_1 = datetime.datetime.now() - datetime.timedelta(days=4)
    time_2 = datetime.datetime.now()
    mock_approvable_by.return_value = set([1, 2, 3])
    review_models.Approval(
        feature_id=self.feature_2.key.integer_id(),
        field_id=1, state=review_models.Approval.REVIEW_REQUESTED,
        set_by='feature_owner@example', set_on=time_1).put()
    review_models.Approval(
        feature_id=self.feature_1.key.integer_id(),
        field_id=1, state=review_models.Approval.NEEDS_WORK,
        set_by='feature_owner@example.com', set_on=time_2).put()

    feature_ids = search.process_pending_approval_me_query()
    self.assertEqual(1, len(feature_ids))
    # Results are sorted by set_on timestamp, but there is only one.
    self.assertEqual(
        [self.feature_2.key.integer_id()],
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
    self.assertEqual(actual[0], self.feature_1.key.integer_id())

  @mock.patch('internals.review_models.Approval.get_approvals')
  @mock.patch('internals.approval_defs.fields_approvable_by')
  def test_process_recent_reviews_query__none(
      self, mock_approvable_by, mock_get_approvals):
    """Nothing has been reviewed recently."""
    mock_approvable_by.return_value = set({1, 2, 3})
    mock_get_approvals.return_value = []

    actual = search.process_recent_reviews_query()

    self.assertEqual(0, len(actual))

  @mock.patch('internals.review_models.Approval.get_approvals')
  @mock.patch('internals.approval_defs.fields_approvable_by')
  def test_process_recent_reviews_query__some(
      self, mock_approvable_by, mock_get_approvals):
    """Some features have been reviewed recently."""
    mock_approvable_by.return_value = set({1, 2, 3})
    time_1 = datetime.datetime.now() - datetime.timedelta(days=4)
    time_2 = datetime.datetime.now()
    mock_get_approvals.return_value = [
        review_models.Approval(
            feature_id=self.feature_1.key.integer_id(),
            field_id=1, state=review_models.Approval.NA, set_on=time_2),
        review_models.Approval(
            feature_id=self.feature_2.key.integer_id(),
            field_id=1, state=review_models.Approval.APPROVED, set_on=time_1),
    ]

    actual = search.process_recent_reviews_query()

    self.assertEqual(2, len(actual))
    self.assertEqual(actual[0], self.feature_1.key.integer_id())  # Most recent
    self.assertEqual(actual[1], self.feature_2.key.integer_id())

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
    mock_recent.return_value = [self.feature_1.key.integer_id()]
    mock_own_me.return_value = [self.feature_2.key.integer_id()]
    mock_star_me.return_value = [self.feature_1.key.integer_id()]
    mock_pend_me.return_value = [self.feature_2.key.integer_id()]

    actual_pending, tc = search.process_query('pending-approval-by:me')
    self.assertEqual(actual_pending[0]['name'], 'feature 2')

    actual_star_me, tc = search.process_query('starred-by:me')
    self.assertEqual(actual_star_me[0]['name'], 'feature 1')

    actual_own_me, tc = search.process_query('owner:me')
    self.assertEqual(actual_own_me[0]['name'], 'feature 2')

    actual_recent, tc = search.process_query('is:recently-reviewed')
    self.assertEqual(actual_recent[0]['name'],'feature 1')

  def test_process_query__single_field(self):
    """We can can run single-field queries."""

    actual, tc = search.process_query('category=1')
    self.assertEqual(1, len(actual))
    self.assertEqual(actual[0]['name'], 'feature 1')

    actual, tc = search.process_query('category=2')
    self.assertEqual(1, len(actual))
    self.assertEqual(actual[0]['name'], 'feature 2')

    actual, tc = search.process_query('category="2"')
    self.assertEqual(1, len(actual))
    self.assertEqual(actual[0]['name'], 'feature 2')

    actual, tc = search.process_query('name="feature 2"')
    self.assertEqual(1, len(actual))
    self.assertEqual(actual[0]['name'], 'feature 2')

    actual, tc = search.process_query('browsers.webdev.view=1')
    self.assertEqual(2, len(actual))
    self.assertCountEqual(
        [f['name'] for f in actual],
        ['feature 1', 'feature 2'])

  @mock.patch('logging.warning')
  def test_process_query__bad(self, mock_warn):
    """Query terms that are not valid, give warnings."""
    self.assertEqual(
        search.process_query('any:thing e=lse'),
        ([], 0))
    self.assertEqual(2, len(mock_warn.mock_calls))
