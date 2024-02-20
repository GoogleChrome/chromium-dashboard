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
from datetime import datetime, timezone
import logging
from typing import Any
import requests

from framework import secrets
from internals.data_types import OriginTrialInfo
import settings


CHROMIUM_SCHEDULE_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'


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


def _get_trial_end_time(end_milestone: str) -> int:
  """Get the end time of the origin trial based on end milestone.

  Returns:
    The end time of the origin trial, represented in seconds since epoch.

  Raises:
    requests.exceptions.RequestException: If the request fails to connect or
      the HTTP status code is not successful.
    KeyError: If the response from Chromium schedule API is not in the expected
      format.
  """
  milestone_plus_two = int(end_milestone) + 2
  try:
    response = requests.get(
      'https://chromiumdash.appspot.com/fetch_milestone_schedule'
      f'?mstone={milestone_plus_two}')
    response.raise_for_status()
  except requests.exceptions.RequestException as e:
    logging.exception('Failed to get response from Chromium schedule API.')
    raise e
  response_json = response.json()

  # Raise error if the response is not in the expected format.
  if ('mstones' not in response_json
      or len(response_json['mstones']) == 0
      or 'late_stable_date' not in response_json['mstones'][0]):
    raise KeyError('Chromium schedule response not in expected format.')
  date = datetime.strptime(
      response_json['mstones'][0]['late_stable_date'],
      CHROMIUM_SCHEDULE_DATE_FORMAT)
  return int(date.replace(tzinfo=timezone.utc).timestamp())


def _get_ot_access_token() -> str:
  """Obtain the service account credentials to be used in the request
  using the origin trials auth scope
  
  Returns:
    The access token to be used for origin trials requests.
  """
  credentials, _ = google.auth.default(scopes=[
      'https://www.googleapis.com/auth/chromeorigintrials'])
  credentials.refresh(Request())
  if credentials.token is None:
    return ''
  return credentials.token


def extend_origin_trial(trial_id: str, end_milestone: str, intent_url: str):
  """Extend an existing origin trial.

  Raises:
    requests.exceptions.RequestException: If the request fails to connect or
      the HTTP status code is not successful.
  """
  if settings.DEV_MODE:
    logging.info('Extension request will not be sent to origin trials API in '
                 'local environment.')
    return
  key = secrets.get_ot_api_key()
  # Return if no API key is found.
  if key == None:
    return

  end_seconds = _get_trial_end_time(end_milestone)
  access_token = _get_ot_access_token()
  url = (f'{settings.OT_API_URL}/v1/trials/{trial_id}:add_extension')
  headers = {'Authorization': f'Bearer {access_token}'}
  json = {
    'trial_id': trial_id,
    'end_date': {
      'seconds': end_seconds
    },
    'milestone_end': end_milestone,
    'extension_intent_url': intent_url,
  }

  try:
    response = requests.post(
        url, headers=headers, params={'key': key}, json=json)
    response.raise_for_status()
  except requests.exceptions.RequestException as e:
    logging.exception('Failed to get response from origin trials API.')
    raise e
