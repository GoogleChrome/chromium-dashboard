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

from typing import Any

from chromestatus_openapi.models import (
  Activity as ActivityModel,
)
from chromestatus_openapi.models import (
  Amendment as AmendmentModel,
)
from chromestatus_openapi.models import (
  CommentsRequest,
  GetCommentsResponse,
  PatchCommentRequest,
  SuccessMessage,
)

from framework import basehandlers, permissions
from internals import approval_defs, notifier, notifier_helpers, slo
from internals.review_models import Activity, Amendment, Gate


def amendment_to_OAM(amendment: Amendment) -> AmendmentModel:
  return AmendmentModel(
      field_name = amendment.field_name,
      old_value = amendment.old_value.strip('[]'),
      new_value = amendment.new_value.strip('[]'),
  )


def activity_to_OAM(comment: Activity) -> ActivityModel:
  amendments_json = [
      amendment_to_OAM(amnd) for amnd in comment.amendments
      if amnd.old_value != 'None' or amnd.new_value != '[]']
  return ActivityModel(
      comment_id = comment.key.id(),
      feature_id = comment.feature_id,
      gate_id = comment.gate_id,
      created = str(comment.created),  # YYYY-MM-DD HH:MM:SS.SSS
      author = comment.author,
      content = comment.content,
      deleted_by = comment.deleted_by,
      amendments = amendments_json,
  )


class CommentsAPI(basehandlers.APIHandler):
  """Users may see the list of comments on one of the approvals of a feature,
   and add their own, if allowed."""

  def _should_show_comment(
      self, comment: Activity, email: str | None, is_admin: bool) -> bool:
    """Check whether a comment should be visible to the user."""
    return comment.deleted_by is None or email == comment.deleted_by or is_admin

  def do_get(self, **kwargs) -> dict[str, list[dict[str, Any]]]:
    """Return a list of all review comments on the given feature."""
    feature_id = kwargs['feature_id']
    gate_id = kwargs.get('gate_id', None)
    # Note: We assume that anyone may view approval comments.
    comments = Activity.get_activities(feature_id, gate_id)
    user = self.get_current_user()
    is_admin = permissions.can_admin_site(user)

    # Filter deleted comments the user can't see.
    user_email = user.email() if user else None
    comments = list(filter(
      lambda c: self._should_show_comment(c, user_email, is_admin), comments))

    dicts = [activity_to_OAM(c) for c in comments]
    return GetCommentsResponse(comments=dicts).to_dict()

  def do_post(self, **kwargs) -> dict[str, str]:
    """Add a review comment and possibly set a approval value."""
    feature_id = kwargs['feature_id']
    gate_id = kwargs.get('gate_id', None)
    feature = self.get_specified_feature(feature_id=feature_id)
    user = self.get_current_user(required=True)

    comment_request = CommentsRequest.from_dict(self.request.json)
    comment_content = comment_request.comment
    post_to_thread_type = comment_request.post_to_thread_type

    if comment_content:
      can_comment = (permissions.can_comment(user) or
                     permissions.can_edit_feature(user, feature_id))
      if not can_comment:
        self.abort(403, msg='User is not allowed to comment')

      comment_activity = Activity(feature_id=feature_id, gate_id=gate_id,
          author=user.email(), content=comment_content)
      comment_activity.put()

    # Notify subscribers of new comments when user posts a comment
    # via the gate column.  Also, record SLO initial response time.
    if gate_id:
      gate = Gate.get_by_id(gate_id)
      if not gate:
        self.abort(404, msg='Gate not found; notifications abort.')
      notifier_helpers.notify_subscribers_of_new_comments(
          feature, gate, user.email(), comment_content)
      approvers = approval_defs.get_approvers(gate.gate_type)
      if slo.record_comment(feature, gate, user, approvers):
        gate.put()

    # We can only be certain which intent thread we want to post to with
    # a relevant gate ID in order to get the intent_thread_url field from
    # the corresponding Stage entity.
    if post_to_thread_type and gate_id:
      notifier.post_comment_to_mailing_list(
          feature, gate_id, post_to_thread_type, user.email(), comment_content)

    # Callers don't use the JSON response for this API call.
    return SuccessMessage(message='Done').to_dict()

  def do_patch(self, **kwargs) -> dict[str, str]:
    patch_request = PatchCommentRequest.from_dict(self.request.json)
    comment: Activity = Activity.get_by_id(patch_request.comment_id)

    user = self.get_current_user(required=True)
    if not permissions.can_admin_site(user) and (
        comment and user.email() != comment.author):
      self.abort(403, msg='User does not have comment edit permissions')

    if patch_request.is_undelete:
      comment.deleted_by = None
    else:
      comment.deleted_by = user.email()
    comment.put()

    return SuccessMessage(message='Done').to_dict()
