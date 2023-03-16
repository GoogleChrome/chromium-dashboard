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

import datetime
import testing_config  # Must be imported before the module under test.

import flask
from unittest import mock
import werkzeug.exceptions  # Flask HTTP stuff.
from google.cloud import ndb  # type: ignore

from api import approvals_api
from internals import core_enums
from internals import core_models
from internals.legacy_models import Approval, ApprovalConfig
from internals.review_models import Gate, Vote

test_app = flask.Flask(__name__)

NOW = datetime.datetime.now()


class ApprovalsAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = core_models.FeatureEntry(
        name='feature one', summary='sum', category=1)
    self.feature_1.put()
    self.feature_id = self.feature_1.key.integer_id()

    self.gate_1 = Gate(id=1, feature_id=self.feature_id, stage_id=1,
        gate_type=1, state=Vote.NA)
    self.gate_1.put()
    self.gate_2 = Gate(id=2, feature_id=self.feature_id, stage_id=2,
        gate_type=2, state=Vote.NA)
    self.gate_2.put()

    self.handler = approvals_api.ApprovalsAPI()
    self.request_path = '/api/v0/features/%d/approvals' % self.feature_id

    # These are not in the datastore unless a specific test calls put().
    self.appr_1_1 = Approval(
        feature_id=self.feature_id, field_id=1,
        set_by='owner1@example.com', set_on=NOW,
        state=Approval.APPROVED)
    self.appr_1_2 = Approval(
        feature_id=self.feature_id, field_id=2,
        set_by='owner2@example.com', set_on=NOW,
        state=Approval.NEEDS_WORK)

    # Vote entity equivalents.
    self.vote_1_1 = Vote(feature_id=self.feature_id, gate_id=10,
        gate_type=1, set_on=NOW,
        set_by='owner1@example.com', state=Vote.APPROVED)
    self.vote_1_2 = Vote(feature_id=self.feature_id, gate_id=11, gate_type=2,
        set_by='owner2@example.com', set_on=NOW, state=Vote.NEEDS_WORK)

    self.expected1 = {
        'feature_id': self.feature_id,
        'field_id': 1,
        'set_by': 'owner1@example.com',
        'set_on': str(NOW),
        'state': Approval.APPROVED,
        }
    self.expected2 = {
        'feature_id': self.feature_id,
        'field_id': 2,
        'set_by': 'owner2@example.com',
        'set_on': str(NOW),
        'state': Approval.NEEDS_WORK,
        }

    self.vote_expected1 = {
        'feature_id': self.feature_id,
        'gate_id': 10,
        'gate_type': 1,
        'set_by': 'owner1@example.com',
        'set_on': str(NOW),
        'state': Vote.APPROVED,
        }
    self.vote_expected2 = {
        'feature_id': self.feature_id,
        'gate_id': 11,
        'gate_type': 2,
        'set_by': 'owner2@example.com',
        'set_on': str(NOW),
        'state': Vote.NEEDS_WORK,
        }

  def tearDown(self):
    self.feature_1.key.delete()
    kinds: list[ndb.Model] = [Approval, Gate, Vote]
    for kind in kinds:
      for entity in kind.query():
        entity.key.delete()

  def test_get__all_empty(self):
    """We can get all approvals for a given feature, even if there none."""
    testing_config.sign_out()
    with test_app.test_request_context(self.request_path):
      actual_response = self.handler.do_get(feature_id=self.feature_id)
    self.assertEqual({"approvals": []}, actual_response)

  def test_get__all_some(self):
    """We can get all approvals for a given feature."""
    testing_config.sign_out()
    self.vote_1_1.put()
    self.vote_1_2.put()

    with test_app.test_request_context(self.request_path):
      actual_response = self.handler.do_get(feature_id=self.feature_id)

    self.assertEqual(
        {"approvals": [self.vote_expected1, self.vote_expected2]},
        actual_response)

  def test_get__field_empty(self):
    """We can get approvals for given feature and field, even if there none."""
    testing_config.sign_out()
    with test_app.test_request_context(self.request_path + '/1'):
      actual_response = self.handler.do_get(
          feature_id=self.feature_id, gate_type=1)
    self.assertEqual({"approvals": []}, actual_response)

  def test_get__field_some(self):
    """We can get approvals for a given feature and gate_type."""
    testing_config.sign_out()
    self.vote_1_1.put()
    self.vote_1_2.put()

    with test_app.test_request_context(self.request_path + '/1'):
      actual_response = self.handler.do_get(
          feature_id=self.feature_id, gate_type=1)

    self.assertEqual({"approvals": [self.vote_expected1]}, actual_response)

  def test_post__bad_feature_id(self):
    """Handler rejects requests that don't specify a feature ID correctly."""
    params = {}
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post()

    params = {'featureId': 'not an int'}
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post()

  def test_post__bad_field_id(self):
    """Handler rejects requests that don't specify a field ID correctly."""
    params = {'featureId': self.feature_id}
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post()

    params = {'featureId': self.feature_id, 'fieldId': 'not an int'}
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post()

    params = {'featureId': self.feature_id, 'fieldId': 999}
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post()

  def test_post__bad_state(self):
    """Handler rejects requests that don't specify a state correctly."""
    params = {'featureId': self.feature_id, 'gateType': 1}
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post()

    params = {'featureId': self.feature_id, 'gateType': 1,
              'state': 'not an int'}
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post()

    params = {'featureId': self.feature_id, 'gateType': 1,
              'state': 999}
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post()

  def test_post__feature_not_found(self):
    """Handler rejects requests that don't match an existing feature."""
    params = {'featureId': 12345, 'gateType': 1,
              'state': Approval.NEEDS_WORK }
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.do_post()

  @mock.patch('internals.approval_defs.get_approvers')
  def test_post__forbidden(self, mock_get_approvers):
    """Handler rejects requests from anon users and non-approvers."""
    mock_get_approvers.return_value = ['owner1@example.com']
    params = {'featureId': self.feature_id, 'gateType': 1,
              'state': Approval.NEEDS_WORK}

    testing_config.sign_out()
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post()

    testing_config.sign_in('user7@example.com', 123567890)
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post()

    testing_config.sign_in('user@google.com', 123567890)
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post()

  @mock.patch('internals.approval_defs.get_approvers')
  def test_post__add_or_update(self, mock_get_approvers):
    """Handler adds approval when one did not exist before."""
    mock_get_approvers.return_value = ['owner1@example.com']
    testing_config.sign_in('owner1@example.com', 123567890)
    params = {'featureId': self.feature_id, 'gateType': 1,
              'state': Vote.NEEDS_WORK}
    with test_app.test_request_context(self.request_path, json=params):
      actual = self.handler.do_post(feature_id=self.feature_id)

    self.assertEqual(actual, {'message': 'Done'})
    updated_approvals = Vote.get_votes(feature_id=self.feature_id)
    self.assertEqual(1, len(updated_approvals))
    vote = updated_approvals[0]
    self.assertEqual(vote.feature_id, self.feature_id)
    self.assertEqual(vote.gate_id, 1)
    self.assertEqual(vote.set_by, 'owner1@example.com')
    self.assertEqual(vote.state, Vote.NEEDS_WORK)


class ApprovalConfigsAPITest(testing_config.CustomTestCase):

  POSSIBLE_OWNERS = {
      core_enums.GATE_API_PROTOTYPE: ['owner@example.com'],
      core_enums.GATE_API_ORIGIN_TRIAL: ['owner@example.com'],
      core_enums.GATE_API_EXTEND_ORIGIN_TRIAL: ['owner@example.com'],
      core_enums.GATE_API_SHIP: ['owner@example.com'],
      core_enums.GATE_PRIVACY_ORIGIN_TRIAL: ['owner@example.com'],
      core_enums.GATE_PRIVACY_SHIP: ['owner@example.com'],
      core_enums.GATE_SECURITY_ORIGIN_TRIAL: ['owner@example.com'],
      core_enums.GATE_SECURITY_SHIP: ['owner@example.com'],
      core_enums.GATE_ENTERPRISE_SHIP: ['owner@example.com'],
      core_enums.GATE_DEBUGGABILITY_ORIGIN_TRIAL: ['owner@example.com'],
      core_enums.GATE_DEBUGGABILITY_SHIP: ['owner@example.com'],
      core_enums.GATE_TESTING_SHIP: ['owner@example.com'],
      }

  def setUp(self):
    self.feature_1 = core_models.FeatureEntry(
        name='feature one', summary='sum', category=1)
    self.feature_1.put()
    self.feature_1_id = self.feature_1.key.integer_id()
    self.config_1 = ApprovalConfig(
        feature_id=self.feature_1_id, field_id=1,
        owners=['one_a@example.com', 'one_b@example.com'])
    self.config_1.put()

    self.feature_2 = core_models.FeatureEntry(
        name='feature two', summary='sum', category=1)
    self.feature_2.put()
    self.feature_2_id = self.feature_2.key.integer_id()
    self.config_2 = ApprovalConfig(
        feature_id=self.feature_2_id, field_id=2,
        owners=['two_a@example.com', 'two_b@example.com'])
    self.config_2.put()

    self.feature_3 = core_models.FeatureEntry(
        name='feature three', summary='sum', category=1)
    self.feature_3.put()
    self.feature_3_id = self.feature_3.key.integer_id()
    # Feature 3 has no configs

    self.handler = approvals_api.ApprovalConfigsAPI()
    self.request_path = '/api/v0/features/%d/configs' % self.feature_1_id

  def tearDown(self):
    self.feature_1.key.delete()
    self.feature_2.key.delete()
    self.feature_3.key.delete()
    for config in ApprovalConfig.query():
      config.key.delete()

  @mock.patch('internals.approval_defs.get_approvers')
  def test_do_get__found(self, mock_get_approvers):
    """Anon or any user can get some configs."""
    mock_get_approvers.return_value = ['owner@example.com']
    testing_config.sign_in('other@example.com', 123567890)
    with test_app.test_request_context(self.request_path):
      actual = self.handler.do_get(feature_id=self.feature_1_id)
    self.assertEqual(
        {'configs': [{
            'feature_id': self.feature_1_id,
            'field_id': 1,
            'owners': ['one_a@example.com', 'one_b@example.com'],
            'additional_review': False,
            'next_action': None,
            }],
         'possible_owners': self.POSSIBLE_OWNERS,
        },
        actual)

    testing_config.sign_out()
    with test_app.test_request_context(self.request_path):
      actual = self.handler.do_get(feature_id=self.feature_2_id)
    self.assertEqual(
        {'configs': [{
            'feature_id': self.feature_2_id,
            'field_id': 2,
            'owners': ['two_a@example.com', 'two_b@example.com'],
            'additional_review': False,
            'next_action': None,
            }],
         'possible_owners': self.POSSIBLE_OWNERS,
        },
        actual)

  @mock.patch('internals.approval_defs.get_approvers')
  def test_do_get__no_configs(self, mock_get_approvers):
    """If there are no configs, we return an empty list."""
    mock_get_approvers.return_value = ['owner@example.com']
    with test_app.test_request_context(self.request_path):
      actual = self.handler.do_get(feature_id=self.feature_3_id)

    self.assertEqual(
        {'configs': [],
         'possible_owners': self.POSSIBLE_OWNERS,
        },
        actual)

  @mock.patch('internals.approval_defs.get_approvers')
  def test_do_post__add_a_config(self, mock_get_approvers):
    """If there are already existing configs, we can add new one."""
    mock_get_approvers.return_value = ['owner1@example.com']
    testing_config.sign_in('owner1@example.com', 123567890)

    params = {'fieldId': 3,
              'owners': ' one@example.com, two@example.com, ',
              'nextAction': '2021-11-30',
              'additionalReview': False}
    with test_app.test_request_context(self.request_path, json=params):
      actual = self.handler.do_post(feature_id=self.feature_1_id)

    self.assertEqual({'message': 'Done'}, actual)
    revised_configs = ApprovalConfig.query(
        ApprovalConfig.feature_id == self.feature_1_id).order(
            ApprovalConfig.field_id).fetch(None)
    self.assertEqual(2, len(revised_configs))
    revised_config_3 = revised_configs[1]
    self.assertEqual(3, revised_config_3.field_id)
    self.assertEqual(['one@example.com', 'two@example.com'],
                     revised_config_3.owners)

  @mock.patch('internals.approval_defs.get_approvers')
  def test_do_post__update(self, mock_get_approvers):
    """We can update an existing config."""
    mock_get_approvers.return_value = ['owner1@example.com']
    testing_config.sign_in('owner1@example.com', 123567890)

    params = {'fieldId': 1,
              'owners': 'one_a@example.com, one_b@example.com',
              'nextAction': '2021-11-30',
              'additionalReview': False}
    with test_app.test_request_context(self.request_path, json=params):
      actual = self.handler.do_post(feature_id=self.feature_1_id)

    self.assertEqual({'message': 'Done'}, actual)
    revised_config = ApprovalConfig.query(
        ApprovalConfig.feature_id == self.feature_1_id).fetch(None)[0]
    self.assertEqual(self.feature_1_id, revised_config.feature_id)
    self.assertEqual(1, revised_config.field_id)
    self.assertEqual(datetime.date.fromisoformat('2021-11-30'),
                     revised_config.next_action)
    self.assertEqual(['one_a@example.com', 'one_b@example.com'],
                     revised_config.owners)
    self.assertEqual(False, revised_config.additional_review)

  @mock.patch('internals.approval_defs.get_approvers')
  def test_do_post__clear(self, mock_get_approvers):
    """We can update an existing config to clear values."""
    mock_get_approvers.return_value = ['owner1@example.com']
    testing_config.sign_in('owner1@example.com', 123567890)

    params = {'fieldId': 1,
              'owners': '',
              'nextAction': '',
              'additionalReview': False}
    with test_app.test_request_context(self.request_path, json=params):
      actual = self.handler.do_post(feature_id=self.feature_1_id)

    self.assertEqual({'message': 'Done'}, actual)
    revised_config = ApprovalConfig.query(
        ApprovalConfig.feature_id == self.feature_1_id).fetch(None)[0]
    self.assertEqual(self.feature_1_id, revised_config.feature_id)
    self.assertEqual(1, revised_config.field_id)
    self.assertEqual(None, revised_config.next_action)
    self.assertEqual([], revised_config.owners)
    self.assertEqual(False, revised_config.additional_review)

  @mock.patch('internals.approval_defs.get_approvers')
  def test_do_post__no_configs(self, mock_get_approvers):
    """If there are no existing configs, we create one."""
    mock_get_approvers.return_value = ['owner1@example.com']
    testing_config.sign_in('owner1@example.com', 123567890)

    params = {'fieldId': 3,
              'owners': '',
              'nextAction': '2021-11-30',
              'additionalReview': False}
    with test_app.test_request_context(self.request_path, json=params):
      actual = self.handler.do_post(feature_id=self.feature_3_id)

    self.assertEqual({'message': 'Done'}, actual)
    new_config = ApprovalConfig.query(
        ApprovalConfig.feature_id == self.feature_3_id).fetch(None)[0]
    self.assertEqual(self.feature_3_id, new_config.feature_id)
    self.assertEqual(3, new_config.field_id)
    self.assertEqual(datetime.date.fromisoformat('2021-11-30'),
                     new_config.next_action)
    self.assertEqual([], new_config.owners)
    self.assertEqual(False, new_config.additional_review)

  @mock.patch('internals.approval_defs.get_approvers')
  def test_do_post__bad_date(self, mock_get_approvers):
    """We reject bad date formats and values."""
    mock_get_approvers.return_value = ['owner1@example.com']
    testing_config.sign_in('owner1@example.com', 123567890)

    params = {'fieldId': 3,
              'owners': '',
              'nextAction': '11/30/21',
              'additionalReview': False}
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post(feature_id=self.feature_3_id)

    params = {'fieldId': 3,
              'owners': '',
              'nextAction': '2021-11-35',
              'additionalReview': False}
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post(feature_id=self.feature_3_id)
