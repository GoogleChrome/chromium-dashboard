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
from datetime import date
from unittest import mock

from api import converters
from internals import maintenance_scripts
from internals import core_enums
from internals.core_models import FeatureEntry, Stage, MilestoneSet

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
    self.ot_stage_1_dict = converters.stage_to_json_dict(self.ot_stage_1)

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
    self.ot_stage_2_dict = converters.stage_to_json_dict(self.ot_stage_2)

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

  def tearDown(self):
    for kind in [FeatureEntry, Stage]:
      for entity in kind.query():
        entity.key.delete()

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
    mock_create_origin_trial.side_effect = ['111222333', '-444555666']

    result = self.handler.get_template_data()
    self.assertEqual('2 trial creation request(s) processed.', result)
    # Check that different email notifications were sent.
    mock_enqueue_task.assert_has_calls([
        mock.call(
            '/tasks/email-ot-activated', {'stage': self.ot_stage_1_dict}),
        mock.call(
            '/tasks/email-ot-creation-processed',
            {'stage': self.ot_stage_2_dict})
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
    mock_create_origin_trial.side_effect = requests.RequestException(
        mock.Mock(status=503), 'Unavailable')

    result = self.handler.get_template_data()
    self.assertEqual('2 trial creation request(s) processed.', result)
    # Failure notications should be sent to the OT support team.
    mock_enqueue_task.assert_has_calls([
        mock.call(
            '/tasks/email-ot-creation-request-failed',
            {'stage': self.ot_stage_1_dict}),
        mock.call(
            '/tasks/email-ot-creation-request-failed',
            {'stage': self.ot_stage_2_dict})
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
    # No actions were successful, so no OT IDs should be added to stages.
    self.assertIsNone(self.ot_stage_1.origin_trial_id)
    self.assertIsNone(self.ot_stage_2.origin_trial_id)
    self.assertIsNone(self.ot_stage_3.origin_trial_id)

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
    mock_create_origin_trial.side_effect = ['111222333', '-444555666']
    # Activate trial request is failing.
    mock_activate_origin_trial.side_effect = requests.RequestException(
        mock.Mock(status=503), 'Unavailable')

    result = self.handler.get_template_data()
    self.assertEqual('2 trial creation request(s) processed.', result)
    # One trial activation should have failed, and one should be processed.
    mock_enqueue_task.assert_has_calls([
        mock.call(
            '/tasks/email-ot-activation-failed',
            {'stage': self.ot_stage_1_dict}),
        mock.call(
            '/tasks/email-ot-creation-processed',
            {'stage': self.ot_stage_2_dict})
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

  def tearDown(self):
    for kind in [FeatureEntry, Stage]:
      for entity in kind.query():
        entity.key.delete()

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
