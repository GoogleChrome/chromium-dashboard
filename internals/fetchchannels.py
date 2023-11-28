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

import json
import logging
import requests

from framework import rediscache
# Note: this file cannot import core_models because it would be circular.

OMAHA_URL_TEMPLATE = (
    'https://versionhistory.googleapis.com'
    '/v1/chrome/platforms/win/channels/%s/versions/?pageSize=1')

def get_channel_info(channel):
  url = OMAHA_URL_TEMPLATE % channel
  logging.info('fetching %s' % url)
  result = requests.get(url)
  if result.status_code != 200:
    logging.info('Could not fetch channel info')
    return None
  channel_info = json.loads(result.content)
  logging.info('channel_info is %r', channel_info)
  version = channel_info['versions'][0]['version']
  return {'channel': channel, 'version': version}


def get_omaha_data():
  omaha_data = rediscache.get('omaha_data')

  if omaha_data is None:
    stable_info = get_channel_info('stable')
    beta_info = get_channel_info('beta')
    dev_info = get_channel_info('dev')
    win_versions = [stable_info, beta_info, dev_info]
    omaha_info = [{'versions': win_versions}]
    omaha_data = json.dumps(omaha_info)
    rediscache.set('omaha_data', omaha_data, time=86400) # cache for 24hrs.

  return json.loads(omaha_data)
