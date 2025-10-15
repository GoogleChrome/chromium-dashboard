# -*- coding: utf-8 -*-
# Copyright 2021 Google Inc.
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

from framework import basehandlers
from internals import fetchchannels
import settings


TEST_CHANNEL_DATA = {
  "stable": {
    "branch_point": "2025-09-01T00:00:00",
    "earliest_beta": "2025-09-03T00:00:00",
    "earliest_beta_chromeos": "2025-09-16T00:00:00",
    "earliest_beta_ios": "2025-09-03T00:00:00",
    "early_stable": "2025-09-24T00:00:00",
    "early_stable_ios": "2025-09-17T00:00:00",
    "final_beta": "2025-09-24T00:00:00",
    "final_beta_cut": "2025-09-23T00:00:00",
    "late_stable_date": "2025-10-14T00:00:00",
    "latest_beta": "2025-09-18T00:00:00",
    "mstone": 141,
    "next_late_stable_refresh": "2025-10-28T00:00:00",
    "next_stable_refresh": "2025-10-14T00:00:00",
    "stable_cut": "2025-09-23T00:00:00",
    "stable_cut_ios": "2025-09-16T00:00:00",
    "stable_date": "2025-09-30T00:00:00",
    "stable_refresh_first": "2025-10-14T00:00:00",
    "version": 141
  },
  "beta": {
    "branch_point": "2025-09-29T00:00:00",
    "earliest_beta": "2025-10-01T00:00:00",
    "earliest_beta_chromeos": "2025-10-14T00:00:00",
    "earliest_beta_ios": "2025-10-01T00:00:00",
    "early_stable": "2025-10-22T00:00:00",
    "early_stable_ios": "2025-10-22T00:00:00",
    "final_beta": "2025-10-22T00:00:00",
    "final_beta_cut": "2025-10-21T00:00:00",
    "late_stable_date": "2025-11-11T00:00:00",
    "latest_beta": "2025-10-16T00:00:00",
    "mstone": 142,
    "stable_cut": "2025-10-21T00:00:00",
    "stable_cut_ios": "2025-10-21T00:00:00",
    "stable_date": "2025-10-28T00:00:00",
    "stable_refresh_first": "2025-11-11T00:00:00",
    "stable_refresh_second": "2025-12-02T00:00:00",
    "stable_refresh_third": "2025-12-16T00:00:00",
    "version": 142
  }, "dev": {
    "branch_point": "2025-10-27T00:00:00",
    "earliest_beta": "2025-10-29T00:00:00",
    "earliest_beta_chromeos": "2025-11-11T00:00:00",
    "earliest_beta_ios": "2025-10-29T00:00:00",
    "early_stable": "2025-11-19T00:00:00",
    "early_stable_ios": "2025-11-19T00:00:00",
    "final_beta": "2025-11-19T00:00:00",
    "final_beta_cut": "2025-11-18T00:00:00",
    "late_stable_date": "2025-12-16T00:00:00",
    "latest_beta": "2025-11-13T00:00:00",
    "mstone": 143,
    "stable_cut": "2025-11-18T00:00:00",
    "stable_cut_ios": "2025-11-18T00:00:00",
    "stable_date": "2025-12-02T00:00:00",
    "version": 143
  }
}


def construct_chrome_channels_details():
  omaha_data = fetchchannels.get_omaha_data()
  channels = {}
  win_versions = omaha_data[0]['versions']

  for v in win_versions:
    channel = v['channel']
    major_version = int(v['version'].split('.')[0])
    channels[channel] = fetchchannels.fetch_chrome_release_info(major_version)
    channels[channel]['version'] = major_version

  # Adjust for the brief period after next miletone gets promted to stable/beta
  # channel and their major versions are the same.
  if channels['stable']['version'] == channels['beta']['version']:
    new_beta_version = channels['stable']['version'] + 1
    channels['beta'] = fetchchannels.fetch_chrome_release_info(new_beta_version)
    channels['beta']['version'] = new_beta_version
  if channels['beta']['version'] == channels['dev']['version']:
    new_dev_version = channels['beta']['version'] + 1
    channels['dev'] = fetchchannels.fetch_chrome_release_info(new_dev_version)
    channels['dev']['version'] = new_dev_version

  # In the situation where some versions are in a gap between
  # stable and beta, show one as 'stable_soon'.
  if channels['stable']['version'] + 1 < channels['beta']['version']:
    stable_soon_version = channels['stable']['version'] + 1
    channels['stable_soon'] = fetchchannels.fetch_chrome_release_info(stable_soon_version)
    channels['stable_soon']['version'] = stable_soon_version

  return channels


def construct_specified_milestones_details(start, end):
  channels = {}
  win_versions = list(range(start,end+1))

  for milestone in win_versions:
    channels[milestone] = fetchchannels.fetch_chrome_release_info(milestone)

  return channels


class ChannelsAPI(basehandlers.APIHandler):
  """Channels are the Chrome Versions across platforms."""

  def do_get(self, **kwargs):
    # Query-string parameters 'start' and 'end' are provided
    start = self.get_int_arg('start')
    end = self.get_int_arg('end')
    if start is None or end is None:
      # Use default values when tests are running.
      if settings.UNIT_TEST_MODE or settings.PLAYWRIGHT_MODE:
        return TEST_CHANNEL_DATA
      return construct_chrome_channels_details()

    if start > end:
      raise ValueError

    return construct_specified_milestones_details(start, end)

  # TODO(jrobbins): do_post

  # TODO(jrobbins): do_patch
