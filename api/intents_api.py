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

from flask import Response, render_template

from api import converters
from chromestatus_openapi.models import (
  GetIntentResponse, PostIntentRequest, MessageResponse)
from framework import basehandlers
from framework import cloud_tasks_helpers
from framework import permissions
from internals import processes
from internals import stage_helpers
from internals.core_enums import INTENT_STAGES_BY_STAGE_TYPE
from internals.core_models import FeatureEntry
from internals.review_models import Gate
from pages.intentpreview import compute_subject_prefix
import settings


# Format for Google Cloud Task body passed to cloud_tasks_helpers.enqueue_task
class IntentGenerationOptions(TypedDict):
  subject: str
  feature_id: int
  sections_to_show: list[str]
  intent_stage: int|None
  default_url: str
  intent_cc_emails: list[str]


class IntentsAPI(basehandlers.APIHandler):

  def do_get(self, **kwargs) -> Response|dict|str:
    """Get the body of a draft intent."""
    feature_id = int(kwargs['feature_id'])
    # Check that feature ID is valid.
    if not feature_id:
      self.abort(400, msg='No feature specified')
    feature: FeatureEntry = self.get_specified_feature(feature_id)

    # Check that stage ID is valid.
    stage_id = int(kwargs.get('stage_id', 0))
    if not stage_id:
      self.abort(400, msg='No stage specified.')
    stage = self.get_specified_stage(stage_id)
    if stage.feature_id != feature_id:
      self.abort(400, msg='Stage does not belong to given feature')

    gate_id = int(kwargs.get('gate_id', 0))
    if gate_id:
      gate: Gate|None = Gate.get_by_id(gate_id)
      if not gate:
        self.abort(400, msg='Invalid Gate ID')
      elif gate.stage_id != stage_id:
        self.abort(400, msg='Given gate does not belong to stage')

    # Check that the user has feature edit permissions.
    redirect_resp = permissions.validate_feature_edit_permission(
        self, feature_id)
    if redirect_resp:
      return redirect_resp

    stage_info = stage_helpers.get_stage_info_for_templates(feature)
    intent_stage = INTENT_STAGES_BY_STAGE_TYPE[stage.stage_type]
    default_url = (f'{self.request.scheme}://{self.request.host}'
                   f'/feature/{feature_id}')
    if gate_id:
      default_url += f'?gate={gate_id}'

    template_data = {
      'feature': converters.feature_entry_to_json_verbose(feature),
      'stage_info': stage_helpers.get_stage_info_for_templates(feature),
      'should_render_mstone_table': stage_info['should_render_mstone_table'],
      'should_render_intents': stage_info['should_render_intents'],
      'sections_to_show': processes.INTENT_EMAIL_SECTIONS.get(
          intent_stage, []),
      'intent_stage': intent_stage,
      'default_url': default_url,
      'APP_TITLE': settings.APP_TITLE,
    }
    return GetIntentResponse(
      subject=(f'{compute_subject_prefix(feature, intent_stage)}: '
               f'{feature.name}'),
      email_body=render_template(
          'blink/intent_to_implement.html', **template_data)).to_dict()

  def do_post(self, **kwargs) -> Response|dict|MessageResponse:
    """Submit an intent email directly to blink-dev."""
    feature_id = int(kwargs.get('feature_id', 0))
    # Check that feature ID is valid.
    if not feature_id:
      self.abort(400, msg='No feature specified.')
    feature: FeatureEntry = self.get_specified_feature(feature_id)

    # Check that stage ID is valid.
    stage_id = int(kwargs.get('stage_id', 0))
    if not stage_id:
      self.abort(400, msg='No stage specified.')
    stage = self.get_specified_stage(stage_id)
    if stage.feature_id != feature_id:
      self.abort(400, msg='Stage does not belong to given feature')

    # Check that the user has feature edit permissions.
    redirect_resp = permissions.validate_feature_edit_permission(
        self, feature_id)
    if redirect_resp:
      return redirect_resp

    parsed_args = PostIntentRequest(**self.request.get_json())
    intent_stage = INTENT_STAGES_BY_STAGE_TYPE[stage.stage_type]
    default_url = (f'{self.request.scheme}://{self.request.host}'
                   f'/feature/{feature_id}')

    # Add gate to Chromestatus URL query string if it is found.
    gate: Gate|None = None
    if parsed_args.gate_id:
      gate = Gate.get_by_id(parsed_args.gate_id)
    if gate:
      default_url += f'?gate={parsed_args.gate_id}'

    subject = f'{compute_subject_prefix(feature, intent_stage)}: {feature.name}'
    cc_emails = parsed_args.intent_cc_emails or []
    # Make sure emails are not empty and are unique.
    cc_emails = sorted(list(set([email for email in cc_emails if email])))
    params: IntentGenerationOptions = {
      'subject': subject,
      'feature_id': feature_id,
      'sections_to_show': processes.INTENT_EMAIL_SECTIONS.get(
          intent_stage, []),
      'intent_stage': intent_stage,
      'default_url': default_url,
      'intent_cc_emails': cc_emails,
    }

    cloud_tasks_helpers.enqueue_task('/tasks/email-intent-to-blink-dev',
                                     params)
    return {'message': 'Email task submitted successfully.'}
