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

from internals import core_models
from internals import review_models
from internals import search_queries


class SearchFeaturesTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = core_models.Feature(
        name='feature a', summary='sum', owner=['owner@example.com'],
        category=1, impl_status_chrome=3)
    self.feature_1.put()
    self.feature_1_id = self.feature_1.key.integer_id()

    self.feature_2 = core_models.Feature(
        name='feature b', summary='sum', owner=['owner@example.com'],
        category=1, impl_status_chrome=3)
    self.feature_2.put()
    self.feature_2_id = self.feature_2.key.integer_id()

    self.approval_1_1 = review_models.Approval(
        feature_id=self.feature_1_id, field_id=1,
        state=review_models.Approval.REVIEW_REQUESTED,
        set_on=datetime.datetime(2022, 7, 1),
        set_by='feature_owner@example.com')
    self.approval_1_1.put()

    self.approval_1_2 = review_models.Approval(
        feature_id=self.feature_1_id, field_id=1,
        state=review_models.Approval.APPROVED,
        set_on=datetime.datetime(2022, 7, 2),
        set_by='reviewer@example.com')
    self.approval_1_2.put()

    self.approval_2_1 = review_models.Approval(
        feature_id=self.feature_2_id, field_id=1,
        state=review_models.Approval.REVIEW_REQUESTED,
        set_on=datetime.datetime(2022, 8, 1),
        set_by='feature_owner@example.com')
    self.approval_2_1.put()

    self.approval_2_2 = review_models.Approval(
        feature_id=self.feature_2_id, field_id=1,
        state=review_models.Approval.APPROVED,
        set_on=datetime.datetime(2022, 8, 2),
        set_by='reviewer@example.com')
    self.approval_2_2.put()

  def tearDown(self):
    self.feature_1.key.delete()
    self.feature_2.key.delete()
    for appr in review_models.Approval.query():
      appr.key.delete()

  def test_single_field_query_async__normal(self):
    """We get a promise to run the DB query, which produces results."""
    actual_promise = search_queries.single_field_query_async(
        'summary', '=', 'sum')
    actual = actual_promise.get_result()
    self.assertCountEqual(
        [self.feature_1_id, self.feature_2_id],
        [key.integer_id() for key in actual])

  def test_single_field_query_async__zero_results(self):
    """When there are no matching results, we get back a promise for []."""
    actual_promise = search_queries.single_field_query_async(
        'summary', '=', 'nope')
    actual = actual_promise.get_result()
    self.assertCountEqual([], actual)

  @mock.patch('logging.warning')
  def test_single_field_query_async__bad_field(self, mock_warn):
    """An unknown field imediately gives zero results."""
    actual = search_queries.single_field_query_async('zodiac', '=', 'leo')
    self.assertCountEqual([], actual)

  def test_total_order_query_async__field_asc(self):
    """We can get keys used to sort features in ascending order."""
    actual_promise = search_queries.total_order_query_async('name')
    actual = actual_promise.get_result()
    self.assertEqual(
        [self.feature_1_id, self.feature_2_id],
        [key.integer_id() for key in actual])

  def test_total_order_query_async__field_desc(self):
    """We can get keys used to sort features in descending order."""
    actual_promise = search_queries.total_order_query_async('-name')
    actual = actual_promise.get_result()
    self.assertEqual(
        [self.feature_2_id, self.feature_1_id],
        [key.integer_id() for key in actual])

  def test_total_order_query_async__requested_on(self):
    """We can get feature IDs sorted by approval review requests."""
    actual = search_queries.total_order_query_async('approvals.requested_on')
    self.assertEqual(
        [self.feature_1_id, self.feature_2_id],
        actual)

  def test_total_order_query_async__reviewed_on(self):
    """We can get feature IDs sorted by approval granting times."""
    actual = search_queries.total_order_query_async('approvals.reviewed_on')
    self.assertEqual(
        [self.feature_1_id, self.feature_2_id],
        actual)
