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

from api.converters import stage_to_json_dict
from internals.core_enums import OT_EXTENSION_STAGE_TYPES
from internals.core_models import Stage

from framework import basehandlers
from framework import permissions


class OriginTrialsRequests(basehandlers.FlaskHandler):
  """Display any origin trials requests."""

  TEMPLATE_PATH = 'admin/features/ot_requests.html'

  @permissions.require_admin_site
  def get_template_data(self, **kwargs):
    stages_with_requests = Stage.query(
        Stage.ot_action_requested == True).fetch()
    creation_stages = []
    extension_stages = []
    for stage in stages_with_requests:
      stage_dict = stage_to_json_dict(stage)
      # Add the request note that is not typically visible to non-admins.
      if stage.ot_request_note:
        stage_dict['ot_request_note'] = stage.ot_request_note
      # Group up creation and extension requests.
      if stage_dict['stage_type'] in OT_EXTENSION_STAGE_TYPES:
        # Information will be needed from the original OT stage.
        ot_stage = Stage.get_by_id(stage_dict['ot_stage_id'])
        ot_stage_dict = stage_to_json_dict(ot_stage)
        # Supply both the OT stage and the extension stage.
        extension_stages.append({
            'ot_stage': ot_stage_dict,
            'extension_stage': stage_dict,
          })
      else:
        creation_stages.append(stage_dict)

    return {
        'creation_stages': creation_stages,
        'extension_stages': extension_stages,
      }
