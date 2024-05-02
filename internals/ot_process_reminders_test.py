# Copyright 2024 Google Inc.
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
from unittest import mock

from internals import ot_process_reminders
from internals.core_models import FeatureEntry, Stage


class OTProcessRemindersTest(testing_config.CustomTestCase):
  def setUp(self):
    self.feature_1 = FeatureEntry(
        feature_type=1, name='feature one', summary='sum', category=1)
    self.feature_1.put()
    self.stage_1 = Stage(
        feature_id=1, stage_type=150, ot_owner_email='ot_owner1@google.com',
        ot_emails=['contact1@example.com', 'contact2@example.com'],
        origin_trial_id='4199606652522987521')
    self.stage_1.put()
    self.stage_2 = Stage(
        feature_id=2, stage_type=150, ot_owner_email='ot_owner2@google.com',
        ot_emails=['sample_contact@example.com', 'another@example.com'],
        origin_trial_id='1')
    self.stage_2.put()
    self.mock_get_trials_list_return_value = [
      {
        'id': '4199606652522987521',
        'display_name': 'feature one',
        'description': 'Another origin trial',
        'origin_trial_feature_name': 'ChromiumTrialName',
        'enabled': True,
        'status': 'ACTIVE',
        'chromestatus_url': 'https://chromestatus.com/feature/123',
        'start_milestone': '97',
        'end_milestone': '103',
        'original_end_milestone': '100',
        'end_time': '2020-11-10T23:59:59Z',
        'documentation_url': 'https://example.com/docs',
        'feedback_url': 'https://example.com/feedback',
        'intent_to_experiment_url': 'https://example.com/experiment',
        'trial_extensions': [
          {
            'endMilestone': '110',
            'endTime': '2020-11-10T23:59:59Z',
            'extensionIntentUrl': 'https://example.com/extension',
          }
        ],
        'type': 'DEPRECATION',
        'allow_third_party_origins': True,
      },
      {
        'id': '1',
        'display_name': 'Sample trial 2',
        'description': 'Another origin trial 2',
        'origin_trial_feature_name': 'ChromiumTrialName2',
        'enabled': True,
        'status': 'ACTIVE',
        'chromestatus_url': 'https://chromestatus.com/feature/456',
        'start_milestone': '103',
        'end_milestone': '109',
        'original_end_milestone': '106',
        'end_time': '2020-11-10T23:59:59Z',
        'documentation_url': 'https://example.com/docs2',
        'feedback_url': 'https://example.com/feedback2',
        'intent_to_experiment_url': 'https://example.com/experiment2',
        'trial_extensions': [
          {
            'endMilestone': '109',
            'endTime': '2020-11-10T23:59:59Z',
            'extensionIntentUrl': 'https://example.com/extension2',
          }
        ],
        'type': 'ORIGIN_TRIAL',
        'allow_third_party_origins': False,
      },
      {
        'id': '2',
        'display_name': 'Sample trial 3',
        'description': 'Another origin trial 3',
        'origin_trial_feature_name': 'ChromiumTrialName3',
        'enabled': True,
        'status': 'ACTIVE',
        'chromestatus_url': 'https://chromestatus.com/feature/789',
        'start_milestone': '110',
        'end_milestone': '116',
        'original_end_milestone': '116',
        'end_time': '2020-11-10T23:59:59Z',
        'documentation_url': 'https://example.com/docs3',
        'feedback_url': 'https://example.com/feedback3',
        'intent_to_experiment_url': 'https://example.com/experiment3',
        'trial_extensions': [],
        'type': 'ORIGIN_TRIAL',
        'allow_third_party_origins': False,
      },
    ]
    self.maxDiff = None

  @mock.patch('framework.origin_trials_client.get_trials_list')
  def test_get_trials(self, mock_get_trials_list):
    mock_get_trials_list.return_value = self.mock_get_trials_list_return_value
    relevant_trials = ot_process_reminders.get_trials(103)
    expected_trials = {
      'starting_trials': [
        {
          'id': '1',
          'name': 'Sample trial 2',
          'start_milestone': 103,
          'end_milestone': 109,
          'contacts': [
            'sample_contact@example.com',
            'another@example.com',
            'ot_owner2@google.com',
          ],
        }
      ],
      'ending_trials': [
        {
          'id': '4199606652522987521',
          'name': 'feature one',
          'start_milestone': 97,
          'end_milestone': 103,
          'contacts': [
            'contact1@example.com',
            'contact2@example.com',
            'ot_owner1@google.com',
          ],
        }
      ],
    }

    self.assertEqual(len(relevant_trials['starting_trials']), 1)
    self.assertEqual(len(relevant_trials['ending_trials']), 1)
    starting_trial = relevant_trials['starting_trials'][0]
    ending_trial = relevant_trials['ending_trials'][0]
    self.assertEqual(starting_trial['id'],
                     expected_trials['starting_trials'][0]['id'])
    self.assertEqual(ending_trial['id'],
                     expected_trials['ending_trials'][0]['id'])
    self.assertEqual(starting_trial['name'],
                     expected_trials['starting_trials'][0]['name'])
    self.assertEqual(ending_trial['name'],
                     expected_trials['ending_trials'][0]['name'])
    self.assertEqual(set(starting_trial['contacts']),
                     set(expected_trials['starting_trials'][0]['contacts']))
    self.assertEqual(set(ending_trial['contacts']),
                     set(expected_trials['ending_trials'][0]['contacts']))
