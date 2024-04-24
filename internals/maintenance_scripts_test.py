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
from unittest import mock

from internals import maintenance_scripts
import testing_config  # Must be imported before the module under test.
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

    self.ot_stage_1 = Stage(
        id=321, feature_id=123, stage_type=150)
    self.ot_stage_1.put()

    self.ot_stage_2 = Stage(
        id=654, feature_id=456, stage_type=150, origin_trial_id='1')
    self.ot_stage_2.put()

    self.ot_stage_3 = Stage(
        id=987, feature_id=789, stage_type=150, origin_trial_id='-12395825')
    self.ot_stage_3.put()

    self.ot_stage_4 = Stage(
        id=1002, feature_id=789, stage_type=150)
    self.ot_stage_4.put()

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

    # Check that the extension request was cleared.
    self.assertFalse(self.extension_stage_1.ot_action_requested)
