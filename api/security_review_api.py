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

"""
This module provides the API handler for creating security review issues.
"""

import logging

import requests
from chromestatus_openapi.models import CreateLaunchIssueRequest, SuccessMessage

from framework import basehandlers, origin_trials_client, permissions
from internals.core_models import FeatureEntry
from internals.review_models import Gate

class SecurityReviewAPI(basehandlers.APIHandler):
  """API handler for creating security review issues in the issue tracker."""

  def do_post(self, **kwargs) -> SuccessMessage:
    """
    Endpoint to create a new security review in IssueTracker.

    The request body should be a JSON object with the following fields:
    - feature_id: The ID of the feature to create the review for.
    - gate_id: The ID of the gate associated with this review.

    Returns:
      A success message containing the newly created issue ID.
    """
    try:
      body = CreateLaunchIssueRequest.from_dict(self.get_json_param_dict())
    except Exception:
      self.abort(400, msg='Could not parse request body.')

    feature = self.get_validated_entity(
      body.feature_id, FeatureEntry)

    if feature.security_launch_issue_id is not None:
      self.abort(
        400,msg=(f'Feature {feature.key.integer_id()} '
                 'already has a security review issue.'))

    permission_error = permissions.validate_feature_edit_permission(
      self, feature.key.integer_id())
    if permission_error:
      self.abort(
        403, msg='User does not have permission to edit this feature.')

    gate = self.get_validated_entity(body.gate_id, Gate)

    try:
      issue_id, failed_reason = origin_trials_client.create_launch_issue(
        feature_id=feature.key.integer_id(),
        gate_id=gate.key.integer_id(),
        security_continuity_id=feature.security_continuity_id
      )
    except requests.exceptions.RequestException as e:
      logging.error(f"Error calling origin trials API: {e}")
      self.abort(
        500, 'Error communicating with the issue creation service.')
    except KeyError:
      logging.error("Malformed response from origin trials API.")
      self.abort(
        500, 'Malformed response from the issue creation service.')

    if failed_reason:
      self.abort(500, msg=failed_reason)

    if issue_id is None:
      # If no issue was created and no reason was given, it's an
      # unexpected state.
      logging.error("Issue creation returned no ID and no failure reason.")
      self.abort(
        500, 'Issue creation failed for an unknown reason.')

    feature.security_launch_issue_id = issue_id
    feature.put()

    return SuccessMessage(
      message=f'Security review issue {issue_id} created successfully.')