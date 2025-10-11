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

from api.converters import feature_entry_to_json_verbose
from api.intents_api import compute_subject_prefix
from internals.core_enums import INTENT_DRAFT_TYPES_BY_STAGE_TYPE, IntentDraftType
from internals import stage_helpers
from internals.core_models import FeatureEntry, Stage
from internals.review_models import Gate
from framework import basehandlers

VIEW_FEATURE_URL = '/feature'

class IntentEmailPreviewHandler(basehandlers.FlaskHandler):
  """Show a preview of an intent email. Used for testing the intent template."""

  TEMPLATE_PATH = 'blink/intent_to_implement.html'

  def get_template_data(self, **kwargs):
    f = self.get_validated_entity(kwargs.get('feature_id'), FeatureEntry)
    s = self.get_validated_entity(kwargs.get('stage_id'), Stage)
    intent_type = INTENT_DRAFT_TYPES_BY_STAGE_TYPE[s.stage_type]

    gate_id = kwargs.get('gate_id', None)
    gate = None
    # Find the gate to add to the Chromestatus URL.
    if gate_id:
      gate = Gate.get_by_id(gate_id)
      if not gate:
        self.abort(404, f'Gate not found for given ID {gate_id}')

    page_data = self.get_page_data(f, intent_type, gate)
    return page_data

  def get_page_data(
    self,
    f: FeatureEntry,
    intent_type: IntentDraftType,
    gate: Gate | None=None
  ):
    """Return a dictionary of data used to render the intent template."""

    default_url = (f'{self.request.scheme}://{self.request.host}'
                   f'{VIEW_FEATURE_URL}/{f.key.integer_id()}')
    if gate:
      default_url += f'?gate={gate.key.integer_id()}'

    stage_info = stage_helpers.get_stage_info_for_templates(f)
    page_data = {
        'subject_prefix': compute_subject_prefix(f.feature_type, intent_type),
        'feature': feature_entry_to_json_verbose(f),
        'stage_info': stage_info,
        'should_render_mstone_table': stage_info['should_render_mstone_table'],
        'should_render_intents': stage_info['should_render_intents'],
        'intent_type': intent_type,
        'default_url': default_url,
    }

    return page_data
