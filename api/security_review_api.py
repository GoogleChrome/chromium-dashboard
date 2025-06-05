# Copyright 2025 Google Inc.
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

from chromestatus_openapi.models import (
    CreateLaunchIssueRequest, SuccessMessage)

from framework import permissions
from framework import basehandlers, origin_trials_client
from internals.core_models import FeatureEntry
from internals.review_models import Gate

class SecurityReviewAPI(basehandlers.APIHandler):

  def do_post(self, **kwargs):
    """Endpoint to create a new security review in IssueTracker.

    Returns:
      The issue ID if the security review issue was successfully created.
    """
    body = CreateLaunchIssueRequest.from_dict(
        self.get_json_param_dict())
    # Check that feature ID is provided.
    if body.feature_id is None:
      self.abort(400, msg='No feature specified.')
    if not isinstance(body.feature_id, int):
      self.abort(400, msg='Invalid feature ID.')
    feature: FeatureEntry | None = FeatureEntry.get_by_id(body.feature_id)
    if feature is None:
      self.abort(404, msg=f'Feature {body.feature_id} not found')
    if feature.launch_issue_id is not None:
      self.abort(400, msg='Feature already has a security review issue.')

    # Validate the user has edit permissions and redirect if needed.
    redirect_resp = permissions.validate_feature_edit_permission(
        self, body.feature_id)
    if redirect_resp:
      self.abort(403, msg='User does not have permission to edit this feature.')

    # Check that gate_id is provided.
    if body.gate_id is None:
      self.abort(400, msg='No gate specified.')
    if not isinstance(body.gate_id, int):
      self.abort(400, msg='Invalid gate ID.')
    gate: Gate | None = Gate.get_by_id(body.gate_id)
    if gate is None:
      self.abort(404, msg=f'Gate {body.gate_id} not found')

    try:
      issue_id, failed_reason = (
          origin_trials_client.create_launch_issue(
              body.feature_id, body.gate_id, feature.continuity_id))
    except requests.exceptions.RequestException:
      self.abort(500, 'Error obtaining origin trial data from API')
    except KeyError:
      self.abort(500, 'Malformed response from origin trials API')

    if issue_id is not None:
      feature.launch_issue_id = issue_id
      feature.put()
    if failed_reason:
      self.abort(500, failed_reason)
    return SuccessMessage(message=f'Security review issue {issue_id} created')
