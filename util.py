from __future__ import division
from __future__ import print_function

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

from framework import ramcache
import requests

def get_omaha_data():
  omaha_data = ramcache.get('omaha_data')
  if omaha_data is None:
    result = requests.get('https://omahaproxy.appspot.com/all.json')
    if result.status_code == 200:
      omaha_data = json.loads(result.content)
      ramcache.set('omaha_data', omaha_data, time=86400) # cache for 24hrs.
  return omaha_data
