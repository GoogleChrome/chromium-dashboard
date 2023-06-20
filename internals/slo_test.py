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
from unittest import mock

from framework import permissions
from framework.users import User
from internals import approval_defs
from internals.core_models import FeatureEntry
from internals.review_models import Gate, Vote
from internals import slo


class SLOFunctionTests(testing_config.CustomTestCase):

  def test_is_weekday(self):
    """We can tell if a day is a weekday or weekend."""
    self.assertFalse(slo.is_weekday(datetime.datetime(2023, 6, 4)))  # Sun
    self.assertTrue(slo.is_weekday(datetime.datetime(2023, 6, 5)))  # Mon
    self.assertTrue(slo.is_weekday(datetime.datetime(2023, 6, 6)))  # Tue
    self.assertTrue(slo.is_weekday(datetime.datetime(2023, 6, 7)))  # Wed
    self.assertTrue(slo.is_weekday(datetime.datetime(2023, 6, 8)))  # Thu
    self.assertTrue(slo.is_weekday(datetime.datetime(2023, 6, 9)))  # Fri
    self.assertFalse(slo.is_weekday(datetime.datetime(2023, 6, 10)))  # Sat

  def test_weekdays_between__same_day(self):
    """There are zero days between different times on the same day."""
    start = datetime.datetime(2023, 6, 7, 12, 30, 0)
    end = datetime.datetime(2023, 6, 7, 14, 15, 10)
    actual = slo.weekdays_between(start, end)
    self.assertEqual(0, actual)

  def test_weekdays_between__normal(self):
    """We can count the weekdays between dates."""
    start = datetime.datetime(2023, 6, 7, 12, 30, 0)
    end = datetime.datetime(2023, 6, 8, 14, 15, 10)
    actual = slo.weekdays_between(start, end)
    self.assertEqual(1, actual)

    start = datetime.datetime(2023, 6, 7, 12, 30, 0)
    end = datetime.datetime(2023, 6, 9, 14, 15, 10)
    actual = slo.weekdays_between(start, end)
    self.assertEqual(2, actual)

  def test_weekdays_between__friday_into_weekend(self):
    """We can count the weekdays between dates."""
    start = datetime.datetime(2023, 6, 9, 12, 30, 0)  # Fri
    end = datetime.datetime(2023, 6, 10, 14, 15, 10)  # Sat
    actual = slo.weekdays_between(start, end)
    # Friday does not count because it is the day of the request,
    # and Saturday is a weekend.
    self.assertEqual(0, actual)

  def test_weekdays_between__backwards(self):
    """If end is before start, that counts as zero."""
    start = datetime.datetime(2023, 6, 7, 12, 30, 0)
    end = datetime.datetime(2023, 6, 1, 14, 15, 10)
    actual = slo.weekdays_between(start, end)
    self.assertEqual(0, actual)

  def test_weekdays_between__huge(self):
    """We can stop counting at 9999 days."""
    start = datetime.datetime(1970, 6, 7, 12, 30, 0)
    end = datetime.datetime(2111, 6, 9, 14, 15, 10)
    actual = slo.weekdays_between(start, end)
    self.assertEqual(9999, actual)

  def test_now_utc(self):
    """This function returns a datetime."""
    actual = slo.now_utc()
    self.assertEqual(datetime.datetime, type(actual))

  @mock.patch('internals.slo.now_utc')
  def test_remaining_days__starting_midweek(self, mock_now):
    """We can calculate days remaining in the SLO limit."""
    start = datetime.datetime(2023, 6, 7, 12, 30, 0)  # Wed
    mock_now.return_value = datetime.datetime(2023, 6, 7, 12, 30, 0)  # Wed
    actual = slo.remaining_days(start, 2)
    self.assertEqual(2, actual)

    mock_now.return_value = datetime.datetime(2023, 6, 8, 12, 30, 0)  # Thu
    actual = slo.remaining_days(start, 2)
    self.assertEqual(1, actual)

    mock_now.return_value = datetime.datetime(2023, 6, 9, 12, 30, 0)  # Fri
    actual = slo.remaining_days(start, 2)
    self.assertEqual(0, actual)

    mock_now.return_value = datetime.datetime(2023, 6, 10, 12, 30, 0)  # Sat
    actual = slo.remaining_days(start, 2)
    self.assertEqual(0, actual)

    mock_now.return_value = datetime.datetime(2023, 6, 11, 12, 30, 0)  # Sun
    actual = slo.remaining_days(start, 2)
    self.assertEqual(0, actual)

    mock_now.return_value = datetime.datetime(2023, 6, 12, 12, 30, 0)  # Mon
    actual = slo.remaining_days(start, 2)
    self.assertEqual(-1, actual)

  @mock.patch('internals.slo.now_utc')
  def test_remaining_days__starting_weekend(self, mock_now):
    """We can calculate days remaining in the SLO limit."""
    start = datetime.datetime(2023, 6, 10, 12, 30, 0)  # Sat
    mock_now.return_value = datetime.datetime(2023, 6, 11, 12, 30, 0)  # Sun
    actual = slo.remaining_days(start, 2)
    self.assertEqual(2, actual)

    mock_now.return_value = datetime.datetime(2023, 6, 12, 12, 30, 0)  # Mon
    actual = slo.remaining_days(start, 2)
    self.assertEqual(1, actual)

  @mock.patch('internals.slo.now_utc')
  def test_remaining_days__backwards(self, mock_now):
    """If the end is before the start, we count zero days used."""
    start = datetime.datetime(2023, 6, 7, 12, 30, 0)  # Wed
    mock_now.return_value = datetime.datetime(2023, 6, 7, 12, 30, 0)  # Tue
    actual = slo.remaining_days(start, 2)
    self.assertEqual(2, actual)


class SLORecordingTests(testing_config.CustomTestCase):

  def setUp(self):
    self.gate = Gate(feature_id=1, stage_id=2, gate_type=34, state=4)
    self.vote_review_requested = Vote(
        feature_id=1, gate_id=2, gate_type=34, state=Vote.REVIEW_REQUESTED,
        set_on=datetime.datetime(2023, 6, 7, 1, 2, 3),  # Wed
        set_by='feature-owner@example.com')
    self.vote_needs_work = Vote(
        feature_id=1, gate_id=2, gate_type=34, state=Vote.NEEDS_WORK,
        set_on=datetime.datetime(2023, 6, 12, 1, 2, 3),  # Mon
        set_by='reviewer@example.com')
    self.a_date = datetime.datetime(2023, 6, 17, 1, 2, 3)

  def test_record_vote__not_started(self):
    """If this somehow gets called before the review starts, it's a no-op."""
    # Note that self.gate.requested_on is None.
    self.assertFalse(slo.record_vote(self.gate, []))
    self.assertFalse(slo.record_vote(self.gate, [self.vote_review_requested]))
    self.assertFalse(slo.record_vote(
        self.gate, [self.vote_review_requested, self.vote_needs_work]))
    self.assertIsNone(self.gate.requested_on)
    self.assertIsNone(self.gate.responded_on)

  def test_record_vote__just_started(self):
    """If checked after the request but before the response, it's a no-op."""
    self.gate.requested_on = self.vote_review_requested.set_on
    self.assertFalse(slo.record_vote(self.gate, []))
    self.assertFalse(slo.record_vote(self.gate, [self.vote_review_requested]))
    self.assertEqual(self.vote_review_requested.set_on, self.gate.requested_on)
    self.assertIsNone(self.gate.responded_on)

  def test_record_vote__got_response(self):
    """If called with the reviewer's response, that is recorded."""
    self.gate.requested_on = self.vote_review_requested.set_on
    self.assertTrue(slo.record_vote(
        self.gate, [self.vote_review_requested, self.vote_needs_work]))
    self.assertEqual(self.vote_review_requested.set_on, self.gate.requested_on)
    self.assertEqual(self.vote_needs_work.set_on, self.gate.responded_on)

  def test_record_vote__already_finished(self):
    """If this gets called after the review is done, it's a no-op."""
    self.gate.requested_on = self.a_date
    self.gate.responded_on = self.a_date
    self.assertFalse(slo.record_vote(self.gate, []))
    self.assertFalse(slo.record_vote(self.gate, [self.vote_review_requested]))
    self.assertFalse(slo.record_vote(
        self.gate, [self.vote_review_requested, self.vote_needs_work]))
    self.assertEqual(self.a_date, self.gate.requested_on)
    self.assertEqual(self.a_date, self.gate.responded_on)

  @mock.patch('framework.permissions.can_approve_feature')
  def test_record_comment__not_started(self, mock_caf):
    """Comments posted before the review starts don't count."""
    feature, user, approvers = 'fake feature', 'fake user', ['fake approvers']
    # Note that self.gate.requested_on is None.
    mock_caf.return_value = False
    self.assertFalse(slo.record_comment(feature, self.gate, user, approvers))
    mock_caf.return_value = True
    self.assertFalse(slo.record_comment(feature, self.gate, user, approvers))
    self.assertIsNone(self.gate.requested_on)
    self.assertIsNone(self.gate.responded_on)

  @mock.patch('framework.permissions.can_approve_feature')
  def test_record_comment__non_appover(self, mock_caf):
    """Comments posted during the review by non-approvers don't count."""
    feature, user, approvers = 'fake feature', 'fake user', ['fake approvers']
    self.gate.requested_on = self.a_date
    mock_caf.return_value = False
    self.assertFalse(slo.record_comment(feature, self.gate, user, approvers))
    self.assertEqual(self.a_date, self.gate.requested_on)
    self.assertIsNone(self.gate.responded_on)

  @mock.patch('internals.slo.now_utc')
  @mock.patch('framework.permissions.can_approve_feature')
  def test_record_comment__appover(self, mock_caf, mock_now):
    """Comments posted during the review by an approver do count."""
    feature, user, approvers = 'fake feature', 'fake user', ['fake approvers']
    self.gate.requested_on = self.a_date
    mock_caf.return_value = True
    mock_now.return_value = self.a_date
    self.assertTrue(slo.record_comment(feature, self.gate, user, approvers))
    self.assertEqual(self.a_date, self.gate.requested_on)
    self.assertEqual(self.a_date, self.gate.responded_on)


APPR_FIELDS = approval_defs.APPROVAL_FIELDS_BY_ID
DEFAULT_SLO_LIMIT = approval_defs.DEFAULT_SLO_LIMIT

class SLOReportingTests(testing_config.CustomTestCase):

  def setUp(self):
    self.gate_1 = Gate(feature_id=1, stage_id=2, gate_type=34, state=4)
    self.gate_1.requested_on = datetime.datetime(2023, 6, 7, 12, 30, 0)  # Wed
    self.gate_1.put()

    self.gate_2 = Gate(feature_id=2, stage_id=2, gate_type=54, state=5)
    self.gate_2.requested_on = datetime.datetime(2023, 6, 7, 12, 30, 0)  # Wed
    self.gate_2.put()

    self.gate_3 = Gate(feature_id=2, stage_id=2, gate_type=54, state=4)
    self.gate_3.requested_on = datetime.datetime(2023, 6, 9, 12, 30, 0)  # Fri
    self.gate_3.put()

  def tearDown(self):
    self.gate_1.key.delete()
    self.gate_2.key.delete()
    self.gate_3.key.delete()

  def test_is_gate_overdue__not_started(self):
    """A gate is not overdue if the review has not started yet."""
    self.gate_1.requested_on = None
    self.assertFalse(slo.is_gate_overdue(
        self.gate_1, APPR_FIELDS, DEFAULT_SLO_LIMIT))

  def test_is_gate_overdue__already_responded(self):
    """A gate is not overdue if the reviewer already responded."""
    self.gate_1.responded_on = datetime.datetime(2023, 6, 12, 12, 30, 0)  # Mon
    self.assertFalse(slo.is_gate_overdue(
        self.gate_1, APPR_FIELDS, DEFAULT_SLO_LIMIT))

  @mock.patch('internals.slo.now_utc')
  def test_is_gate_overdue__defined_gate_type(self, mock_now):
    """We can tell if a gate is overdue based on the configured SLO limit."""
    mock_now.return_value = datetime.datetime(2023, 6, 7, 12, 30, 0)  # Wed
    self.assertFalse(slo.is_gate_overdue(
        self.gate_1, APPR_FIELDS, DEFAULT_SLO_LIMIT))

    mock_now.return_value = datetime.datetime(2023, 6, 12, 12, 30, 0)  # Mon
    self.assertTrue(slo.is_gate_overdue(
        self.gate_1, APPR_FIELDS, DEFAULT_SLO_LIMIT))

  @mock.patch('internals.slo.now_utc')
  def test_is_gate_overdue__undefined_gate_type(self, mock_now):
    """We can tell if a gate is overdue based on a default SLO limit."""
    mock_now.return_value = datetime.datetime(2023, 6, 7, 12, 30, 0)  # Wed
    self.assertFalse(slo.is_gate_overdue(
        self.gate_1, {}, DEFAULT_SLO_LIMIT))

    mock_now.return_value = datetime.datetime(2023, 6, 12, 12, 30, 0)  # Mon
    self.assertTrue(slo.is_gate_overdue(
        self.gate_1, {}, DEFAULT_SLO_LIMIT))

  @mock.patch('internals.slo.now_utc')
  def test_get_overdue_gates(self, mock_now):
    """We can tell if a gate is overdue based on a default SLO limit."""
    mock_now.return_value = datetime.datetime(2023, 6, 12, 12, 30, 0)  # Mon

    actual = slo.get_overdue_gates(APPR_FIELDS, DEFAULT_SLO_LIMIT)
    # gate_1 is overdue.
    # gate_2 was approved so it is no longer pending.
    # gate_3 was requested later so it is not overdue yet.
    self.assertEqual([self.gate_1], actual)
