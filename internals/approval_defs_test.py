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
import testing_config  # Must be imported before the module under test.

from unittest import mock

from framework import rediscache
from internals import approval_defs
from internals import core_enums
from internals.review_models import Gate, GateDef, Vote, OwnersFile


class FetchOwnersTest(testing_config.CustomTestCase):

  FILE_CONTENTS = (
      '# Blink API owners are responsible for ...\n'
      '#\n'
      '# See https://www.chromium.org/blink#new-features for details.\n'
      'owner1@example.com\n'
      'owner2@example.com\n'
      'owner3@example.com\n'
      '\n')

  def setUp(self):
    for owners_file in OwnersFile.query():
      owners_file.key.delete()

  @mock.patch('requests.get')
  def test__normal(self, mock_get):
    """We can fetch and parse an OWNERS file.  And reuse cached value."""
    encoded = base64.b64encode(self.FILE_CONTENTS.encode())
    mock_get.return_value = testing_config.Blank(
        status_code=200,
        content=encoded)

    actual = approval_defs.fetch_owners('https://example.com')
    again = approval_defs.fetch_owners('https://example.com')

    # Only called once because second call will be an ndb hit.
    mock_get.assert_called_once_with('https://example.com')
    self.assertEqual(
        actual,
        ['owner1@example.com', 'owner2@example.com', 'owner3@example.com'])
    self.assertEqual(again, actual)

  @mock.patch('logging.error')
  @mock.patch('requests.get')
  def test__error__use_ndb(self, mock_get, mock_err):
    """If NDB is old and we can't read the OWNERS file, use old value anyway."""
    encoded = base64.b64encode(self.FILE_CONTENTS.encode())
    OwnersFile(
        url='https://example.com',
        raw_content=encoded,
        created_on=datetime.datetime(2022, 1, 1)).put()
    mock_get.return_value = testing_config.Blank(
        status_code=404)

    actual = approval_defs.fetch_owners('https://example.com')
    self.assertEqual(
        actual,
        ['owner1@example.com', 'owner2@example.com', 'owner3@example.com'])

  @mock.patch('logging.error')
  @mock.patch('requests.get')
  def test__error__use_empty_list(self, mock_get, mock_err):
    """If NDB is missing and we can't read the OWNERS file, use []."""
    # Don't create any test existing OwnersFile in NDB.
    mock_get.return_value = testing_config.Blank(
        status_code=404)

    actual = approval_defs.fetch_owners('https://example.com')
    self.assertEqual(actual, [])


class AutoAssignmentTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_id = 123456789
    self.gate_1 = Gate(
        feature_id=self.feature_id, stage_id=12300, state=0,
        gate_type=core_enums.GATE_PRIVACY_ORIGIN_TRIAL)
    self.gate_1.put()
    self.gate_2 = Gate(
        feature_id=self.feature_id, stage_id=12399, state=0,
        gate_type=core_enums.GATE_PRIVACY_SHIP,
        assignee_emails=['reviewer@example.com'])
    self.gate_3 = Gate(
        feature_id=self.feature_id, stage_id=12399, state=0,
        gate_type=core_enums.GATE_SECURITY_SHIP)

  def test__with_prior_assignment__match(self):
    """If there was a prior assignement, use it."""
    self.gate_2.put()
    approval_defs.auto_assign_reviewer(self.gate_1)
    self.assertEqual(['reviewer@example.com'], self.gate_1.assignee_emails)

  def test__with_prior_assignment__wrong_rule(self):
    """If there was a prior assignement, but a different rule, bail."""
    self.gate_1.gate_type = core_enums.GATE_API_SHIP
    self.gate_1.put()
    self.gate_2.gate_type = core_enums.GATE_API_ORIGIN_TRIAL  # Different rule
    self.gate_2.put()
    approval_defs.auto_assign_reviewer(self.gate_1)
    self.assertEqual([], self.gate_1.assignee_emails)

  def test__no_prior_assignment__no_gate_def(self):
    """If there is no prior assigned and members are not in NDB, bail."""
    # Note that gate_2 and gate_3 not saved to NDB.
    approval_defs.auto_assign_reviewer(self.gate_1)
    self.assertEqual([], self.gate_1.assignee_emails)

    self.gate_2.assignee_emails = []
    self.gate_2.put()  # Same team, but it has not assignement.
    self.assertEqual([], self.gate_1.assignee_emails)

    self.gate_3.put()  # Gate for a different team
    self.assertEqual([], self.gate_1.assignee_emails)



MOCK_APPROVALS_BY_ID = {
    1: approval_defs.GateInfo(
        'Intent to test',
        'You need permission to test',
        1, approval_defs.ONE_LGTM, ['approver@example.com'], 'API Owners'),
    2: approval_defs.GateInfo(
        'Intent to optimize',
        'You need permission to optimize',
        2, approval_defs.THREE_LGTM, 'https://example.com', 'API Owners'),
    3: approval_defs.GateInfo(
        'Intent to memorize',
        'You need permission to memorize',
        3, approval_defs.THREE_LGTM, approval_defs.IN_NDB, 'API Owners'),
}


class GetApproversTest(testing_config.CustomTestCase):

  def setUp(self):
    self.clearCache()

  def tearDown(self):
    self.clearCache()
    for gate_def in GateDef.query():
      gate_def.key.delete()

  def clearCache(self):
    for gate_type in approval_defs.APPROVAL_FIELDS_BY_ID:
      cache_key = '%s|%s' % (approval_defs.APPROVERS_CACHE_KEY, gate_type)
      rediscache.delete(cache_key)

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

  @mock.patch('internals.approval_defs.APPROVAL_FIELDS_BY_ID',
              MOCK_APPROVALS_BY_ID)
  @mock.patch('internals.approval_defs.fetch_owners')
  def test__ndb_new(self, mock_fetch_owner):
    """Some approvals will have approvers in NDB, but they are not found."""
    actual = approval_defs.get_approvers(3)
    mock_fetch_owner.assert_not_called()
    self.assertEqual(actual, [])
    updated_gate_defs = GateDef.query().fetch()
    self.assertEqual(1, len(updated_gate_defs))
    self.assertEqual(3, updated_gate_defs[0].gate_type)
    self.assertEqual([], updated_gate_defs[0].approvers)

  @mock.patch('internals.approval_defs.APPROVAL_FIELDS_BY_ID',
              MOCK_APPROVALS_BY_ID)
  @mock.patch('internals.approval_defs.fetch_owners')
  def test__ndb_existing(self, mock_fetch_owner):
    """Some approvals will have approvers in NDB, use it if found."""
    gate_def_3 = GateDef(gate_type=3, approvers=['a', 'b'])
    gate_def_3.put()
    actual = approval_defs.get_approvers(3)
    mock_fetch_owner.assert_not_called()
    self.assertEqual(actual, ['a', 'b'])
    existing_gate_defs = GateDef.query().fetch()
    self.assertEqual(1, len(existing_gate_defs))
    self.assertEqual(3, existing_gate_defs[0].gate_type)
    self.assertEqual(['a', 'b'], existing_gate_defs[0].approvers)


class IsValidGateTypeTest(testing_config.CustomTestCase):

  @mock.patch('internals.approval_defs.APPROVAL_FIELDS_BY_ID',
              MOCK_APPROVALS_BY_ID)
  def test(self):
    """We know if a gate_type is defined or not."""
    self.assertTrue(approval_defs.is_valid_gate_type(1))
    self.assertTrue(approval_defs.is_valid_gate_type(2))
    self.assertFalse(approval_defs.is_valid_gate_type(99))


class IsApprovedTest(testing_config.CustomTestCase):

  def setUp(self):
    feature_1_id = 123456
    self.appr_nr = Vote(
        feature_id=feature_1_id, gate_type=1,
        state=Vote.REVIEW_REQUESTED,
        set_on=datetime.datetime.now(),
        set_by='one@example.com')
    self.appr_na = Vote(
        feature_id=feature_1_id, gate_type=1,
        state=Vote.NA,
        set_on=datetime.datetime.now(),
        set_by='one@example.com')
    self.appr_no = Vote(
        feature_id=feature_1_id, gate_type=1,
        state=Vote.DENIED,
        set_on=datetime.datetime.now(),
        set_by='two@example.com')
    self.appr_yes = Vote(
        feature_id=feature_1_id, gate_type=1,
        state=Vote.APPROVED,
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
IR = Vote.INTERNAL_REVIEW
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

  def test_request_one_approved__no_request(self):
    """An API Owner gave LGTM1 Approval on an intent that was not detected."""
    self.assertEqual(('approved', 'review_requested'),
                     self.do_calc(AP))

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

  def test_request_internal_review(self):
    """Owner requested a review and a reviewer opts for internal review."""
    self.assertEqual(('internal_review', 'internal_review'),
                     self.do_calc(RR, IR))
    self.assertEqual(('internal_review', 'internal_review'),
                     self.do_calc(RR, RS, IR))
    self.assertEqual(('internal_review', 'internal_review'),
                     self.do_calc(RR, NW, IR))

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
    self.gate_1 = Gate(
        id=1001, feature_id=1, stage_id=1, gate_type=2, state=Gate.PREPARING)
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

    self.gate_2 = Gate(
        id=1002, feature_id=2, stage_id=2, gate_type=2, state=Vote.APPROVED)
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
    # Gate 1 should evaluate to approved after updating.
    votes = Vote.get_votes(gate_id=self.gate_1.key.integer_id())
    self.assertTrue(
        approval_defs.update_gate_approval_state(self.gate_1, votes))
    self.assertEqual(self.gate_1.state, Vote.APPROVED)

  def test_update_approval_state__no_change(self):
    """Gate's approval state does not change unless it needs to."""
    # Gate 2 is already marked as approved and should not change.
    votes = Vote.get_votes(gate_id=self.gate_2.key.integer_id())
    self.assertFalse(
        approval_defs.update_gate_approval_state(self.gate_2, votes))
    self.assertEqual(self.gate_2.state, Vote.APPROVED)

  def test_update_approval_state__unsupported_gate_type(self):
    """If we don't recognize the gate type, assume rule ONE_LGTM."""
    self.gate_1.gate_type = 999
    # Gate 1 should evaluate to approved after updating.
    votes = Vote.get_votes(gate_id=self.gate_1.key.integer_id())
    self.assertTrue(
        approval_defs.update_gate_approval_state(self.gate_1, votes))
    self.assertEqual(self.gate_1.state, Vote.APPROVED)
