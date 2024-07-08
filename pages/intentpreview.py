# -*- coding: utf-8 -*-
# Copyright 2021 Google Inc.
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

# from google.appengine.api import users
from api.converters import feature_entry_to_json_verbose

from internals import core_enums
from internals import processes
from internals import stage_helpers
from internals.core_models import Stage
from internals.review_models import Gate
from framework import basehandlers
from framework import permissions

INTENT_PARAM = 'intent'
LAUNCH_PARAM = 'launch'
VIEW_FEATURE_URL = '/feature'


def compute_subject_prefix(feature, intent_stage):
  """Return part of the subject line for an intent email."""

  if intent_stage == core_enums.INTENT_IMPLEMENT:
    if feature.feature_type == core_enums.FEATURE_TYPE_DEPRECATION_ID:
      return 'Intent to Deprecate and Remove'
    else:
      return 'Intent to Prototype'
  elif intent_stage == core_enums.INTENT_EXPERIMENT:
    return 'Ready for Developer Testing'
  elif intent_stage == core_enums.INTENT_ORIGIN_TRIAL:
    if feature.feature_type == core_enums.FEATURE_TYPE_DEPRECATION_ID:
      return 'Request for Deprecation Trial'
    else:
      return 'Intent to Experiment'
  elif intent_stage == core_enums.INTENT_EXTEND_ORIGIN_TRIAL:
    if feature.feature_type == core_enums.FEATURE_TYPE_DEPRECATION_ID:
      return 'Intent to Extend Deprecation Trial'
    else:
      return 'Intent to Extend Experiment'
  elif intent_stage == core_enums.INTENT_SHIP:
    if feature.feature_type == core_enums.FEATURE_TYPE_CODE_CHANGE_ID:
      return 'Web-Facing Change PSA'
    else:
      return 'Intent to Ship'
  elif intent_stage == core_enums.INTENT_REMOVED:
    return 'Intent to Extend Deprecation Trial'

  return f'Intent stage "{core_enums.INTENT_STAGES[intent_stage]}"'


class IntentEmailPreviewHandler(basehandlers.FlaskHandler):
  """Show a preview of an intent email, as appropriate to the feature stage."""

  TEMPLATE_PATH = 'admin/features/launch.html'

  def get_template_data(self, **kwargs):
    feature_id = kwargs.get('feature_id', None)
    intent_stage = kwargs.get('intent_stage', None)
    gate_id = kwargs.get('gate_id', None)
    if not gate_id and not intent_stage:
      self.abort(400, 'Invalid gate ID and intent stage')

    # Validate the user has edit permissions and redirect if needed.
    redirect_resp = permissions.validate_feature_edit_permission(
        self, feature_id)
    if redirect_resp:
      return redirect_resp

    f = self.get_specified_feature(feature_id=feature_id)
    gate = None
    # Find the gate to add to the Chromestatus URL, and make sure the intent
    # stage matches the gate.
    if gate_id:
      gate = Gate.get_by_id(gate_id)
      if not gate:
        self.abort(404, f'Gate not found for given ID {gate_id}')
      stage = Stage.get_by_id(gate.stage_id)
      intent_stage = (core_enums.INTENT_STAGES_BY_STAGE_TYPE[stage.stage_type]
                      if stage else f.intent_stage)

    page_data = self.get_page_data(feature_id, f, intent_stage, gate)
    return page_data

  def get_page_data(self, feature_id, f, intent_stage, gate: Gate | None=None):
    """Return a dictionary of data used to render the page."""

    default_url = (f'{self.request.scheme}://{self.request.host}'
                   f'{VIEW_FEATURE_URL}/{feature_id}')
    if gate:
      default_url += f'?gate={gate.key.integer_id()}'

    stage_info = stage_helpers.get_stage_info_for_templates(f)
    page_data = {
        'subject_prefix': compute_subject_prefix(f, intent_stage),
        'feature': feature_entry_to_json_verbose(f),
        'stage_info': stage_info,
        'should_render_mstone_table': stage_info['should_render_mstone_table'],
        'should_render_intents': stage_info['should_render_intents'],
        'sections_to_show': processes.INTENT_EMAIL_SECTIONS.get(
            intent_stage, []),
        'intent_stage': intent_stage,
        'default_url': default_url,
    }

    if LAUNCH_PARAM in self.request.args:
      page_data[LAUNCH_PARAM] = True
    if INTENT_PARAM in self.request.args:
      page_data[INTENT_PARAM] = True

    return page_data
