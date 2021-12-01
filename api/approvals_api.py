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

from framework import basehandlers
from framework import permissions
from internals import approval_defs
from internals import models


class ApprovalsAPI(basehandlers.APIHandler):
  """Users may see the set of approvals on a feature, and add their own,
  if allowed."""

  def do_get(self, feature_id, field_id=None):
    """Return a list of all approval values on the given feature."""
    # Note: We assume that anyone may view approvals.
    approvals = models.Approval.get_approvals(
        feature_id=feature_id, field_id=field_id)
    dicts = [av.format_for_template(add_id=False) for av in approvals]
    data = {
        'approvals': dicts,
        }
    return data

  def do_post(self, feature_id=None):
    """Set an approval value for the specified feature."""
    field_id = self.get_int_param('fieldId')
    new_state = self.get_int_param(
        'state', validator=models.Approval.is_valid_state)
    feature = self.get_specified_feature(feature_id=feature_id)
    feature_id = feature.key.integer_id()
    user = self.get_current_user(required=True)

    approvers = approval_defs.get_approvers(field_id)
    if not permissions.can_approve_feature(user, feature, approvers):
      self.abort(403, msg='User is not an approver')

    models.Approval.set_approval(
        feature_id, field_id, new_state, user.email())

    all_approval_values = models.Approval.get_approvals(feature_id, field_id)
    if approval_defs.is_resolved(all_approval_values, field_id):
      models.Approval.clear_request(feature_id, field_id)

    # Callers don't use the JSON response for this API call.
    return {'message': 'Done'}


class ApprovalConfigsAPI(basehandlers.APIHandler):
  """Get and set the approval configs for a feature."""

  def do_get(self, feature_id):
    """Return a list of all approval configs on the given feature."""
    # Note: We assume that anyone may view approval configs.
    configs = models.ApprovalConfig.get_configs(feature_id)
    dicts = [ac.format_for_template(add_id=False) for ac in configs]
    data = {
        'configs': dicts,
        }
    return data

  def do_post(self, feature_id):
    """Set an approval config for the specified feature."""
    field_id = self.get_int_param('fieldId')
    owners_str = self.get_param('owners', required=False)
    next_action_str = self.get_param('next_action', required=False)
    additional_review = self.get_param('additional_review', required=False)
    feature = self.get_specified_feature(feature_id=feature_id)
    user = self.get_current_user(required=True)

    # A user can set the config iff they could approve.
    approvers = approval_defs.get_approvers(field_id)
    if not permissions.can_approve_feature(user, feature, approvers):
      self.abort(403, msg='User is not an approver')

    owners = None
    if owners_str:
      owners = self.split_emails('owners')

    next_action = None
    if next_action_str:
      try:
        next_action = datetime.date.fromisoformat(next_action_str)
      except ValueError:
        self.abort(400, msg='Invalid date formate or value')

    models.ApprovalConfig.set_config(
        feature_id, field_id, owners, next_action, additional_review)

    # Callers don't use the JSON response for this API call.
    return {'message': 'Done'}
