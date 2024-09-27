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

import logging
import json
import requests

from framework import basehandlers
from framework import rediscache
from internals import fetchchannels
import settings


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
      return construct_chrome_channels_details()

    if start > end:
      raise ValueError

    return construct_specified_milestones_details(start, end)

  # TODO(jrobbins): do_post

  # TODO(jrobbins): do_patch
