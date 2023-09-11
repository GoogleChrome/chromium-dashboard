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
    
    return {'stages': [stage_to_json_dict(s) for s in stages_with_requests]}
