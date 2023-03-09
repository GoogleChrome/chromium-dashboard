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

import base64
import datetime
import requests
import testing_config  # Must be imported before the module under test.
import unittest
import urllib.request, urllib.parse, urllib.error

from unittest import mock
import flask
import werkzeug

from internals import approval_defs
from internals.legacy_models import Approval
from internals.review_models import Gate, Vote


class FetchOwnersTest(testing_config.CustomTestCase):

  @mock.patch('requests.get')
  def test__normal(self, mock_get):
    """We can fetch and parse an OWNERS file.  And reuse cached value."""
    file_contents = (
        '# Blink API owners are responsible for ...\n'
        '#\n'
        '# See https://www.chromium.org/blink#new-features for details.\n'
        'owner1@example.com\n'
        'owner2@example.com\n'
        'owner3@example.com\n'
        '\n')
    encoded = base64.b64encode(file_contents.encode())
    mock_get.return_value = testing_config.Blank(
        status_code=200,
        content=encoded)

    actual = approval_defs.fetch_owners('https://example.com')
    again = approval_defs.fetch_owners('https://example.com')

    # Only called once because second call will be a redis hit.
    mock_get.assert_called_once_with('https://example.com')
    self.assertEqual(
        actual,
        ['owner1@example.com', 'owner2@example.com', 'owner3@example.com'])
    self.assertEqual(again, actual)

  @mock.patch('logging.error')
  @mock.patch('requests.get')
  def test__error(self, mock_get, mock_err):
    """If we can't read the OWNER file, raise an exception."""
    mock_get.return_value = testing_config.Blank(
        status_code=404)

    with self.assertRaises(ValueError):
      approval_defs.fetch_owners('https://example.com')

    mock_get.assert_called_once_with('https://example.com')



MOCK_APPROVALS_BY_ID = {
    1: approval_defs.ApprovalFieldDef(
        'Intent to test',
        'You need permission to test',
        1, approval_defs.ONE_LGTM, ['approver@example.com'], 'API Owners'),
    2: approval_defs.ApprovalFieldDef(
        'Intent to optimize',
        'You need permission to optimize',
        2, approval_defs.THREE_LGTM, 'https://example.com', 'API Owners'),
}


class GetApproversTest(testing_config.CustomTestCase):

  @mock.patch('internals.approval_defs.APPROVAL_FIELDS_BY_ID',
              MOCK_APPROVALS_BY_ID)
  @mock.patch('internals.approval_defs.fetch_owners')
  def test__hard_coded(self, mock_fetch_owner):
    """Some approvals may have a hard-coded list of appovers."""
    actual = approval_defs.get_approvers(1)
    mock_fetch_owner.assert_not_called()
    self.assertEqual(actual, ['approver@example.com'])

  @mock.patch('internals.approval_defs.APPROVAL_FIELDS_BY_ID',
              MOCK_APPROVALS_BY_ID)
  @mock.patch('internals.approval_defs.fetch_owners')
  def test__url(self, mock_fetch_owner):
    """Some approvals may have a hard-coded list of appovers."""
    mock_fetch_owner.return_value = ['owner@example.com']
    actual = approval_defs.get_approvers(2)
    mock_fetch_owner.assert_called_once_with('https://example.com')
    self.assertEqual(actual, ['owner@example.com'])


class IsValidFieldIdTest(testing_config.CustomTestCase):

  @mock.patch('internals.approval_defs.APPROVAL_FIELDS_BY_ID',
              MOCK_APPROVALS_BY_ID)
  def test(self):
    """We know if a field_id is defined or not."""
    self.assertTrue(approval_defs.is_valid_field_id(1))
    self.assertTrue(approval_defs.is_valid_field_id(2))
    self.assertFalse(approval_defs.is_valid_field_id(3))


class IsApprovedTest(testing_config.CustomTestCase):

  def setUp(self):
    feature_1_id = 123456
    self.appr_nr = Approval(
        feature_id=feature_1_id, field_id=1,
        state=Approval.REVIEW_REQUESTED,
        set_on=datetime.datetime.now(),
        set_by='one@example.com')
    self.appr_na = Approval(
        feature_id=feature_1_id, field_id=1,
        state=Approval.NA,
        set_on=datetime.datetime.now(),
        set_by='one@example.com')
    self.appr_no = Approval(
        feature_id=feature_1_id, field_id=1,
        state=Approval.DENIED,
        set_on=datetime.datetime.now(),
        set_by='two@example.com')
    self.appr_yes = Approval(
        feature_id=feature_1_id, field_id=1,
        state=Approval.APPROVED,
        set_on=datetime.datetime.now(),
        set_by='three@example.com')

  @mock.patch('internals.approval_defs.APPROVAL_FIELDS_BY_ID',
              MOCK_APPROVALS_BY_ID)
  def test_is_approved(self):
    """We know if an approval rule has been satisfied."""

    # Field requires 1 LGTM
    self.assertFalse(approval_defs.is_approved([], 1))
    self.assertFalse(approval_defs.is_approved([self.appr_nr], 1))
    self.assertFalse(approval_defs.is_approved([self.appr_no], 1))
    self.assertTrue(approval_defs.is_approved([self.appr_yes], 1))
    self.assertTrue(approval_defs.is_approved([self.appr_na], 1))
    self.assertFalse(approval_defs.is_approved([self.appr_nr, self.appr_no], 1))
    self.assertFalse(approval_defs.is_approved(
        [self.appr_nr, self.appr_no, self.appr_yes], 1))
    self.assertTrue(approval_defs.is_approved([self.appr_nr, self.appr_yes], 1))
    self.assertTrue(approval_defs.is_approved([self.appr_nr, self.appr_na], 1))

    # Field requires 3 LGTMs
    self.assertFalse(approval_defs.is_approved([], 2))
    self.assertFalse(approval_defs.is_approved([self.appr_nr], 2))
    self.assertFalse(approval_defs.is_approved([self.appr_no], 2))
    self.assertFalse(approval_defs.is_approved([self.appr_yes], 2))
    self.assertFalse(approval_defs.is_approved([self.appr_na], 2))
    self.assertFalse(approval_defs.is_approved([self.appr_nr, self.appr_no], 2))
    self.assertFalse(approval_defs.is_approved(
        [self.appr_nr, self.appr_no, self.appr_yes], 2))
    self.assertFalse(approval_defs.is_approved([self.appr_nr, self.appr_yes], 2))

    self.assertTrue(approval_defs.is_approved(
        [self.appr_yes, self.appr_yes, self.appr_yes], 2))
    self.assertTrue(approval_defs.is_approved(
        [self.appr_yes, self.appr_yes, self.appr_na], 2))
    self.assertTrue(approval_defs.is_approved(
        [self.appr_na, self.appr_na, self.appr_na], 2))
    self.assertFalse(approval_defs.is_approved(
        [self.appr_yes, self.appr_yes, self.appr_yes, self.appr_no], 2))
    self.assertFalse(approval_defs.is_approved(
        [self.appr_na, self.appr_yes, self.appr_yes, self.appr_no], 2))

  @mock.patch('internals.approval_defs.APPROVAL_FIELDS_BY_ID',
              MOCK_APPROVALS_BY_ID)
  def test_is_resolved(self):
    """We know if an approval request has been resolved."""
    # Field requires 1 LGTM
    self.assertFalse(approval_defs.is_resolved([], 1))
    self.assertFalse(approval_defs.is_resolved([self.appr_nr], 1))
    self.assertTrue(approval_defs.is_resolved([self.appr_no], 1))
    self.assertTrue(approval_defs.is_resolved([self.appr_yes], 1))
    self.assertTrue(approval_defs.is_resolved([self.appr_nr, self.appr_no], 1))
    self.assertTrue(approval_defs.is_resolved(
        [self.appr_nr, self.appr_no, self.appr_yes], 1))
    self.assertTrue(approval_defs.is_resolved([self.appr_nr, self.appr_yes], 1))

    # Field requires 3 LGTMs
    self.assertFalse(approval_defs.is_resolved([], 2))
    self.assertFalse(approval_defs.is_resolved([self.appr_nr], 2))
    self.assertTrue(approval_defs.is_resolved([self.appr_no], 2))
    self.assertFalse(approval_defs.is_resolved([self.appr_yes], 2))
    self.assertTrue(approval_defs.is_resolved([self.appr_nr, self.appr_no], 2))
    self.assertTrue(approval_defs.is_resolved(
        [self.appr_nr, self.appr_no, self.appr_yes], 2))
    self.assertFalse(approval_defs.is_resolved([self.appr_nr, self.appr_yes], 2))

    self.assertTrue(approval_defs.is_resolved(
        [self.appr_yes, self.appr_yes, self.appr_yes], 2))
    self.assertTrue(approval_defs.is_resolved(
        [self.appr_yes, self.appr_yes, self.appr_yes, self.appr_no], 2))



RR = Vote.REVIEW_REQUESTED
AP = Vote.APPROVED
DN = Vote.DENIED
NW = Vote.NEEDS_WORK
RS = Vote.REVIEW_STARTED
NA = Vote.NA
GATE_VALUES= Vote.VOTE_VALUES.copy()
GATE_VALUES.update({Gate.PREPARING: 'preparing'})


class CalcGateStateTest(testing_config.CustomTestCase):

  def do_calc(self, *vote_states):
    votes = [    # set_on dates are in the order of the given list.
        Vote(state=state, set_on=datetime.datetime(2022, 1, i+1))
        for i, state in enumerate(vote_states)]
    actual_1 = approval_defs._calc_gate_state(votes, approval_defs.ONE_LGTM)
    actual_3 = approval_defs._calc_gate_state(votes, approval_defs.THREE_LGTM)
    return GATE_VALUES[actual_1], GATE_VALUES[actual_3]

  def test_no_votes_yet(self):
    """A newly created gate has no votes and should be PREPARING."""
    self.assertEqual(('preparing', 'preparing'),
                     self.do_calc())

  def test_just_requested(self):
    """The user has requested a review."""
    self.assertEqual(('review_requested', 'review_requested'),
                     self.do_calc(RR))

  def test_request_one_approved(self):
    """The user has requested a review and it was approved."""
    self.assertEqual(('approved', 'review_requested'),
                     self.do_calc(RR, AP))

  def test_request_three_approved(self):
    """The user has requested a review and it got 3 approvals."""
    self.assertEqual(('approved', 'approved'),
                     self.do_calc(RR, AP, AP, AP))

  def test_request_needs_work(self):
    """The user has requested a review and a reviewer said it needs work."""
    self.assertEqual(('needs_work', 'needs_work'),
                     self.do_calc(RR, NW))
    self.assertEqual(('needs_work', 'needs_work'),
                     self.do_calc(RR, RS, NW))
    self.assertEqual(('needs_work', 'needs_work'),
                     self.do_calc(RR, NW, NW))

  def test_request_disagreement(self):
    """Reviewers may have different opinions, needed LGTMs counted."""
    self.assertEqual(('approved', 'needs_work'),
                     self.do_calc(RR, AP, NW))
    self.assertEqual(('approved', 'needs_work'),
                     self.do_calc(RR, NW, AP))
    self.assertEqual(('approved', 'review_requested'),
                     self.do_calc(RR, AP))
    self.assertEqual(('approved', 'review_requested'),
                     self.do_calc(RR, AP, AP))
    self.assertEqual(('approved', 'review_started'),
                     self.do_calc(RR, AP, AP, RS))
    self.assertEqual(('approved', 'needs_work'),
                     self.do_calc(RR, AP, NW, AP))

  def test_ping(self):
    """Feature owner re-requested review after feedback or waiting."""
    self.assertEqual(('review_requested', 'review_requested'),
                     self.do_calc(NW, RR))
    self.assertEqual(('review_requested', 'review_requested'),
                     self.do_calc(DN, RR))
    self.assertEqual(('review_requested', 'review_requested'),
                     self.do_calc(RS, RR))
    self.assertEqual(('review_requested', 'review_requested'),
                     self.do_calc(NW, NW, RS, RR))

  def test_ping_pong(self):
    """More reviewer votes after re-request."""
    self.assertEqual(('review_started', 'review_started'),
                     self.do_calc(NW, RR, RS))
    self.assertEqual(('approved', 'review_requested'),
                     self.do_calc(DN, RR, AP))
    self.assertEqual(('approved', 'needs_work'),
                     self.do_calc(RS, RR, AP, NW))
    self.assertEqual(('approved', 'approved'),
                     self.do_calc(AP, AP, RS, AP))


class UpdateTest(testing_config.CustomTestCase):

  def setUp(self):
    self.gate_1 = Gate(feature_id=1, stage_id=1, gate_type=2, state=Vote.APPROVED)
    self.gate_1.put()
    gate_id = self.gate_1.key.integer_id()
    self.votes = []
    # Votes that reference gate_1 show that it got the one APPROVED needed.
    self.votes.append(Vote(feature_id=1, gate_id=gate_id, state=Vote.APPROVED,
        set_on=datetime.datetime(2020, 1, 1), set_by='user1@example.com'))
    self.votes.append(Vote(feature_id=1, gate_id=gate_id,
        state=Vote.DENIED, set_on=datetime.datetime(2020, 1, 1),
        set_by='use21@example.com'))
    self.votes.append(Vote(feature_id=1, gate_id=gate_id,
        state=Vote.REVIEW_REQUESTED, set_on=datetime.datetime(2020, 2, 1),
        set_by='use31@example.com'))
    self.votes.append(Vote(feature_id=1, gate_id=gate_id,
        state=Vote.REVIEW_REQUESTED, set_on=datetime.datetime(2020, 3, 1),
        set_by='user4@example.com'))
    self.votes.append(Vote(feature_id=1, gate_id=gate_id,
        state=Vote.REVIEW_REQUESTED, set_on=datetime.datetime(2020, 1, 2),
        set_by='user5@example.com'))

    self.gate_2 = Gate(feature_id=2, stage_id=2, gate_type=2,
        state=Vote.APPROVED)
    self.gate_2.put()
    gate_id = self.gate_2.key.integer_id()
    self.votes.append(Vote(feature_id=1, gate_id=gate_id,
        state=Vote.REVIEW_REQUESTED, set_on=datetime.datetime(2020, 7, 1),
        set_by='user6@example.com'))
    # Votes that reference gate_2 indicate it should be APPROVED.
    self.votes.append(Vote(feature_id=1, gate_id=gate_id, state=Vote.APPROVED,
        set_on=datetime.datetime(2020, 2, 1), set_by='user7@example.com'))
    self.votes.append(Vote(feature_id=1, gate_id=gate_id, state=Vote.APPROVED,
        set_on=datetime.datetime(2020, 4, 10), set_by='user8@example.com'))
    self.votes.append(Vote(feature_id=1, gate_id=gate_id, state=Vote.NEEDS_WORK,
        set_on=datetime.datetime(2020, 1, 15), set_by='user9@example.com'))
    self.votes.append(Vote(
        feature_id=1, gate_id=gate_id, state=Vote.REVIEW_STARTED,
        set_on=datetime.datetime(2020, 8, 23), set_by='user10@example.com'))
    self.votes.append(Vote(feature_id=1, gate_id=gate_id, state=Vote.APPROVED,
        set_on=datetime.datetime(2021, 1, 1), set_by='user11@example.com'))

    # Some additional votes that should have no bearing on the gates.
    self.votes.append(Vote(feature_id=2, gate_id=5, state=Vote.DENIED,
        set_on=datetime.datetime(2021, 1, 1), set_by='user11@example.com'))
    self.votes.append(Vote(feature_id=3, gate_id=3, state=Vote.REVIEW_REQUESTED,
        set_on=datetime.datetime(2021, 1, 1), set_by='user11@example.com'))
    self.votes.append(Vote(feature_id=2, gate_id=1, state=Vote.REVIEW_REQUESTED,
        set_on=datetime.datetime(2021, 1, 1), set_by='user11@example.com'))
    self.votes.append(Vote(feature_id=2, gate_id=1, state=Vote.NA,
        set_on=datetime.datetime(2021, 1, 1), set_by='user11@example.com'))
    self.votes.append(Vote(feature_id=1, gate_id=2, state=Vote.APPROVED,
        set_on=datetime.datetime(2021, 1, 1), set_by='user11@example.com'))

    for vote in self.votes:
      vote.put()

  def tearDown(self):
    self.gate_1.key.delete()
    self.gate_2.key.delete()
    for vote in self.votes:
      vote.key.delete()

  def test_update_approval_stage__needs_update(self):
    """Gate's approval state will be updated based on votes."""
    # Gate 1 should evaluate to not approved after updating.
    self.assertEqual(
        approval_defs.update_gate_approval_state(self.gate_1), Vote.APPROVED)
    self.assertEqual(self.gate_1.state, Vote.APPROVED)

  def test_update_approval_state__no_change(self):
    """Gate's approval state does not change unless it needs to."""
    # Gate 2 is already marked as approved and should not change.
    self.assertEqual(
        approval_defs.update_gate_approval_state(self.gate_2), Vote.APPROVED)
    self.assertEqual(self.gate_2.state, Vote.APPROVED)
