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

from framework import basehandlers
from framework import permissions
from internals import approval_defs
from internals import review_models


def approval_value_to_json_dict(appr):
  return {
      'feature_id': appr.feature_id,
      'field_id': appr.field_id,
      'state': appr.state,
      'set_on': str(appr.set_on),  # YYYY-MM-DD HH:MM:SS.SSS
      'set_by': appr.set_by,
      }


class ApprovalsAPI(basehandlers.APIHandler):
  """Users may see the set of approvals on a feature, and add their own,
  if allowed."""

  def do_get(self, feature_id, field_id=None):
    """Return a list of all approval values on the given feature."""
    # Note: We assume that anyone may view approvals.
    approvals = review_models.Approval.get_approvals(
        feature_id=feature_id, field_id=field_id)
    dicts = [approval_value_to_json_dict(av) for av in approvals]
    data = {
        'approvals': dicts,
        }
    return data

  def do_post(self, feature_id=None):
    """Set an approval value for the specified feature."""
    field_id = self.get_int_param('fieldId')
    new_state = self.get_int_param(
        'state', validator=review_models.Approval.is_valid_state)
    feature = self.get_specified_feature(feature_id=feature_id)
    feature_id = feature.key.integer_id()
    user = self.get_current_user(required=True)

    approvers = approval_defs.get_approvers(field_id)
    if not permissions.can_approve_feature(user, feature, approvers):
      self.abort(403, msg='User is not an approver')

    review_models.Approval.set_approval(
        feature_id, field_id, new_state, user.email())
    approval_defs.set_vote(feature_id, field_id, new_state, user.email())

    all_approval_values = review_models.Approval.get_approvals(
        feature_id=feature_id, field_id=field_id)
    logging.info(
        'found approvals %r',
        [appr.key.integer_id() for appr in all_approval_values])
    if approval_defs.is_resolved(all_approval_values, field_id):
      review_models.Approval.clear_request(feature_id, field_id)

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

  def do_get(self, feature_id):
    """Return a list of all approval configs on the given feature."""
    # Note: We assume that anyone may view approval configs.
    configs = review_models.ApprovalConfig.get_configs(feature_id)
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

  def do_post(self, feature_id):
    """Set an approval config for the specified feature."""
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

    review_models.ApprovalConfig.set_config(
        feature_id, field_id, owners, next_action, additional_review)

    # Callers don't use the JSON response for this API call.
    return {'message': 'Done'}
