# Copyright 2023 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the 'License')
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import csv
import testing_config  # Must be imported before the module under test.
from google.cloud import ndb

from io import StringIO
import requests
from datetime import date, datetime, timedelta
from unittest import mock

from api import converters
from internals import maintenance_scripts
from internals import core_enums
from internals.core_models import FeatureEntry, Stage, MilestoneSet
from internals.review_models import Activity, Amendment, Gate, Vote
from internals import stage_helpers
from internals.webdx_feature_models import WebdxFeatures
from webstatus_openapi import FeaturePage, ApiException
import settings

class EvaluateGateStatusTest(testing_config.CustomTestCase):

  def setUp(self):
    self.delete_gates_and_votes()
    self.handler = maintenance_scripts.EvaluateGateStatus()

  def tearDown(self):
    self.delete_gates_and_votes()

  def delete_gates_and_votes(self):
    for kind in [Gate, Vote]:
      for entity in kind.query():
        entity.key.delete()

  def test_get_template_data__no_gates(self):
    """If there no votes or gates, nothing happens."""
    actual = self.handler.get_template_data()
    self.assertEqual(actual, '0 Gate entities updated.')

  def test_get_template_data__no_updates_needed(self):
    """If the gates already have the right state, no updates are needed."""
    gate_1 = Gate(feature_id=1, state=Gate.PREPARING, gate_type=1, stage_id=11)
    gate_1.put()
    actual = self.handler.get_template_data()
    self.assertEqual(actual, '0 Gate entities updated.')

    gate_2 = Gate(
        feature_id=1, state=Vote.REVIEW_REQUESTED, gate_type=2, stage_id=11)
    gate_2.put()
    vote_2_1 = Vote(
        feature_id=1, gate_id=gate_2.key.integer_id(),
        state=Vote.REVIEW_REQUESTED, set_by='one@example.com',
        set_on=datetime.now())
    vote_2_1.put()
    actual = self.handler.get_template_data()
    self.assertEqual(actual, '0 Gate entities updated.')

    gate_2.state = Vote.APPROVED
    gate_2.put()
    vote_2_2 = Vote(
        feature_id=1, gate_id=gate_2.key.integer_id(),
        state=Vote.APPROVED, set_by='two@example.com',
        set_on=datetime.now())
    vote_2_2.put()
    actual = self.handler.get_template_data()
    self.assertEqual(actual, '0 Gate entities updated.')

  def test_get_template_data__still_preparing(self):
    """If a gate has no votes, it should be PREPARING."""
    gate_1 = Gate(feature_id=1, state=Vote.NA, gate_type=1, stage_id=11)
    gate_1.put()

    actual = self.handler.get_template_data()

    self.assertEqual(actual, '1 Gate entities updated.')
    revised_gate_1 = Gate.get_by_id(gate_1.key.integer_id())
    self.assertEqual(revised_gate_1.state, Gate.PREPARING)

  def test_get_template_data__was_approved(self):
    """If a gate got the needed approval votes, it shuold be approved."""
    gate_1 = Gate(feature_id=1, state=Gate.PREPARING, gate_type=1, stage_id=11)
    gate_1.put()
    vote_1_1 = Vote(
        feature_id=1, gate_id=gate_1.key.integer_id(),
        state=Vote.APPROVED, set_by='three@example.com',
        set_on=datetime.now())
    vote_1_1.put()

    actual = self.handler.get_template_data()

    self.assertEqual(actual, '1 Gate entities updated.')
    revised_gate_1 = Gate.get_by_id(gate_1.key.integer_id())
    self.assertEqual(revised_gate_1.state, Vote.APPROVED)


class AssociateOTsTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = FeatureEntry(
        id=123,
        name='feature a', summary='sum', category=1,
        owner_emails=['feature_owner@example.com'])
    self.feature_1.put()
    self.feature_2 = FeatureEntry(
        id=456,
        name='feature b', summary='sum', category=1,
        owner_emails=['feature_owner@example.com'])
    self.feature_2.put()

    self.feature_3 = FeatureEntry(
        id=789,
        name='feature c', summary='sum', category=1,
        owner_emails=['feature_owner@example.com'])
    self.feature_3.put()

    self.feature_4 = FeatureEntry(
        id=890,
        name='feature d', summary='sum', category=1,
        owner_emails=['feature_owner4@example.com'])
    self.feature_4.put()

    self.ot_stage_1 = Stage(id=321, feature_id=123, stage_type=150)
    self.ot_stage_1.put()

    self.ot_stage_2 = Stage(
        id=654, feature_id=456, stage_type=150, origin_trial_id='1')
    self.ot_stage_2.put()

    self.ot_stage_3 = Stage(
        id=987, feature_id=789, stage_type=150, origin_trial_id='-12395825')
    self.ot_stage_3.put()

    self.ot_stage_4 = Stage(id=1002, feature_id=789, stage_type=150)
    self.ot_stage_4.put()

    self.ot_stage_5 = Stage(
      id=1003, feature_id=890, stage_type=150, origin_trial_id='100020301')
    self.ot_stage_5.put()

    self.extension_stage_1 = Stage(
        feature_id=456,
        stage_type=151,
        ot_stage_id=654,
        ot_action_requested=True,
        milestones=MilestoneSet(desktop_last=126))
    self.extension_stage_1.put()

    self.trials_list_return_value =   [{
        'id': '4199606652522987521',
        'display_name': 'Sample trial',
        'description': 'Another origin trial',
        'origin_trial_feature_name': 'ChromiumTrialName',
        'enabled': True,
        'status': 'ACTIVE',
        'chromestatus_url': 'https://chromestatus.com/feature/123',
        'start_milestone': '97',
        'end_milestone': '110',
        'original_end_milestone': '100',
        'end_time': '2020-11-10T23:59:59Z',
        'documentation_url': 'https://example.com/docs',
        'feedback_url': 'https://example.com/feedback',
        'intent_to_experiment_url': 'https://example.com/experiment',
        'trial_extensions': [
          {
            'endMilestone': '110',
            'endTime': '2020-11-10T23:59:59Z',
            'extensionIntentUrl': 'https://example.com/extension'
          }
        ],
        'type': 'DEPRECATION',
        'allow_third_party_origins': True
      },
      {
        'id': '1',
        'display_name': 'Sample trial 2',
        'description': 'Another origin trial 2',
        'origin_trial_feature_name': 'ChromiumTrialName2',
        'enabled': True,
        'status': 'ACTIVE',
        'chromestatus_url': 'https://chromestatus.com/feature/456',
        'start_milestone': '120',
        'end_milestone': '126',
        'original_end_milestone': '123',
        'end_time': '2020-11-10T23:59:59Z',
        'documentation_url': 'https://example.com/docs2',
        'feedback_url': 'https://example.com/feedback2',
        'intent_to_experiment_url': 'https://example.com/experiment2',
        'trial_extensions': [
          {
            'endMilestone': '126',
            'endTime': '2020-11-10T23:59:59Z',
            'extensionIntentUrl': 'https://example.com/extension2'
          }
        ],
        'type': 'ORIGIN_TRIAL',
        'allow_third_party_origins': False
      },
      {
        'id': '121240182987',
        'display_name': 'Sample trial 3',
        'description': 'Another origin trial 3',
        'origin_trial_feature_name': 'ChromiumTrialName3',
        'enabled': True,
        'status': 'ACTIVE',
        'chromestatus_url': 'https://chromestatus.com/feature/789',
        'start_milestone': '130',
        'end_milestone': '136',
        'original_end_milestone': '123',
        'end_time': '2023-11-10T23:59:59Z',
        'documentation_url': 'https://example.com/docs3',
        'feedback_url': 'https://example.com/feedback3',
        'intent_to_experiment_url': 'https://example.com/experiment3',
        'trial_extensions': [
          {
            'endMilestone': '136',
            'endTime': '2030-11-10T23:59:59Z',
            'extensionIntentUrl': 'https://example.com/extension3'
          }
        ],
        'type': 'ORIGIN_TRIAL',
        'allow_third_party_origins': True
      },
      {
        'id': '2230401243',
        'display_name': 'Sample trial 4',
        'description': 'Another origin trial 4',
        'origin_trial_feature_name': 'ChromiumTrialName4',
        'enabled': True,
        'status': 'ACTIVE',
        'chromestatus_url': 'https://chromestatus.com/feature/890',
        'start_milestone': '130',
        'end_milestone': '136',
        'original_end_milestone': '123',
        'end_time': '2023-11-10T23:59:59Z',
        'documentation_url': 'https://example.com/docs4',
        'feedback_url': 'https://example.com/feedback4',
        'intent_to_experiment_url': 'https://example.com/experiment4',
        'trial_extensions': [
          {
            'endMilestone': '136',
            'endTime': '2030-11-10T23:59:59Z',
            'extensionIntentUrl': 'https://example.com/extension4'
          }
        ],
        'type': 'ORIGIN_TRIAL',
        'allow_third_party_origins': False
      }]

    testing_config.sign_in('one@example.com', 123567890)

  def tearDown(self):
    for kind in [FeatureEntry, Stage]:
      for entity in kind.query():
        entity.key.delete()
    testing_config.sign_out()

  @mock.patch('framework.origin_trials_client.get_trials_list')
  def test_associate_ots(self, mock_ot_client):
    mock_ot_client.return_value = self.trials_list_return_value

    handler = maintenance_scripts.AssociateOTs()
    msg = handler.get_template_data()
    self.assertEqual(
        msg, '3 Stages updated with trial data.\n1 extension requests cleared.')

    # Check that fields were updated.
    ot_1 = self.ot_stage_1
    self.assertEqual(ot_1.ot_display_name, 'Sample trial')
    self.assertEqual(ot_1.origin_trial_id, '4199606652522987521')
    self.assertEqual(ot_1.ot_chromium_trial_name, 'ChromiumTrialName')
    self.assertEqual(ot_1.ot_documentation_url, 'https://example.com/docs')
    self.assertEqual(ot_1.intent_thread_url, 'https://example.com/experiment')
    self.assertTrue(ot_1.ot_has_third_party_support)
    self.assertTrue(ot_1.ot_is_deprecation_trial)
    self.assertEqual(ot_1.milestones.desktop_first, 97)
    self.assertEqual(ot_1.milestones.desktop_last, 100)
    # OT setup status should be marked as activated.
    self.assertEqual(ot_1.ot_setup_status, core_enums.OT_ACTIVATED)

    # Feature with multiple OT stages should still be recognized.
    self.assertEqual(self.ot_stage_4.origin_trial_id, '121240182987')

    # OT stage with already set ID should not have changed.
    self.assertEqual(self.ot_stage_5.origin_trial_id, '100020301')

    # Check that the extension request was cleared.
    self.assertFalse(self.extension_stage_1.ot_action_requested)


def mock_mstone_return_value_generator(*args, **kwargs):
  """Returns mock milestone info based on input."""
  if args == (100,):
    return {'mstones': [{'branch_point': '2020-01-01T00:00:00'}]}
  if args == (200,):
    return {'mstones': [{'branch_point': '2030-01-01T00:00:00'}]}
  else:
    return {'mstones': [{'branch_point': '2025-01-01T00:00:00'}]}

class CreateOriginTrialsTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = FeatureEntry(
        id=1, name='feature one', summary='sum', category=1, feature_type=0)
    self.feature_1.put()
    self.feature_2 = FeatureEntry(
        id=2, name='feature one', summary='sum', category=1, feature_type=1)
    self.feature_2.put()
    self.ot_stage_1 = Stage(
        id=100, feature_id=1, stage_type=150, ot_display_name='Example Trial',
        ot_owner_email='feature_owner@google.com',
        ot_chromium_trial_name='ExampleTrial',
        milestones=MilestoneSet(desktop_first=100, desktop_last=106),
        ot_documentation_url='https://example.com/docs',
        ot_feedback_submission_url='https://example.com/feedback',
        intent_thread_url='https://example.com/experiment',
        ot_description='OT description', ot_has_third_party_support=True,
        ot_is_deprecation_trial=False,
        ot_setup_status=core_enums.OT_READY_FOR_CREATION)
    self.ot_stage_1.put()

    self.ot_stage_2 = Stage(
        id=200, feature_id=2, stage_type=250, ot_display_name='Example Trial 2',
        ot_owner_email='feature_owner2@google.com',
        ot_chromium_trial_name='ExampleTrial2',
        milestones=MilestoneSet(desktop_first=200, desktop_last=206),
        ot_documentation_url='https://example.com/docs2',
        ot_feedback_submission_url='https://example.com/feedback2',
        intent_thread_url='https://example.com/experiment2',
        ot_description='OT description2', ot_has_third_party_support=True,
        ot_is_deprecation_trial=False,
        ot_setup_status=core_enums.OT_READY_FOR_CREATION)
    self.ot_stage_2.put()

    self.ot_stage_3 = Stage(
        id=300, feature_id=3, stage_type=450, ot_display_name='Example Trial 3',
        ot_owner_email='feature_owner2@google.com',
        ot_chromium_trial_name='ExampleTrial3',
        milestones=MilestoneSet(desktop_first=200, desktop_last=206),
        ot_documentation_url='https://example.com/docs3',
        ot_feedback_submission_url='https://example.com/feedback3',
        intent_thread_url='https://example.com/experiment3',
        ot_description='OT description3', ot_has_third_party_support=True,
        ot_is_deprecation_trial=True,
        ot_setup_status=core_enums.OT_CREATION_FAILED)
    self.ot_stage_3
    self.handler = maintenance_scripts.CreateOriginTrials()

    # Needs to be set in order to test any functionality here.
    settings.AUTOMATED_OT_CREATION = True

  def tearDown(self):
    for kind in [FeatureEntry, Stage]:
      for entity in kind.query():
        entity.key.delete()
    settings.AUTOMATED_OT_CREATION = False

  @mock.patch('framework.cloud_tasks_helpers.enqueue_task')
  @mock.patch('internals.maintenance_scripts.CreateOriginTrials._get_today')
  @mock.patch('framework.utils.get_chromium_milestone_info')
  @mock.patch('framework.origin_trials_client.activate_origin_trial')
  @mock.patch('framework.origin_trials_client.create_origin_trial')
  def test_create_trials(
      self,
      mock_create_origin_trial,
      mock_activate_origin_trial,
      mock_get_chromium_milestone_info,
      mock_today,
      mock_enqueue_task):
    """Origin trials are created and activated if it is after branch point."""

    mock_today.return_value = date(2020, 6, 1)  # 2020-06-01
    mock_get_chromium_milestone_info.side_effect = mock_mstone_return_value_generator
    mock_create_origin_trial.side_effect = [
        ('111222333', None), ('-444555666', None)]

    result = self.handler.get_template_data()
    self.assertEqual('2 trial creation request(s) processed.', result)
    # Check that different email notifications were sent.
    mock_enqueue_task.assert_has_calls([
        mock.call(
            '/tasks/email-ot-activated',
            {'stage': converters.stage_to_json_dict(self.ot_stage_1)}),
        mock.call(
            '/tasks/email-ot-creation-processed',
            {'stage': converters.stage_to_json_dict(self.ot_stage_2)})
        ], any_order=True)
    # Activation was handled, so a delayed activation date should not be set.
    self.assertIsNone(self.ot_stage_1.ot_activation_date)
    # OT 2 should have delayed activation date set.
    self.assertEqual(date(2030, 1, 1), self.ot_stage_2.ot_activation_date)
    # Setup status should be verified.
    self.assertEqual(self.ot_stage_1.ot_setup_status, core_enums.OT_ACTIVATED)
    self.assertEqual(self.ot_stage_2.ot_setup_status, core_enums.OT_CREATED)
    # New origin trial ID should be associated with the stages.ss
    self.assertIsNotNone(self.ot_stage_1.origin_trial_id)
    self.assertIsNotNone(self.ot_stage_2.origin_trial_id)
    # OT 3 had no action request, so it should not have changed.
    self.assertIsNone(self.ot_stage_3.origin_trial_id)

  @mock.patch('logging.warning')
  @mock.patch('framework.cloud_tasks_helpers.enqueue_task')
  @mock.patch('internals.maintenance_scripts.CreateOriginTrials._get_today')
  @mock.patch('framework.utils.get_chromium_milestone_info')
  @mock.patch('framework.origin_trials_client.activate_origin_trial')
  @mock.patch('framework.origin_trials_client.create_origin_trial')
  def test_create_trials__failed(
      self,
      mock_create_origin_trial,
      mock_activate_origin_trial,
      mock_get_chromium_milestone_info,
      mock_today,
      mock_enqueue_task,
      mock_logging):
    self.ot_stage_1.ot_action_requested = True
    self.ot_stage_1.put()
    self.ot_stage_2.ot_action_requested = True
    self.ot_stage_2.put()

    mock_today.return_value = date(2020, 6, 1)  # 2020-06-01
    mock_get_chromium_milestone_info.side_effect = mock_mstone_return_value_generator
    # Create trial request is failing.
    mock_create_origin_trial.side_effect = [
        (None, '503, Unavailable'),
        ('1112223334', '500, Problems happened after trial was created')]

    result = self.handler.get_template_data()
    self.assertEqual('2 trial creation request(s) processed.', result)
    # Failure notications should be sent to the OT support team.
    mock_enqueue_task.assert_has_calls([
        mock.call(
            '/tasks/email-ot-creation-request-failed',
            {'stage': converters.stage_to_json_dict(self.ot_stage_1),
             'error_text': '503, Unavailable'}),
        mock.call(
            '/tasks/email-ot-creation-request-failed',
            {'stage': converters.stage_to_json_dict(self.ot_stage_2),
             'error_text': '500, Problems happened after trial was created'})
        ], any_order=True)
    mock_logging.assert_has_calls([
        mock.call('Origin trial could not be created for stage 100'),
        mock.call('Origin trial could not be created for stage 200')],
        any_order=True)
    # Creation wasn't handled, so activation dates shouldn't be set.
    self.assertIsNone(self.ot_stage_1.ot_activation_date)
    self.assertIsNone(self.ot_stage_2.ot_activation_date)
    # Setup status should be marked as "Failed".
    self.assertEqual(self.ot_stage_1.ot_setup_status,
                     core_enums.OT_CREATION_FAILED)
    self.assertEqual(self.ot_stage_2.ot_setup_status,
                     core_enums.OT_CREATION_FAILED)
    # No OT IDs should be added to stages that had no successful actions.
    self.assertIsNone(self.ot_stage_1.origin_trial_id)
    self.assertIsNone(self.ot_stage_3.origin_trial_id)
    # OT stage 2 had an error, but a trial was successfully created.
    self.assertEqual('1112223334', self.ot_stage_2.origin_trial_id)

  @mock.patch('framework.cloud_tasks_helpers.enqueue_task')
  @mock.patch('internals.maintenance_scripts.CreateOriginTrials._get_today')
  @mock.patch('framework.utils.get_chromium_milestone_info')
  @mock.patch('framework.origin_trials_client.activate_origin_trial')
  @mock.patch('framework.origin_trials_client.create_origin_trial')
  def test_create_trials__failed_activation(
      self,
      mock_create_origin_trial,
      mock_activate_origin_trial,
      mock_get_chromium_milestone_info,
      mock_today,
      mock_enqueue_task):
    """Proper notifications are sent when trials are created but activation
    fails.
    """
    self.ot_stage_1.ot_action_requested = True
    self.ot_stage_1.put()
    self.ot_stage_2.ot_action_requested = True
    self.ot_stage_2.put()

    mock_today.return_value = date(2020, 6, 1)  # 2020-06-01
    mock_get_chromium_milestone_info.side_effect = mock_mstone_return_value_generator
    mock_create_origin_trial.side_effect = [
        ('111222333', None), ('-444555666', None)]
    # Activate trial request is failing.
    mock_activate_origin_trial.side_effect = requests.RequestException(
        mock.Mock(status=503), 'Unavailable')

    result = self.handler.get_template_data()
    self.assertEqual('2 trial creation request(s) processed.', result)
    # One trial activation should have failed, and one should be processed.
    mock_enqueue_task.assert_has_calls([
        mock.call(
            '/tasks/email-ot-activation-failed',
            {'stage': converters.stage_to_json_dict(self.ot_stage_1)}),
        mock.call(
            '/tasks/email-ot-creation-processed',
            {'stage': converters.stage_to_json_dict(self.ot_stage_2)})
        ], any_order=True)

    # Activation failed, so an activation date should have been set.
    self.assertEqual(self.ot_stage_1.ot_activation_date, date.today())
    # OT 2 should have delayed activation date set.
    self.assertEqual(date(2030, 1, 1), self.ot_stage_2.ot_activation_date)
    # OT 1 setup status should be verified, but activation failed.
    self.assertEqual(self.ot_stage_1.ot_setup_status,
                     core_enums.OT_ACTIVATION_FAILED)
    # OT 2 should have been created but not yet activated.
    self.assertEqual(self.ot_stage_2.ot_setup_status,
                     core_enums.OT_CREATED)
    # New origin trial ID should be associated with the stages.
    self.assertIsNotNone(self.ot_stage_1.origin_trial_id)
    self.assertIsNotNone(self.ot_stage_2.origin_trial_id)
    # OT 3 had no action request, so it should not have changed.
    self.assertIsNone(self.ot_stage_3.origin_trial_id)

  def test_create_trials__automation_not_active(self):
    """Cron job doesn't run when automated creation is not turned on."""
    settings.AUTOMATED_OT_CREATION = False

    result = self.handler.get_template_data()
    self.assertEqual('Automated OT creation process is not active.', result)

class ActivateOriginTrialsTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = FeatureEntry(
        id=1, name='feature one', summary='sum', category=1, feature_type=0)
    self.feature_1.put()
    self.feature_2 = FeatureEntry(
        id=2, name='feature one', summary='sum', category=1, feature_type=1)
    self.feature_2.put()
    self.ot_stage_1 = Stage(
        feature_id=1, stage_type=150, ot_display_name='Example Trial',
        origin_trial_id='111222333', ot_activation_date=date(2020, 1, 1),
        ot_setup_status=core_enums.OT_CREATED,
        ot_owner_email='feature_owner@google.com',
        ot_chromium_trial_name='ExampleTrial',
        milestones=MilestoneSet(desktop_first=100, desktop_last=106),
        ot_documentation_url='https://example.com/docs',
        ot_feedback_submission_url='https://example.com/feedback',
        intent_thread_url='https://example.com/experiment',
        ot_description='OT description', ot_has_third_party_support=True,
        ot_is_deprecation_trial=False)
    self.ot_stage_1.put()
    self.ot_stage_1_dict = converters.stage_to_json_dict(self.ot_stage_1)

    self.ot_stage_2 = Stage(
        feature_id=2, stage_type=250, ot_display_name='Example Trial 2',
        origin_trial_id='444555666', ot_activation_date=date(2020, 2, 15),
        ot_setup_status=core_enums.OT_CREATED,
        ot_owner_email='feature_owner2@google.com',
        ot_chromium_trial_name='ExampleTrial2',
        milestones=MilestoneSet(desktop_first=200, desktop_last=206),
        ot_documentation_url='https://example.com/docs2',
        ot_feedback_submission_url='https://example.com/feedback2',
        intent_thread_url='https://example.com/experiment2',
        ot_description='OT description2', ot_has_third_party_support=True,
        ot_is_deprecation_trial=False)
    self.ot_stage_2.put()
    self.ot_stage_2_dict = converters.stage_to_json_dict(self.ot_stage_2)

    self.ot_stage_3 = Stage(
        feature_id=3, stage_type=450, ot_display_name='Example Trial 3',
        origin_trial_id='777888999', ot_activation_date=date(2024, 1, 1),
        ot_setup_status=core_enums.OT_CREATED,
        ot_owner_email='feature_owner2@google.com',
        ot_chromium_trial_name='ExampleTrial3',
        milestones=MilestoneSet(desktop_first=200, desktop_last=206),
        ot_documentation_url='https://example.com/docs3',
        ot_feedback_submission_url='https://example.com/feedback3',
        intent_thread_url='https://example.com/experiment3',
        ot_description='OT description3', ot_has_third_party_support=True,
        ot_is_deprecation_trial=True)
    self.ot_stage_3
    self.handler = maintenance_scripts.ActivateOriginTrials()

    # Needs to be set in order to test any functionality here.
    settings.AUTOMATED_OT_CREATION = True

  def tearDown(self):
    for kind in [FeatureEntry, Stage]:
      for entity in kind.query():
        entity.key.delete()
    settings.AUTOMATED_OT_CREATION = False

  @mock.patch('framework.cloud_tasks_helpers.enqueue_task')
  @mock.patch('internals.maintenance_scripts.ActivateOriginTrials._get_today')
  @mock.patch('framework.origin_trials_client.activate_origin_trial')
  def test_activate_trials(
      self, mock_activate_origin_trial, mock_today, mock_enqueue_task):
    """Origin trials are activated if it is on or after the activation date."""

    mock_today.return_value = date(2020, 6, 1)  # 2020-06-01

    result = self.handler.get_template_data()
    self.assertEqual('2 activation(s) successfully processed and 0 '
                     'activation(s) failed to process.', result)
    # Activation requests should have been sent.
    mock_activate_origin_trial.assert_has_calls([
        mock.call('111222333', ), mock.call('444555666')], any_order=True)
    # Check that different email notifications were sent.
    mock_enqueue_task.assert_has_calls([
        mock.call(
            '/tasks/email-ot-activated', {'stage': self.ot_stage_1_dict}),
        mock.call(
            '/tasks/email-ot-activated', {'stage': self.ot_stage_2_dict})
        ], any_order=True)
    # Activation was handled, so a delayed activation date should not be set.
    self.assertIsNone(self.ot_stage_1.ot_activation_date)
    self.assertIsNone(self.ot_stage_2.ot_activation_date)
    # OT 3 should still have delayed activation date set in the future.
    self.assertEqual(date(2024, 1, 1), self.ot_stage_3.ot_activation_date)

  @mock.patch('framework.cloud_tasks_helpers.enqueue_task')
  @mock.patch('internals.maintenance_scripts.ActivateOriginTrials._get_today')
  @mock.patch('framework.origin_trials_client.activate_origin_trial')
  def test_activate_trials__failed(
      self, mock_activate_origin_trial, mock_today, mock_enqueue_task):
    """Proper notifications are sent if activation fails."""

    mock_today.return_value = date(2020, 6, 1)  # 2020-06-01
    # Activate trial request is failing.
    mock_activate_origin_trial.side_effect = requests.RequestException(
        mock.Mock(status=503), 'Unavailable')

    result = self.handler.get_template_data()
    self.assertEqual('0 activation(s) successfully processed and 2 '
                     'activation(s) failed to process.', result)
    # Activation requests should have been sent.
    mock_activate_origin_trial.assert_has_calls([
        mock.call('111222333', ), mock.call('444555666')], any_order=True)
    # Failure notications should be sent to the OT support team.
    mock_enqueue_task.assert_has_calls([
        mock.call(
            '/tasks/email-ot-activation-failed',
            {'stage': self.ot_stage_1_dict}),
        mock.call(
            '/tasks/email-ot-activation-failed',
            {'stage': self.ot_stage_2_dict})
        ], any_order=True)
    # Activation wasn't handled, so activation dates should still be set.
    self.assertIsNotNone(self.ot_stage_1.ot_activation_date)
    self.assertIsNotNone(self.ot_stage_2.ot_activation_date)

  def test_activate_trials__automation_not_active(self):
    """Cron job doesn't run when automated creation is not turned on."""
    settings.AUTOMATED_OT_CREATION = False

    result = self.handler.get_template_data()
    self.assertEqual('Automated OT creation process is not active.', result)


class DeleteEmptyExtensionStagesTest(testing_config.CustomTestCase):

  def setUp(self):
    # Fully filled out extension stage.
    self.extension_stage_1 = Stage(
        feature_id=1, stage_type=151, experiment_extension_reason='idk',
        milestones=MilestoneSet(desktop_last=100),
        intent_thread_url='https://example.com/extend')
    self.extension_stage_1.put()

    self.gate_1 = Gate(
        feature_id=1, stage_id=self.extension_stage_1.key.integer_id(),
        gate_type=core_enums.GATE_API_EXTEND_ORIGIN_TRIAL,
        state=Vote.NA)
    self.gate_1.put()

    # Stage with intent thread set.
    self.extension_stage_2 = Stage(
        feature_id=1, stage_type=251,
        intent_thread_url='https://example.com/extend')
    self.extension_stage_2.put()

    # Stage with end milestone set.
    self.extension_stage_3 = Stage(
        feature_id=1, stage_type=451, milestones=MilestoneSet(desktop_last=100))
    self.extension_stage_3.put()

    # Stage with extension reason set.
    self.extension_stage_4 = Stage(
        feature_id=1, stage_type=151, experiment_extension_reason='idk')
    self.extension_stage_4.put()

    # Stage with no info set.
    self.extension_stage_5 = Stage(feature_id=1, stage_type=251)
    self.extension_stage_5.put()

    self.gate_5 = Gate(
        feature_id=1, stage_id=self.extension_stage_5.key.integer_id(),
        gate_type=core_enums.GATE_API_EXTEND_ORIGIN_TRIAL,
        state=Vote.NA)
    self.gate_5.put()
    self.handler = maintenance_scripts.DeleteEmptyExtensionStages()

  def tearDown(self):
    for kind in [Gate, Stage]:
      for entity in kind.query():
        entity.key.delete()

  def test_delete_empty_extensions(self):
    """Only extension stages with no information should be deleted."""
    result = self.handler.get_template_data()
    self.assertEqual('1 empty extension stages deleted.', result)

    # The empty extension stage should be deleted.
    deleted_stage = Stage.get_by_id(self.extension_stage_5.key.integer_id())
    deleted_gate = Gate.get_by_id(self.gate_5.key.integer_id())
    self.assertIsNone(deleted_stage)
    self.assertIsNone(deleted_gate)

    # The 4 other extension stages should still exist.
    stages = Stage.query().fetch()
    gates = Gate.query().fetch()
    self.assertEqual(len(stages), 4)
    self.assertEqual(len(gates), 1)


class BackfillShippingYearTest(testing_config.CustomTestCase):

  def setUp(self):
    self.stage_1_1 = Stage(
        feature_id=11111,
        milestones=MilestoneSet())
    self.stage_2_1 = Stage(
        feature_id=22222,
        milestones=MilestoneSet(desktop_first=123))
    self.stage_2_2 = Stage(
        feature_id=22222,
        milestones=MilestoneSet(desktop_first=121, android_first=120))
    self.stage_3_1 = Stage(
        feature_id=33333,
        milestones=MilestoneSet(desktop_first=126))
    self.stage_4_1 = Stage(
        feature_id=44444,
        milestones=MilestoneSet(desktop_first=200))
    self.handler = maintenance_scripts.BackfillShippingYear()

  @mock.patch('internals.stage_helpers.get_all_shipping_stages_with_milestones')
  def test_calc_all_shipping_years__empty(self, mock_gasswm: mock.MagicMock):
    """An empty list of stages has no shipping years."""
    mock_gasswm.return_value = []
    actual = self.handler.calc_all_shipping_years()
    self.assertEqual({}, actual)

  @mock.patch('internals.stage_helpers.get_all_shipping_stages_with_milestones')
  def test_calc_all_shipping_years__some(self, mock_gasswm: mock.MagicMock):
    """We can calculate a dict of earliest milestones for a set of stages."""
    mock_gasswm.return_value = [
        self.stage_1_1, self.stage_2_1, self.stage_2_2, self.stage_3_1,
        self.stage_4_1]
    actual = self.handler.calc_all_shipping_years()
    expected = {22222: 2023, 33333: 2024, 44444: 2030}
    self.assertEqual(expected, actual)


class BackfillGateDatesTest(testing_config.CustomTestCase):

  def setUp(self):
    self.gate = Gate(
        feature_id=1, stage_id=2,
        gate_type=core_enums.GATE_API_EXTEND_ORIGIN_TRIAL,
        state=Gate.PREPARING)
    self.handler = maintenance_scripts.BackfillGateDates()

  def test_calc_resolved_on__not_resolved(self):
    """If a gate is not resolved, don't set a resolved_on date."""
    self.assertIsNone(
        self.handler.calc_resolved_on(self.gate, []))

    self.gate.state = Vote.REVIEW_REQUESTED
    self.assertIsNone(
        self.handler.calc_resolved_on(self.gate, []))

    self.gate.state = Vote.NA_REQUESTED
    self.assertIsNone(
        self.handler.calc_resolved_on(self.gate, []))

    self.gate.state = Vote.REVIEW_STARTED
    self.assertIsNone(
        self.handler.calc_resolved_on(self.gate, []))

    self.gate.state = Vote.NEEDS_WORK
    self.assertIsNone(
        self.handler.calc_resolved_on(self.gate, []))

  def test_calc_resolved_on__resolved(self):
    """If a gate was resolved, resolved_on is the last approval."""
    self.gate.state = Vote.APPROVED
    gate_id = 1234
    v1 = Vote(gate_id=gate_id, set_by='feature_owner@example.com',
              state=Vote.REVIEW_REQUESTED,
              set_on=datetime(2023, 1, 1, 12, 30, 0))
    v2 = Vote(gate_id=gate_id, set_by='reviewer_a@example.com',
              state=Vote.REVIEW_STARTED,
              set_on=datetime(2023, 1, 2, 12, 30, 0))
    v3 = Vote(gate_id=gate_id, set_by='reviewer_b@example.com',
              state=Vote.APPROVED,
              set_on=datetime(2023, 1, 3, 12, 30, 0))
    v4 = Vote(gate_id=gate_id, set_by='reviewer_c@example.com',
              state=Vote.APPROVED,
              set_on=datetime(2023, 1, 4, 12, 30, 0))
    v5 = Vote(gate_id=gate_id, set_by='reviewer_d@example.com',
              state=Vote.REVIEW_STARTED,
              set_on=datetime(2023, 1, 5, 12, 30, 0))

    self.assertEqual(
        self.handler.calc_resolved_on(self.gate, [v1, v2, v3, v4, v5]),
        v4.set_on)

  def test_calc_needs_work_started_on__not_needed(self):
    """If a gate is not NEEDS_WORK, don't set a needs_work_started_on date."""
    self.assertIsNone(
        self.handler.calc_needs_work_started_on(self.gate, []))

    self.gate.state = Vote.REVIEW_REQUESTED
    self.assertIsNone(
        self.handler.calc_needs_work_started_on(self.gate, []))

    self.gate.state = Vote.NA_REQUESTED
    self.assertIsNone(
        self.handler.calc_needs_work_started_on(self.gate, []))

    self.gate.state = Vote.REVIEW_STARTED
    self.assertIsNone(
        self.handler.calc_needs_work_started_on(self.gate, []))

    self.gate.state = Vote.APPROVED
    self.assertIsNone(
        self.handler.calc_needs_work_started_on(self.gate, []))

  def test_calc_needs_work_started_on__needed(self):
    """If a gate is NEEDS_WORK, it started on the last NEEDS_WORK vote."""
    self.gate.state = Vote.NEEDS_WORK
    gate_id = 1234
    v1 = Vote(gate_id=gate_id, set_by='feature_owner@example.com',
              state=Vote.REVIEW_REQUESTED,
              set_on=datetime(2023, 1, 1, 12, 30, 0))
    v2 = Vote(gate_id=gate_id, set_by='reviewer_a@example.com',
              state=Vote.NEEDS_WORK,
              set_on=datetime(2023, 1, 2, 12, 30, 0))
    v3 = Vote(gate_id=gate_id, set_by='reviewer_b@example.com',
              state=Vote.APPROVED,
              set_on=datetime(2023, 1, 3, 12, 30, 0))
    v4 = Vote(gate_id=gate_id, set_by='reviewer_c@example.com',
              state=Vote.NEEDS_WORK,
              set_on=datetime(2023, 1, 4, 12, 30, 0))
    v5 = Vote(gate_id=gate_id, set_by='reviewer_d@example.com',
              state=Vote.REVIEW_STARTED,
              set_on=datetime(2023, 1, 5, 12, 30, 0))

    self.assertEqual(
        self.handler.calc_needs_work_started_on(
            self.gate, [v1, v2, v3, v4, v5]),
        v4.set_on)


class FetchWebdxFeatureIdTest(testing_config.CustomTestCase):

   def setUp(self):
     self.handler = maintenance_scripts.FetchWebdxFeatureId()
     self.webdx_features = WebdxFeatures(feature_ids = ['test1'])
     self.webdx_features.put()

   def tearDown(self):
     for entity in WebdxFeatures.query():
       entity.key.delete()

   @mock.patch('webstatus_openapi.DefaultApi.list_features')
   def test_fetch_webdx_feature_ids__success(self, mock_list_features):
     feature_page_dict = {
       'data': [
         {
           'baseline': {'low_date': '2024-07-25', 'status': 'newly'},
           'browser_implementations': {
             'chrome': {'date': '2024-07-23', 'status': 'available', 'version': '127'},
             'edge': {'date': '2024-07-25', 'status': 'available', 'version': '127'},
             'firefox': {'date': '2008-06-17', 'status': 'available', 'version': '3'},
             'safari': {'date': '2023-03-27', 'status': 'available', 'version': '16.4'},
           },
           'feature_id': 'foo',
           'name': 'font-size-adjust',
           'spec': {
             'links': [
               {'link': 'https://drafts.csswg.org/css-fonts-5/#font-size-adjust-prop'}
             ]
           },
           'usage': {'chromium': {'daily': 0.011191}},
           'wpt': {
             'experimental': {
               'chrome': {'score': 0.974514563},
               'edge': {'score': 0.998786408},
               'firefox': {'score': 0.939320388},
               'safari': {'score': 0.998786408},
             },
             'stable': {
               'chrome': {'score': 0.939320388},
               'edge': {'score': 0.939320388},
               'firefox': {'score': 0.939320388},
               'safari': {'score': 0.998786408},
             },
           },
         }
       ],
       'metadata': {'next_page_token': 'eyJvZmZzZXQiOjUwfQ', 'total': 1},
     }
     feature_page_1 = FeaturePage.from_dict(feature_page_dict)
     feature_page_2 = FeaturePage.from_dict(feature_page_dict)
     feature_page_2.data[0].feature_id = 'bar'
     feature_page_2.metadata.next_page_token = ''
     mock_list_features.side_effect = [
       feature_page_1,
       feature_page_2
     ]

     result = self.handler.get_template_data()

     self.assertEqual('2 feature ids are successfully stored.', result)
     expected = WebdxFeatures.get_by_id(self.webdx_features.key.integer_id())
     self.assertEqual(len(expected.feature_ids), 2)
     self.assertEqual(expected.feature_ids[0], 'foo')
     self.assertEqual(expected.feature_ids[1], 'bar')

   @mock.patch('webstatus_openapi.DefaultApi.list_features')
   def test_fetch_webdx_feature_ids__exceptions(self, mock_list_features):
     mock_list_features.side_effect = ApiException(status=503)

     result = self.handler.get_template_data()

     self.assertEqual('Running FetchWebdxFeatureId() job failed.', result)


class SendManualOTCreatedEmailTest(testing_config.CustomTestCase):

  def setUp(self):
    self.handler = maintenance_scripts.SendManualOTCreatedEmail()
    self.feature_1 = FeatureEntry(
        id=1, name='feature a', summary='sum', category=1)
    self.feature_1.put()
    self.ot_stage = Stage(id=111,
        feature_id=1, stage_type=150, ot_owner_email='owner1@google.com',
        ot_emails=['editor1@example.com'], ot_display_name='Example trial',
        ot_activation_date=date(2020, 1, 1))
    self.ot_stage.put()
    self.ot_stage_id=self.ot_stage.key.integer_id()
    self.non_ot_stage = Stage(id=222, feature_id=1, stage_type=120)
    self.non_ot_stage.put()

  def tearDown(self):
    for kind in [Stage, FeatureEntry]:
      for entity in kind.query():
        entity.key.delete()

  @mock.patch('framework.cloud_tasks_helpers.enqueue_task')
  def test_send__valid(self, mock_enqueue):
    """An email is sent if the stage meets all requirements."""
    result = self.handler.get_template_data(stage_id=self.ot_stage_id)
    self.assertEqual('Email task enqueued', result)
    mock_enqueue.assert_called_once()

  @mock.patch('framework.cloud_tasks_helpers.enqueue_task')
  def test_send__invalid_stage(self, mock_enqueue):
    """No email is sent if the stage does not exist."""
    result = self.handler.get_template_data(stage_id=12345)
    self.assertEqual('Stage 12345 not found', result)
    mock_enqueue.assert_not_called()

  @mock.patch('framework.cloud_tasks_helpers.enqueue_task')
  def test_send__non_ot_stage(self, mock_enqueue):
    """No email is sent if the stage is not an OT stage."""
    result = self.handler.get_template_data(
        stage_id=self.non_ot_stage.key.integer_id())
    self.assertEqual('Stage 222 is not an origin trial stage', result)
    mock_enqueue.assert_not_called()

  @mock.patch('framework.cloud_tasks_helpers.enqueue_task')
  def test_send__no_contacts(self, mock_enqueue):
    """No email is sent if the stage contains no OT contacts."""
    self.ot_stage.ot_owner_email = None
    self.ot_stage.ot_emails = []
    self.ot_stage.put()
    result = self.handler.get_template_data(stage_id=self.ot_stage_id)
    self.assertEqual('Stage 111 has no OT contacts set', result)
    mock_enqueue.assert_not_called()

  @mock.patch('framework.cloud_tasks_helpers.enqueue_task')
  def test_send__no_display_name(self, mock_enqueue):
    """No email is sent if the stage does not have a display name."""
    self.ot_stage.ot_display_name = None
    self.ot_stage.put()
    result = self.handler.get_template_data(stage_id=self.ot_stage_id)
    self.assertEqual('Stage 111 does not have ot_display_name set', result)
    mock_enqueue.assert_not_called()

  @mock.patch('framework.cloud_tasks_helpers.enqueue_task')
  def test_send__no_activation_date(self, mock_enqueue):
    """No email is sent if the stage does not have a scheduled activation
    date."""
    self.ot_stage.ot_activation_date = None
    self.ot_stage.put()
    result = self.handler.get_template_data(stage_id=self.ot_stage_id)
    self.assertEqual('Stage 111 does not have ot_activation_date set', result)
    mock_enqueue.assert_not_called()


class SendManualOTActivatedEmailTest(testing_config.CustomTestCase):

  def setUp(self):
    self.handler = maintenance_scripts.SendManualOTActivatedEmail()
    self.feature_1 = FeatureEntry(
        id=1, name='feature a', summary='sum', category=1)
    self.feature_1.put()
    self.ot_stage = Stage(id=111,
        feature_id=1, stage_type=150, ot_owner_email='owner1@google.com',
        ot_emails=['editor1@example.com'], ot_display_name='Example trial')
    self.ot_stage.put()
    self.ot_stage_id=self.ot_stage.key.integer_id()
    self.non_ot_stage = Stage(id=222, feature_id=1, stage_type=120)
    self.non_ot_stage.put()

  def tearDown(self):
    for kind in [Stage, FeatureEntry]:
      for entity in kind.query():
        entity.key.delete()

  @mock.patch('framework.cloud_tasks_helpers.enqueue_task')
  def test_send__valid(self, mock_enqueue):
    """An email is sent if the stage meets all requirements."""
    result = self.handler.get_template_data(stage_id=self.ot_stage_id)
    self.assertEqual('Email task enqueued', result)
    mock_enqueue.assert_called_once()

  @mock.patch('framework.cloud_tasks_helpers.enqueue_task')
  def test_send__invalid_stage(self, mock_enqueue):
    """No email is sent if the stage does not exist."""
    result = self.handler.get_template_data(stage_id=12345)
    self.assertEqual('Stage 12345 not found', result)
    mock_enqueue.assert_not_called()

  @mock.patch('framework.cloud_tasks_helpers.enqueue_task')
  def test_send__non_ot_stage(self, mock_enqueue):
    """No email is sent if the stage is not an OT stage."""
    result = self.handler.get_template_data(
        stage_id=self.non_ot_stage.key.integer_id())
    self.assertEqual('Stage 222 is not an origin trial stage', result)
    mock_enqueue.assert_not_called()

  @mock.patch('framework.cloud_tasks_helpers.enqueue_task')
  def test_send__no_contacts(self, mock_enqueue):
    """No email is sent if the stage contains no OT contacts."""
    self.ot_stage.ot_owner_email = None
    self.ot_stage.ot_emails = []
    self.ot_stage.put()
    result = self.handler.get_template_data(stage_id=self.ot_stage_id)
    self.assertEqual('Stage 111 has no OT contacts set', result)
    mock_enqueue.assert_not_called()

  @mock.patch('framework.cloud_tasks_helpers.enqueue_task')
  def test_send__no_display_name(self, mock_enqueue):
    """No email is sent if the stage does not have a display name."""
    self.ot_stage.ot_display_name = None
    self.ot_stage.put()
    result = self.handler.get_template_data(stage_id=self.ot_stage_id)
    self.assertEqual('Stage 111 does not have ot_display_name set', result)
    mock_enqueue.assert_not_called()


class GenerateReviewActivityFileTest(testing_config.CustomTestCase):
  def setUp(self):
    self.maxDiff = None
    self.handler = maintenance_scripts.GenerateReviewActivityFile()

    self.gate_1 = Gate(id=11, feature_id=1, stage_id=100,
                       gate_type=4, # API Owners.
                       state=Vote.NA)
    self.gate_1.put()

    self.gate_2 = Gate(id=12, feature_id=2, stage_id=200,
                       gate_type=32, # Privacy team.
                       state=Vote.NA)
    self.gate_2.put()

    self.activity_1 = Activity(
      feature_id=1, gate_id=11, author='user1@example.com',
      created=datetime(2020, 1, 1, 11), content='test comment', amendments=[])
    self.activity_1.put()

    self.activity_2 = Activity(
      feature_id=1, gate_id=11, created=datetime(2020, 1, 2, 9),
      author='user1@example.com', content=None,
      amendments=[Amendment(
          field_name='review_status', old_value='na', new_value='no_response')
      ])
    self.activity_2.put()

    self.activity_3 = Activity(
      feature_id=1, gate_id=11, author='user2@example.com',
      created=datetime(2020, 1, 3, 8), content='test "comment" 2', amendments=[])
    self.activity_3.put()

    self.activity_4 = Activity(
      feature_id=1, gate_id=11, created=datetime(2020, 1, 4, 12),
      author='user1@example.com', content=None,
      amendments=[Amendment(
          field_name='review_status', old_value='na', new_value='needs_work')
      ])
    self.activity_4.put()

    # Deleted comment.
    self.activity_5 = Activity(
      feature_id=1, gate_id=11, author='user2@example.com',
      created=datetime(2020, 1, 11, 8), content='test comment 3', amendments=[],
      deleted_by='user2@example.com')
    self.activity_5.put()

    self.activity_6 = Activity(
      feature_id=1, gate_id=11, created=datetime(2020, 1, 6, 12),
      author='user2@example.com', content=None,
      amendments=[Amendment(
          field_name='review_status', old_value='needs_work',
          new_value='approved')
      ])
    self.activity_6.put()

    # Comment with no gate ID.
    self.activity_7 = Activity(
      feature_id=2, gate_id=None, author='user3@example.com',
      created=datetime(2020, 1, 10, 8), content='test comment 4', amendments=[])
    self.activity_7.put()

    self.activity_8 = Activity(
      feature_id=2, gate_id=12, author='user3@example.com',
      created=datetime(2020, 1, 11, 9), content=None,
      amendments=[Amendment(
          field_name='review_status', old_value='needs_work',
          new_value='approved')
      ])
    self.activity_8.put()

    self.activity_9 = Activity(
      feature_id=2, gate_id=12, author='user4@example.com',
      created=datetime(2020, 1, 12, 10), content=None,
      amendments=[Amendment(
          field_name='review_assignee', old_value='',
          new_value='user3@example.com')
      ])
    self.activity_9.put()

    self.activity_10 = Activity(
      feature_id=2, gate_id=12, author='user3@example.com',
      created=datetime(2020, 1, 15, 8), content='test comment 5', amendments=[])
    self.activity_10.put()

    # Activity whose gate doesn't exist.
    self.activity_11 = Activity(feature_id=2, gate_id=13, author='user4@example.com',
      created=datetime(2020, 1, 14, 8), content='test comment 5', amendments=[])
    self.activity_11.put()

  def tearDown(self):
    for kind in [Activity]:
      for entity in kind.query():
        entity.key.delete()

  @mock.patch('logging.warning')
  def test_generate_new_activities__all(self, mock_warning):
    """Generates CSV in the expected shape and format."""
    csv_rows = self.handler._generate_new_activities(datetime(1970, 1, 1), datetime.now())
    expected_rows = [
      [
        'http://127.0.0.1:7777/feature/1',
        'API Owners',
        'comment',
        '2020-01-01T11:00:00',
        '',
        '',
        'user1@example.com',
        'test comment',
        'chromestatus'
      ],
      [
        'http://127.0.0.1:7777/feature/1',
        'API Owners',
        'review_status',
        '2020-01-02T09:00:00',
        'PENDING_REVIEW',
        '',
        'user1@example.com',
        '',
        'chromestatus'
      ],
      [
        'http://127.0.0.1:7777/feature/1',
        'API Owners',
        'comment',
        '2020-01-03T08:00:00',
        '',
        '',
        'user2@example.com',
        'test "comment" 2',
        'chromestatus'
      ],
      [
        'http://127.0.0.1:7777/feature/1',
        'API Owners',
        'review_status',
        '2020-01-04T12:00:00',
        'NEEDS_WORK',
        '',
        'user1@example.com',
        '',
        'chromestatus'],
      [
        'http://127.0.0.1:7777/feature/1',
        'API Owners',
        'review_status',
        '2020-01-06T12:00:00',
        'APPROVED',
        '',
        'user2@example.com',
        '',
        'chromestatus'
      ],
      [
        'http://127.0.0.1:7777/feature/2',
        'Privacy',
        'review_status',
        '2020-01-11T09:00:00',
        'APPROVED',
        '',
        'user3@example.com',
        '',
        'chromestatus'
      ],
      [
        'http://127.0.0.1:7777/feature/2',
        'Privacy',
        'review_assignee',
        '2020-01-12T10:00:00',
        '',
        'user3@example.com',
        'user4@example.com',
        '',
        'chromestatus'
      ],
      [
        'http://127.0.0.1:7777/feature/2',
        'Privacy',
        'comment',
        '2020-01-15T08:00:00',
        '',
        '',
        'user3@example.com',
        'test comment 5',
        'chromestatus'
      ],
    ]
    self.assertEqual(expected_rows, csv_rows)

  def test_generate_new_activities__subset(self):
    """Generates a subset of rows based on the given timestamps."""
    csv_rows = self.handler._generate_new_activities(
        datetime(2020, 1, 4), datetime(2020, 1, 7))
    expected_rows = [
      [
        'http://127.0.0.1:7777/feature/1',
        'API Owners',
        'review_status',
        '2020-01-04T12:00:00',
        'NEEDS_WORK',
        '',
        'user1@example.com',
        '',
        'chromestatus'],
      [
        'http://127.0.0.1:7777/feature/1',
        'API Owners',
        'review_status',
        '2020-01-06T12:00:00',
        'APPROVED',
        '',
        'user2@example.com',
        '',
        'chromestatus'
      ],
    ]
    self.assertEqual(expected_rows, csv_rows)


class GenerateStaleFeaturesFileTest(testing_config.CustomTestCase):
  """Tests for the GenerateStaleFeaturesFile handler."""

  def setUp(self):
    self.maxDiff = None
    self.handler = maintenance_scripts.GenerateStaleFeaturesFile()
    self.current_milestone = 125

    now = datetime.now()
    self.recently = now - timedelta(days=15)
    self.long_ago = now - timedelta(days=45)

    # Feature 1: Stale (old 'accurate_as_of') AND notifications >= 1.
    # Has matching shipping milestone.
    # Should be INCLUDED.
    self.feature_1 = FeatureEntry(
        id=1, name='Stale Feature 1', summary='summary', category=1,
        feature_type=0,
        owner_emails=['owner1@example.com'], accurate_as_of=self.long_ago,
        outstanding_notifications=5)
    self.feature_1.put()
    self.stage_1 = Stage(
        id=101, feature_id=1, stage_type=160,
        milestones=MilestoneSet(desktop_first=self.current_milestone))
    self.stage_1.put()

    # Feature 2: Stale (None 'accurate_as_of'), but notifications = 0.
    # Has matching shipping milestone.
    # Should be EXCLUDED (due to outstanding_notifications < 1).
    self.feature_2 = FeatureEntry(
        id=2, name='Stale Feature 2 (Zero notifications)', summary='summary', category=1,
        feature_type=core_enums.FEATURE_TYPE_INCUBATE_ID,
        owner_emails=['owner2@example.com', 'owner2.2@example.com'],
        accurate_as_of=None, outstanding_notifications=0) # <-- Now an exclusion case
    self.feature_2.put()
    self.stage_2 = Stage(
        id=102, feature_id=2, stage_type=160,
        milestones=MilestoneSet(android_first=self.current_milestone))
    self.stage_2.put()

    # Feature 3: Not stale ('accurate_as_of' is recent).
    # Has notifications and matching milestone.
    # Should be EXCLUDED (due to accurate_as_of).
    self.feature_3 = FeatureEntry(
        id=3, name='Fresh Feature', summary='summary', category=1,
        feature_type=0,
        owner_emails=['owner3@example.com'], accurate_as_of=self.recently,
        outstanding_notifications=5) # Added for clarity
    self.feature_3.put()
    self.stage_3 = Stage(
        id=103, feature_id=3, stage_type=160,
        milestones=MilestoneSet(desktop_first=self.current_milestone))
    self.stage_3.put()

    # Feature 4: Stale, has notifications, but milestone is not current.
    # Should be EXCLUDED (due to milestone).
    self.feature_4 = FeatureEntry(
        id=4, name='Stale Feature Wrong Milestone', summary='summary', category=1,
        feature_type=1,
        owner_emails=['owner4@example.com'], accurate_as_of=self.long_ago,
        outstanding_notifications=5) # Added for clarity
    self.feature_4.put()
    self.stage_4 = Stage(
        id=104, feature_id=4, stage_type=260,
        milestones=MilestoneSet(desktop_first=self.current_milestone + 1))
    self.stage_4.put()

    # Feature 5: Stale, has notifications, but has no shipping stage.
    # Should be EXCLUDED (due to no stage).
    self.feature_5 = FeatureEntry(
        id=5, name='Stale Feature No Shipping Stage', summary='summary', category=1,
        feature_type=0,
        owner_emails=['owner5@example.com'], accurate_as_of=self.long_ago,
        outstanding_notifications=5) # Added for clarity
    self.feature_5.put()

    # Feature 6: Stale, has notifications. Stage type is not the
    # feature's shipping type (160), but it IS STAGE_ENT_ROLLOUT (mocked to 110).
    # Should be INCLUDED (due to new OR condition).
    self.feature_6 = FeatureEntry(
        id=6, name='Stale Feature Non-Shipping Stage', summary='summary', category=1,
        feature_type=core_enums.FEATURE_TYPE_INCUBATE_ID,
        owner_emails=['owner6@example.com'], accurate_as_of=self.long_ago,
        outstanding_notifications=5)
    self.feature_6.put()
    self.stage_6 = Stage(
        id=106, feature_id=6, stage_type=1061,
        milestones=MilestoneSet(desktop_first=self.current_milestone))
    self.stage_6.put()

    # Feature 7: Stale (None 'accurate_as_of') AND notifications = 1 (boundary).
    # Has matching shipping milestone.
    # Should be INCLUDED.
    self.feature_7 = FeatureEntry(
        id=7, name='Stale Feature 7 (None date, 1 notification)', summary='summary', category=1,
        feature_type=core_enums.FEATURE_TYPE_INCUBATE_ID,
        owner_emails=['owner7@example.com'],
        accurate_as_of=None, outstanding_notifications=1)
    self.feature_7.put()
    self.stage_7 = Stage(
        id=107, feature_id=7, stage_type=160,
        milestones=MilestoneSet(ios_first=self.current_milestone))
    self.stage_7.put()

  def tearDown(self):
    for kind in [FeatureEntry, Stage]:
      for entity in kind.query():
        entity.key.delete()

  @mock.patch('internals.maintenance_scripts.datetime')
  def test_gather_stale_features(self, mock_datetime):
    """Should return only stale features with a current shipping milestone."""
    # Freeze time to make the "one month ago" calculation deterministic.
    mock_datetime.now.return_value = datetime.now()
    mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

    stale_features = self.handler._gather_stale_features(self.current_milestone)

    self.assertEqual(len(stale_features), 3)

    feature_ids = {f.key.integer_id() for f in stale_features}
    expected_ids = {
        self.feature_1.key.integer_id(),
        self.feature_6.key.integer_id(),
        self.feature_7.key.integer_id()
    }
    self.assertEqual(feature_ids, expected_ids)

  def test_generate_rows(self):
    """Should format feature data into correct feature and owner CSV rows."""
    features_to_process = [self.feature_1, self.feature_7, self.feature_2]
    feature_rows, owner_rows = self.handler._generate_rows(features_to_process, self.current_milestone)

    expected_feature_rows = [
        [
            '1',
            str(self.current_milestone),
            'Stale Feature 1',
            f'{settings.SITE_URL}feature/1',
            self.long_ago.strftime(self.handler.DATE_FORMAT),
            '5'
        ],
        [
            '7',
            str(self.current_milestone),
            'Stale Feature 7 (None date, 1 notification)',
            f'{settings.SITE_URL}feature/7',
            '',
            '1'
        ],
        [
            '2',
            str(self.current_milestone),
            'Stale Feature 2 (Zero notifications)',
            f'{settings.SITE_URL}feature/2',
            '',
            '0'
        ]
    ]
    expected_owner_rows = [
        ['1', 'owner1@example.com'],
        ['7', 'owner7@example.com'],
        ['2', 'owner2@example.com'],
        ['2', 'owner2.2@example.com'],
    ]

    self.assertEqual(expected_feature_rows, feature_rows)
    self.assertCountEqual(expected_owner_rows, owner_rows)

  def test_write_csv(self):
    """Should write the correct headers and rows to two GCS blobs."""
    mock_bucket = mock.MagicMock()
    mock_feature_blob = mock.MagicMock()
    mock_owner_blob = mock.MagicMock()

    # Use side_effect to return the correct blob mock based on the filename
    def blob_switcher(blob_name):
      if blob_name == 'chromestatus-stale-features.csv':
        return mock_feature_blob
      if blob_name == 'chromestatus-stale-feature-owners.csv':
        return mock_owner_blob
      return mock.MagicMock()
    mock_bucket.blob.side_effect = blob_switcher

    feature_rows = [
        ['1', '125', 'Feat A', 'url_a', '2025-10-01T00:00:00', '1'],
        ['2', '125', 'Feat B', 'url_b', '', '3']
    ]
    owner_rows = [
        ['1', 'a@example.com'],
        ['2', 'b@example.com'],
        ['2', 'b2@example.com']
    ]

    self.handler._write_csv(mock_bucket, feature_rows, owner_rows)

    # Check that .blob() was called for both files
    expected_calls = [
        mock.call('chromestatus-stale-features.csv'),
        mock.call('chromestatus-stale-feature-owners.csv')
    ]
    mock_bucket.blob.assert_has_calls(expected_calls)
    self.assertEqual(mock_bucket.blob.call_count, 2)

    feature_upload_call = mock_feature_blob.upload_from_string.call_args
    self.assertIsNotNone(feature_upload_call)
    uploaded_string = feature_upload_call[0][0]
    string_io = StringIO(uploaded_string)
    reader = csv.reader(string_io, lineterminator='\n')

    header = next(reader)
    self.assertEqual(header, [
        'id', 'current_milestone', 'name', 'chromestatus_url',
        'accurate_as_of', 'outstanding_notifications'
    ])
    self.assertEqual(list(reader), feature_rows)

    owner_upload_call = mock_owner_blob.upload_from_string.call_args
    self.assertIsNotNone(owner_upload_call)
    uploaded_string = owner_upload_call[0][0]
    string_io = StringIO(uploaded_string)
    reader = csv.reader(string_io, lineterminator='\n')

    header = next(reader)
    self.assertEqual(header, ['id', 'owner_email'])
    self.assertEqual(list(reader), owner_rows)


  @mock.patch('framework.utils.get_current_milestone_info')
  @mock.patch('google.cloud.storage.Client')
  @mock.patch('framework.basehandlers.FlaskHandler.require_cron_header')
  @mock.patch('internals.maintenance_scripts.datetime')
  def test_get_template_data__end_to_end(
      self, mock_datetime, mock_require_cron, mock_storage_client, mock_get_milestone):
    """Should correctly orchestrate the entire file generation process for both files."""
    mock_datetime.now.return_value = datetime.now()
    mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
    mock_get_milestone.return_value = {'mstone': str(self.current_milestone)}

    mock_bucket = mock.MagicMock()
    mock_storage_client.return_value.bucket.return_value = mock_bucket

    mock_feature_blob = mock.MagicMock()
    mock_owner_blob = mock.MagicMock()

    mock_bucket.blob.side_effect = [mock_feature_blob, mock_owner_blob]

    result = self.handler.get_template_data()

    mock_require_cron.assert_called_once()
    mock_storage_client.return_value.bucket.assert_called_once_with(
        settings.FILES_BUCKET)

    # Check that .blob() was called for both files in order
    expected_calls = [
        mock.call('chromestatus-stale-features.csv'),
        mock.call('chromestatus-stale-feature-owners.csv')
    ]
    mock_bucket.blob.assert_has_calls(expected_calls)

    # Verify Feature CSV content
    feature_upload_call = mock_feature_blob.upload_from_string.call_args[0][0]
    feature_reader = list(csv.reader(StringIO(feature_upload_call), lineterminator='\n'))

    self.assertEqual(len(feature_reader), 4)
    self.assertEqual(feature_reader[0], [
        'id', 'current_milestone', 'name', 'chromestatus_url',
        'accurate_as_of', 'outstanding_notifications'
    ])
    feature_ids = {row[0] for row in feature_reader[1:]}
    self.assertEqual(feature_ids, {'1', '6', '7'})

    # Verify Owner CSV content
    owner_upload_call = mock_owner_blob.upload_from_string.call_args[0][0]
    owner_reader = list(csv.reader(StringIO(owner_upload_call), lineterminator='\n'))

    self.assertEqual(len(owner_reader), 4)
    self.assertEqual(owner_reader[0], ['id', 'owner_email'])
    expected_owners = [
        [str(self.feature_1.key.integer_id()), self.feature_1.owner_emails[0]],
        [str(self.feature_6.key.integer_id()), self.feature_6.owner_emails[0]],
        [str(self.feature_7.key.integer_id()), self.feature_7.owner_emails[0]],
    ]
    self.assertCountEqual(owner_reader[1:], expected_owners)

    self.assertEqual(result, '3 rows added to chromestatus-stale-features.csv')


class ResetOutstandingNotificationsTest(testing_config.CustomTestCase):
  """Tests for the ResetOutstandingNotifications handler."""

  def setUp(self):
    """Set up test data before each test."""
    self.handler = maintenance_scripts.ResetOutstandingNotifications()

    # Feature 1: Has multiple outstanding notifications.
    # Should be RESET to 0.
    self.feature_to_reset = FeatureEntry(
        id=101, name='Feature to Reset', summary='summary', category=1,
        outstanding_notifications=5)
    self.feature_to_reset.put()

    # Feature 2: Has exactly one outstanding notification (boundary condition).
    # Should be RESET to 0.
    self.feature_at_boundary = FeatureEntry(
        id=102, name='Feature at Boundary', summary='summary', category=1,
        outstanding_notifications=1)
    self.feature_at_boundary.put()

    # Feature 3: Has zero outstanding notifications.
    # Should be IGNORED and remain 0.
    self.feature_to_ignore_zero = FeatureEntry(
        id=103, name='Feature to Ignore (Zero)', summary='summary', category=1,
        outstanding_notifications=0)
    self.feature_to_ignore_zero.put()

    # Feature 4: Has a null (None) value for notifications.
    # Should be IGNORED and remain None.
    self.feature_to_ignore_none = FeatureEntry(
        id=104, name='Feature to Ignore (None)', summary='summary', category=1,
        outstanding_notifications=None)
    self.feature_to_ignore_none.put()

  def tearDown(self):
    """Clean up test data after each test."""
    for entity in FeatureEntry.query():
      entity.key.delete()

  @mock.patch('framework.basehandlers.FlaskHandler.require_cron_header')
  def test_get_template_data__resets_counters_and_ignores_others(
      self, mock_require_cron):
    """Should reset counters >= 1, ignore others, and return correct summary."""
    result = self.handler.get_template_data()

    mock_require_cron.assert_called_once()

    self.assertEqual('2 reverted to 0 outstanding notifications.', result)

    updated_feature_1 = self.feature_to_reset.key.get()
    self.assertEqual(0, updated_feature_1.outstanding_notifications)

    updated_feature_2 = self.feature_at_boundary.key.get()
    self.assertEqual(0, updated_feature_2.outstanding_notifications)

    ignored_feature_1 = self.feature_to_ignore_zero.key.get()
    self.assertEqual(0, ignored_feature_1.outstanding_notifications)

    # This feature should have been untouched and its counter should still be None.
    ignored_feature_2 = self.feature_to_ignore_none.key.get()
    self.assertIsNone(ignored_feature_2.outstanding_notifications)


class ResetStaleShippingMilestonesTest(testing_config.CustomTestCase):
  """Tests for the ResetStaleShippingMilestones handler."""

  def setUp(self):
    self.handler = maintenance_scripts.ResetStaleShippingMilestones()

    # 1. Stale feature (notifications=5) with shipping milestones.
    #    EXPECTED: Feature notifications reset to 0, Stage milestones reset to None.
    #    Activity created with 2 amendments.
    self.feature_stale_reset = FeatureEntry(
        id=201, name='Stale w/ Milestones', summary='summary', category=1,
        feature_type=0,
        outstanding_notifications=5)
    self.milestones_1 = MilestoneSet(desktop_first=141, android_first=456)
    self.stage_stale_reset = Stage(
        id=301, feature_id=201, stage_type=160,
        milestones=self.milestones_1)

    # 2. Stale feature (notifications=4, boundary) with shipping milestones.
    #    EXPECTED: Feature notifications reset to 0, Stage milestones reset to None.
    #    Activity created with 1 amendment.
    self.feature_boundary_reset = FeatureEntry(
        id=202, name='Stale Boundary w/ Milestones', summary='summary', category=1,
        feature_type=0,
        outstanding_notifications=4)
    self.milestones_2 = MilestoneSet(desktop_first=789)
    self.stage_boundary_reset = Stage(
        id=302, feature_id=202, stage_type=160,
        milestones=self.milestones_2)

    # 3. Stale feature (notifications=5) with NO milestones (milestones=None).
    #    EXPECTED: Feature notifications reset to 0. Stage is untouched.
    #    No Activity created.
    self.feature_stale_no_milestones = FeatureEntry(
        id=203, name='Stale w/ No Milestones', summary='summary', category=1,
        feature_type=2,
        outstanding_notifications=5)
    self.stage_stale_no_milestones = Stage(
        id=303, feature_id=203, stage_type=260,
        milestones=None)

    # 4. Stale feature (notifications=5) with NO shipping stage.
    #    (It has a *non-shipping* stage, which should be ignored).
    #    EXPECTED: Feature notifications reset to 0. Non-shipping stage untouched.
    #    No Activity created.
    self.feature_stale_no_stage = FeatureEntry(
        id=204, name='Stale w/ No Shipping Stage', summary='summary', category=1,
        feature_type=0,
        outstanding_notifications=5)
    self.milestones_3 = MilestoneSet(desktop_first=111)
    self.stage_stale_wrong_type = Stage(
        id=304, feature_id=204, stage_type=150,
        milestones=self.milestones_3)

    # 5. Non-stale feature (notifications=3) with milestones.
    #    EXPECTED: IGNORED. Feature and Stage untouched.
    self.feature_not_stale = FeatureEntry(
        id=205, name='Not Stale w/ Milestones', summary='summary', category=1,
        feature_type=3,
        outstanding_notifications=3)
    self.milestones_4 = MilestoneSet(desktop_first=222)
    self.stage_not_stale = Stage(
        id=305, feature_id=205, stage_type=460,
        milestones=self.milestones_4)

    # 6. Non-stale feature (notifications=0) with milestones.
    #    EXPECTED: IGNORED. Feature and Stage untouched.
    self.feature_zero = FeatureEntry(
        id=206, name='Zero Notifications w/ Milestones', summary='summary', category=1,
        feature_type=0,
        outstanding_notifications=0)
    self.milestones_5 = MilestoneSet(desktop_first=333)
    self.stage_zero = Stage(
        id=306, feature_id=206, stage_type=160,
        milestones=self.milestones_5)

    ndb.put_multi([
        self.feature_stale_reset, self.stage_stale_reset,
        self.feature_boundary_reset, self.stage_boundary_reset,
        self.feature_stale_no_milestones, self.stage_stale_no_milestones,
        self.feature_stale_no_stage, self.stage_stale_wrong_type,
        self.feature_not_stale, self.stage_not_stale,
        self.feature_zero, self.stage_zero
    ])

  def tearDown(self):
    for kind in [Stage, FeatureEntry, Activity]:
      for entity in kind.query():
        entity.key.delete()

  @mock.patch('framework.basehandlers.FlaskHandler.require_cron_header')
  def test_get_template_data__resets_stale_features_and_milestones(
      self, mock_require_cron):
    """Should reset counters and milestones for features >= 4, ignore others."""
    result = self.handler.get_template_data()

    mock_require_cron.assert_called_once()

    # Features 201, 202, 203, and 204 should be reset.
    self.assertEqual('4 features with shipping milestones reset.', result)

    # 1. Check Stale feature (notifications=5) w/ milestones
    self.assertEqual(0, self.feature_stale_reset.outstanding_notifications)
    self.assertIsNone(self.stage_stale_reset.milestones.desktop_first)
    self.assertIsNone(self.stage_stale_reset.milestones.android_first)
    self.assertIsNone(self.stage_stale_reset.milestones.ios_first)
    self.assertIsNone(self.stage_stale_reset.milestones.webview_first)

    # 2. Check Stale feature (notifications=4, boundary) w/ milestones
    self.assertEqual(0, self.feature_boundary_reset.outstanding_notifications)
    self.assertIsNone(self.stage_boundary_reset.milestones.desktop_first)

    # 3. Check Stale feature (notifications=5) w/ NO milestones
    self.assertEqual(0, self.feature_stale_no_milestones.outstanding_notifications)
    self.assertIsNone(self.stage_stale_no_milestones.milestones)

    # 4. Check Stale feature (notifications=5) w/ NO shipping stage
    self.assertEqual(0, self.feature_stale_no_stage.outstanding_notifications)
    self.assertEqual(111, self.stage_stale_wrong_type.milestones.desktop_first)

    # 5. Check Non-stale feature (notifications=3)  is ignored.
    self.assertEqual(3, self.feature_not_stale.outstanding_notifications)
    self.assertEqual(222, self.stage_not_stale.milestones.desktop_first)

    # 6. Check Non-stale feature (notifications=0) is ignored
    self.assertEqual(0, self.feature_zero.outstanding_notifications)
    self.assertEqual(333, self.stage_zero.milestones.desktop_first)

    # Check that Activity and Amendment entities were created
    activities = Activity.query().fetch()
    # Only features 201 and 202 should have generated an activity
    self.assertEqual(2, len(activities))

    # Check Activity for Feature 201
    act_201 = Activity.query(Activity.feature_id == 201).get()
    self.assertIsNotNone(act_201)
    self.assertEqual(
        'Shipping milestones were unset due to failure to verify accuracy.',
        act_201.content)
    # Sort amendments to have a stable test
    amends_201 = sorted(act_201.amendments, key=lambda a: a.field_name)
    self.assertEqual(2, len(amends_201))
    self.assertEqual('android_first', amends_201[0].field_name)
    self.assertEqual('456', amends_201[0].old_value)
    self.assertIsNone(amends_201[0].new_value)
    self.assertEqual('desktop_first', amends_201[1].field_name)
    self.assertEqual('141', amends_201[1].old_value)
    self.assertIsNone(amends_201[1].new_value)

    # Check Activity for Feature 202
    act_202 = Activity.query(Activity.feature_id == 202).get()
    self.assertIsNotNone(act_202)
    self.assertEqual(1, len(act_202.amendments))
    self.assertEqual('desktop_first', act_202.amendments[0].field_name)
    self.assertEqual('789', act_202.amendments[0].old_value)
    self.assertIsNone(act_202.amendments[0].new_value)
