# -*- coding: utf-8 -*-
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

import datetime
import testing_config  # Must be imported before the module under test.

import flask
from unittest import mock
import werkzeug.exceptions  # Flask HTTP stuff.

from api import comments_api
from internals import core_models
from internals import review_models

test_app = flask.Flask(__name__)

NOW = datetime.datetime.now()


class CommentsAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = core_models.Feature(
        name='feature one', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1)
    self.feature_1.put()
    self.feature_id = self.feature_1.key.integer_id()
    self.field_id = 1
    self.handler = comments_api.CommentsAPI()
    self.request_path = ('/api/v0/features/%d/approvals/%d/comments' %
                         (self.feature_id, self.field_id))

    self.appr_1_1 = review_models.Approval(
        feature_id=self.feature_id, field_id=1,
        set_by='owner1@example.com', set_on=NOW,
        state=review_models.Approval.APPROVED)
    self.appr_1_1.put()

    # This is not in the datastore unless a specific test calls put().
    self.cmnt_1_1 = review_models.Comment(
        feature_id=self.feature_id, field_id=1,
        author='owner1@example.com', created=NOW,
        content='Good job',
        new_approval_state=review_models.Approval.APPROVED)

    self.expected_1 = {
        'feature_id': self.feature_id,
        'field_id': self.field_id,
        'author': 'owner1@example.com',
        'deleted_by': None,
        'content': 'Good job',
        'old_approval_state': None,
        'new_approval_state': review_models.Approval.APPROVED,
        }

  def tearDown(self):
    self.feature_1.key.delete()
    for appr in review_models.Approval.query():
      appr.key.delete()
    for cmnt in review_models.Comment.query():
      cmnt.key.delete()

  def test_get__empty(self):
    """We can get comments for a given approval, even if there none."""
    testing_config.sign_out()
    with test_app.test_request_context(self.request_path):
      actual_response = self.handler.do_get(self.feature_id, self.field_id)
    self.assertEqual({'comments': []}, actual_response)

  def test_get__all_some(self):
    """We can get all comments for a given approval."""
    testing_config.sign_out()
    self.cmnt_1_1.put()

    with test_app.test_request_context(self.request_path):
      actual_response = self.handler.do_get(self.feature_id, self.field_id)

    actual_comment = actual_response['comments'][0]
    del actual_comment['created']
    self.assertEqual(
        self.expected_1,
        actual_comment)

  def test_post__bad_state(self):
    """Handler rejects requests that don't specify a state correctly."""
    params = {'state': 'not an int'}
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post(self.feature_id, self.field_id)

    params = {'state': 999}
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post(self.feature_id, self.field_id)

  def test_post__feature_not_found(self):
    """Handler rejects requests that don't match an existing feature."""
    bad_path = '/api/v0/features/12345/approvals/1/comments'
    params = {'state': review_models.Approval.NEED_INFO }
    with test_app.test_request_context(bad_path, json=params):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.do_post(12345, self.field_id)

  @mock.patch('internals.approval_defs.get_approvers')
  def test_post__forbidden(self, mock_get_approvers):
    """Handler rejects requests from anon users and non-approvers."""
    mock_get_approvers.return_value = ['owner1@example.com']
    params = {'state': review_models.Approval.NEED_INFO}

    testing_config.sign_out()
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post(self.feature_id, self.field_id)

    testing_config.sign_in('user7@example.com', 123567890)
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post(self.feature_id, self.field_id)

    testing_config.sign_in('user@google.com', 123567890)
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post(self.feature_id, self.field_id)

  @mock.patch('internals.approval_defs.get_approvers')
  def test_post__update(self, mock_get_approvers):
    """Handler adds comment and updates approval value."""
    mock_get_approvers.return_value = ['owner1@example.com']
    testing_config.sign_in('owner1@example.com', 123567890)
    params = {'state': review_models.Approval.NEED_INFO}
    with test_app.test_request_context(self.request_path, json=params):
      actual = self.handler.do_post(self.feature_id, self.field_id)

    self.assertEqual(actual, {'message': 'Done'})
    updated_approvals = review_models.Approval.get_approvals(
        feature_id=self.feature_id)
    self.assertEqual(1, len(updated_approvals))
    appr = updated_approvals[0]
    self.assertEqual(appr.feature_id, self.feature_id)
    self.assertEqual(appr.field_id, 1)
    self.assertEqual(appr.set_by, 'owner1@example.com')
    self.assertEqual(appr.state, review_models.Approval.NEED_INFO)
    updated_comments = review_models.Comment.get_comments(
        self.feature_id, self.field_id)
    cmnt = updated_comments[0]
    self.assertEqual(None, cmnt.content)
    self.assertEqual(review_models.Approval.APPROVED, cmnt.old_approval_state)
    self.assertEqual(review_models.Approval.NEED_INFO, cmnt.new_approval_state)

  @mock.patch('internals.approval_defs.get_approvers')
  def test_post__comment_only(self, mock_get_approvers):
    """Handler adds a comment only, does not require approval permission."""
    mock_get_approvers.return_value = []
    testing_config.sign_in('owner2@example.com', 123567890)
    params = {'comment': 'Congratulations'}
    with test_app.test_request_context(self.request_path, json=params):
      actual = self.handler.do_post(self.feature_id, self.field_id)

    self.assertEqual(actual, {'message': 'Done'})
    updated_approvals = review_models.Approval.get_approvals(
        feature_id=self.feature_id)
    self.assertEqual(1, len(updated_approvals))
    appr = updated_approvals[0]
    self.assertEqual(appr.feature_id, self.feature_id)
    self.assertEqual(appr.field_id, 1)
    self.assertEqual(appr.set_by, 'owner1@example.com')  # Unchanged
    self.assertEqual(appr.state, review_models.Approval.APPROVED)  # Unchanged
    updated_comments = review_models.Comment.get_comments(
        self.feature_id, self.field_id)
    cmnt = updated_comments[0]
    self.assertEqual('Congratulations', cmnt.content)
    self.assertIsNone(cmnt.old_approval_state)
    self.assertIsNone(cmnt.new_approval_state)
