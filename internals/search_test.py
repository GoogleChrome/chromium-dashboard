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

import mock

from internals import models
from internals import notifier
from internals import search


class SearchFunctionsTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = models.Feature(
        name='feature a', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=3)
    self.feature_1.owner = ['owner@example.com']
    self.feature_1.put()
    notifier.FeatureStar.set_star(
        'starrer@example.com', self.feature_1.key.integer_id())

  def tearDown(self):
    notifier.FeatureStar.set_star(
        'starrer@example.com', self.feature_1.key.integer_id(),
        starred=False)
    self.feature_1.key.delete()

  def test_process_pending_approval_me_query(self):
    """We can return a list of features pending approval."""
    # TODO(jrobbins): write this
    pass

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
    self.assertEqual(actual[0]['summary'], 'sum')

  def test_process_owner_me_query__none(self):
    """We can return a list of features owned by the user."""
    testing_config.sign_in('visitor@example.com', 111)
    actual = search.process_owner_me_query()
    self.assertEqual(actual, [])

  def test_process_owner_me_query__some(self):
    """We can return a list of features owned by the user."""
    testing_config.sign_in('owner@example.com', 111)
    actual = search.process_owner_me_query()
    self.assertEqual(len(actual), 1)
    self.assertEqual(actual[0]['summary'], 'sum')

  @mock.patch('logging.warning')
  @mock.patch('internals.search.process_pending_approval_me_query')
  @mock.patch('internals.search.process_starred_me_query')
  @mock.patch('internals.search.process_owner_me_query')
  def test_process_query(
      self, mock_own_me, mock_star_me, mock_pend_me, mock_warn):
    """We can match predefined queries."""
    mock_own_me.return_value = 'fake owner result'
    mock_star_me.return_value = 'fake star result'
    mock_pend_me.return_value = 'fake pend result'

    self.assertEqual(
        search.process_query('pending-approval-by:me'),
        'fake pend result')

    self.assertEqual(
        search.process_query('starred-by:me'),
        'fake star result')

    self.assertEqual(
        search.process_query('owner:me'),
        'fake owner result')

    self.assertEqual(
        search.process_query('anything else'),
        [])
    mock_warn.assert_called_once()
