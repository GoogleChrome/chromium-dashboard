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

import testing_config  # Must be imported before the module under test.

import requests
from datetime import date, datetime
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

  def tearDown(self):
    for kind in [Activity]:
      for entity in kind.query():
        entity.key.delete()

  def test_generate_csv_all(self):
    """Generates CSV in the expected shape and format."""
    csv_rows = self.handler._generate_csv(datetime(1970, 1, 1), datetime.now())
    expected_rows = [
      'http://127.0.0.1:7777/feature/1,API Owners,comment,2020-01-01T11:00:00,,,user1@example.com,"test comment",chromestatus',
      'http://127.0.0.1:7777/feature/1,API Owners,review_status,2020-01-02T09:00:00,PENDING_REVIEW,,user1@example.com,,chromestatus',
      'http://127.0.0.1:7777/feature/1,API Owners,comment,2020-01-03T08:00:00,,,user2@example.com,"test ""comment"" 2",chromestatus',
      'http://127.0.0.1:7777/feature/1,API Owners,review_status,2020-01-04T12:00:00,NEEDS_WORK,,user1@example.com,,chromestatus',
      'http://127.0.0.1:7777/feature/1,API Owners,review_status,2020-01-06T12:00:00,APPROVED,,user2@example.com,,chromestatus',
      'http://127.0.0.1:7777/feature/2,Privacy,review_status,2020-01-11T09:00:00,APPROVED,,user3@example.com,,chromestatus',
      'http://127.0.0.1:7777/feature/2,Privacy,review_assignee,2020-01-12T10:00:00,,user3@example.com,user4@example.com,,chromestatus',
      'http://127.0.0.1:7777/feature/2,Privacy,comment,2020-01-15T08:00:00,,,user3@example.com,"test comment 5",chromestatus',
    ]
    self.assertEqual(expected_rows, csv_rows)

  def test_generate_csv_subset(self):
    """Generates a subset of rows based on the given timestamps."""
    csv_rows = self.handler._generate_csv(
        datetime(2020, 1, 4), datetime(2020, 1, 7))
    expected_rows = [
      'http://127.0.0.1:7777/feature/1,API Owners,review_status,2020-01-04T12:00:00,NEEDS_WORK,,user1@example.com,,chromestatus',
      'http://127.0.0.1:7777/feature/1,API Owners,review_status,2020-01-06T12:00:00,APPROVED,,user2@example.com,,chromestatus',
    ]
    self.assertEqual(expected_rows, csv_rows)
  