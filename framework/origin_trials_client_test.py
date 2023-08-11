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

test_app = flask.Flask(__name__)


class OriginTrialsClientTest(testing_config.CustomTestCase):

  mock_list_trials_json = {
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
        'endTime': '2025-01-01T00:00:00Z',
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
        'end_time': '2025-01-01T00:00:00Z',
      },
    ]
    trials_list = origin_trials_client.get_trials_list()
    self.assertEqual(trials_list, expected)

    mock_api_key_get.assert_called_once()
    mock_requests_get.assert_called_once()
