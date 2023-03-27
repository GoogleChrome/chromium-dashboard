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
from internals.core_models import FeatureEntry
from internals.review_models import Activity, Amendment, Gate, Vote

test_app = flask.Flask(__name__)

NOW = datetime.datetime.now()


class CommentsConvertersTest(testing_config.CustomTestCase):

  def test_amendment_to_json_dict(self):
    amnd = Amendment(
        field_name='summary', old_value='foo', new_value='bar')
    expected = dict(field_name='summary', old_value='foo', new_value='bar')
    actual = comments_api.amendment_to_json_dict(amnd)
    self.assertEqual(expected, actual)

  def test_amendment_to_json_dict__arrays(self):
    """Arrays are shown without the brackets."""
    amnd = Amendment(
        field_name='summary', old_value='[1, 2]', new_value='[1, 2, 3]')
    expected = dict(field_name='summary', old_value='1, 2', new_value='1, 2, 3')
    actual = comments_api.amendment_to_json_dict(amnd)
    self.assertEqual(expected, actual)

  def test_activity_to_json_dict(self):
    amnd_1 = Amendment(
        field_name='summary', old_value='foo', new_value='bar')
    amnd_2 = Amendment(
        field_name='owner_emails', old_value='None', new_value='[]')
    created = datetime.datetime(2022, 10, 28, 0, 0, 0)
    act = Activity(
        id=1, feature_id=123, gate_id=456, created=created,
        author='author@example.com', content='hello',
        amendments=[amnd_1, amnd_2])
    actual = comments_api.activity_to_json_dict(act)
    expected = {
      'comment_id': 1,
      'feature_id': 123,
      'gate_id': 456,
      'created': '2022-10-28 00:00:00',
      'author': 'author@example.com',
      'content': 'hello',
      'deleted_by': None,
      'amendments': [{
          'field_name': 'summary',
          'old_value': 'foo',
          'new_value': 'bar',
      }],
    }
    self.assertEqual(expected, actual)


class CommentsAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = FeatureEntry(
        name='feature one', summary='sum', category=1)
    self.feature_1.put()
    self.feature_id = self.feature_1.key.integer_id()

    self.gate_1 = Gate(feature_id=self.feature_id,
        stage_id=1, gate_type=2, state=Vote.NA)
    self.gate_1.put()
    self.gate_1_id = self.gate_1.key.integer_id()

    self.handler = comments_api.CommentsAPI()
    self.request_path = ('/api/v0/features/%d/approvals/%d/comments' %
                         (self.feature_id, self.gate_1_id))

    self.act_1_1 = Activity(
      feature_id=self.feature_id, gate_id=self.gate_1_id,
      author='owner1@example.com', created=NOW, content='Good job')

    self.expected_1 = {
        'feature_id': self.feature_id,
        'gate_id': self.gate_1_id,
        'author': 'owner1@example.com',
        'deleted_by': None,
        'content': 'Good job',
        'amendments': [],
        }

  def tearDown(self):
    self.feature_1.key.delete()
    for activity in Activity.query():
      activity.key.delete()

  def test_get__empty(self):
    """We can get comments for a given approval, even if there none."""
    testing_config.sign_out()
    testing_config.sign_in('user7@example.com', 123567890)
    with test_app.test_request_context(self.request_path):
      actual_response = self.handler.do_get(
          feature_id=self.feature_id, gate_id=self.gate_1_id)
    testing_config.sign_out()
    self.assertEqual({'comments': []}, actual_response)

  def test_get__legacy_comments(self):
    """We can get legacy comments."""
    testing_config.sign_out()
    testing_config.sign_in('user7@example.com', 123567890)

    legacy_comment = Activity(
      feature_id=self.feature_id, author='owner1@example.com',
      created=NOW, content='nothing')
    legacy_comment.put()

    with test_app.test_request_context(self.request_path):
      actual_response = self.handler.do_get(
          feature_id=self.feature_id, gate_id=self.gate_1_id)
    testing_config.sign_out()
    actual_comment = actual_response['comments'][0]
    self.assertEqual('nothing', actual_comment['content'])

  def test_get__all_some(self):
    """We can get all comments for a given approval."""
    testing_config.sign_out()
    testing_config.sign_in('user7@example.com', 123567890)
    self.act_1_1.put()

    random_activity = Activity(
      feature_id=self.feature_id, gate_id=99,
      author='owner1@example.com', created=NOW, content='nothing')
    random_activity.put()

    with test_app.test_request_context(self.request_path):
      actual_response = self.handler.do_get(
          feature_id=self.feature_id, gate_id=self.gate_1_id)
    testing_config.sign_out()

    self.assertEqual(1, len(actual_response['comments']))
    actual_comment = actual_response['comments'][0]
    del actual_comment['created']
    del actual_comment['comment_id']
    self.assertEqual(
        self.expected_1,
        actual_comment)

  def test_get__deleted_comment(self):
    """A deleted comment should not show the original content."""
    testing_config.sign_out()
    testing_config.sign_in('user7@example.com', 123567890)
    self.act_1_1.deleted_by = 'other_user@example.com'
    self.act_1_1.put()

    with test_app.test_request_context(self.request_path):
      resp = self.handler.do_get(
        feature_id=self.feature_id, gate_id=self.gate_1_id)
    testing_config.sign_out()
    self.assertEqual(resp['comments'], [])


  def test_get__comment_deleted_by_user(self):
    """The user who deleted a comment can see the original content."""
    testing_config.sign_out()
    testing_config.sign_in('user7@example.com', 123567890)
    self.act_1_1.deleted_by = 'user7@example.com'
    self.act_1_1.put()

    with test_app.test_request_context(self.request_path):
      resp = self.handler.do_get(
          feature_id=self.feature_id, gate_id=self.gate_1_id)
    testing_config.sign_out()
    comment = resp['comments'][0]
    self.assertNotEqual(comment['content'], '[Deleted]')

  def test_post__feature_not_found(self):
    """Handler rejects requests that don't match an existing feature."""
    bad_path = '/api/v0/features/12345/approvals/1/comments'
    with test_app.test_request_context(bad_path, json={}):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.do_post(feature_id=12345, gate_id=self.gate_1_id)

  def test_patch__forbidden(self):
    """Handler rejects requests from users who can't edit the given comment."""
    self.act_1_1.put()
    params = {'commentId': self.act_1_1.key.id(), 'isUndelete': False}

    testing_config.sign_out()
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_patch(feature_id=self.feature_id)

    testing_config.sign_in('user7@example.com', 123567890)
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_patch(feature_id=self.feature_id)

  def test_patch__delete_comment(self):
    """Handler marks a comment as deleted as requested by authorized user."""
    self.act_1_1.put()

    user_email = 'owner1@example.com'
    params = {'commentId': self.act_1_1.key.id(), 'isUndelete': False}
    testing_config.sign_in(user_email, 123567890)
    with test_app.test_request_context(self.request_path, json=params):
      resp = self.handler.do_patch(feature_id=self.feature_id)
      get_resp = self.handler.do_get(
          feature_id=self.feature_id, gate_id=self.gate_1_id)
    testing_config.sign_out()
    self.assertEqual(get_resp['comments'][0]['deleted_by'], user_email)
    self.assertEqual(resp, {'message': 'Done'})

    # Check activity is also deleted.
    activity = Activity.get_by_id(self.act_1_1.key.integer_id())
    self.assertIsNotNone(activity)
    self.assertEqual(activity.deleted_by, user_email)

  def test_patch__undelete_comment(self):
    """Handler unmarks a comment as deleted as requested by authorized user."""
    user_email = 'owner1@example.com'
    self.act_1_1.deleted_by = user_email
    self.act_1_1.put()

    params = {'commentId': self.act_1_1.key.id(), 'isUndelete': True}
    testing_config.sign_in(user_email, 123567890)
    with test_app.test_request_context(self.request_path, json=params):
      resp = self.handler.do_patch(feature_id=self.feature_id)
      get_resp = self.handler.do_get(
          feature_id=self.feature_id, gate_id=self.gate_1_id)
    testing_config.sign_out()
    self.assertEqual(get_resp['comments'][0]['deleted_by'], None)
    self.assertEqual(resp, {'message': 'Done'})

    # Check activity is also undeleted.
    activity = Activity.get_by_id(self.act_1_1.key.integer_id())
    self.assertIsNotNone(activity)
    self.assertIsNone(activity.deleted_by)

  @mock.patch('internals.notifier_helpers.notify_subscribers_of_new_comments')
  @mock.patch('internals.approval_defs.get_approvers')
  def test_post__comment_only(self, mock_get_approvers, mock_notifier):
    """Handler adds a comment only, does not require approval permission."""
    mock_get_approvers.return_value = []
    testing_config.sign_in('user2@chromium.org', 123567890)
    params = {'comment': 'Congratulations'}
    with test_app.test_request_context(self.request_path, json=params):
      actual = self.handler.do_post(feature_id=self.feature_id,
          gate_id=self.gate_1_id)

    self.assertEqual(actual, {'message': 'Done'})
    updated_comments = Activity.get_activities(
        self.feature_id, self.gate_1.key.integer_id(), comments_only=True)
    cmnt = updated_comments[0]
    self.assertEqual('Congratulations', cmnt.content)
    self.assertEqual('user2@chromium.org', cmnt.author)

    # Check activity is also created.
    activity = Activity.get_by_id(cmnt.key.integer_id())
    self.assertIsNotNone(activity)

  @mock.patch('internals.approval_defs.get_approvers')
  def test_post__comment_rejected(self, mock_get_approvers):
    """Outsiders cannot comment."""
    mock_get_approvers.return_value = []
    testing_config.sign_in('outsider@example.com', 123567890)
    params = {'comment': 'Could be spam'}
    with test_app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post(
            feature_id=self.feature_id, gate_id=self.gate_1_id)
