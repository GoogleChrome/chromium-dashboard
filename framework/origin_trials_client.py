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

import google.auth
from google.auth.transport.requests import Request

from dataclasses import asdict
import logging
from typing import Any
import requests

from framework import secrets
from internals.data_types import OriginTrialInfo
import settings


def get_trials_list() -> list[dict[str, Any]]:
  """Get a list of all origin trials.
  
  Returns:
    A list of data on all public origin trials.

  Raises:
    requests.exceptions.RequestException: If the request fails to connect or
      the HTTP status code is not successful.
    KeyError: If the response from the OT API is not in the expected format.
  """
  key = secrets.get_ot_api_key()
  # Return an empty list if no API key is found.
  if key == None:
    return []

  credentials, project_id = google.auth.default(scopes=[
      "https://www.googleapis.com/auth/chromeorigintrials"])
  credentials.refresh(Request())
  # credentials = app_engine.Credentials(scopes=[
  #     "https://www.googleapis.com/auth/chromeorigintrials"], service_account_id='113400961428040496994', quota_project_id='cr-status-staging')
  token_header = f'Bearer {credentials.token}'
  response = requests.post(
      f'{settings.OT_API_URL}/v1/trials/4544132024016830465:add_extension?key={key}',
      headers={'Authorization': token_header},
      json={
        "trial_id": "4544132024016830465",
        "end_date": {
            "seconds": 2008384422
        },
        "milestone_end": "250",
        "extension_intent_url": "https://example.com/from_chromestatus2"
      })
  return str({
    'token_header': token_header,
    'response': response.json()})
  # return str(credentials.__dict__)
  try:
    response = requests.get(
        f'{settings.OT_API_URL}/v1/trials',
        params={'prettyPrint': 'false', 'key': key})
    response.raise_for_status()
  except requests.exceptions.RequestException as e:
    logging.exception('Failed to get response from origin trials API.')
    raise e

  response_json = response.json()

  trials_list = [asdict(OriginTrialInfo(api_trial))
                 for api_trial in response_json['trials']
                 if api_trial['isPublic']]
  return trials_list


def extend_origin_trial(trial_id: str, milestone_end: str, intent_url: str):
  """Extend an existing origin trial.

  Returns:
    Boolean value if the extension request was successful.

  Raises:
    requests.exceptions.RequestException: If the request fails to connect or
      the HTTP status code is not successful.
  """
  key = secrets.get_ot_api_key()
  # Return False if no API key is found.
  if key == None:
    return False

  end_seconds = 0
  # Obtain the service account credentials to be used in the request
  # using the origin trials auth scope.
  credentials, _ = google.auth.default(scopes=[
      'https://www.googleapis.com/auth/chromeorigintrials'])
  credentials.refresh(Request())
  url = (f'{settings.OT_API_URL}/v1/trials/{trial_id}:add_extension'
         f'key={key}')
  headers = {'Authorization': f'Bearer {credentials.token}'}
  json = {
    'trial_id': trial_id,
    'end_date': {
      'seconds': end_seconds
    },
    'extension_intent_url': intent_url,
  }

  try:
    response = requests.post(url, headers=headers, json=json)
  except requests.exceptions.RequestException as e:
    logging.exception('Failed to get response from origin trials API.')
    raise e

  return response.status_code == 200
