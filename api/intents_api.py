# Copyright 2024 Google Inc.
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

from typing import TypedDict

from api import converters
from framework import basehandlers
from framework import cloud_tasks_helpers
from framework import permissions
from internals import processes
from internals import stage_helpers
from internals.core_enums import INTENT_STAGES_BY_STAGE_TYPE
from internals.core_models import FeatureEntry, Stage
from internals.data_types import VerboseFeatureDict
from internals.review_models import Gate
from pages.intentpreview import compute_subject_prefix


class IntentOptions(TypedDict):
  subject: str
  feature: VerboseFeatureDict
  stage_info: stage_helpers.StageTemplateInfo
  should_render_mstone_table: bool
  should_render_intents: bool
  sections_to_show: list[str]
  intent_stage: int|None
  default_url: str
  intent_cc_emails: list[str]



class IntentsAPI(basehandlers.APIHandler):

  def do_post(self, **kwargs):
    """Submit an intent email directly to blink-dev."""
    feature_id = int(kwargs['feature_id'])
    # Check that feature ID is valid.
    if not feature_id:
      self.abort(404, msg='No feature specified.')
    feature: FeatureEntry|None = FeatureEntry.get_by_id(feature_id)
    if feature is None:
      self.abort(404, msg=f'Feature {feature_id} not found')

    body = self.get_json_param_dict()
    # Check that stage ID is valid.
    stage_id = body.get('stage_id')
    if not stage_id:
      self.abort(404, msg='No stage specified')
    stage: Stage|None = Stage.get_by_id(stage_id)
    if stage is None:
      self.abort(404, msg=f'Stage {stage_id} not found')

    # Check that the user has feature edit permissions.
    redirect_resp = permissions.validate_feature_edit_permission(
        self, feature_id)
    if redirect_resp:
      return redirect_resp

    intent_stage = INTENT_STAGES_BY_STAGE_TYPE[stage.stage_type]
    stage_info = stage_helpers.get_stage_info_for_templates(feature)
    default_url = (f'{self.request.scheme}://{self.request.host}'
                   f'/feature/{feature_id}')

    # Add gate to Chromestatus URL query string if it is found.
    gate: Gate|None = None
    if body.get('gate_id'):
      gate = Gate.get_by_id(body['gate_id'])
    if gate:
      default_url += f'?gate={gate.key.integer_id()}'

    params: IntentOptions = {
        'subject': compute_subject_prefix(feature, intent_stage),
        'feature': converters.feature_entry_to_json_verbose(feature),
        'stage_info': stage_helpers.get_stage_info_for_templates(feature),
        'should_render_mstone_table': stage_info['should_render_mstone_table'],
        'should_render_intents': stage_info['should_render_intents'],
        'sections_to_show': processes.INTENT_EMAIL_SECTIONS.get(
            intent_stage, []),
        'intent_stage': intent_stage,
        'default_url': default_url,
        'intent_cc_emails': body.get('intent_cc_emails', [])
    }

    cloud_tasks_helpers.enqueue_task('/tasks/email-intent-to-blink-dev',
                                     params)
    return {'message': 'Email task submitted successfully.'}
