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

import datetime
import testing_config  # Must be imported before the module under test.

import flask
from unittest import mock
import werkzeug.exceptions  # Flask HTTP stuff.
from google.cloud import ndb  # type: ignore

from api import reviews_api
from internals import approval_defs
from internals.core_enums import *
from internals import core_models
from internals.review_models import Gate, Vote

test_app = flask.Flask(__name__)

NOW = datetime.datetime.now()

ALL_SHIPPING_GATE_TYPES = [
    GATE_PRIVACY_SHIP, GATE_SECURITY_SHIP, GATE_ENTERPRISE_SHIP,
    GATE_DEBUGGABILITY_SHIP, GATE_TESTING_SHIP, GATE_API_SHIP]


class VotesAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = core_models.FeatureEntry(
        name='feature one', summary='sum', category=1,
        owner_emails=['owner1@example.com'])
    self.feature_1.put()
    self.feature_id = self.feature_1.key.integer_id()

    self.gate_1 = Gate(id=1, feature_id=self.feature_id, stage_id=1,
        gate_type=1, state=Vote.NA)
    self.gate_1.put()
    self.gate_1_id = self.gate_1.key.integer_id()

    self.gate_2 = Gate(id=2, feature_id=self.feature_id, stage_id=1,
        gate_type=2, state=Vote.NA)
    self.gate_2.put()
    self.gate_2_id = self.gate_2.key.integer_id()

    self.handler = reviews_api.VotesAPI()
    self.request_path = '/api/v0/features/%d/votes' % self.feature_id

    # These are not in the datastore unless a specific test calls put().
    self.vote_1_1 = Vote(
        feature_id=self.feature_id, gate_id=self.gate_1_id,
        gate_type=1,
        set_by='reviewer1@example.com', set_on=NOW,
        state=Vote.APPROVED)
    self.vote_2_1 = Vote(
        feature_id=self.feature_id, gate_id=self.gate_2_id,
        gate_type=1,
        set_by='reviewer2@example.com', set_on=NOW,
        state=Vote.NEEDS_WORK)

    self.vote_expected1 = {
        'feature_id': self.feature_id,
        'gate_id': self.gate_1_id,
        'gate_type': 1,
        'set_by': 'reviewer1@example.com',
        'set_on': str(NOW),
        'state': Vote.APPROVED,
        }
    self.vote_expected2 = {
        'feature_id': self.feature_id,
        'gate_id': self.gate_2_id,
        'gate_type': 1,
        'set_by': 'reviewer2@example.com',
        'set_on': str(NOW),
        'state': Vote.NEEDS_WORK,
        }

  def tearDown(self):
    self.feature_1.key.delete()
    kinds: list[ndb.Model] = [Gate, Vote]
    for kind in kinds:
      for entity in kind.query():
        entity.key.delete()

  def test_get__feature_empty(self):
    """We can get all votes for a given feature, even if there none."""
    testing_config.sign_out()
    with test_app.test_request_context(self.request_path):
      actual_response = self.handler.do_get(feature_id=self.feature_id)
    self.assertEqual({'votes': []}, actual_response)

  def test_get__feature_some(self):
    """We can get all votes for a given feature."""
    testing_config.sign_out()
    self.vote_1_1.put()
    self.vote_2_1.put()

    with test_app.test_request_context(self.request_path):
      actual_response = self.handler.do_get(feature_id=self.feature_id)

    self.assertEqual(
        {'votes': [self.vote_expected1, self.vote_expected2]},
        actual_response)

  def test_get__gate_empty(self):
    """We can get votes for given feature and field, even if there none."""
    testing_config.sign_out()
    with test_app.test_request_context(self.request_path + '/1'):
      actual_response = self.handler.do_get(
          feature_id=self.feature_id, gate_id=self.gate_1_id)
    self.assertEqual({'votes': []}, actual_response)

  def test_get__gate_some(self):
    """We can get votes for a given feature and gate_id."""
    testing_config.sign_out()
    self.vote_1_1.put()  # Found.
    self.vote_2_1.put()  # On a different gate.

    with test_app.test_request_context(self.request_path + '/1'):
      actual_response = self.handler.do_get(
          feature_id=self.feature_id, gate_id=self.gate_1_id)

    self.assertEqual({'votes': [self.vote_expected1]}, actual_response)

  def test_post__bad_feature_id(self):
    """Handler rejects requests that don't specify an existing feature."""
    params = {}
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.do_post(feature_id=999, gate_id=self.gate_1_id)

  def test_post__bad_gate_id(self):
    """Handler rejects requests that don't specify an existing gate."""
    testing_config.sign_in('admin@example.com', 1234567890)
    params = {'state': Vote.APPROVED}
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.do_post(feature_id=self.feature_id, gate_id=999)

  def test_post__bad_state(self):
    """Handler rejects requests that don't specify a state correctly."""
    params = {'state': 'not an int'}
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post(
            feature_id=self.feature_id, gate_id=self.gate_1_id)

    params = {'state': 999}
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post(
            feature_id=self.feature_id, gate_id=self.gate_1_id)

  @mock.patch('internals.approval_defs.get_approvers')
  def test_post__forbidden(self, mock_get_approvers):
    """Handler rejects requests from anon users and non-approvers."""
    mock_get_approvers.return_value = ['reviewer1@example.com']
    params = {'state': Vote.NEEDS_WORK}

    testing_config.sign_out()
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post(
            feature_id=self.feature_id, gate_id=self.gate_1_id)

    testing_config.sign_in('user7@example.com', 123567890)
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post(
            feature_id=self.feature_id, gate_id=self.gate_1_id)

    testing_config.sign_in('user@google.com', 123567890)
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post(
            feature_id=self.feature_id, gate_id=self.gate_1_id)

    testing_config.sign_in('owner1@example.com', 123567890)
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post(
            feature_id=self.feature_id, gate_id=self.gate_1_id)

    params = {'state': Vote.REVIEW_REQUESTED}
    testing_config.sign_in('user7@example.com', 123567890)
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post(
            feature_id=self.feature_id, gate_id=self.gate_1_id)

  @mock.patch('internals.approval_defs.get_approvers')
  def test_post__mismatched(self, mock_get_approvers):
    """Handler rejects requests with gate of a different feature."""
    mock_get_approvers.return_value = ['reviewer1@example.com']
    params = {'state': Vote.NEEDS_WORK}

    self.gate_1.feature_id = 999
    self.gate_1.put()  # This gate belongs to some other feature.

    testing_config.sign_in('reviewer1@example.com', 123567890)
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post(
            feature_id=self.feature_id, gate_id=self.gate_1_id)

  @mock.patch('internals.notifier_helpers.notify_subscribers_of_vote_changes')
  @mock.patch('internals.approval_defs.get_approvers')
  def test_post__add_new_vote(self, mock_get_approvers, mock_notifier):
    """Handler adds a vote when one did not exist before."""
    mock_get_approvers.return_value = ['reviewer1@example.com']
    testing_config.sign_in('reviewer1@example.com', 123567890)
    params = {'state': Vote.NEEDS_WORK}
    with test_app.test_request_context(self.request_path, json=params):
      actual = self.handler.do_post(
          feature_id=self.feature_id, gate_id=self.gate_1_id)

    self.assertEqual(actual, {'message': 'Done'})
    updated_votes = Vote.get_votes(feature_id=self.feature_id)
    self.assertEqual(1, len(updated_votes))
    vote = updated_votes[0]
    self.assertEqual(vote.feature_id, self.feature_id)
    self.assertEqual(vote.gate_id, 1)
    self.assertEqual(vote.set_by, 'reviewer1@example.com')
    self.assertEqual(vote.state, Vote.NEEDS_WORK)

    mock_notifier.assert_called_once_with(
        self.feature_1, self.gate_1, 'reviewer1@example.com',
        Vote.NEEDS_WORK, Vote.NO_RESPONSE)

  @mock.patch('internals.notifier_helpers.notify_subscribers_of_vote_changes')
  @mock.patch('internals.approval_defs.get_approvers')
  def test_post__update_vote(self, mock_get_approvers, mock_notifier):
    """Handler updates a vote when one already exists for that reviwer."""
    mock_get_approvers.return_value = ['reviewer1@example.com']
    testing_config.sign_in('reviewer1@example.com', 123567890)
    self.vote_1_1.put()  # Existing vote from reviewer1@.

    params = {'state': Vote.DENIED}
    with test_app.test_request_context(self.request_path, json=params):
      actual = self.handler.do_post(
          feature_id=self.feature_id, gate_id=self.gate_1_id)

    self.assertEqual(actual, {'message': 'Done'})
    updated_votes = Vote.get_votes(feature_id=self.feature_id)
    self.assertEqual(1, len(updated_votes))
    vote = updated_votes[0]
    self.assertEqual(vote.feature_id, self.feature_id)
    self.assertEqual(vote.gate_id, 1)
    self.assertEqual(vote.set_by, 'reviewer1@example.com')
    self.assertEqual(vote.state, Vote.DENIED)

    mock_notifier.assert_called_once_with(
        self.feature_1, self.gate_1, 'reviewer1@example.com',
        Vote.DENIED, Vote.APPROVED)

  @mock.patch('internals.notifier_helpers.notify_approvers_of_reviews')
  @mock.patch('internals.approval_defs.get_approvers')
  def test_post__request_review(self, mock_get_approvers, mock_notifier):
    """Handler allows a feature owner to rquest a review."""
    mock_get_approvers.return_value = ['reviewer1@example.com']
    testing_config.sign_in('owner1@example.com', 123567890)

    params = {'state': Vote.REVIEW_REQUESTED}
    with test_app.test_request_context(self.request_path, json=params):
      actual = self.handler.do_post(
          feature_id=self.feature_id, gate_id=self.gate_1_id)

    self.assertEqual(actual, {'message': 'Done'})
    updated_votes = Vote.get_votes(feature_id=self.feature_id)
    self.assertEqual(1, len(updated_votes))
    vote = updated_votes[0]
    self.assertEqual(vote.feature_id, self.feature_id)
    self.assertEqual(vote.gate_id, 1)
    self.assertEqual(vote.set_by, 'owner1@example.com')
    self.assertEqual(vote.state, Vote.REVIEW_REQUESTED)

    mock_notifier.assert_called_once_with(
        self.feature_1, self.gate_1, Vote.REVIEW_REQUESTED,
        'owner1@example.com')


class GatesAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = core_models.FeatureEntry(
        name='feature one', summary='sum', category=1,
        owner_emails=['owner1@example.com'])
    self.feature_1.put()
    self.feature_id = self.feature_1.key.integer_id()

    self.gate_1 = Gate(id=1, feature_id=self.feature_id, stage_id=1,
        gate_type=1, state=Vote.NA)
    self.gate_1.put()
    self.gate_1_id = self.gate_1.key.integer_id()

    self.handler = reviews_api.GatesAPI()
    self.request_path = '/api/v0/features/%d/gates' % self.feature_id

  def tearDown(self):
    self.feature_1.key.delete()
    kinds: list[ndb.Model] = [Gate, Vote]
    for kind in kinds:
      for entity in kind.query():
        entity.key.delete()

  @mock.patch('internals.approval_defs.get_approvers')
  def test_do_get__success(self, mock_get_approvers):
    """Handler retrieves all gates associated with a given feature."""
    mock_get_approvers.return_value = ['reviewer1@example.com']

    with test_app.test_request_context(self.request_path):
      actual = self.handler.do_get(feature_id=self.feature_id)

    expected = {
        "gates": [
            {
                "id": 1,
                "feature_id": self.feature_id,
                "stage_id": 1,
                "gate_type": 1,
                "team_name": "API Owners",
                "gate_name": "Intent to Prototype",
                "escalation_email": None,
                "state": 1,
                "requested_on": None,
                "responded_on": None,
                "assignee_emails": [],
                "next_action": None,
                "additional_review": False,
                'slo_initial_response': 5,
                'slo_initial_response_took': None,
                'slo_initial_response_remaining': None,
                'possible_assignee_emails': ['reviewer1@example.com'],
            },
        ],
        }

    self.assertEqual(actual, expected)

  @mock.patch('internals.approval_defs.get_approvers')
  def test_do_get__empty_gates(self, mock_get_approvers):
    """Handler cannnot find any gates."""
    mock_get_approvers.return_value = ['reviewer1@example.com']

    with test_app.test_request_context(self.request_path):
      actual = self.handler.do_get(feature_id=999)

    expected = {
        'gates': [],
    }
    self.assertEqual(actual, expected)


class XfnGatesAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = core_models.FeatureEntry(
        name='feature one', summary='sum', category=1,
        owner_emails=['owner1@example.com'])
    self.feature_1.put()
    self.feature_id = self.feature_1.key.integer_id()

    self.stage_1 = core_models.Stage(
        feature_id=self.feature_id, stage_type=STAGE_BLINK_SHIPPING)
    self.stage_1.put()
    self.stage_id = self.stage_1.key.integer_id()

    self.gate_1 = Gate(id=1, feature_id=self.feature_id, stage_id=self.stage_id,
        gate_type=GATE_API_SHIP, state=Vote.NA)
    self.gate_1.put()
    self.gate_1_id = self.gate_1.key.integer_id()

    self.handler = reviews_api.XfnGatesAPI()
    self.request_path = '/api/v0/features/%d/stages/%d/addXfnGates' % (
        self.feature_id, self.stage_id)

  def tearDown(self):
    self.feature_1.key.delete()
    kinds: list[ndb.Model] = [Gate, Vote]
    for kind in kinds:
      for entity in kind.query():
        entity.key.delete()

  def test_get(self):
    """We reject all GETs to this endpoint."""
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.MethodNotAllowed):
        self.handler.do_get()

  def test_do_post__not_found(self):
    """Handler rejects bad requests."""
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.do_post(
            feature_id=self.feature_id + 1, stage_id=self.stage_id)

    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.do_post(
            feature_id=self.feature_id, stage_id=self.stage_id + 1)

  def test_do_post__not_allowed(self):
    """Handler rejects users who lack permission."""
    testing_config.sign_out()
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post(
            feature_id=self.feature_id, stage_id=self.stage_id)

    testing_config.sign_in('other@example.com', 999)
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post(
            feature_id=self.feature_id, stage_id=self.stage_id)

  @mock.patch('api.reviews_api.XfnGatesAPI.create_xfn_gates')
  def test_do_post__editors_allowed(self, mock_create):
    """Handler accepts users who can edit the feature."""
    testing_config.sign_in('owner1@example.com', 123567890)
    mock_create.return_value = 111
    with test_app.test_request_context(self.request_path):
      actual = self.handler.do_post(
          feature_id=self.feature_id, stage_id=self.stage_id)

    mock_create.assert_called_once_with(self.feature_id, self.stage_id)
    self.assertEqual(actual, {'message': 'Created 111 gates'})

  @mock.patch('api.reviews_api.XfnGatesAPI.create_xfn_gates')
  def test_do_post__reviewers_allowed(self, mock_create):
    """Handler accepts users who can review any gate."""
    testing_config.sign_in(approval_defs.ENTERPRISE_APPROVERS[0], 123567890)
    mock_create.return_value = 222
    with test_app.test_request_context(self.request_path):
      actual = self.handler.do_post(
          feature_id=self.feature_id, stage_id=self.stage_id)

    mock_create.assert_called_once_with(self.feature_id, self.stage_id)
    self.assertEqual(actual, {'message': 'Created 222 gates'})

  def test_get_needed_gate_types(self):
    """We always assume that we are adding all gates for STAGE_BLINK_SHIPPING."""
    actual = self.handler.get_needed_gate_types()
    self.assertEqual(actual,ALL_SHIPPING_GATE_TYPES)

  def test_create_xfn_gates__normal(self):
    """We can create the missing gates from STAGE_BLINK_SHIPPING."""
    actual = self.handler.create_xfn_gates(self.feature_id, self.stage_id)

    self.assertEqual(actual, 5)
    actual_gates_dict = Gate.get_feature_gates(self.feature_id)
    self.assertCountEqual(
        actual_gates_dict.keys(), ALL_SHIPPING_GATE_TYPES)
