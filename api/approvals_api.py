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

import logging

from framework import basehandlers
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
    json_body = self.request.get_json(force=True)
    feature_id = json_body.get('featureId')
    field_id = json_body.get('fieldId')
    new_state = json_body.get('state')

    if type(feature_id) != int:
      logging.info('Invalid feature_id: %r', feature_id)
      self.abort(400)

    if type(field_id) != int:
      logging.info('Invalid field_id: %r', field_id)
      self.abort(400)

    feature = models.Feature.get_feature(feature_id)
    if not feature:
      logging.info('feature not found: %r', feature_id)
      self.abort(404)

    user = self.get_current_user()
    if not user:
      logging.info('User must be signed in before approving')
      self.abort(400)

    # TODO(jrobbins): Validate field_id

    approvers = approval_defs.get_approvers(field_id)
    if not permissions.can_approve_feature(user, feature, approvers):
      logging.info('User is not an approver')
      self.abort(403)

    models.Approval.set_approval(feature_id, field_id, new_state, user.email())
    # Callers don't use the JSON response for this API call.
    return {'message': 'Done'}
