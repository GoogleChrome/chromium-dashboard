# Copyright 2023 Google Inc.
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

from framework import origin_trials_client
from internals.core_models import MilestoneSet, Stage
import settings

test_app = flask.Flask(__name__)


class OriginTrialsClientTest(testing_config.CustomTestCase):

  def setUp(self):
    self.ot_stage = Stage(
        feature_id=1, stage_type=150, ot_display_name='Example Trial',
        milestones=MilestoneSet(desktop_first=100, desktop_last=106),
        ot_documentation_url='https://example.com/docs',
        ot_feedback_submission_url='https://example.com/feedback',
        intent_thread_url='https://example.com/experiment',
        ot_owner_email='someuser@google.com',
        ot_emails=['anotheruser@chromium.org', 'contact@microsoft.com',
                   'editor@google.com', 'someuser@google.com'],
        ot_description='OT description', ot_has_third_party_support=True,
        ot_require_approvals=True, ot_approval_buganizer_component=123456,
        ot_approval_criteria_url='https://example.com/criteria',
        ot_approval_group_email='somegroup@google.com',
        ot_approval_buganizer_custom_field_id=111111,
        ot_is_deprecation_trial=True)
    self.ot_stage.put()
    self.mock_list_trials_json = {
      'trials': [
        {
          'id': '-5269211564023480319',
          'displayName': 'Example Trial',
          'description': 'A description.',
          'originTrialFeatureName': 'ExampleTrial',
          'status': 'ACTIVE',
          'enabled': True,
          'isPublic': True,
          'chromestatusUrl': 'https://example.com/chromestatus',
          'startMilestone': '123',
          'endMilestone': '456',
          'originalEndMilestone': '450',
          'endTime': '2025-01-01T00:00:00Z',
          'feedbackUrl': 'https://example.com/feedback',
          'documentationUrl': 'https://example.com/docs',
          'intentToExperimentUrl': 'https://example.com/intent',
          'type': 'ORIGIN_TRIAL',
          'allowThirdPartyOrigins': True,
          'trialExtensions': [{}],
        },
        {
          'id': '3611886901151137793',
          'displayName': 'Non-public trial',
          'description': 'Another description.',
          'originTrialFeatureName': 'SampleTrial',
          'status': 'COMPLETE',
          'enabled': True,
          'isPublic': False,
          'chromestatusUrl': 'https://example.com/chromestatus2',
          'startMilestone': '100',
          'endMilestone': '200',
          'endTime': '2024-01-01T00:00:00Z',
        }
      ]
    }

  def tearDown(self):
    for entity in Stage.query():
      entity.key.delete()

  @mock.patch('framework.secrets.get_ot_api_key')
  @mock.patch('requests.get')
  def test_get_trials_list__no_api_key(
      self, mock_requests_get, mock_api_key_get):
    """If no API key is available, return an empty list of trials."""
    mock_api_key_get.return_value = None
    trials_list = origin_trials_client.get_trials_list()

    self.assertEqual(trials_list, [])
    mock_api_key_get.assert_called_once()
    # GET request should not be executed with no API key.
    mock_requests_get.assert_not_called()

  @mock.patch('framework.secrets.get_ot_api_key')
  @mock.patch('requests.get')
  def test_get_trials_list__with_api_key(
      self, mock_requests_get, mock_api_key_get):
    """If an API key is available, GET should return a list of trials."""
    mock_requests_get.return_value = mock.MagicMock(
        status_code=200, json=lambda : self.mock_list_trials_json)
    mock_api_key_get.return_value = 'api_key_value'

    expected = [
      {
        'id': '-5269211564023480319',
        'display_name': 'Example Trial',
        'description': 'A description.',
        'origin_trial_feature_name': 'ExampleTrial',
        'status': 'ACTIVE',
        'enabled': True,
        'chromestatus_url': 'https://example.com/chromestatus',
        'start_milestone': '123',
        'end_milestone': '456',
        'original_end_milestone': '450',
        'feedback_url': 'https://example.com/feedback',
        'documentation_url': 'https://example.com/docs',
        'intent_to_experiment_url': 'https://example.com/intent',
        'trial_extensions': [{}],
        'type': 'ORIGIN_TRIAL',
        'allow_third_party_origins': True,
        'end_time': '2025-01-01T00:00:00Z',
      },
    ]
    trials_list = origin_trials_client.get_trials_list()
    self.assertEqual(trials_list, expected)

    mock_api_key_get.assert_called_once()
    mock_requests_get.assert_called_once()

  @mock.patch('framework.secrets.get_ot_api_key')
  @mock.patch('requests.post')
  def test_extend_origin_trial__no_api_key(
      self, mock_requests_post, mock_api_key_get):
    """If no API key is available, do not send extension request."""
    mock_api_key_get.return_value = None
    origin_trials_client.extend_origin_trial(
        '1234567890', '123', 'https://example.com/intent')

    mock_api_key_get.assert_called_once()
    # POST request should not be executed with no API key.
    mock_requests_post.assert_not_called()

  @mock.patch('framework.secrets.get_ot_api_key')
  @mock.patch('framework.origin_trials_client._get_ot_access_token')
  @mock.patch('framework.origin_trials_client._get_trial_end_time')
  @mock.patch('requests.post')
  def test_extend_origin_trial__with_api_key(
      self, mock_requests_post, mock_get_trial_end_time,
      mock_get_ot_access_token, mock_api_key_get):
    """If an API key is available, POST should extend trial."""
    mock_requests_post.return_value = mock.MagicMock(
        status_code=200, json=lambda : {})
    mock_get_trial_end_time.return_value = 111222333
    mock_get_ot_access_token.return_value = mock.MagicMock('access_token')
    mock_api_key_get.return_value = 'api_key_value'

    origin_trials_client.extend_origin_trial(
        '1234567890', '123', 'https://example.com/intent')

    mock_api_key_get.assert_called_once()
    mock_get_ot_access_token.assert_called_once()
    mock_requests_post.assert_called_once()

  @mock.patch('requests.get')
  def test_get_trial_end_time(self, mock_requests_get):
    """Should return an int value based on the date from the request."""
    mock_requests_get.return_value = mock.MagicMock(
        status_code=200,
        json=lambda : {
          'mstones': [
            {'late_stable_date': '2023-04-30T00:00:00'}
          ]
        })

    return_result = origin_trials_client._get_trial_end_time(123)
    self.assertEqual(return_result, 1682812800)
    mock_requests_get.assert_called_once()

  @mock.patch('framework.secrets.get_ot_api_key')
  @mock.patch('requests.post')
  def test_create_origin_trial__no_api_key(
      self, mock_requests_post, mock_api_key_get):
    """If no API key is available, do not send creation request."""
    mock_api_key_get.return_value = None
    ot_id, error_text = origin_trials_client.create_origin_trial(self.ot_stage)

    self.assertIsNone(ot_id)
    self.assertEqual('No API key found for origin trials API', error_text)
    mock_api_key_get.assert_called_once()
    # POST request should not be executed with no API key.
    mock_requests_post.assert_not_called()

  @mock.patch('framework.secrets.get_ot_data_access_admin_group')
  @mock.patch('framework.secrets.get_ot_api_key')
  @mock.patch('framework.origin_trials_client._get_ot_access_token')
  @mock.patch('framework.origin_trials_client._get_trial_end_time')
  @mock.patch('requests.post')
  def test_create_origin_trial__with_api_key(
      self, mock_requests_post, mock_get_trial_end_time,
      mock_get_ot_access_token, mock_api_key_get, mock_get_admin_group):
    """If an API key is available, POST should create trial and return true."""
    mock_requests_post.return_value = mock.MagicMock(
        status_code=200, json=lambda : (
            {'trial': {'id': -1234567890}, 'should_retry': False}))
    mock_get_trial_end_time.return_value = 111222333
    mock_get_ot_access_token.return_value = 'access_token'
    mock_api_key_get.return_value = 'api_key_value'
    mock_get_admin_group.return_value = 'test-group-123'

    ot_id, error_text = origin_trials_client.create_origin_trial(self.ot_stage)
    self.assertEqual(ot_id, '-1234567890')
    self.assertIsNone(error_text)

    mock_api_key_get.assert_called_once()
    mock_get_ot_access_token.assert_called_once()
    # Two separate POST requests made.
    self.assertEqual(2, mock_requests_post.call_count)
    create_trial_json = mock_requests_post.call_args_list[0][1]['json']
    self.assertEqual({
          'display_name': 'Example Trial',
          'start_milestone': '100',
          'end_milestone': '106',
          'end_time': {
            'seconds': 111222333
          },
          'description': 'OT description',
          'documentation_url': 'https://example.com/docs',
          'feedback_url': 'https://example.com/feedback',
          'intent_to_experiment_url': 'https://example.com/experiment',
          'chromestatus_url': f'{settings.SITE_URL}feature/1',
          'allow_third_party_origins': True,
          'type': 'DEPRECATION',
        }, create_trial_json['trial'])
    self.assertEqual({
          'allow_public_suffix_subdomains': True,
          'approval_type': 'CUSTOM',
          'approval_buganizer_component_id': 123456,
          'approval_criteria_url': 'https://example.com/criteria',
          'approval_group_email': 'somegroup@google.com',
          'approval_buganizer_custom_field_id': 111111,
        }, create_trial_json['registration_config'])

    set_up_trial_json = mock_requests_post.call_args_list[1][1]['json']
    # Only unique @google.com emails should be sent as contacts.
    self.assertCountEqual(['someuser@google.com', 'editor@google.com'],
                          set_up_trial_json['trial_contacts'])
    self.assertEqual('test-group-123',
                     set_up_trial_json['data_access_admin_group_name'])
    self.assertEqual(-1234567890, set_up_trial_json['trial_id'])

  @mock.patch('framework.secrets.get_ot_api_key')
  @mock.patch('requests.post')
  def test_activate_origin_trial__no_api_key(
      self, mock_requests_post, mock_api_key_get):
    """If no API key is available, do not send activation request."""
    mock_api_key_get.return_value = None
    origin_trials_client.create_origin_trial(self.ot_stage)

    mock_api_key_get.assert_called_once()
    # POST request should not be executed with no API key.
    mock_requests_post.assert_not_called()

  @mock.patch('framework.secrets.get_ot_api_key')
  @mock.patch('framework.origin_trials_client._get_ot_access_token')
  @mock.patch('framework.origin_trials_client._get_trial_end_time')
  @mock.patch('requests.post')
  def test_activate_origin_trial__with_api_key(
      self, mock_requests_post, mock_get_trial_end_time,
      mock_get_ot_access_token, mock_api_key_get):
    """If an API key is available, POST should activate trial."""
    mock_requests_post.return_value = mock.MagicMock(
        status_code=200, json=lambda : {})
    mock_get_trial_end_time.return_value = 111222333
    mock_get_ot_access_token.return_value = 'access_token'
    mock_api_key_get.return_value = 'api_key_value'

    origin_trials_client.activate_origin_trial('-1234567890')

    mock_api_key_get.assert_called_once()
    mock_get_ot_access_token.assert_called_once()
    mock_requests_post.assert_called_once_with(
      f'{settings.OT_API_URL}/v1/trials/-1234567890:start',
      headers={'Authorization': 'Bearer access_token'},
      params={'key': 'api_key_value'},
      json={'id': '-1234567890'}
    )
