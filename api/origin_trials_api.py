# -*- coding: utf-8 -*-
# Copyright 2023 Google Inc.
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
from framework.secrets import get_ot_api_key
import requests
import settings


class OriginTrialsAPI(basehandlers.APIHandler):

  def do_get(self, **kwargs):
    """Get a list of all origin trials."""
    key = get_ot_api_key()
    # Return an empty list if no API key is found.
    if key == None:
      return []

    try:
      response = requests.get(
          f'{settings.OT_API_URL}/v1/trials',
          params={'prettyPrint': 'false', 'key': key})
      response.raise_for_status()
      if response.ok:
        trials = response.json()['trials']
        return trials
    except:
      self.abort(500, 'Error obtaining origin trial data from API.')
    return []
