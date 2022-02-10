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

import os
import flask

from unittest import mock
import unittest
import html5lib

from framework import ramcache
from pages import schedule

test_app = flask.Flask(__name__)

class TestWithFeature(testing_config.CustomTestCase):

  REQUEST_PATH_FORMAT = 'subclasses fill this in'
  HANDLER_CLASS = 'subclasses fill this in'

  def setUp(self):
    self.request_path = self.REQUEST_PATH_FORMAT
    self.handler = self.HANDLER_CLASS()

  def tearDown(self):
    ramcache.flush_all()
    ramcache.check_for_distributed_invalidation()

class ScheduleTemplateTest(TestWithFeature):

  HANDLER_CLASS = schedule.ScheduleHandler

  def setUp(self):
    super(ScheduleTemplateTest, self).setUp()
    with test_app.test_request_context(self.request_path):
      self.template_data = self.handler.get_template_data()

      self.template_data.update(self.handler.get_common_data())
      self.template_data['nonce'] = 'fake nonce'
      template_path = self.handler.get_template_path(self.template_data)
      self.full_template_path = os.path.join(template_path)

  def test_html_rendering(self):
    """We can render the template with valid html."""
    template_text = self.handler.render(
        self.template_data, self.full_template_path)
    parser = html5lib.HTMLParser(strict=True)
    document = parser.parse(template_text)


class ScheduleFunctionsTest(unittest.TestCase):

  @mock.patch('pages.schedule.fetch_chrome_release_info')
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
