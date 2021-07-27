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

from __future__ import division
from __future__ import print_function

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
    approvals = models.Approval.get_approvals(feature_id, field_id=field_id)
    dicts = [av.format_for_template(add_id=False) for av in approvals]
    data = {
        'approvals': dicts,
        }
    return data

  def do_post(self):
    """Set an approval value for the specified feature."""
    field_id = self.get_int_param('fieldId')
    new_state = self.get_int_param(
        'state', validator= models.Approval.is_valid_state)
    feature = self.get_specified_feature()
    user = self.get_current_user(required=True)

    approvers = approval_defs.get_approvers(field_id)
    if not permissions.can_approve_feature(user, feature, approvers):
      self.abort(403, msg='User is not an approver')

    models.Approval.set_approval(
        feature.key.integer_id(), field_id, new_state, user.email())
    # Callers don't use the JSON response for this API call.
    return {'message': 'Done'}
