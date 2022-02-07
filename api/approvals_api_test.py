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

from api import approvals_api
from internals import models

test_app = flask.Flask(__name__)

NOW = datetime.datetime.now()


class ApprovalsAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = models.Feature(
        name='feature one', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1)
    self.feature_1.put()
    self.feature_id = self.feature_1.key.integer_id()
    self.handler = approvals_api.ApprovalsAPI()
    self.request_path = '/api/v0/features/%d/approvals' % self.feature_id

    # These are not in the datastore unless a specific test calls put().
    self.appr_1_1 = models.Approval(
        feature_id=self.feature_id, field_id=1,
        set_by='owner1@example.com', set_on=NOW,
        state=models.Approval.APPROVED)
    self.appr_1_2 = models.Approval(
        feature_id=self.feature_id, field_id=2,
        set_by='owner2@example.com', set_on=NOW,
        state=models.Approval.NEED_INFO)

    self.expected1 = {
        'feature_id': self.feature_id,
        'field_id': 1,
        'set_by': 'owner1@example.com',
        'set_on': str(NOW),
        'state': models.Approval.APPROVED,
        }
    self.expected2 = {
        'feature_id': self.feature_id,
        'field_id': 2,
        'set_by': 'owner2@example.com',
        'set_on': str(NOW),
        'state': models.Approval.NEED_INFO,
        }

  def tearDown(self):
    self.feature_1.key.delete()
    for appr in models.Approval.query():
      appr.key.delete()

  def test_get__all_empty(self):
    """We can get all approvals for a given feature, even if there none."""
    testing_config.sign_out()
    with test_app.test_request_context(self.request_path):
      actual_response = self.handler.do_get(self.feature_id)
    self.assertEqual({"approvals": []}, actual_response)

  def test_get__all_some(self):
    """We can get all approvals for a given feature."""
    testing_config.sign_out()
    self.appr_1_1.put()
    self.appr_1_2.put()

    with test_app.test_request_context(self.request_path):
      actual_response = self.handler.do_get(self.feature_id)

    self.assertEqual(
        {"approvals": [self.expected1, self.expected2]},
        actual_response)

  def test_get__field_empty(self):
    """We can get approvals for given feature and field, even if there none."""
    testing_config.sign_out()
    with test_app.test_request_context(self.request_path + '/1'):
      actual_response = self.handler.do_get(self.feature_id, field_id=1)
    self.assertEqual({"approvals": []}, actual_response)

  def test_get__field_some(self):
    """We can get approvals for a given feature and field_id."""
    testing_config.sign_out()
    self.appr_1_1.put()
    self.appr_1_2.put()

    with test_app.test_request_context(self.request_path + '/1'):
      actual_response = self.handler.do_get(self.feature_id, field_id=1)

    self.assertEqual(
        {"approvals": [self.expected1]},
        actual_response)

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
    params = {'featureId': self.feature_id, 'fieldId': 1}
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post()

    params = {'featureId': self.feature_id, 'fieldId': 1,
              'state': 'not an int'}
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post()

    params = {'featureId': self.feature_id, 'fieldId': 1,
              'state': 999}
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post()

  def test_post__feature_not_found(self):
    """Handler rejects requests that don't match an existing feature."""
    params = {'featureId': 12345, 'fieldId': 1,
              'state': models.Approval.NEED_INFO }
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.do_post()

  @mock.patch('internals.approval_defs.get_approvers')
  def test_post__forbidden(self, mock_get_approvers):
    """Handler rejects requests from anon users and non-approvers."""
    mock_get_approvers.return_value = ['owner1@example.com']
    params = {'featureId': self.feature_id, 'fieldId': 1,
              'state': models.Approval.NEED_INFO}

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
    params = {'featureId': self.feature_id, 'fieldId': 1,
              'state': models.Approval.NEED_INFO}
    with test_app.test_request_context(self.request_path, json=params):
      actual = self.handler.do_post()

    self.assertEqual(actual, {'message': 'Done'})
    updated_approvals = models.Approval.get_approvals(
        feature_id=self.feature_id)
    self.assertEqual(1, len(updated_approvals))
    appr = updated_approvals[0]
    self.assertEqual(appr.feature_id, self.feature_id)
    self.assertEqual(appr.field_id, 1)
    self.assertEqual(appr.set_by, 'owner1@example.com')
    self.assertEqual(appr.state, models.Approval.NEED_INFO)


class ApprovalConfigsAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = models.Feature(
        name='feature one', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1)
    self.feature_1.put()
    self.feature_1_id = self.feature_1.key.integer_id()
    self.config_1 = models.ApprovalConfig(
        feature_id=self.feature_1_id, field_id=1,
        owners=['one_a@example.com', 'one_b@example.com'])
    self.config_1.put()

    self.feature_2 = models.Feature(
        name='feature two', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1)
    self.feature_2.put()
    self.feature_2_id = self.feature_2.key.integer_id()
    self.config_2 = models.ApprovalConfig(
        feature_id=self.feature_2_id, field_id=2,
        owners=['two_a@example.com', 'two_b@example.com'])
    self.config_2.put()

    self.feature_3 = models.Feature(
        name='feature three', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1)
    self.feature_3.put()
    self.feature_3_id = self.feature_3.key.integer_id()
    # Feature 3 has no configs

    self.handler = approvals_api.ApprovalConfigsAPI()
    self.request_path = '/api/v0/features/%d/configs' % self.feature_1_id

  def tearDown(self):
    self.feature_1.key.delete()
    self.feature_2.key.delete()
    self.feature_3.key.delete()
    for config in models.ApprovalConfig.query():
      config.key.delete()

  @mock.patch('internals.approval_defs.get_approvers')
  def test_do_get__found(self, mock_get_approvers):
    """Anon or any user can get some configs."""
    mock_get_approvers.return_value = ['owner@example.com']
    testing_config.sign_in('other@example.com', 123567890)
    with test_app.test_request_context(self.request_path):
      actual = self.handler.do_get(self.feature_1_id)
    self.assertEqual(
        {'configs': [{
            'feature_id': self.feature_1_id,
            'field_id': 1,
            'owners': ['one_a@example.com', 'one_b@example.com'],
            'additional_review': False,
            'next_action': None,
            }],
         'possible_owners': {
             1: ['owner@example.com'],
             2: ['owner@example.com'],
             3: ['owner@example.com'],
             4: ['owner@example.com'],
         },
        },
        actual)

    testing_config.sign_out()
    with test_app.test_request_context(self.request_path):
      actual = self.handler.do_get(self.feature_2_id)
    self.assertEqual(
        {'configs': [{
            'feature_id': self.feature_2_id,
            'field_id': 2,
            'owners': ['two_a@example.com', 'two_b@example.com'],
            'additional_review': False,
            'next_action': None,
            }],
         'possible_owners': {
             1: ['owner@example.com'],
             2: ['owner@example.com'],
             3: ['owner@example.com'],
             4: ['owner@example.com'],
         },
        },
        actual)

  @mock.patch('internals.approval_defs.get_approvers')
  def test_do_get__no_configs(self, mock_get_approvers):
    """If there are no configs, we return an empty list."""
    mock_get_approvers.return_value = ['owner@example.com']
    with test_app.test_request_context(self.request_path):
      actual = self.handler.do_get(self.feature_3_id)

    self.assertEqual(
        {'configs': [],
         'possible_owners': {
             1: ['owner@example.com'],
             2: ['owner@example.com'],
             3: ['owner@example.com'],
             4: ['owner@example.com'],
         },
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
      actual = self.handler.do_post(self.feature_1_id)

    self.assertEqual({'message': 'Done'}, actual)
    revised_configs = models.ApprovalConfig.query(
        models.ApprovalConfig.feature_id == self.feature_1_id).order(
            models.ApprovalConfig.field_id).fetch(None)
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
      actual = self.handler.do_post(self.feature_1_id)

    self.assertEqual({'message': 'Done'}, actual)
    revised_config = models.ApprovalConfig.query(
        models.ApprovalConfig.feature_id == self.feature_1_id).fetch(None)[0]
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
      actual = self.handler.do_post(self.feature_1_id)

    self.assertEqual({'message': 'Done'}, actual)
    revised_config = models.ApprovalConfig.query(
        models.ApprovalConfig.feature_id == self.feature_1_id).fetch(None)[0]
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
      actual = self.handler.do_post(self.feature_3_id)

    self.assertEqual({'message': 'Done'}, actual)
    new_config = models.ApprovalConfig.query(
        models.ApprovalConfig.feature_id == self.feature_3_id).fetch(None)[0]
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
        self.handler.do_post(self.feature_3_id)

    params = {'fieldId': 3,
              'owners': '',
              'nextAction': '2021-11-35',
              'additionalReview': False}
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post(self.feature_3_id)
