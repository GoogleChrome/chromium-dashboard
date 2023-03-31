# -*- coding: utf-8 -*-
# Copyright 2022 Google Inc.
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

import flask
from unittest import mock
from google.cloud import ndb  # type: ignore
import werkzeug.exceptions

from api import stages_api
from internals.user_models import AppUser
from internals.core_models import FeatureEntry, MilestoneSet, Stage
from internals.review_models import Gate

test_app = flask.Flask(__name__)

class StagesAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_owner = AppUser(email='feature_owner@example.com')
    self.feature_owner.put()

    self.basic_user = AppUser(email='basic_user@example.com')
    self.basic_user.put()

    self.fe = FeatureEntry(id=1, name='feature one', summary='summary',
        owner_emails=[self.feature_owner.email], feature_type=0, category=1)
    self.fe.put()

    # Origin trial stage.
    self.stage_1 = Stage(id=10, feature_id=1, stage_type=150, browser='Chrome',
        ux_emails=['ux_person@example.com'],
        intent_thread_url='https://example.com/intent',
        milestones=MilestoneSet(desktop_first=100),
        experiment_goals='To be the very best.')
    self.stage_1.put()
    # Shipping stage.
    self.stage_2 = Stage(id=11, feature_id=1, stage_type=160)
    self.stage_2.put()

    self.stage_3 = Stage(id=30, feature_id=99, stage_type=150, browser='Chrome',
        ux_emails=['ux_person@example.com'],
        intent_thread_url='https://example.com/intent',
        milestones=MilestoneSet(desktop_first=100),
        experiment_goals='To be the very best.')
    self.stage_3.put()

    self.stage_4 = Stage(id=40, feature_id=1, stage_type=150, browser='Chrome',
        ux_emails=['ux_person@example.com'],
        intent_thread_url='https://example.com/intent',
        milestones=MilestoneSet(desktop_first=100),
        experiment_goals='To be the very best.')
    self.stage_4.put()

    self.stage_5 = Stage(id=50, feature_id=1, stage_type=150, browser='Chrome',
        ot_stage_id=40,
        ux_emails=['ux_person@example.com'],
        intent_thread_url='https://example.com/intent',
        milestones=MilestoneSet(desktop_first=100),
        experiment_goals='To be the very best.')
    self.stage_5.put()

    self.expected_stage_1 = {
        'android_first': None,
        'android_last': None,
        'announcement_url': None,
        'desktop_first': 100,
        'desktop_last': None,
        'display_name': None,
        'enterprise_policies': [],
        'origin_trial_feedback_url': None,
        'experiment_extension_reason': None,
        'experiment_goals': 'To be the very best.',
        'experiment_risks': None,
        'extensions': [],
        'feature_id': 1,
        'finch_url': None,
        'id': 10,
        'intent_stage': 3,
        'intent_thread_url': 'https://example.com/intent',
        'ios_first': None,
        'ios_last': None,
        'ot_stage_id': None,
        'pm_emails': [],
        'rollout_details': None,
        'rollout_impact': 2,
        'rollout_milestone': None,
        'rollout_platforms': [],
        'stage_type': 150,
        'te_emails': [],
        'tl_emails': [],
        'ux_emails': ['ux_person@example.com'],
        'webview_first': None,
        'webview_last': None}

    self.handler = stages_api.StagesAPI()
    self.request_path = '/api/v0/features/'

    self.maxDiff = None

  def tearDown(self):
    testing_config.sign_out()
    kinds: list[ndb.Model] = [AppUser, FeatureEntry, Gate, MilestoneSet, Stage]
    for kind in kinds:
      for entity in kind.query():
        entity.key.delete()

  @mock.patch('flask.abort')
  def test_get__bad_id(self, mock_abort):
    """Raises 404 if stage ID does not match any stage."""
    mock_abort.side_effect = werkzeug.exceptions.BadRequest
    with test_app.test_request_context(f'{self.request_path}1/stages/3001'):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_get(feature_id=1, stage_id=3001)
    mock_abort.assert_called_once_with(404, description=f'Stage 3001 not found')

  @mock.patch('flask.abort')
  def test_get__no_id(self, mock_abort):
    """Sends a basic response with id=0 when no ID specified."""
    mock_abort.side_effect = werkzeug.exceptions.BadRequest
    with test_app.test_request_context(f'{self.request_path}1/stages'):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
                self.handler.do_get(feature_id=1)
    mock_abort.assert_called_once_with(404, description='No stage specified.')

  def test_get__valid(self):
    """Returns stage data if requesting a valid stage ID."""
    with test_app.test_request_context(f'{self.request_path}1/stages/10'):
      actual = self.handler.do_get(feature_id=1, stage_id=10)

    self.assertEqual(self.expected_stage_1, actual)

  def test_get__valid_with_extension(self):
    """Returns stage data with extension if requesting a valid stage ID."""
    extension = {
        'id': 50,
        'feature_id': 1,
        'stage_type': 150,
        'intent_stage': 3,
        'pm_emails': [],
        'tl_emails': [],
        'ux_emails': ['ux_person@example.com'],
        'te_emails': [],
        'intent_thread_url': 'https://example.com/intent',
        'desktop_first': 100,
        'display_name': None,
        'desktop_last': None,
        'android_first': None,
        'android_last': None,
        'webview_first': None,
        'webview_last': None,
        'experiment_goals': 'To be the very best.',
        'experiment_risks': None,
        'origin_trial_feedback_url': None,
        'announcement_url': None,
        'enterprise_policies': [],
        'experiment_extension_reason': None,
        'extensions': [],
        'finch_url': None,
        'ios_first': None,
        'ios_last': None,
        'ot_stage_id': 40,
        'rollout_details': None,
        'rollout_impact': 2,
        'rollout_milestone': None,
        'rollout_platforms': [],
}

    expect = {
        'id': 40,
        'feature_id': 1,
        'stage_type': 150,
        'intent_stage': 3,
        'pm_emails': [],
        'tl_emails': [],
        'ux_emails': ['ux_person@example.com'],
        'te_emails': [],
        'intent_thread_url': 'https://example.com/intent',
        'desktop_first': 100,
        'display_name': None,
        'desktop_last': None,
        'android_first': None,
        'android_last': None,
        'webview_first': None,
        'webview_last': None,
        'experiment_extension_reason': None,
        'experiment_goals': 'To be the very best.',
        'experiment_risks': None,
        'extensions': [extension],
        'announcement_url': None,
        'enterprise_policies': [],
        'origin_trial_feedback_url': None,
        'rollout_details': None,
        'rollout_impact': 2,
        'rollout_milestone': None,
        'rollout_platforms': [],
        'ot_stage_id': None,
        'ios_first': None,
        'ios_last': None,
        'finch_url': None,
}

    with test_app.test_request_context(f'{self.request_path}1/stages/10'):
      actual = self.handler.do_get(feature_id=1, stage_id=40)

    self.assertEqual(expect, actual)

  @mock.patch('flask.abort')
  def test_post__not_allowed(self, mock_abort):
    """Raises 403 if user has no edit access to feature."""
    testing_config.sign_in('basic_user@example.com', 123)
    mock_abort.side_effect = werkzeug.exceptions.Forbidden
    request_path = f'{self.request_path}1/stages'
    json = {
        'stage_type': 151,
        'intent_thread_url': 'https://example.com/different'}

    with test_app.test_request_context(request_path, json=json):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post(feature_id=1)
    mock_abort.assert_called_once_with(403)

  @mock.patch('framework.permissions.validate_feature_edit_permission')
  def test_post__Redirect(self, permission_call):
    """Lack of permission in POST and redirect users."""
    permission_call.return_value = 'fake response'
    testing_config.sign_in('feature_owner@example.com', 123)

    with test_app.test_request_context(
        f'{self.request_path}1/stages/10'):
      actual = self.handler.do_post(feature_id=1)

    self.assertEqual(actual, 'fake response')

  @mock.patch('flask.abort')
  def test_post__bad_id(self, mock_abort):
    """Raises 404 if ID does not match any feature."""
    testing_config.sign_in('feature_owner@example.com', 123)
    mock_abort.side_effect = werkzeug.exceptions.BadRequest
    json = {
        'stage_type': 151,
        'intent_thread_url': 'https://example.com/different'}

    with test_app.test_request_context(
        f'{self.request_path}3001/stages', json=json):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post(feature_id=3001)
    mock_abort.assert_called_once_with(
        404, description=f'Feature 3001 not found')

  @mock.patch('flask.abort')
  def test_post__no_stage_type(self, mock_abort):
    """Raises 404 if no stage type was given."""
    testing_config.sign_in('feature_owner@example.com', 123)
    mock_abort.side_effect = werkzeug.exceptions.BadRequest
    with test_app.test_request_context(f'{self.request_path}1/stages'):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post(feature_id=1)
    mock_abort.assert_called_once_with(
        404, description='Stage type not specified.')

  def test_post__valid(self):
    """A valid POST request should create a new stage."""
    testing_config.sign_in('feature_owner@example.com', 123)
    json = {
        'stage_type': 151,
        'intent_thread_url': 'https://example.com/different'}

    with test_app.test_request_context(
        f'{self.request_path}/1/stages', json=json):
      actual = self.handler.do_post(feature_id=1)
    self.assertEqual(actual['message'], 'Stage created.')
    stage_id = actual['stage_id']
    stage: Stage | None = Stage.get_by_id(stage_id)
    self.assertIsNotNone(stage)
    self.assertEqual(stage.stage_type, 151)
    self.assertEqual(stage.intent_thread_url, 'https://example.com/different')

  def test_post__gate_created(self):
    """A Gate entity is created when a gated stage is created."""
    testing_config.sign_in('feature_owner@example.com', 123)
    json = {
        'stage_type': 151,
        'desktop_first': 100, 
        'intent_thread_url': 'https://example.com/different'}

    with test_app.test_request_context(
        f'{self.request_path}1/stages', json=json):
      actual = self.handler.do_post(feature_id=1)
    self.assertEqual(actual['message'], 'Stage created.')
    stage_id = actual['stage_id']
    gates: list[Gate] = Gate.query(Gate.stage_id == stage_id).fetch()
    self.assertTrue(len(gates) == 1)

  def test_post__gate_not_needed(self):
    """A Gate entity is created when a non-gated stage is created."""
    testing_config.sign_in('feature_owner@example.com', 123)
    json = {
        'stage_type': 110,
        'intent_thread_url': 'https://example.com/different'}

    with test_app.test_request_context(
        f'{self.request_path}1/stages', json=json):
      actual = self.handler.do_post(feature_id=1)
    self.assertEqual(actual['message'], 'Stage created.')
    stage_id = actual['stage_id']
    gates: list[Gate] = Gate.query(Gate.stage_id == stage_id).fetch()
    self.assertTrue(len(gates) == 0)

  @mock.patch('flask.abort')
  def test_patch__not_allowed(self, mock_abort):
    """Raises 403 if user does not have edit access to the stage."""
    testing_config.sign_in('basic_user@example.com', 123)
    json = {'intent_thread_url': 'https://example.com/different'}

    mock_abort.side_effect = werkzeug.exceptions.Forbidden
    with test_app.test_request_context(
        f'{self.request_path}1/stages/10', json=json):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_patch(feature_id=1, stage_id=10)
    mock_abort.assert_called_once_with(403)

  @mock.patch('flask.abort')
  def test_patch__bad_id(self, mock_abort):
    """Raises 404 if ID does not match any stage."""
    testing_config.sign_in('feature_owner@example.com', 123)
    json = {'intent_thread_url': 'https://example.com/different'}

    mock_abort.side_effect = werkzeug.exceptions.BadRequest
    with test_app.test_request_context(
        f'{self.request_path}1/stages/3001', json=json):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_patch(feature_id=1, stage_id=3001)
    mock_abort.assert_called_once_with(
        404, description=f'Stage 3001 not found')

  @mock.patch('flask.abort')
  def test_patch__no_id(self, mock_abort):
    """Raises 404 if no stage ID was given."""
    testing_config.sign_in('feature_owner@example.com', 123)
    json = {'intent_thread_url': 'https://example.com/different'}

    mock_abort.side_effect = werkzeug.exceptions.BadRequest
    with test_app.test_request_context(
        f'{self.request_path}1/stages', json=json):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_patch(feature_id=1)
    mock_abort.assert_called_once_with(404, description='No stage specified.')

  @mock.patch('flask.abort')
  def test_patch__no_feature(self, mock_abort):
    """Raises 404 if no feature was found."""
    testing_config.sign_in('feature_owner@example.com', 123)
    json = {
        'intent_thread_url': 'https://example.com/different'}
    mock_abort.side_effect = werkzeug.exceptions.BadRequest

    with test_app.test_request_context(
        f'{self.request_path}1/stages', json=json):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_patch(stage_id=30)

    description = 'Feature 99 not found associated with stage 30'
    mock_abort.assert_called_once_with(404, description=description)

  @mock.patch('framework.permissions.validate_feature_edit_permission')
  def test_patch__Redirect(self, permission_call):
    """Lack of permission in Patch and redirect users."""
    permission_call.return_value = 'fake response'
    testing_config.sign_in('feature_owner@example.com', 123)

    with test_app.test_request_context(
        f'{self.request_path}1/stages/10'):
      actual = self.handler.do_patch(stage_id=10)

    self.assertEqual(actual, 'fake response')

  @mock.patch('flask.abort')
  def test_patch__stage_type_change_attempt(self, mock_abort):
    """stage_type field cannot be mutated."""
    testing_config.sign_in('feature_owner@example.com', 123)
    json = {
        'stage_type': 260,
        'intent_thread_url': 'https://example.com/different'}

    with test_app.test_request_context(
        f'{self.request_path}1/stages/10', json=json):
      self.handler.do_patch(feature_id=1, stage_id=10)
    # Stage type not changed.
    self.assertEqual(self.stage_1.stage_type, 150)

  def test_patch__valid(self):
    """A valid PATCH request should update an existing stage."""
    testing_config.sign_in('feature_owner@example.com', 123)
    json = {
        'intent_thread_url': 'https://example.com/different',
        'announcement_url': 'https://example.com/announce',
        'experiment_risks': 'No risks.',
        'browser': None}

    with test_app.test_request_context(
        f'{self.request_path}1/stages/10', json=json):
      actual = self.handler.do_patch(feature_id=1, stage_id=10)
    self.assertEqual(actual['message'], 'Stage values updated.')
    stage = self.stage_1
    self.assertEqual(stage.experiment_risks, 'No risks.')
    self.assertEqual(stage.intent_thread_url, 'https://example.com/different')
    # Values can be set to null.
    self.assertIsNone(stage.browser)
    # Type-specific stage fields should not be put onto incorrect stages.
    self.assertIsNone(stage.announcement_url)
    # Existing fields not specified should not be changed.
    self.assertEqual(stage.experiment_goals, 'To be the very best.')

  @mock.patch('flask.abort')
  def test_delete__not_allowed(self, mock_abort):
    """Raises 403 if user does not have edit access to the stage."""
    testing_config.sign_in('basic_user@example.com', 123)
    mock_abort.side_effect = werkzeug.exceptions.Forbidden
    with test_app.test_request_context(f'{self.request_path}1/stages/10'):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_delete(stage_id=10)
    mock_abort.assert_called_once_with(403)

  @mock.patch('flask.abort')
  def test_delete__no_id(self, mock_abort):
    """Raises 404 if no stage ID was given."""
    testing_config.sign_in('feature_owner@example.com', 123)
    mock_abort.side_effect = werkzeug.exceptions.BadRequest
    with test_app.test_request_context(f'{self.request_path}1/stages'):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_delete(feature_id=1)
    mock_abort.assert_called_once_with(404, description='No stage specified.')

  @mock.patch('flask.abort')
  def test_delete__bad_id(self, mock_abort):
    """Raises 404 if ID does not match any stage."""
    testing_config.sign_in('feature_owner@example.com', 123)
    mock_abort.side_effect = werkzeug.exceptions.BadRequest
    with test_app.test_request_context(f'{self.request_path}1/stages/3001'):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_delete(stage_id=3001)
    mock_abort.assert_called_once_with(404, description='Stage 3001 not found.')

  def test_delete__valid(self):
    """A valid DELETE request should mark the existing stage as archived."""
    testing_config.sign_in('feature_owner@example.com', 123)
    with test_app.test_request_context(f'{self.request_path}1/stages/10'):
      actual = self.handler.do_delete(feature_id=1, stage_id=10)
    self.assertEqual(actual['message'], 'Stage archived.')
    self.assertEqual(self.stage_1.archived, True)


  @mock.patch('framework.permissions.validate_feature_edit_permission')
  def test_delete__Redirect(self, permission_call):
    """Lack of permission in Delete and redirect users."""
    permission_call.return_value = 'fake response'

    with test_app.test_request_context(f'{self.request_path}1/stages/10'):
      actual = self.handler.do_delete(feature_id=1, stage_id=10)

    self.assertEqual(actual, 'fake response')
