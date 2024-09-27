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
from typing import Any, NotRequired, TypedDict
import requests

from framework import secrets
from framework import utils
from internals.core_models import Stage
from internals.data_types import OriginTrialInfo
import settings


class RequestTrial(TypedDict):
  id: NotRequired[int]
  display_name: str
  start_milestone: str
  end_milestone: str
  end_time: dict
  description: str
  documentation_url: str
  feedback_url: str
  intent_to_experiment_url: str
  chromestatus_url: str
  allow_third_party_origins: bool
  type: str
  origin_trial_feature_name: NotRequired[str]


class InternalRegistrationConfig(TypedDict):
  allow_public_suffix_subdomains: NotRequired[bool]
  approval_type: NotRequired[str]
  approval_buganizer_component_id: NotRequired[int]
  approval_buganizer_custom_field_id: NotRequired[int]
  approval_criteria_url: NotRequired[str]
  approval_group_email: NotRequired[str]


class CreateOriginTrialRequest(TypedDict):
  trial: RequestTrial
  registration_config: InternalRegistrationConfig
  trial_contacts: list[str]


class SetUpTrialRequest(TypedDict):
  trial_id: int
  data_access_admin_group_name: str
  announcement_groups_owners: list[str]
  trial_contacts: list[str]


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
  if key is None:
    return []

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


def _get_trial_end_time(end_milestone: int) -> int:
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
  mstone_info = utils.get_chromium_milestone_info(milestone_plus_two)

  # Raise error if the response is not in the expected format.
  if ('mstones' not in mstone_info
      or len(mstone_info['mstones']) == 0
      or 'late_stable_date' not in mstone_info['mstones'][0]):
    raise KeyError('Chromium schedule response not in expected format.')
  date = datetime.strptime(
      mstone_info['mstones'][0]['late_stable_date'],
      utils.CHROMIUM_SCHEDULE_DATE_FORMAT)
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


def _send_create_trial_request(
    ot_stage: Stage, api_key: str, access_token: str
  ) -> tuple[int|None, str|None]:
  """Send an origin trial creation request to the origin trials API.
  Returns:
    Newly created origin trial ID if trial was created, any error text if there
    was an issue during the creation process.
  """
  json: CreateOriginTrialRequest = {
    'trial': {
      'display_name': ot_stage.ot_display_name,
      'start_milestone': str(ot_stage.milestones.desktop_first),
      'end_milestone': str(ot_stage.milestones.desktop_last),
      'end_time': {
        'seconds': _get_trial_end_time(ot_stage.milestones.desktop_last)
      },
      'description': ot_stage.ot_description,
      'documentation_url': ot_stage.ot_documentation_url,
      'feedback_url': ot_stage.ot_feedback_submission_url,
      'intent_to_experiment_url': ot_stage.intent_thread_url,
      'chromestatus_url': f'{settings.SITE_URL}feature/{ot_stage.feature_id}',
      'allow_third_party_origins': ot_stage.ot_has_third_party_support,
      'type': ('DEPRECATION'
                if ot_stage.ot_is_deprecation_trial else 'ORIGIN_TRIAL'),
    },
    'registration_config': {'approval_type': 'NONE'},
    'trial_contacts': []
  }
  if ot_stage.ot_require_approvals:
    json['registration_config'] = {
      'approval_type': 'CUSTOM',
      'approval_buganizer_component_id': ot_stage.ot_approval_buganizer_component,
      'approval_criteria_url': ot_stage.ot_approval_criteria_url,
      'approval_group_email': ot_stage.ot_approval_group_email,
      'approval_buganizer_custom_field_id': ot_stage.ot_approval_buganizer_custom_field_id,
    }
  if ot_stage.ot_chromium_trial_name:
    json['trial']['origin_trial_feature_name'] = ot_stage.ot_chromium_trial_name
  if ot_stage.ot_is_deprecation_trial:
    json['registration_config']['allow_public_suffix_subdomains'] = True

  headers = {'Authorization': f'Bearer {access_token}'}
  url = f'{settings.OT_API_URL}/v1/trials:initialize'

  # Retry the request a number of times if any issues arise.
  try:
    response = requests.post(
        url, headers=headers, params={'key': api_key}, json=json)
    logging.info(f'CreateTrial response text: {response.text}')
    response.raise_for_status()
  except requests.exceptions.RequestException:
    logging.exception(
        f'Failed to get response from origin trials API. {response.text}')
    return None, response.text
  response_json = response.json()
  return response_json['trial']['id'], None


def _send_set_up_trial_request(
    trial_id: int,
    owners: list[str],
    contacts: list[str],
    api_key: str,
    access_token: str
  ) -> str|None:
  """Send an origin trial setup request to the origin trials API.
  Returns:
    Any error text if there was an issue during the setup process.
  """
  data_access_admin_group = secrets.get_ot_data_access_admin_group()
  # Return some error text about the data access group if not found.
  if data_access_admin_group is None:
    return 'No data access admin group found'

  json: SetUpTrialRequest = {
    'trial_id': trial_id,
    'data_access_admin_group_name': data_access_admin_group,
    'announcement_groups_owners': owners,
    'trial_contacts': contacts,
  }
  headers = {'Authorization': f'Bearer {access_token}'}
  url = f'{settings.OT_API_URL}/v1/trials/{trial_id}:setup'
  try:
    response = requests.post(
        url, headers=headers, params={'key': api_key}, json=json)
    logging.info(f'SetUpTrial response text: {response.text}')
    response.raise_for_status()
  except requests.exceptions.RequestException:
    logging.exception(
        f'Failed to get response from origin trials API. {response.text}')
    return response.text
  return None


def create_origin_trial(ot_stage: Stage) -> tuple[str|None, str|None]:
  """Send an origin trial creation request to the origin trials API.

  Raises:
    requests.exceptions.RequestException: If the request fails to connect or
      the HTTP status code is not successful.
  Returns:
    Newly created origin trial ID if trial was created, any error text if there
    was an issue during the creation process.
  """
  if settings.DEV_MODE:
    logging.info('Creation request will not be sent to origin trials API in '
                 'local environment.')
    return None, None
  key = secrets.get_ot_api_key()
  if key is None:
    return None, 'No API key found for origin trials API'
  ot_support_emails = secrets.get_ot_support_emails()
  if ot_support_emails is None:
    return None, 'OT support emails not found'

  # Get a list of all OT @google.com contacts (ot_owner_email must be a google
  # contact).
  unique_contacts = [ot_stage.ot_owner_email]
  unique_contacts.extend(ot_stage.ot_emails)
  unique_contacts = [email for email in set(unique_contacts)
                     if email.endswith('@google.com')]
  # A trial must have a google.com domain contact.
  if len(unique_contacts) == 0:
    return None, 'No trial contacts found in google.com domain'

  access_token = _get_ot_access_token()
  origin_trial_id, error_text = _send_create_trial_request(
      ot_stage, key, access_token)

  if origin_trial_id is None:
    return None, error_text

  error_text = _send_set_up_trial_request(
      origin_trial_id,
      ot_support_emails.split(','),
      unique_contacts,
      key,
      access_token)

  return str(origin_trial_id), error_text


def activate_origin_trial(origin_trial_id: str) -> None:
  """Activate an existing origin trial.

  Raises:
    requests.exceptions.RequestException: If the request fails to connect or
      the HTTP status code is not successful.
  """
  if settings.DEV_MODE:
    logging.info('Activation request will not be sent to origin trials API in '
                 'local environment.')
    return None
  key = secrets.get_ot_api_key()
  if key is None:
    return None

  json = {'id': origin_trial_id}
  access_token = _get_ot_access_token()
  headers = {'Authorization': f'Bearer {access_token}'}
  url = (f'{settings.OT_API_URL}/v1/trials/{origin_trial_id}:start')
  try:
    response = requests.post(
        url, headers=headers, params={'key': key}, json=json)
    logging.info(response.text)
    response.raise_for_status()
  except requests.exceptions.RequestException as e:
    logging.exception(
        f'Failed to get response from origin trials API. {response.text}')
    raise e


def extend_origin_trial(trial_id: str, end_milestone: int, intent_url: str):
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
  if key is None:
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
    'milestone_end': str(end_milestone),
    'extension_intent_url': intent_url,
  }

  try:
    response = requests.post(
        url, headers=headers, params={'key': key}, json=json)
    logging.info(response.text)
    response.raise_for_status()
  except requests.exceptions.RequestException as e:
    logging.exception('Failed to get response from origin trials API.')
    raise e
