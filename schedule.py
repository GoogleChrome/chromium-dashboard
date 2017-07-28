# -*- coding: utf-8 -*-
# Copyright 2017 Google Inc.
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

__author__ = 'ericbidelman@chromium.org (Eric Bidelman)'

import json
import logging
import os
import webapp2

from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.api import users

import common
import models
import settings
import util


def fetch_chrome_release_info(version):
  key = '%s|chromerelease|%s' % (settings.MEMCACHE_KEY_PREFIX, version)

  data = memcache.get(key)
  if data is None:
    url = 'https://chromepmo.appspot.com/schedule/mstone/json?mstone=%s' % version
    result = urlfetch.fetch(url, deadline=60)
    if result.status_code == 200:
      data = json.loads(result.content)['mstones'][0]
      del data['owners']
      del data['feature_freeze']
      del data['ldaps']
      memcache.set(key, data)
  return data

def construct_chrome_channels_details():
  omaha_data = util.get_omaha_data()
  channels = {}
  win_versions = omaha_data[0]['versions']

  for v in win_versions:
    channel = v['channel']
    major_version = int(v['version'].split('.')[0])
    channels[channel] = fetch_chrome_release_info(major_version)
    channels[channel]['version'] = major_version

  # Adjust for the brief period after a stable release where stable and beta
  # are on the same major version.
  if channels['stable']['version'] == channels['beta']['version']:
    channels['beta'] = channels['dev']
    channels['dev'] = channels['canary']

  return channels


class ScheduleHandler(common.ContentHandler):

  @common.strip_trailing_slash
  def get(self, path):
    data = {
      'features': json.dumps(models.Feature.get_chronological()),
      'channels': json.dumps(construct_chrome_channels_details())
    }

    self.render(data, template_path=os.path.join('schedule.html'))


app = webapp2.WSGIApplication([
  ('(.*)', ScheduleHandler),
], debug=settings.DEBUG)

