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
from internals.review_models import Gate, Vote

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
      self.abort(404, f'Extension stage has no end milestone defined.')
    intent_url = extension_stage.intent_thread_url
    if intent_url is None or not validators.url(intent_url):
      self.abort(400, ('Invalid argument for extension_intent_url: '
                       f'{intent_url}'))

    gate = Gate.query(Gate.stage_id == extension_stage.key.integer_id()).get()
    if not gate or gate.state != Vote.APPROVED:
      self.abort(400, 'Extension has not received the required approvals.')

  def do_post(self, **kwargs):
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
    extension_stage_id = int(kwargs['extension_stage_id'])
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
    return {'message': 'Origin trial extended successfully.'}
