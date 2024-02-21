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

import requests
import validators

from framework import basehandlers
from framework import permissions
from framework import origin_trials_client
from internals.core_models import FeatureEntry, Stage


class OriginTrialsAPI(basehandlers.APIHandler):

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

  def _validate_extension_args(self, feature_id: int, stage: Stage, body) -> None:
    """Validates the given arguments used for origin trial extension."""
    # The stage should belong to the feature.
    if feature_id != stage.feature_id:
      self.abort(400, ('Stage does not belong to feature. '
                       f'feature_id: {trial_id}, '
                       f'stage_id: {stage.key.integer_id()}'))
    trial_id = body['origin_trial_id']
    # if (trial_id is None
    #     or not (all(char.isdigit() or char == '-' for char in trial_id))):
    #   self.abort(400, f'Invalid argument for trial_id: {trial_id}')
    # # The origin trial should belong to the stage.
    # if trial_id != stage.origin_trial_id:
    #   self.abort(400, ('Origin trial does not belong to stage.'
    #                    f'origin trial ID: {trial_id}',
    #                    f'stage\'s origin trial ID: {trial_id}'))
    end_milestone = body['end_milestone']
    if end_milestone is None or not end_milestone.isnumeric():
      self.abort(400, f'Invalid argument for end_milestone: {end_milestone}')
    intent_url = body['intent_thread_url']
    if not validators.url(intent_url):
      self.abort(400, ('Invalid argument for extension_intent_url: '
                       f'{intent_url}'))


  def do_post(self, **kwargs):
    """Extends an existing origin trial"""
    feature_id = int(kwargs['feature_id'])
    if feature_id is None or feature_id == 0:
      self.abort(404, msg='No feature specified.')
    feature: FeatureEntry | None = FeatureEntry.get_by_id(feature_id)
    if feature is None:
      self.abort(404, msg=f'Feature {feature_id} not found')

    stage_id = int(kwargs['stage_id'])
    if stage_id is None or stage_id == 0:
      self.abort(404, msg='No stage specified.')
    stage: Stage | None = Stage.get_by_id(stage_id)
    if stage is None:
      self.abort(404, msg=f'Stage {stage_id} not found')

    redirect_resp = permissions.validate_feature_edit_permission(
        self, feature_id)
    if redirect_resp:
      return redirect_resp

    body = self.get_json_param_dict()
    self._validate_extension_args(feature_id, stage, body)

    try:
      origin_trials_client.extend_origin_trial(
        body['origin_trial_id'], body['end_milestone'],
        body['intent_thread_url'])
    except requests.exceptions.RequestException:
      self.abort(500, 'Error in request to origin trials API')
