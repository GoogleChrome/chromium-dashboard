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

from api import origin_trials_api

test_app = flask.Flask(__name__)


class FeaturesAPITestDelete(testing_config.CustomTestCase):

  mock_list_trials_json = {
    'trials': [
      {
        'displayName': 'Example Trial',
        'id': '-5269211564023480319'
      }
    ]
  }

  @mock.patch('framework.secrets.get_ot_api_key')
  @mock.patch('requests.get')
  def test_get__no_api_key(self, mock_requests_get, mock_api_key_get):
    """If no API key is available, return an empty list of trials."""
    mock_api_key_get.return_value = None
    api = origin_trials_api.OriginTrialsAPI()
    ot_list = api.do_get()

    self.assertEqual(ot_list, [])
    mock_api_key_get.assert_called_once()
    # GET request should not be executed with no API key.
    mock_requests_get.assert_not_called()

  @mock.patch('framework.secrets.get_ot_api_key')
  @mock.patch('requests.get')
  def test_get__with_api_key(self, mock_requests_get, mock_api_key_get):
    """If an API key is available, GET should return a list of trials."""
    mock_requests_get.return_value = mock.MagicMock(
        status_code=200, json=lambda : self.mock_list_trials_json)
    mock_api_key_get.return_value = 'api_key_value'
    api = origin_trials_api.OriginTrialsAPI()
    ot_list = api.do_get()

    self.assertEqual(ot_list, self.mock_list_trials_json['trials'])
    mock_api_key_get.assert_called_once()
    mock_requests_get.assert_called_once()
