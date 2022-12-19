# -*- coding: utf-8 -*-
# Copyright 2022 Google Inc.
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

import datetime
import logging
import re
from typing import Any, Optional

from api import converters
from framework import basehandlers
from framework import permissions
from internals import approval_defs
from internals.review_models import Approval, ApprovalConfig, Gate, Vote


class VotesAPI(basehandlers.APIHandler):
  """Users may see the set of votes on a feature, and add their own,
  if allowed."""

  def do_get(self, **kwargs) -> dict[str, list[dict[str, Any]]]:
    """Return a list of all vote values for a given feature."""
    feature_id = kwargs['feature_id']
    gate_id = kwargs['gate_id']
    # Note: We assume that anyone may view approvals.
    votes = Vote.get_votes(feature_id=feature_id, gate_id=gate_id)
    dicts = [converters.vote_value_to_json_dict(v) for v in votes]
    return {'votes': dicts}

  def do_post(self, **kwargs) -> dict[str, str]:
    """Set a user's vote value for the specified feature and gate."""
    feature_id = kwargs['feature_id']
    gate_id = kwargs['gate_id']
    new_state = self.get_int_param(
        'state', validator=Approval.is_valid_state)
    feature = self.get_specified_feature(feature_id=feature_id)
    user = self.get_current_user(required=True)
    gate = Gate.get_by_id(gate_id)
    if not gate:
      self.abort(404, msg='Gate not found')

    approvers = approval_defs.get_approvers(gate.gate_type)
    if not permissions.can_approve_feature(user, feature, approvers):
      self.abort(403, msg='User is not an approver')

    # Note: We no longer write Approval entities.

    gates: list[Gate] = Gate.query(
        Gate.feature_id == feature_id, Gate.gate_id == gate_id).fetch()
    if len(gates) == 0:
      return {'message': 'No gate found for given feature ID and gate ID.'}
    new_state = self.get_int_param('state', validator=Vote.is_valid_state)
    approval_defs.set_vote(feature_id, None, new_state,
        user.email(), gate_id)

    # Callers don't use the JSON response for this API call.
    return {'message': 'Done'}


class GatesAPI(basehandlers.APIHandler):
  """Get gates for a feature."""

  def do_get(self, **kwargs) -> dict[str, Any]:
    """Return a list of all gates associated with the given feature."""
    feature_id = kwargs.get('feature_id', None)
    gates: list[Gate] = Gate.query(Gate.feature_id == feature_id).fetch()

    # No gates associated with this feature.
    if len(gates) == 0:
      return {
          'gates': [],
          'possible_owners': {}
          }

    dicts = [converters.gate_value_to_json_dict(g) for g in gates]
    possible_owners_by_gate_type: dict[int, list[str]] = {
        gate_type: approval_defs.get_approvers(gate_type)
        for gate_type in approval_defs.APPROVAL_FIELDS_BY_ID
        }

    return {
        'gates': dicts,
        'possible_owners': possible_owners_by_gate_type
        }
