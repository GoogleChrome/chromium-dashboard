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

import testing_config  # Must be imported first
import json
from unittest import mock

from internals import fetchchannels


class ChannelsAPITest(testing_config.CustomTestCase):

  @mock.patch('requests.get')
  def test_fetch_chrome_release_info__found(self, mock_requests_get):
    """We can get channel data from the chromiumdash app."""
    mock_requests_get.return_value = testing_config.Blank(
        status_code=200,
        content=json.dumps({
            'mstones': [{
                'owners': 'ignored',
                'feature_freeze': 'ignored',
                'ldaps': 'ignored',
                'everything else': 'kept',
             }],
        }))

    actual = fetchchannels.fetch_chrome_release_info(90)

    self.assertEqual(
        {'everything else': 'kept'},
        actual)

  @mock.patch('requests.get')
  def test_fetch_chrome_release_info__not_found(self, mock_requests_get):
    """If chromiumdash app does not have the data, use a placeholder."""
    mock_requests_get.return_value = testing_config.Blank(
        status_code=404, content='')

    actual = fetchchannels.fetch_chrome_release_info(91)

    self.assertEqual(
        {'stable_date': None,
         'earliest_beta': None,
         'latest_beta': None,
         'mstone': 91,
         'version': 91,
         },
        actual)

  @mock.patch('requests.get')
  def test_fetch_chrome_release_info__error(self, mock_requests_get):
    """We can get channel data from the chromiumdash app."""
    mock_requests_get.return_value = testing_config.Blank(
        status_code=200,
        content='{')

    actual = fetchchannels.fetch_chrome_release_info(90)

    self.assertEqual(
        {'stable_date': None,
         'earliest_beta': None,
         'latest_beta': None,
         'mstone': 90,
         'version': 90,
         },
        actual)
