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
from datetime import datetime
from unittest import mock
from google.cloud import ndb  # type: ignore
import werkzeug.exceptions

from api import stages_api
from internals.core_enums import OT_READY_FOR_CREATION
from internals.core_models import FeatureEntry, MilestoneSet, Stage
from internals.review_models import Gate
from internals.user_models import AppUser

test_app = flask.Flask(__name__)

class StagesAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.now = datetime.now()
    self.feature_owner = AppUser(email='feature_owner@example.com')
    self.feature_owner.put()

    self.basic_user = AppUser(email='basic_user@example.com')
    self.basic_user.put()

    self.fe = FeatureEntry(id=1, name='feature one', summary='summary',
        owner_emails=[self.feature_owner.email], feature_type=0, category=1)
    self.fe.put()

    # Origin trial stage.
    self.stage_1 = Stage(
        id=10,
        feature_id=1,
        stage_type=150,
        display_name='Stage display name',
        ux_emails=['ux_person@example.com'],
        intent_thread_url='https://example.com/intent',
        milestones=MilestoneSet(desktop_first=100),
        experiment_goals='To be the very best.',
        created=self.now,
        ot_setup_status=1)
    self.stage_1.put()
    # Shipping stage.
    self.stage_2 = Stage(id=11, feature_id=1, stage_type=160, created=self.now)
    self.stage_2.put()

    self.stage_3 = Stage(id=30, feature_id=99, stage_type=150, browser='Chrome',
        ux_emails=['ux_person@example.com'],
        intent_thread_url='https://example.com/intent',
        milestones=MilestoneSet(desktop_first=100),
        experiment_goals='To be the very best.',
        created=self.now)
    self.stage_3.put()

    self.stage_4 = Stage(
        id=40, feature_id=1, stage_type=150, browser='Chrome',
        origin_trial_id='-5269211564023480319',
        ux_emails=['ux_person@example.com'],
        intent_thread_url='https://example.com/intent',
        ot_action_requested=True,
        ot_require_approvals=True,
        ot_approval_buganizer_component=123456789,
        ot_approval_buganizer_custom_field_id=111111,
        ot_approval_criteria_url='https://example.com/criteria',
        ot_approval_group_email='fakegroup@google.com',
        ot_chromium_trial_name='ExampleChromiumTrialName',
        ot_description='An origin trial\'s description',
        ot_display_name='The Origin Trial Display Name',
        ot_documentation_url='https://example.com/ot_docs',
        ot_emails=['user1@example.com', 'user2@example.com'],
        ot_feedback_submission_url='https://example.com/submit_feedback',
        ot_has_third_party_support=True,
        ot_is_deprecation_trial=True,
        ot_is_critical_trial=True,
        # ot_request_note should remain confidential and not be displayed in
        # requests obtaining information about the stage.
        ot_request_note='Additional info',
        ot_owner_email='ot_owner@example.com',
        ot_use_counter_bucket_number=11,
        ot_webfeature_use_counter='kExampleUseCounter',
        milestones=MilestoneSet(desktop_first=100),
        experiment_goals='To be the very best.',
        created=self.now)
    self.stage_4.put()

    # Two extension stages for the same origin trial stage.
    self.stage_5 = Stage(id=50, feature_id=1, stage_type=151, browser='Chrome',
        ot_stage_id=40,
        ot_emails=['ot_person2@google.com'],
        intent_thread_url='https://example.com/intent2',
        milestones=MilestoneSet(desktop_last=106),
        experiment_extension_reason='To be the very best again.',
        created=self.now)
    self.stage_5.put()
    self.stage_5 = Stage(id=51, feature_id=1, stage_type=151, browser='Chrome',
        ot_stage_id=40,
        ot_emails=['ot_person@google.com'],
        intent_thread_url='https://example.com/intent',
        milestones=MilestoneSet(desktop_last=103),
        experiment_extension_reason='To be the very best.',
        created=datetime(2020, 1, 1))
    self.stage_5.put()

    self.expected_stage_1 = {
        'android_first': None,
        'android_last': None,
        'announcement_url': None,
        'created': str(self.now),
        'desktop_first': 100,
        'desktop_last': None,
        'display_name': 'Stage display name',
        'enterprise_policies': [],
        'origin_trial_id': None,
        'origin_trial_feedback_url': None,
        'ot_action_requested': False,
        'ot_approval_buganizer_component': None,
        'ot_approval_buganizer_custom_field_id': None,
        'ot_approval_criteria_url': None,
        'ot_approval_group_email': None,
        'ot_chromium_trial_name': None,
        'ot_description': None,
        'ot_display_name': None,
        'ot_documentation_url': None,
        'ot_emails': [],
        'ot_feedback_submission_url': None,
        'ot_has_third_party_support': False,
        'ot_is_critical_trial': False,
        'ot_is_deprecation_trial': False,
        'ot_owner_email': None,
        'ot_require_approvals': False,
        'ot_setup_status': 1,
        'ot_use_counter_bucket_number': None,
        'ot_webfeature_use_counter': None,
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
    mock_abort.assert_called_once_with(404, description='Stage 3001 not found.')

  @mock.patch('flask.abort')
  def test_get__no_id(self, mock_abort):
    """Sends a basic response with id=0 when no ID specified."""
    mock_abort.side_effect = werkzeug.exceptions.BadRequest
    with test_app.test_request_context(f'{self.request_path}1/stages'):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
                self.handler.do_get(feature_id=1)
    mock_abort.assert_called_once_with(400, description='No Stage ID specified.')

  def test_get__valid(self):
    """Returns stage data if requesting a valid stage ID."""
    with test_app.test_request_context(f'{self.request_path}1/stages/10'):
      actual = self.handler.do_get(feature_id=1, stage_id=10)

    self.assertEqual(self.expected_stage_1, actual)

  def test_get__valid_with_extension(self):
    """Returns stage data with extension if requesting a valid stage ID."""
    # TODO(DanielRyanSmith): this dict format should be tested in
    # api/converters_test.py instead.
    extension_1 = {
        'id': 50,
        'created': str(self.now),
        'feature_id': 1,
        'stage_type': 151,
        'intent_stage': 11,
        'pm_emails': [],
        'tl_emails': [],
        'ux_emails': [],
        'te_emails': [],
        'intent_thread_url': 'https://example.com/intent2',
        'desktop_first': None,
        'display_name': None,
        'desktop_last': 106,
        'android_first': None,
        'android_last': None,
        'webview_first': None,
        'webview_last': None,
        'experiment_goals': None,
        'experiment_risks': None,
        'origin_trial_feedback_url': None,
        'ot_action_requested': False,
        'ot_approval_buganizer_component': None,
        'ot_approval_buganizer_custom_field_id': None,
        'ot_approval_criteria_url': None,
        'ot_approval_group_email': None,
        'ot_chromium_trial_name': None,
        'ot_description': None,
        'ot_display_name': None,
        'ot_documentation_url': None,
        'ot_emails': ['ot_person2@google.com'],
        'ot_feedback_submission_url': None,
        'ot_has_third_party_support': False,
        'ot_is_critical_trial': False,
        'ot_is_deprecation_trial': False,
        'ot_owner_email': None,
        'ot_require_approvals': False,
        'ot_use_counter_bucket_number': None,
        'ot_webfeature_use_counter': None,
        'announcement_url': None,
        'enterprise_policies': [],
        'experiment_extension_reason': 'To be the very best again.',
        'extensions': [],
        'finch_url': None,
        'ios_first': None,
        'ios_last': None,
        'origin_trial_id': None,
        'ot_stage_id': 40,
        'rollout_details': None,
        'rollout_impact': 2,
        'rollout_milestone': None,
        'rollout_platforms': [],
        }
    extension_2 = {
        'id': 51,
        'created': '2020-01-01 00:00:00',
        'feature_id': 1,
        'stage_type': 151,
        'intent_stage': 11,
        'pm_emails': [],
        'tl_emails': [],
        'ux_emails': [],
        'te_emails': [],
        'intent_thread_url': 'https://example.com/intent',
        'desktop_first': None,
        'display_name': None,
        'desktop_last': 103,
        'android_first': None,
        'android_last': None,
        'webview_first': None,
        'webview_last': None,
        'experiment_goals': None,
        'experiment_risks': None,
        'origin_trial_feedback_url': None,
        'ot_action_requested': False,
        'ot_approval_buganizer_component': None,
        'ot_approval_buganizer_custom_field_id': None,
        'ot_approval_criteria_url': None,
        'ot_approval_group_email': None,
        'ot_chromium_trial_name': None,
        'ot_description': None,
        'ot_display_name': None,
        'ot_documentation_url': None,
        'ot_emails': ['ot_person@google.com'],
        'ot_feedback_submission_url': None,
        'ot_has_third_party_support': False,
        'ot_is_critical_trial': False,
        'ot_is_deprecation_trial': False,
        'ot_owner_email': None,
        'ot_require_approvals': False,
        'ot_use_counter_bucket_number': None,
        'ot_webfeature_use_counter': None,
        'announcement_url': None,
        'enterprise_policies': [],
        'experiment_extension_reason': 'To be the very best.',
        'extensions': [],
        'finch_url': None,
        'ios_first': None,
        'ios_last': None,
        'origin_trial_id': None,
        'ot_stage_id': 40,
        'rollout_details': None,
        'rollout_impact': 2,
        'rollout_milestone': None,
        'rollout_platforms': [],
    }

    expect = {
        'id': 40,
        'created': str(self.now),
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
        # Extensions should be in the order in which they were created.
        'extensions': [extension_2, extension_1],
        'announcement_url': None,
        'enterprise_policies': [],
        'origin_trial_id': '-5269211564023480319',
        'origin_trial_feedback_url': None,
        'ot_action_requested': True,
        'ot_approval_buganizer_component': 123456789,
        'ot_approval_buganizer_custom_field_id': 111111,
        'ot_approval_criteria_url': 'https://example.com/criteria',
        'ot_approval_group_email': 'fakegroup@google.com',
        'ot_chromium_trial_name': 'ExampleChromiumTrialName',
        'ot_description': 'An origin trial\'s description',
        'ot_display_name': 'The Origin Trial Display Name',
        'ot_documentation_url': 'https://example.com/ot_docs',
        'ot_emails': ['user1@example.com', 'user2@example.com'],
        'ot_feedback_submission_url': 'https://example.com/submit_feedback',
        'ot_has_third_party_support': True,
        'ot_is_critical_trial': True,
        'ot_is_deprecation_trial': True,
        'ot_owner_email': 'ot_owner@example.com',
        'ot_require_approvals': True,
        'ot_use_counter_bucket_number': 11,
        'ot_webfeature_use_counter': 'kExampleUseCounter',
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
        'stage_type': {
          'form_field_name': 'stage_type',
          'value': 151,
        },
        'intent_to_extend_experiment_url': {
          'form_field_name': 'intent_thread_url',
          'value': 'https://example.com/different',
        }
      }

    with test_app.test_request_context(request_path, json=json):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post(feature_id=1)
    mock_abort.assert_called_once_with(
        403, description='User cannot edit feature 1')

  @mock.patch('framework.permissions.validate_feature_edit_permission')
  def test_post__Redirect(self, permission_call):
    """Lack of permission in POST and redirect users."""
    permission_call.return_value = 'fake response'
    testing_config.sign_in('feature_owner@example.com', 123)

    json = {
      'stage_type': {
        'form_field_name': 'stage_type',
        'value': 151,
      }
    }
    with test_app.test_request_context(
        f'{self.request_path}1/stages/10', json=json):
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
        404, description=f'FeatureEntry 3001 not found.')

  @mock.patch('flask.abort')
  def test_post__no_stage_type(self, mock_abort):
    """Raises 404 if no stage type was given."""
    testing_config.sign_in('feature_owner@example.com', 123)
    mock_abort.side_effect = werkzeug.exceptions.BadRequest
    with test_app.test_request_context(f'{self.request_path}1/stages'):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post(feature_id=1)
    mock_abort.assert_called_once_with(
        400, description='Stage type not specified.')

  def test_post__valid(self):
    """A valid POST request should create a new stage."""
    testing_config.sign_in('feature_owner@example.com', 123)
    json = {
      'stage_type': {
        'form_field_name': 'stage_type',
        'value': 151,
      }
    }

    with test_app.test_request_context(
        f'{self.request_path}/1/stages', json=json):
      actual = self.handler.do_post(feature_id=1)
    self.assertEqual(actual['message'], 'Stage created.')
    stage_id = actual['stage_id']
    stage: Stage | None = Stage.get_by_id(stage_id)
    self.assertIsNotNone(stage)
    self.assertEqual(stage.stage_type, 151)

  def test_post__gate_created(self):
    """A Gate entity is created when a gated stage is created."""
    testing_config.sign_in('feature_owner@example.com', 123)
    json = {
      'stage_type': {
        'form_field_name': 'stage_type',
        'value': 151
      }
    }

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
      'stage_type': {
        'form_field_name': 'stage_type',
        'value': 110,
      }
    }

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
    mock_abort.assert_called_once_with(
        403, description='User cannot edit feature 1')

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
        404, description=f'Stage 3001 not found.')

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
    mock_abort.assert_called_once_with(400, description='No Stage ID specified.')

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

    description = 'FeatureEntry 99 not found.'
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
  def test_patch__ot_milestones_during_creation(self, mock_abort):
    """Raises 400 if OT start milestone is updated during OT creation process.
    """
    testing_config.sign_in('feature_owner@example.com', 123)
    json = {
      'id': 10,
      'desktop_first': {
        'form_field_name': 'ot_milestone_desktop_start',
        'value': 200,
      },
    }

    # OT is flagged for automated creation process.
    self.stage_1.ot_setup_status = OT_READY_FOR_CREATION
    self.stage_1.put()
    mock_abort.side_effect = werkzeug.exceptions.BadRequest
    with test_app.test_request_context(
        f'{self.request_path}1/stages/10', json=json):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_patch(feature_id=1, stage_id=10)
    mock_abort.assert_called_once_with(
        400,
        description='Cannot edit OT milestones while creation is in progress.')

  @mock.patch('flask.abort')
  def test_patch__ot_end_milestone_during_creation(self, mock_abort):
    """Raises 400 if OT end milestone is updated during OT creation process."""
    testing_config.sign_in('feature_owner@example.com', 123)
    json = {
      'id': 10,
      'desktop_last': {
        'form_field_name': 'ot_milestone_desktop_end',
        'value': 206,
      },
    }

    # OT is flagged for automated creation process.
    self.stage_1.ot_setup_status = OT_READY_FOR_CREATION
    self.stage_1.put()
    mock_abort.side_effect = werkzeug.exceptions.BadRequest
    with test_app.test_request_context(
        f'{self.request_path}1/stages/10', json=json):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_patch(feature_id=1, stage_id=10)
    mock_abort.assert_called_once_with(
        400,
        description='Cannot edit OT milestones while creation is in progress.')

  def test_patch__valid(self):
    """A valid PATCH request should update an existing stage."""
    testing_config.sign_in('feature_owner@example.com', 123)
    json = {
        'intent_thread_url': {
          'form_field_name': 'intent_to_experiment_url',
          'value': 'https://example.com/different',
        },
        'experiment_risks': {
          'form_field_name': 'experiment_risks',
          'value': 'No risks.',
        },
        'display_name': {
          'form_field_name': 'display_name',
          'value': None,
        },
      }

    with test_app.test_request_context(
        f'{self.request_path}1/stages/10', json=json):
      actual = self.handler.do_patch(feature_id=1, stage_id=10)
    self.assertEqual(actual['message'], 'Stage values updated.')
    stage = self.stage_1
    self.assertEqual(stage.experiment_risks, 'No risks.')
    self.assertEqual(stage.intent_thread_url, 'https://example.com/different')
    # Values can be set to null.
    self.assertIsNone(stage.display_name)
    # Existing fields not specified should not be changed.
    self.assertEqual(stage.experiment_goals, 'To be the very best.')

  @mock.patch('internals.notifier_helpers.send_ot_creation_notification')
  def test_patch__ot_creation(self, mock_send_ot_creation_notification):
    """A valid PATCH request should update an existing stage."""
    testing_config.sign_in('feature_owner@example.com', 123)
    mock_send_ot_creation_notification.return_value = None
    json = {
        'ot_action_requested': {
          'form_field_name': 'ot_action_requested',
          'value': True,
        },
        'ot_chromium_trial_name': {
          'form_field_name': 'ot_chromium_trial_name',
          'value': 'Some name',
        },
      }

    with test_app.test_request_context(
        f'{self.request_path}1/stages/10', json=json):
      actual = self.handler.do_patch(feature_id=1, stage_id=10)
    self.assertEqual(actual['message'], 'Stage values updated.')
    stage = self.stage_1
    self.assertEqual(stage.ot_chromium_trial_name, 'Some name')
    # Values can be set to null.
    self.assertTrue(stage.ot_action_requested)
    # Existing fields not specified should not be changed.
    self.assertEqual(stage.experiment_goals, 'To be the very best.')
    # OT creation request notification should be sent.
    mock_send_ot_creation_notification.assert_called_once()

  @mock.patch('internals.notifier_helpers.send_ot_creation_notification')
  def test_patch__ot_extension(self, mock_send_ot_creation_notification):
    """A valid PATCH request should update an existing stage."""
    testing_config.sign_in('feature_owner@example.com', 123)
    # extension stage type.
    self.stage_1.stage_type = 151
    self.stage_1.put()
    mock_send_ot_creation_notification.return_value = None
    json = {
        'ot_action_requested': {
          'form_field_name': 'ot_action_requested',
          'value': True,
        },
        'ot_chromium_trial_name': {
          'form_field_name': 'ot_extension_reason',
          'value': 'reason',
        },
      }

    with test_app.test_request_context(
        f'{self.request_path}1/stages/10', json=json):
      actual = self.handler.do_patch(feature_id=1, stage_id=10)
    self.assertEqual(actual['message'], 'Stage values updated.')
    stage = self.stage_1
    self.assertEqual(stage.ot_chromium_trial_name, 'reason')
    # Values can be set to null.
    self.assertTrue(stage.ot_action_requested)
    # Existing fields not specified should not be changed.
    self.assertEqual(stage.experiment_goals, 'To be the very best.')
    # OT extension request should NOT send a notification.
    mock_send_ot_creation_notification.assert_not_called()

  def test_patch__ot_request_googler(self):
    """A valid OT creation request from a googler should update stage."""
    testing_config.sign_in('a_googler@google.com', 123)
    json = {
        'ot_action_requested': {
          'form_field_name': 'ot_action_requested',
          'value': True,
        },
        'ot_request_note': {
          'form_field_name': 'ot_request_note',
          'value': 'Additional info.',
        },
        'ot_display_name': {
          'form_field_name': 'ot_display_name',
          'value': 'OT name',
        },
      }

    with test_app.test_request_context(
        f'{self.request_path}1/stages/10', json=json):
      actual = self.handler.do_patch(feature_id=1, stage_id=10)
    self.assertEqual(actual['message'], 'Stage values updated.')
    stage = self.stage_1
    self.assertEqual(stage.ot_action_requested, True)
    self.assertEqual(stage.ot_request_note, 'Additional info.')
    self.assertEqual(stage.ot_display_name, 'OT name')
    # Existing fields not specified should not be changed.
    self.assertEqual(stage.experiment_goals, 'To be the very best.')

  def test_patch__ot_request_chromium(self):
    """A valid OT creation request from a Chromium user should update stage."""
    testing_config.sign_in('chromium_user@chromium.org', 123)
    json = {
        'ot_action_requested': {
          'form_field_name': 'ot_action_requested',
          'value': True,
        },
        'ot_request_note': {
          'form_field_name': 'ot_request_note',
          'value': 'Additional info.',
        },
        'ot_display_name': {
          'form_field_name': 'ot_display_name',
          'value': 'OT name',
        },
      }

    with test_app.test_request_context(
        f'{self.request_path}1/stages/10', json=json):
      actual = self.handler.do_patch(feature_id=1, stage_id=10)
    self.assertEqual(actual['message'], 'Stage values updated.')
    stage = self.stage_1
    self.assertEqual(stage.ot_action_requested, True)
    self.assertEqual(stage.ot_request_note, 'Additional info.')
    self.assertEqual(stage.ot_display_name, 'OT name')
    # Existing fields not specified should not be changed.
    self.assertEqual(stage.experiment_goals, 'To be the very best.')

  def test_patch__ot_request_unauthorized(self):
    """An OT creation request from an unauthorized is not processed."""
    testing_config.sign_in('someone_unexpected@example.com', 123)
    json = {
        'ot_action_requested': {
          'form_field_name': 'ot_action_requested',
          'value': True,
        },
        'ot_request_note': {
          'form_field_name': 'ot_request_note',
          'value': 'Additional info.',
        },
        'ot_display_name': {
          'form_field_name': 'ot_display_name',
          'value': 'OT name',
        },
      }

    with test_app.test_request_context(
        f'{self.request_path}1/stages/10', json=json):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_patch(feature_id=1, stage_id=10)

  @mock.patch('flask.abort')
  def test_delete__not_allowed(self, mock_abort):
    """Raises 403 if user does not have edit access to the stage."""
    testing_config.sign_in('basic_user@example.com', 123)
    mock_abort.side_effect = werkzeug.exceptions.Forbidden
    with test_app.test_request_context(f'{self.request_path}1/stages/10'):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_delete(stage_id=10)
    mock_abort.assert_called_once_with(
        403, description='User cannot edit feature 1')

  @mock.patch('flask.abort')
  def test_delete__no_id(self, mock_abort):
    """Raises 404 if no stage ID was given."""
    testing_config.sign_in('feature_owner@example.com', 123)
    mock_abort.side_effect = werkzeug.exceptions.BadRequest
    with test_app.test_request_context(f'{self.request_path}1/stages'):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_delete(feature_id=1)
    mock_abort.assert_called_once_with(400, description='No Stage ID specified.')

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
