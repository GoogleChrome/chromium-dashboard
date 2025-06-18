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
from chromestatus_openapi.models import (
  CreateLaunchIssueRequest,
  SuccessMessage,
  VerifyContinuityIssueResponse
)

from framework import basehandlers, origin_trials_client, permissions

import requests

import requests
from chromestatus_openapi.models import CreateLaunchIssueRequest, SuccessMessage

from framework import basehandlers, origin_trials_client, permissions
from internals.core_models import FeatureEntry
from internals.review_models import Gate

class SecurityReviewAPI(basehandlers.APIHandler):
  """API handler for creating security review issues in the issue tracker."""

  def do_get(self, **kwargs) -> VerifyContinuityIssueResponse:
    """Endpoint to verify a continuity issue ID and return its launch issue ID.

    This endpoint is used to check if a continuity-tracking bug from
    a security review is valid and linked to an existing feature launch bug
    in Issue Tracker.

    Args:
      **kwargs: Must contain 'continuity_id'.
        continuity_id: The integer ID of the continuity-tracking bug.

    Returns:
      A VerifyContinuityIssueResponse object containing the associated
        launch bug ID, if found, as well as a possible verification failure
        reason.
    """
    continuity_id_arg = kwargs.get('continuity_id')
    if continuity_id_arg is None:
      self.abort(400, msg='No continuity ID provided.')
    try:
      continuity_id = int(continuity_id_arg)
    except (ValueError, TypeError):
      self.abort(400, msg='A valid continuity ID parameter is required.')

    try:
      resp_dict = origin_trials_client.verify_continuity_issue(continuity_id)
    except requests.exceptions.RequestException as e:
      self.abort(500, msg=f'Error communicating with origin trials API: {e}')

    return VerifyContinuityIssueResponse.from_dict(resp_dict)

  def do_post(self, **kwargs) -> SuccessMessage:
    """
    Endpoint to create a new security review in IssueTracker.

    The request body should be a JSON object with the following fields:
    - feature_id: The ID of the feature to create the review for.
    - gate_id: The ID of the gate associated with this review.

    Returns:
      A success message containing the newly created issue ID.
    """
    body = CreateLaunchIssueRequest.from_dict(self.get_json_param_dict())

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
      logging.error(f'Error calling origin trials API: {e}')
      self.abort(
        500, 'Error communicating with the issue creation service.')
    except KeyError:
      logging.error('Malformed response from origin trials API.')
      self.abort(
        500, 'Malformed response from the issue creation service.')

    if issue_id is None and failed_reason is None:
      # This is an unexpected state.
      logging.error("Issue creation returned no ID and no failure reason.")
      self.abort(
        500, 'Issue creation failed for an unknown reason.')

    if issue_id is not None:
      feature.security_launch_issue_id = issue_id
      feature.put()

    if failed_reason:
      self.abort(500, msg=failed_reason)
    return SuccessMessage(
      message=f'Security review issue {issue_id} created successfully.')
