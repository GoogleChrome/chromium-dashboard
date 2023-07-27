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


from dataclasses import asdict
from typing import Any
import requests

from framework import secrets
from internals.data_types import OriginTrialInfo
import settings



# Data type for information if an error occurred. Error code + message.
ERROR_INFO_TYPE = tuple[int, str]|None


def get_trials_list() -> tuple[list[dict[str, Any]], ERROR_INFO_TYPE]:
  """Get a list of all origin trials."""
  key = secrets.get_ot_api_key()
  # Return an empty list if no API key is found.
  if key == None:
    return [], None

  try:
    response = requests.get(
        f'{settings.OT_API_URL}/v1/trials',
        params={'prettyPrint': 'false', 'key': key})
    response.raise_for_status()
  except requests.exceptions.HTTPError:
    return [], (500, 'Error obtaining origin trial data from API')

  response_json = response.json()
  if 'trials' not in response_json:
    return [], (500, 'Malformed response from origin trials API')

  trials_list = [asdict(OriginTrialInfo(api_trial))
                 for api_trial in response_json['trials']
                 if api_trial['isPublic']]
  return trials_list, None
