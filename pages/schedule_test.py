from __future__ import division
from __future__ import print_function

# Copyright 2020 Google Inc.
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
import mock
import unittest

from pages import schedule


class ScheduleFunctionsTest(unittest.TestCase):

  @mock.patch('pages.schedule.fetch_chrome_release_info')
  @mock.patch('util.get_omaha_data')
  def test_construct_chrome_channels_details(
      self, mock_get_omaha_data, mock_fetch_chrome_release_info):
    win_data = {
        'os': 'win',
        'versions': [
            {'branch_commit': 'c83a...',
             'version': '81.0.4041.1',
             'channel': 'canary_asan'},
            {'branch_commit': '865b...',
             'version': '81.0.4041.3',
             'channel': 'canary'},
            {'branch_commit': '223c...',
             'version': '81.0.4040.5',
             'channel': 'dev'},
            {'branch_commit': '07a4...',
             'version': '80.0.3987.66',
             'channel': 'beta'},
            {'branch_commit': '1624...',
             'version': '79.0.3945.130',
             'channel': 'stable'}
        ]}
    mock_get_omaha_data.return_value = [win_data, {'os': 'other OS...'}]
    mstone_data = {
        'earliest_beta': '2020-02-13T00:00:00',
        'mstone': 'fake milestone number',
    }
    def fcri(version):
      result = mstone_data.copy()
      return result
    mock_fetch_chrome_release_info.side_effect = fcri

    actual = schedule.construct_chrome_channels_details()

    expected = {
        'canary_asan': {
            'version': 81,
            'earliest_beta': '2020-02-13T00:00:00',
            'mstone': 'fake milestone number',
            },
        'canary': {
            'version': 81,
            'earliest_beta': '2020-02-13T00:00:00',
            'mstone': 'fake milestone number',
            },
        'dev': {
            'version': 81,
            'earliest_beta': '2020-02-13T00:00:00',
            'mstone': 'fake milestone number',
            },
        'beta': {
            'version': 80,
            'earliest_beta': '2020-02-13T00:00:00',
            'mstone': 'fake milestone number',
            },
        'stable': {
            'version': 79,
            'earliest_beta': '2020-02-13T00:00:00',
            'mstone': 'fake milestone number',
          }
    }
    self.maxDiff = None
    self.assertEqual(expected, actual)
