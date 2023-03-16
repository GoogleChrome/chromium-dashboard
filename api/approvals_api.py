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

import datetime
import logging
import re
from typing import Any, Optional

from api import converters
from framework import basehandlers
from framework import permissions
from internals import approval_defs
from internals.legacy_models import Approval, ApprovalConfig
from internals.review_models import Gate, Vote


class ApprovalsAPI(basehandlers.APIHandler):
  """Users may see the set of approvals on a feature, and add their own,
  if allowed."""

  def do_get(self, **kwargs) -> dict[str, list[dict[str, Any]]]:
    """Return a list of all vote values for a given feature."""
    feature_id = kwargs['feature_id']
    gate_type = kwargs.get('gate_type', None)
    # Note: We assume that anyone may view approvals.
    votes = Vote.get_votes(feature_id=feature_id, gate_type=gate_type)
    dicts = [converters.vote_value_to_json_dict(v) for v in votes]
    return {'approvals': dicts}

  def do_post(self, **kwargs) -> dict[str, str]:
    """Set an approval value for the specified feature."""
    ## Handle writing old Approval entity. ##
    feature_id = kwargs.get('feature_id', None)
    # field_id is now called gate_type.
    gate_type = self.get_int_param('gateType')
    if not feature_id:
      self.get_int_param('featureId')
    new_state = self.get_int_param(
        'state', validator=Approval.is_valid_state)
    feature = self.get_specified_feature(feature_id=feature_id)
    user = self.get_current_user(required=True)

    approvers = approval_defs.get_approvers(gate_type)
    if not permissions.can_approve_feature(user, feature, approvers):
      self.abort(403, msg='User is not an approver')

    Approval.set_approval(
        feature_id, gate_type, new_state, user.email())
    approval_defs.set_vote(feature_id, gate_type, new_state, user.email())

    all_approval_values = Approval.get_approvals(
        feature_id=feature_id, field_id=gate_type)
    logging.info(
        'found approvals %r',
        [appr.key.integer_id() for appr in all_approval_values])
    if approval_defs.is_resolved(all_approval_values, gate_type):
      Approval.clear_request(feature_id, gate_type)

    ## Write to new Vote and Gate entities. ##
    # TODO(danielrsmith): Gate ID should be passed as a POST request param,
    # rather than trying to discern it from the gate type.
    gates: list[Gate] = Gate.query(
        Gate.feature_id == feature_id, Gate.gate_type == gate_type).fetch()
    if len(gates) == 0:
      return {'message': 'No gate found for given feature ID and gate type.'}
    new_state = self.get_int_param('state', validator=Vote.is_valid_state)
    approval_defs.set_vote(feature_id, gate_type, new_state,
        user.email(), gates[0].key.integer_id())

    # Callers don't use the JSON response for this API call.
    return {'message': 'Done'}


def approval_config_to_json_dict(appr_cfg):
  if appr_cfg.next_action:
    next_action = str(appr_cfg.next_action)
  else:
    next_action = None
  return {
      'feature_id': appr_cfg.feature_id,
      'field_id': appr_cfg.field_id,
      'owners': appr_cfg.owners,
      'next_action': next_action,  # YYYY-MM-DD or None
      'additional_review': appr_cfg.additional_review,
      }


class ApprovalConfigsAPI(basehandlers.APIHandler):
  """Get and set the approval configs for a feature."""

  def do_get(self, **kwargs):
    """Return a list of all approval configs on the given feature."""
    feature_id = kwargs.get('feature_id', None)
    # Note: We assume that anyone may view approval configs.
    configs = ApprovalConfig.get_configs(feature_id)
    dicts = [approval_config_to_json_dict(ac) for ac in configs]
    possible_owners_by_field = {
        field_id: approval_defs.get_approvers(field_id)
        for field_id in approval_defs.APPROVAL_FIELDS_BY_ID
    }
    data = {
        'configs': dicts,
        'possible_owners': possible_owners_by_field,
        }
    return data

  def do_post(self, **kwargs):
    """Set an approval config for the specified feature."""
    feature_id = kwargs['feature_id']
    field_id = self.get_int_param('fieldId')
    owners_str = self.get_param('owners')
    next_action_str = self.get_param('nextAction')
    additional_review = self.get_param('additionalReview')
    feature = self.get_specified_feature(feature_id=feature_id)
    user = self.get_current_user(required=True)

    # A user can set the config iff they could approve.
    approvers = approval_defs.get_approvers(field_id)
    if not permissions.can_approve_feature(user, feature, approvers):
      self.abort(403, msg='User is not an approver')

    owners = None
    if owners_str is not None:
      owners = [addr.strip() for addr in re.split(',', owners_str)
                if addr.strip()]

    next_action = None
    if next_action_str:
      try:
        next_action = datetime.date.fromisoformat(next_action_str)
      except ValueError:
        self.abort(400, msg='Invalid date formate or value')

    ApprovalConfig.set_config(
        feature_id, field_id, owners, next_action, additional_review)

    # Callers don't use the JSON response for this API call.
    return {'message': 'Done'}
