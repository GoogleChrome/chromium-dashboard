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
    """For huge differences, we approximate."""
    start = datetime.datetime(1970, 6, 7, 12, 30, 0)
    end = datetime.datetime(2111, 6, 9, 14, 15, 10)
    actual = slo.weekdays_between(start, end)
    self.assertEqual(36786, actual)

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
    self.gate = Gate(
        feature_id=1, stage_id=2, gate_type=34, state=Gate.PREPARING)
    self.vote_review_requested = Vote(
        feature_id=1, gate_id=2, gate_type=34, state=Vote.REVIEW_REQUESTED,
        set_on=datetime.datetime(2023, 6, 7, 1, 2, 3),  # Wed
        set_by='feature-owner@example.com')
    self.vote_no_response = Vote(
        feature_id=1, gate_id=2, gate_type=34, state=Vote.NO_RESPONSE,
        set_on=datetime.datetime(2023, 6, 7, 1, 2, 3),  # Wed
        set_by='reviewer@example.com')
    self.vote_started = Vote(
        feature_id=1, gate_id=2, gate_type=34, state=Vote.REVIEW_STARTED,
        set_on=datetime.datetime(2023, 6, 7, 1, 2, 3),  # Wed
        set_by='reviewer@example.com')
    self.vote_needs_work = Vote(
        feature_id=1, gate_id=2, gate_type=34, state=Vote.NEEDS_WORK,
        set_on=datetime.datetime(2023, 6, 12, 1, 2, 3),  # Mon
        set_by='reviewer@example.com')
    self.vote_review_again = Vote(
        feature_id=1, gate_id=2, gate_type=34, state=Vote.REVIEW_REQUESTED,
        set_on=datetime.datetime(2023, 6, 13, 1, 2, 3),  # Tue
        set_by='feature-owner@example.com')
    self.vote_approved = Vote(
        feature_id=1, gate_id=2, gate_type=34, state=Vote.APPROVED,
        set_on=datetime.datetime(2023, 6, 14, 1, 2, 3),  # Wed
        set_by='reviewer@example.com')
    self.a_date = datetime.datetime(2023, 6, 17, 1, 2, 3)

  def test_record_vote__not_started(self):
    """If this somehow gets called before the review starts, it's a no-op."""
    self.assertFalse(slo.record_vote(self.gate, [], Gate.PREPARING))
    self.assertFalse(slo.record_vote(
        self.gate, [self.vote_no_response], Gate.PREPARING))
    self.assertIsNone(self.gate.requested_on)
    self.assertIsNone(self.gate.responded_on)
    self.assertIsNone(self.gate.resolved_on)
    self.assertIsNone(self.gate.needs_work_started_on)

  def test_record_vote__feature_owner_starting(self):
    """When we get a review request, we set requested_on."""
    self.gate.state = Vote.REVIEW_REQUESTED
    self.assertTrue(slo.record_vote(
        self.gate, [self.vote_review_requested], Gate.PREPARING))
    self.assertEqual(self.vote_review_requested.set_on, self.gate.requested_on)
    self.assertIsNone(self.gate.responded_on)
    self.assertIsNone(self.gate.resolved_on)
    self.assertIsNone(self.gate.needs_work_started_on)

  def test_record_vote__reviewer_starting(self):
    """When a reviewer starts the review, we set both requested_on and responded_on."""
    self.gate.state = Vote.REVIEW_STARTED
    self.assertTrue(slo.record_vote(
        self.gate, [self.vote_started], Gate.PREPARING))
    self.assertEqual(self.vote_started.set_on, self.gate.requested_on)
    self.assertEqual(self.vote_started.set_on, self.gate.responded_on)
    self.assertIsNone(self.gate.resolved_on)
    self.assertIsNone(self.gate.needs_work_started_on)

  def test_record_vote__got_response(self):
    """If called with the reviewer's response, that is recorded."""
    self.gate.requested_on = self.vote_review_requested.set_on
    self.gate.state = Vote.NEEDS_WORK
    self.assertTrue(slo.record_vote(
        self.gate, [self.vote_review_requested, self.vote_needs_work],
        Vote.REVIEW_REQUESTED))
    self.assertEqual(self.vote_review_requested.set_on, self.gate.requested_on)
    self.assertEqual(self.vote_needs_work.set_on, self.gate.responded_on)
    self.assertIsNone(self.gate.resolved_on)
    self.assertEqual(
        self.gate.needs_work_started_on, self.vote_needs_work.set_on)

  def test_record_vote__finished_rework(self):
    """If the feature owner finished needed work, that is recorded."""
    self.gate.requested_on = self.vote_review_requested.set_on
    self.gate.state = Vote.REVIEW_REQUESTED
    self.gate.responded_on = self.vote_needs_work.set_on
    self.gate.needs_work_started_on = self.vote_needs_work.set_on # Mon
    self.assertTrue(slo.record_vote(
        self.gate, [self.vote_review_again], # Tue
        Vote.NEEDS_WORK))
    self.assertEqual(self.vote_review_requested.set_on, self.gate.requested_on)
    self.assertEqual(self.vote_needs_work.set_on, self.gate.responded_on)
    self.assertEqual(self.gate.needs_work_elapsed, 1)
    self.assertIsNone(self.gate.resolved_on)
    self.assertIsNone(self.gate.needs_work_started_on)

  def test_record_vote__resolving(self):
    """If review finishes, that counts as response and resolution."""
    self.gate.requested_on = self.vote_review_requested.set_on
    self.gate.state = Vote.APPROVED
    self.assertTrue(slo.record_vote(
        self.gate, [self.vote_review_requested, self.vote_approved],
        Vote.REVIEW_REQUESTED))
    self.assertEqual(self.vote_review_requested.set_on, self.gate.requested_on)
    self.assertEqual(self.vote_approved.set_on, self.gate.responded_on)
    self.assertIsNone(self.gate.needs_work_elapsed)
    self.assertEqual(self.gate.resolved_on, self.vote_approved.set_on)
    self.assertIsNone(self.gate.needs_work_started_on)

  def test_record_vote__reviewer_immediate_resolution(self):
    """When a review single-handledly resolves, we set all timestamps."""
    self.gate.state = Vote.APPROVED
    self.assertTrue(slo.record_vote(
        self.gate, [self.vote_approved], Gate.PREPARING))
    self.assertEqual(self.vote_approved.set_on, self.gate.requested_on)
    self.assertEqual(self.vote_approved.set_on, self.gate.responded_on)
    self.assertEqual(self.vote_approved.set_on, self.gate.resolved_on)
    self.assertIsNone(self.gate.needs_work_started_on)

  def test_record_vote__already_responded(self):
    """Votes that don't change state, after the initial response, it's a no-op."""
    self.gate.requested_on = self.a_date
    self.gate.responded_on = self.a_date
    self.gate.state = Vote.REVIEW_REQUESTED
    self.assertFalse(slo.record_vote(self.gate, [], Vote.REVIEW_REQUESTED))
    self.assertFalse(slo.record_vote(
        self.gate, [self.vote_review_requested], Vote.REVIEW_REQUESTED))
    self.assertFalse(slo.record_vote(
        self.gate, [self.vote_review_requested, self.vote_started],
        Vote.REVIEW_REQUESTED))
    self.assertEqual(self.a_date, self.gate.requested_on)
    self.assertEqual(self.a_date, self.gate.responded_on)

  def test_record_vote__already_resolved(self):
    """If review was finished, more approvals don't change resolved_on."""
    self.gate.requested_on = self.vote_review_requested.set_on
    self.gate.responded_on = self.vote_approved.set_on
    self.gate.resolved_on = self.vote_approved.set_on
    self.gate.state = Vote.APPROVED
    vote_approved_again = Vote(
        feature_id=1, gate_id=2, gate_type=34, state=Vote.APPROVED,
        set_on=datetime.datetime(2023, 6, 15, 1, 2, 3),  # Thu
        set_by='other-reviewer@example.com')

    self.assertFalse(slo.record_vote(
        self.gate, [
            self.vote_review_requested, self.vote_approved, vote_approved_again],
        Vote.APPROVED))
    self.assertEqual(self.vote_review_requested.set_on, self.gate.requested_on)
    self.assertEqual(self.vote_approved.set_on, self.gate.responded_on)
    self.assertIsNone(self.gate.needs_work_elapsed)
    self.assertEqual(self.vote_approved.set_on, self.gate.resolved_on)
    self.assertIsNone(self.gate.needs_work_started_on)

  @mock.patch('framework.permissions.can_review_gate')
  def test_record_comment__not_started(self, mock_crg):
    """Comments posted before the review starts don't count."""
    feature, user, approvers = 'fake feature', 'fake user', ['fake approvers']
    # Note that self.gate.requested_on is None.
    mock_crg.return_value = False
    self.assertFalse(slo.record_comment(feature, self.gate, user, approvers))
    mock_crg.return_value = True
    self.assertFalse(slo.record_comment(feature, self.gate, user, approvers))
    self.assertIsNone(self.gate.requested_on)
    self.assertIsNone(self.gate.responded_on)

  @mock.patch('framework.permissions.can_review_gate')
  def test_record_comment__non_appover(self, mock_crg):
    """Comments posted during the review by non-approvers don't count."""
    feature, user, approvers = 'fake feature', 'fake user', ['fake approvers']
    self.gate.requested_on = self.a_date
    mock_crg.return_value = False
    self.assertFalse(slo.record_comment(feature, self.gate, user, approvers))
    self.assertEqual(self.a_date, self.gate.requested_on)
    self.assertIsNone(self.gate.responded_on)

  @mock.patch('internals.slo.now_utc')
  @mock.patch('framework.permissions.can_review_gate')
  def test_record_comment__appover(self, mock_crg, mock_now):
    """Comments posted during the review by an approver do count."""
    feature, user, approvers = 'fake feature', 'fake user', ['fake approvers']
    self.gate.requested_on = self.a_date
    mock_crg.return_value = True
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

  def test_get_active_gates(self):
    """We can get a list of active gates that might be overdue."""
    actual = slo.get_active_gates()
    # gate_1 is overdue.
    # gate_2 was approved so it is no longer active.
    # gate_3 was requested later, but it is still active.
    self.assertEqual([self.gate_1, self.gate_3], actual)
