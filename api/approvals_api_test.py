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

from __future__ import division
from __future__ import print_function

import datetime
import testing_config  # Must be imported before the module under test.

import flask
import mock
import werkzeug.exceptions  # Flask HTTP stuff.

from api import register
from api import approvals_api
from internals import models


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
        'set_by': u'owner1@example.com',
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
    with register.app.test_request_context(self.request_path):
      actual_response = self.handler.do_get(self.feature_id)
    self.assertEqual({"approvals": []}, actual_response)

  def test_get__all_some(self):
    """We can get all approvals for a given feature."""
    testing_config.sign_out()
    self.appr_1_1.put()
    self.appr_1_2.put()

    with register.app.test_request_context(self.request_path):
      actual_response = self.handler.do_get(self.feature_id)

    self.assertEqual(
        {"approvals": [self.expected1, self.expected2]},
        actual_response)

  def test_get__field_empty(self):
    """We can get approvals for given feature and field, even if there none."""
    testing_config.sign_out()
    with register.app.test_request_context(self.request_path + '/1'):
      actual_response = self.handler.do_get(self.feature_id, field_id=1)
    self.assertEqual({"approvals": []}, actual_response)

  def test_get__field_some(self):
    """We can get approvals for a given feature and field_id."""
    testing_config.sign_out()
    self.appr_1_1.put()
    self.appr_1_2.put()

    with register.app.test_request_context(self.request_path + '/1'):
      actual_response = self.handler.do_get(self.feature_id, field_id=1)

    self.assertEqual(
        {"approvals": [self.expected1]},
        actual_response)

  def test_post__bad_feature_id(self):
    """Handler rejects requests that don't specify a feature ID correctly."""
    params = {}
    with register.app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post()

    params = {'featureId': 'not an int'}
    with register.app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post()

  def test_post__bad_field_id(self):
    """Handler rejects requests that don't specify a field ID correctly."""
    params = {'featureId': self.feature_id}
    with register.app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post()

    params = {'featureId': self.feature_id, 'fieldId': 'not an int'}
    with register.app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post()

    params = {'featureId': self.feature_id, 'fieldId': 999}
    with register.app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post()

  def test_post__bad_state(self):
    """Handler rejects requests that don't specify a state correctly."""
    params = {'featureId': self.feature_id, 'fieldId': 1}
    with register.app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post()

    params = {'featureId': self.feature_id, 'fieldId': 1,
              'state': 'not an int'}
    with register.app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post()

    params = {'featureId': self.feature_id, 'fieldId': 1,
              'state': 999}
    with register.app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post()

  def test_post__feature_not_found(self):
    """Handler rejects requests that don't match an existing feature."""
    params = {'featureId': 12345, 'fieldId': 1,
              'state': models.Approval.NEED_INFO }
    with register.app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.do_post()

  @mock.patch('internals.approval_defs.get_approvers')
  def test_post__forbidden(self, mock_get_approvers):
    """Handler rejects requests from anon users and non-approvers."""
    mock_get_approvers.return_value = ['owner1@example.com']
    params = {'featureId': self.feature_id, 'fieldId': 1,
              'state': models.Approval.NEED_INFO}

    testing_config.sign_out()
    with register.app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post()

    testing_config.sign_in('user7@example.com', 123567890)
    with register.app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post()

    testing_config.sign_in('user@google.com', 123567890)
    with register.app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post()

  @mock.patch('internals.approval_defs.get_approvers')
  def test_post__add_or_update(self, mock_get_approvers):
    """Handler adds approval when one did not exist before."""
    mock_get_approvers.return_value = ['owner1@example.com']
    testing_config.sign_in('owner1@example.com', 123567890)
    params = {'featureId': self.feature_id, 'fieldId': 1,
              'state': models.Approval.NEED_INFO}
    with register.app.test_request_context(self.request_path, json=params):
      actual = self.handler.do_post()

    self.assertEqual(actual, {'message': 'Done'})
    updated_approvals = models.Approval.get_approvals(self.feature_id)
    self.assertEqual(1, len(updated_approvals))
    appr = updated_approvals[0]
    self.assertEqual(appr.feature_id, self.feature_id)
    self.assertEqual(appr.field_id, 1)
    self.assertEqual(appr.set_by, 'owner1@example.com')
    self.assertEqual(appr.state, models.Approval.NEED_INFO)