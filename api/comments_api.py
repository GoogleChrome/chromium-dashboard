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
from typing import Any

from framework import basehandlers
from framework import permissions
from internals import approval_defs
from internals.review_models import Activity, Approval, Gate, Vote
from internals import notifier


def comment_to_json_dict(comment: Activity) -> dict[str, Any]:
  return {
      'comment_id': comment.key.id(),
      'feature_id': comment.feature_id,
      'gate_id': comment.gate_id,
      'created': str(comment.created),  # YYYY-MM-DD HH:MM:SS.SSS
      'author': comment.author,
      'content': comment.content,
      'deleted_by': comment.deleted_by
      }


class CommentsAPI(basehandlers.APIHandler):
  """Users may see the list of comments on one of the approvals of a feature,
   and add their own, if allowed."""

  def _should_show_comment(
      self, comment: Activity, email: str, is_admin: bool) -> bool:
    """Check whether a comment should be visible to the user."""
    return comment.deleted_by is None or email == comment.deleted_by or is_admin

  def do_get(self, **kwargs) -> dict[str, list[dict[str, Any]]]:
    """Return a list of all review comments on the given feature."""
    feature_id = kwargs['feature_id']
    field_id = kwargs.get('field_id', None)
    # Note: We assume that anyone may view approval comments.
    comments = Activity.get_activities(
        feature_id, field_id, comments_only=True)
    user = self.get_current_user(required=True)
    is_admin = permissions.can_admin_site(user)
    
    # Filter deleted comments the user can't see.
    comments = list(filter(
      lambda c: self._should_show_comment(c, user.email(), is_admin), comments))

    dicts = [comment_to_json_dict(c) for c in comments]
    return {'comments': dicts}

  def do_post(self, **kwargs) -> dict[str, str]:
    """Add a review comment and possibly set a approval value."""
    feature_id = kwargs['feature_id']
    gate_type = kwargs.get('gate_type', None)
    new_state = self.get_int_param(
        'state', required=False,
        validator=Vote.is_valid_state)
    feature = self.get_specified_feature(feature_id=feature_id)
    user = self.get_current_user(required=True)
    post_to_approval_field_id = self.get_param(
        'postToApprovalFieldId', required=False)

    if gate_type is not None and new_state is not None:
      old_approvals = Approval.get_approvals(
          feature_id=feature_id, field_id=gate_type,
          set_by=user.email())

      approvers = approval_defs.get_approvers(gate_type)
      if not permissions.can_approve_feature(user, feature, approvers):
        self.abort(403, msg='User is not an approver')
      Approval.set_approval(
          feature.key.integer_id(), gate_type, new_state, user.email())
      approval_defs.set_vote(feature_id, gate_type, new_state, user.email())

    comment_content = self.get_param('comment', required=False)

    if comment_content:
      # TODO(danielrsmith): After UI changes, gate_id should be passed in
      # post request and not queried for.
      gates: list[Gate] = Gate.query(
          Gate.feature_id == feature_id, Gate.gate_type == gate_type).fetch()
      gate_id = None
      if len(gates) > 0:
        gate_id = gates[0].key.integer_id()
      # Schema migration double-write.
      comment_activity = Activity(feature_id=feature_id, gate_id=gate_id,
          author=user.email(), content=comment_content)
      comment_activity.put()

    if post_to_approval_field_id:
      notifier.post_comment_to_mailing_list(
          feature, post_to_approval_field_id, user.email(), comment_content)

    # Callers don't use the JSON response for this API call.
    return {'message': 'Done'}

  def do_patch(self, **kwargs) -> dict[str, str]:
    comment_id = self.get_param('commentId', required=True)
    comment: Activity = Activity.get_by_id(comment_id)

    user = self.get_current_user(required=True)
    if not permissions.can_admin_site(user) and (
        comment and user.email() != comment.author):
      self.abort(403, msg='User does not have comment edit permissions')

    is_undelete = self.get_param('isUndelete', required=True)
    if is_undelete:
      comment.deleted_by = None
    else:
      comment.deleted_by = user.email()
    comment.put()

    return {'message': 'Done'}
