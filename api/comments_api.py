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




import logging

from framework import basehandlers
from framework import permissions
from internals import approval_defs
from internals import models


class CommentsAPI(basehandlers.APIHandler):
  """Users may see the list of comments on one of the approvals of a feature,
   and add their own, if allowed."""

  def do_get(self, feature_id, field_id=None):
    """Return a list of all review comments on the given feature."""
    # Note: We assume that anyone may view approval comments.
    comments = models.Comment.get_comments(feature_id, field_id)
    dicts = [ac.format_for_template(add_id=False) for ac in comments]
    data = {
        'comments': dicts,
        }
    return data

  def do_post(self, feature_id, field_id=None):
    """Add a review comment and possibly set a approval value."""
    new_state = self.get_int_param(
        'state', required=False,
        validator=models.Approval.is_valid_state)
    feature = self.get_specified_feature(feature_id=feature_id)
    user = self.get_current_user(required=True)

    old_state = None
    if field_id is not None and new_state is not None:
      old_approvals = models.Approval.get_approvals(
          feature_id=feature_id, field_id=field_id,
          set_by=user.email())
      if old_approvals:
        old_state = old_approvals[0].state

      approvers = approval_defs.get_approvers(field_id)
      if not permissions.can_approve_feature(user, feature, approvers):
        self.abort(403, msg='User is not an approver')
      models.Approval.set_approval(
          feature.key.integer_id(), field_id, new_state, user.email())

    comment_content = self.get_param('comment', required=False)

    if comment_content or new_state is not None:
      comment = models.Comment(
          feature_id=feature_id, field_id=field_id,
          author=user.email(), content=comment_content,
          old_approval_state=old_state,
          new_approval_state=new_state)
      comment.put()

    # TODO(jrobbins): Trigger notificaton emails (or not).

    # Callers don't use the JSON response for this API call.
    return {'message': 'Done'}

  # TODO(jrobbins): do_patch to soft-delete comments
