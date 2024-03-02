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
import json
import flask
from unittest import mock
import unittest

from api import channels_api

test_app = flask.Flask(__name__)

class ChannelsAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.handler = channels_api.ChannelsAPI()
    self.request_path = '/api/v0/channels'

  @mock.patch('api.channels_api.fetch_chrome_release_info')
  @mock.patch('internals.fetchchannels.get_omaha_data')
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

    actual = channels_api.construct_chrome_channels_details()

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

  @mock.patch('api.channels_api.fetch_chrome_release_info')
  @mock.patch('internals.fetchchannels.get_omaha_data')
  def test_construct_chrome_channels_details__beta_promotion(
      self, mock_get_omaha_data, mock_fetch_chrome_release_info):
    win_data = {
        'os': 'win',
        'versions': [
            {'branch_commit': '223c...',
             'version': '81.0.4040.5',
             'channel': 'dev'},
            {'branch_commit': '07a4...',
             'version': '79.0.3987.66',
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

    actual = channels_api.construct_chrome_channels_details()

    expected = {
        'beta': {
            'version': 80,
            'earliest_beta': '2020-02-13T00:00:00',
            'mstone': 'fake milestone number',
            },
        'stable': {
            'version': 79,
            'earliest_beta': '2020-02-13T00:00:00',
            'mstone': 'fake milestone number',
          },
        'dev': {
            'version': 81,
            'earliest_beta': '2020-02-13T00:00:00',
            'mstone': 'fake milestone number',
            },
    }
    self.maxDiff = None
    self.assertEqual(expected, actual)

  @mock.patch('api.channels_api.fetch_chrome_release_info')
  @mock.patch('internals.fetchchannels.get_omaha_data')
  def test_construct_chrome_channels_details__dev_promotion(
      self, mock_get_omaha_data, mock_fetch_chrome_release_info):
    win_data = {
        'os': 'win',
        'versions': [

            {'branch_commit': '223c...',
             'version': '80.0.4040.5',
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

    actual = channels_api.construct_chrome_channels_details()

    expected = {
        'beta': {
            'version': 80,
            'earliest_beta': '2020-02-13T00:00:00',
            'mstone': 'fake milestone number',
            },
        'dev': {
            'version': 81,
            'earliest_beta': '2020-02-13T00:00:00',
            'mstone': 'fake milestone number',
            },
        'stable': {
            'version': 79,
            'earliest_beta': '2020-02-13T00:00:00',
            'mstone': 'fake milestone number',
          },
    }
    self.maxDiff = None
    self.assertEqual(expected, actual)

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

    actual = channels_api.fetch_chrome_release_info(90)

    self.assertEqual(
        {'everything else': 'kept'},
        actual)

  @mock.patch('requests.get')
  def test_fetch_chrome_release_info__not_found(self, mock_requests_get):
    """If chromiumdash app does not have the data, use a placeholder."""
    mock_requests_get.return_value = testing_config.Blank(
        status_code=404, content='')

    actual = channels_api.fetch_chrome_release_info(91)

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

    actual = channels_api.fetch_chrome_release_info(90)

    self.assertEqual(
        {'stable_date': None,
         'earliest_beta': None,
         'latest_beta': None,
         'mstone': 90,
         'version': 90,
         },
        actual)

  @mock.patch('api.channels_api.fetch_chrome_release_info')
  def test_construct_specified_milestones_details(
      self, mock_fetch_chrome_release_info):
    mstone_data = {
        'earliest_beta': '2020-02-13T00:00:00',
        'mstone': 'fake milestone number',
    }
    def fcri(version):
      result = mstone_data.copy()
      return result
    mock_fetch_chrome_release_info.side_effect = fcri

    actual = channels_api.construct_specified_milestones_details(1, 4)

    expected = {
        1: {
            'earliest_beta': '2020-02-13T00:00:00',
            'mstone': 'fake milestone number',
            },
        2: {
            'earliest_beta': '2020-02-13T00:00:00',
            'mstone': 'fake milestone number',
            },
        3: {
            'earliest_beta': '2020-02-13T00:00:00',
            'mstone': 'fake milestone number',
            },
        4: {
            'earliest_beta': '2020-02-13T00:00:00',
            'mstone': 'fake milestone number',
            }
    }
    self.maxDiff = None
    self.assertEqual(expected, actual)

  @mock.patch('api.channels_api.construct_chrome_channels_details')
  def test_do_get__simple(self, mock_call):
    expected =  {
        'earliest_beta': '2020-02-13T00:00:00',
        'mstone': 'fake milestone number',
    }
    mock_call.return_value = expected

    with test_app.test_request_context(self.request_path):
      actual_response = self.handler.do_get()

    self.assertEqual(expected, actual_response)

  def test_do_get__error(self):
    with test_app.test_request_context(self.request_path + '?start=2&end=1'):
      with self.assertRaises(ValueError):
        self.handler.do_get()

  @mock.patch('api.channels_api.construct_specified_milestones_details')
  def test_do_get__start_and_end(self, mock_call):
    expected = {
        1: '123',
    }
    mock_call.return_value = expected

    with test_app.test_request_context(self.request_path + '?start=1&end=2'):
      actual_response = self.handler.do_get()

    self.assertEqual(expected, actual_response)
