# Copyright 2023 Google Inc.
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

from internals.legacy_models import Approval
from internals.core_models import FeatureEntry


class ApprovalTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = FeatureEntry(
        name='feature a', summary='sum', category=1, impl_status_chrome=3)
    self.feature_1.put()
    self.feature_1_id = self.feature_1.key.integer_id()
    self.appr_1 = Approval(
        feature_id=self.feature_1_id, field_id=1,
        state=Approval.REVIEW_REQUESTED,
        set_on=datetime.datetime.now() - datetime.timedelta(1),
        set_by='one@example.com')
    self.appr_1.put()

    self.appr_2 = Approval(
        feature_id=self.feature_1_id, field_id=1,
        state=Approval.APPROVED,
        set_on=datetime.datetime.now(),
        set_by='two@example.com')
    self.appr_2.put()
    self.appr_3 = Approval(
        feature_id=self.feature_1_id, field_id=1,
        state=Approval.APPROVED,
        set_on=datetime.datetime.now() + datetime.timedelta(1),
        set_by='three@example.com')
    self.appr_3.put()

  def tearDown(self):
    self.feature_1.key.delete()
    for appr in Approval.query().fetch():
      appr.key.delete()

  def test_get_approvals(self):
    """We can retrieve Approval entities."""
    actual = Approval.get_approvals(feature_id=self.feature_1_id)
    self.assertEqual(3, len(actual))
    self.assertEqual(Approval.REVIEW_REQUESTED, actual[0].state)
    self.assertEqual(Approval.APPROVED, actual[1].state)
    self.assertEqual(
        sorted(actual, key=lambda appr: appr.set_on),
        actual)

    actual = Approval.get_approvals(field_id=1)
    self.assertEqual(Approval.REVIEW_REQUESTED, actual[0].state)
    self.assertEqual(Approval.APPROVED, actual[1].state)

    actual = Approval.get_approvals(
        states={Approval.REVIEW_REQUESTED,
                Approval.REVIEW_STARTED})
    self.assertEqual(1, len(actual))

    actual = Approval.get_approvals(set_by='one@example.com')
    self.assertEqual(1, len(actual))
    self.assertEqual(Approval.REVIEW_REQUESTED, actual[0].state)

  def test_is_valid_state(self):
    """We know what approval states are valid."""
    self.assertTrue(
        Approval.is_valid_state(Approval.REVIEW_REQUESTED))
    self.assertFalse(Approval.is_valid_state(None))
    self.assertFalse(Approval.is_valid_state('not an int'))
    self.assertFalse(Approval.is_valid_state(999))

  def test_set_approval(self):
    """We can set an Approval entity."""
    Approval.set_approval(
        self.feature_1_id, 2, Approval.REVIEW_REQUESTED,
        'owner@example.com')
    self.assertEqual(
        4,
        len(Approval.query().fetch(None)))

  def test_clear_request(self):
    """We can clear a review request so that it is no longer pending."""
    self.appr_1.state = Approval.REVIEW_REQUESTED
    self.appr_1.put()

    Approval.clear_request(self.feature_1_id, 1)

    remaining_apprs = Approval.get_approvals(
        feature_id=self.feature_1_id, field_id=1,
        states=[Approval.REVIEW_REQUESTED])
    self.assertEqual([], remaining_apprs)
