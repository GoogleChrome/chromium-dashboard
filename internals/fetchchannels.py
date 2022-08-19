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
import requests

from framework import rediscache
# Note: this file cannot import models because it would be circular.


def get_omaha_data():
  omaha_data = rediscache.get('omaha_data')
  if omaha_data is None:
    result = requests.get('https://omahaproxy.appspot.com/all.json')
    if result.status_code == 200:
      omaha_data = json.loads(result.content)
      rediscache.set('omaha_data', omaha_data, time=86400) # cache for 24hrs.
  return omaha_data
