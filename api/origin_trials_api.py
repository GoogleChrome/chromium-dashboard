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

import asyncio
import json5
import logging
import requests
import validators
from base64 import b64decode

from framework import basehandlers
from framework import origin_trials_client
from internals import notifier_helpers
from framework import permissions
from internals.core_models import FeatureEntry, Stage
from internals.review_models import Gate, Vote


WEBFEATURE_FILE_URL = 'https://chromium.googlesource.com/chromium/src/+/main/third_party/blink/public/mojom/use_counter/metrics/web_feature.mojom?format=TEXT'
ENABLED_FEATURES_FILE_URL = 'https://chromium.googlesource.com/chromium/src/+/main/third_party/blink/renderer/platform/runtime_enabled_features.json5?format=TEXT'
GRACE_PERIOD_FILE = 'https://chromium.googlesource.com/chromium/src/+/main/third_party/blink/common/origin_trials/manual_completion_origin_trial_features.cc?format=TEXT'


def get_chromium_file(url: str) -> asyncio.Future[requests.Response]:
  """Get chromium file contents from a given URL"""
  loop = asyncio.get_running_loop()
  try:
    file_future = loop.run_in_executor(None, requests.get, url)
  except requests.RequestException as e:
    logging.exception(
        f'Failed to get response to obtain Chromium file: {url}')
    raise e
  return file_future


class OriginTrialsAPI(basehandlers.EntitiesAPIHandler):

  def do_get(self, **kwargs):
    """Get a list of all origin trials.

    Returns:
      A list of data on all public origin trials.
    """
    try:
      trials_list = origin_trials_client.get_trials_list()
    except requests.exceptions.RequestException:
      self.abort(500, 'Error obtaining origin trial data from API')
    except KeyError:
      self.abort(500, 'Malformed response from origin trials API')

    return trials_list

  async def _validate_creation_args(
      self, body: dict) -> dict[str, str]:
    """Check that all provided OT creation arguments are valid."""
    try:
      files_async = [
          get_chromium_file(ENABLED_FEATURES_FILE_URL),
          get_chromium_file(WEBFEATURE_FILE_URL),
          get_chromium_file(GRACE_PERIOD_FILE)]
      responses = await asyncio.gather(*files_async)
      enabled_features_text, webfeature_file, grace_period_file = [
          b64decode(resp.text).decode('utf-8') for resp in responses]
    except requests.exceptions.RequestException:
      self.abort(500, 'Error obtaining Chromium file for validation')
    validation_errors: dict[str, str] = {}
    chromium_trial_name = body.get(
        'ot_chromium_trial_name', {}).get('value')
    if chromium_trial_name is None:
      self.abort(400, 'Chromium trial name not specified.')

    # Check if a trial already exists with the same name.
    try:
      trials_list = origin_trials_client.get_trials_list()
    except requests.exceptions.RequestException:
      self.abort(500, 'Error obtaining origin trial data from API')

    if (any(trial['origin_trial_feature_name'] == chromium_trial_name
            for trial in trials_list)):
      validation_errors['ot_chromium_trial_name'] = (
          'Chromium trial name is already used by another origin trial')

    enabled_features_json = json5.loads(enabled_features_text)
    if (not any(feature.get('origin_trial_feature_name') == chromium_trial_name
                for feature in enabled_features_json['data'])):
      validation_errors['ot_chromium_trial_name'] = (
          'Origin trial feature name not found in file')

    if not body.get('ot_is_deprecation_trial', {}).get('value', False):
      use_counter = body.get('ot_webfeature_use_counter', {}).get('value')
      if use_counter is None:
        validation_errors['ot_webfeature_use_counter'] = (
            'No UseCounter specified for non-deprecation trial.')
      elif f'{use_counter} =' not in webfeature_file:
          validation_errors['ot_webfeature_use_counter'] = (
              'UseCounter not landed in web_feature.mojom')

    if body.get('ot_has_third_party_support', {}).get('value', False):
      for feature in enabled_features_json['data']:
        if (feature.get('origin_trial_feature_name') == chromium_trial_name and
            not feature.get('origin_trial_allows_third_party', False)):
          validation_errors['ot_has_third_party_support'] = (
              'One or more features do not have third party support '
              'set in runtime_enabled_features.json5. Feature name: '
              f'{feature["name"]}')

    if body.get('ot_is_critical_trial', {}).get('value', False):
      if (f'blink::mojom::OriginTrialFeature::k{chromium_trial_name}'
          not in grace_period_file):
        validation_errors['ot_is_critical_trial'] = (
            'Use counter has not landed in grace period array '
            'for critical trial')

    return validation_errors

  def do_post(self, **kwargs):
    feature_id = int(kwargs['feature_id'])
    # Check that feature ID is valid.
    if not feature_id:
      self.abort(404, msg='No feature specified.')
    feature: FeatureEntry | None = FeatureEntry.get_by_id(feature_id)
    if feature is None:
      self.abort(404, msg=f'Feature {feature_id} not found')

    # Check that stage ID is valid.
    ot_stage_id = int(kwargs['stage_id'])
    if not ot_stage_id:
      self.abort(404, msg='No stage specified.')
    ot_stage: Stage | None = Stage.get_by_id(ot_stage_id)
    if ot_stage is None:
      self.abort(404, msg=f'Stage {ot_stage_id} not found')

    # Check that user has permission to edit the feature
    # associated with the origin trial.
    redirect_resp = permissions.validate_feature_edit_permission(
        self, feature_id)
    if redirect_resp:
      return redirect_resp

    body = self.get_json_param_dict()
    validation_errors = asyncio.run(self._validate_creation_args(body))
    if validation_errors:
      return {
          'message': 'Errors found when validating arguments',
          'errors': validation_errors
          }
    self.update_stage(ot_stage, body, [])
    return {'message': 'Origin trial creation request submitted.'}

  def _validate_extension_args(
        self, feature_id: int, ot_stage: Stage, extension_stage: Stage) -> None:
    """Abort if any arguments used for origin trial extension are invalid."""
    # The stage should belong to the feature.
    if feature_id != extension_stage.feature_id:
      self.abort(400, ('Stage does not belong to feature. '
                       f'feature_id: {feature_id}, '
                       f'stage_id: {extension_stage.key.integer_id()}'))

    trial_id = ot_stage.origin_trial_id
    if trial_id is None:
      self.abort(400, f'Invalid argument for trial_id: {trial_id}')

    milestones = extension_stage.milestones
    if milestones is None or milestones.desktop_last is None:
      self.abort(404, 'Extension stage has no end milestone defined.')
    intent_url = extension_stage.intent_thread_url
    if intent_url is None or not validators.url(intent_url):
      self.abort(400, ('Invalid argument for extension_intent_url: '
                       f'{intent_url}'))

    gate = Gate.query(Gate.stage_id == extension_stage.key.integer_id()).get()
    if not gate or gate.state != Vote.APPROVED:
      self.abort(400, 'Extension has not received the required approvals.')

  def do_patch(self, **kwargs):
    """Extends an existing origin trial"""
    feature_id = int(kwargs['feature_id'])
    extension_stage_id = int(kwargs['extension_stage_id'])
    # Check that feature ID is valid.
    if not feature_id:
      self.abort(404, msg='No feature specified.')
    feature: FeatureEntry | None = FeatureEntry.get_by_id(feature_id)
    if feature is None:
      self.abort(404, msg=f'Feature {feature_id} not found')

    # Check that stage ID is valid.
    if not extension_stage_id:
      self.abort(404, msg='No stage specified.')
    extension_stage: Stage | None = Stage.get_by_id(extension_stage_id)
    if extension_stage is None:
      self.abort(404, msg=f'Stage {extension_stage_id} not found')
    if extension_stage.ot_stage_id is None:
      self.abort(400, msg=(f'Extension stage {extension_stage_id} does not '
                           'have associated origin trial stage.'))
    ot_stage: Stage | None = Stage.get_by_id(extension_stage.ot_stage_id)
    if ot_stage is None:
      self.abort(404, msg=f'OT stage {extension_stage.ot_stage_id} not found')

    # Check that user has permission to edit the feature
    # associated with the origin trial.
    redirect_resp = permissions.validate_feature_edit_permission(
        self, feature_id)
    if redirect_resp:
      return redirect_resp

    self._validate_extension_args(feature_id, ot_stage, extension_stage)

    try:
      origin_trials_client.extend_origin_trial(
        ot_stage.origin_trial_id, extension_stage.milestones.desktop_last,
        extension_stage.intent_thread_url)
    except requests.exceptions.RequestException:
      self.abort(500, 'Error in request to origin trials API')
    except KeyError:
      self.abort(500, 'Malformed response from Schedule API')

    # This extension has been processed and action is no longer needed.
    extension_stage.ot_action_requested = False
    extension_stage.put()

    notifier_helpers.send_trial_extended_notification(ot_stage, extension_stage)
    return {'message': 'Origin trial extended successfully.'}
