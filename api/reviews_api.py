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

from datetime import datetime
import logging
from typing import Any, Tuple

from chromestatus_openapi.models import (GetVotesResponse, GetGateResponse, PatchGateRequest, SuccessMessage)
from google.cloud import ndb
from google.cloud.ndb.tasklets import Future  # for type checking only

from api import converters
from framework import basehandlers, permissions
from framework.users import User
from internals import approval_defs, notifier_helpers, self_certify
from internals.core_enums import *
from internals.core_models import FeatureEntry, Stage
from internals.review_models import Gate, Vote, Amendment, Activity


def get_user_feature_and_gate(handler, kwargs) -> Tuple[
    User, FeatureEntry, Gate, int, int]:
  """Get common parameters from the request."""
  feature_id: int = kwargs['feature_id']
  gate_id: int = kwargs['gate_id']
  fe: FeatureEntry = handler.get_specified_feature(feature_id=feature_id)

  user: User = handler.get_current_user(required=True)
  gate: Gate = Gate.get_by_id(gate_id)
  if not gate:
    handler.abort(404, msg='Gate not found')
  if gate.feature_id != feature_id:
    handler.abort(400, msg='Mismatched feature and gate')

  return user, fe, gate, feature_id, gate_id


class VotesAPI(basehandlers.APIHandler):
  """Users may see the set of votes on a feature, and add their own,
  if allowed."""

  def do_get(self, **kwargs) -> dict[str, list[dict[str, Any]]]:
    """Return a list of all vote values for a given feature."""
    feature_id = kwargs['feature_id']
    gate_id = kwargs.get('gate_id', None)
    # Note: We assume that anyone may view approvals.
    votes = Vote.get_votes(feature_id=feature_id, gate_id=gate_id)
    dicts = [converters.vote_value_to_json_dict(v) for v in votes]
    return GetVotesResponse.from_dict({'votes': dicts}).to_dict()

  def do_post(self, **kwargs) -> dict[str, str]:
    """Set a user's vote value for the specified feature and gate."""
    user, fe, gate, feature_id, gate_id = get_user_feature_and_gate(
        self, kwargs)
    new_state = self.get_int_param('state', validator=Vote.is_valid_state)

    old_votes = Vote.get_votes(
        feature_id=feature_id, gate_id=gate_id, set_by=user.email())
    old_state = old_votes[0].state if old_votes else Vote.NO_RESPONSE
    self.require_permissions(user, fe, gate, new_state)
    self.check_voting_rules(gate, new_state)

    old_gate_state = gate.state
    new_gate_state = approval_defs.set_vote(feature_id, None, new_state,
        user.email(), gate_id)
    fe.updated = datetime.now()
    fe.put()

    # Send any notifications necessary if the gate is newly approved.
    recently_approved = (old_gate_state not in Gate.APPROVED_STATES and
                         new_gate_state in Gate.APPROVED_STATES)
    if recently_approved:
      stage = Stage.get_by_id(gate.stage_id)
      notifier_helpers.notify_approvals(fe, stage, gate)

    if new_state in (Vote.REVIEW_REQUESTED, Vote.NA_REQUESTED):
      old_assignees = gate.assignee_emails[:]
      approval_defs.auto_assign_reviewer(gate)
      new_assignees = gate.assignee_emails[:]
      if old_assignees != new_assignees:
        amendment = Amendment(
            field_name='review_assignee',
            old_value=', '.join(old_assignees),
            new_value=', '.join(new_assignees))
        activity = Activity(
            feature_id=fe.key.integer_id(), gate_id=gate_id,
            author=user.email(), amendments=[amendment])
        activity.put()
        # Note: We don't notify assignee about autoassignment, because they
        # will get a notification of review state change anyway.

      notifier_helpers.notify_approvers_of_reviews(
          fe, gate, new_state, user.email())
    else:
      notifier_helpers.notify_subscribers_of_vote_changes(
          fe, gate, user.email(), new_state, old_state)

    # Callers don't use the JSON response for this API call.
    return SuccessMessage(message='Done').to_dict()

  def require_permissions(self, user, feature, gate, new_state):
    """Abort the request if the user lacks permission to set this vote."""
    is_requesting_review = new_state in (Vote.REVIEW_REQUESTED, Vote.NA_REQUESTED)
    is_approving = new_state in Gate.APPROVED_STATES
    is_editor = permissions.can_edit_feature(user, feature.key.integer_id())
    approvers = approval_defs.get_approvers(gate.gate_type)
    is_approver = permissions.can_review_gate(user, feature, gate, approvers)

    if is_requesting_review and is_editor:
      return

    if is_approving and is_editor and self_certify.is_eligible(gate):
      return

    if is_approver:
      return

    if is_requesting_review:
      self.abort(403, msg='User may not request a review')
    else:
      self.abort(403, msg='User is not an approver')

  def check_voting_rules(self, gate, new_state):
    """Abort the request if the user casts a vote that we cannot accept."""
    if (new_state == Vote.NA_VERIFIED and
        gate.state not in [Vote.NA_SELF, Vote.NA_VERIFIED]):
      self.abort(
          400, msg='User may not verify when gate was not self-certified')


class GatesAPI(basehandlers.APIHandler):
  """Get gates for a feature."""

  def do_get(self, **kwargs) -> dict[str, Any]:
    """Return a list of all gates associated with the given feature."""
    feature_id = kwargs.get('feature_id', None)
    feature: FeatureEntry = self.get_specified_feature(feature_id=feature_id)
    gates: list[Gate] = []

    if not feature.deleted or self.get_bool_arg('include_deleted'):
      gates = Gate.query(Gate.feature_id == feature_id).fetch()

    dicts = [converters.gate_value_to_json_dict(g) for g in gates]
    for g in dicts:
      approvers = approval_defs.get_approvers(g['gate_type'])
      g['possible_assignee_emails'] = approvers

    return GetGateResponse.from_dict({
        'gates': dicts,
        }).to_dict()

  # TODO(jrobbins): phase out do_post here because it should have been patch.
  def do_post(self, **kwargs) -> dict[str, str]:
    return self.do_patch(**kwargs)

  def do_patch(self, **kwargs) -> dict[str, str]:
    """Set the assignees for a gate."""
    user, fe, gate, feature_id, gate_id = get_user_feature_and_gate(
        self, kwargs)
    request = PatchGateRequest.from_dict(self.request.json)
    changes: list[str] = []
    new_assignees = request.assignees
    new_answers = request.survey_answers

    self.require_permissions(user, fe, gate)

    if new_assignees is not None:
      self.validate_assignees(new_assignees, fe, gate)
      old_assignees = gate.assignee_emails
      gate.assignee_emails = new_assignees
      notifier_helpers.notify_assignees(
          fe, gate, user.email(), old_assignees, new_assignees)
      changes.append('assignees')

    if new_answers is not None:
      self_certify.update_survey_answers(gate, new_answers)
      # Note: these changes don't generate notifications or activities.
      changes.append('answers')

    if changes:
      gate.put()

    # Callers don't use the JSON response for this API call.
    message = 'Changed: %s' % (', '.join(changes) or None)
    return SuccessMessage(message=message).to_dict()

  def require_permissions(self, user, feature, gate):
    """Abort the request if the user lacks permission to set assignees."""
    is_editor = permissions.can_edit_feature(user, feature.key.integer_id())
    approvers = approval_defs.get_approvers(gate.gate_type)
    is_approver = permissions.can_review_gate(user, feature, gate, approvers)

    if not is_editor and not is_approver:
      self.abort(403, msg='User lacks permission to assign reviews')

  def validate_assignees(self, assignees, fe, gate):
    """Each assignee must have permission to review."""
    approvers = approval_defs.get_approvers(gate.gate_type)
    for email in assignees:
      reviewer = User(email=email)
      is_approver = permissions.can_review_gate(reviewer, fe, gate, approvers)
      if not is_approver:
        self.abort(400, 'Assignee is not a reviewer')


class PendingGatesAPI(basehandlers.APIHandler):

  def get_stage_ids_of_gates_pending_my_approval(self) -> list[int] | Future:
    """Return a list of stage_id needing approval by current user."""
    user = self.get_current_user()
    if not user:
      return []

    approvable_gate_types = approval_defs.fields_approvable_by(user)
    if not approvable_gate_types:
      logging.info('User has no approvable_gate_types')
      return []
    query = Gate.query(
        Gate.state.IN(Gate.PENDING_STATES),
        Gate.gate_type.IN(approvable_gate_types))
    future_stage_ids = query.fetch_async(projection=['stage_id'])
    return future_stage_ids

  def do_get(self, **kwargs):
    """Return a list of gates on features that have some active gates."""
    # 1. Get the feature IDs of any active gates.  Also, prefetch approvers.
    future_projections = self.get_stage_ids_of_gates_pending_my_approval()
    prefetched_approvers = {
        gate_type: approval_defs.get_approvers(gate_type)
        for gate_type in approval_defs.APPROVAL_FIELDS_BY_ID}
    if type(future_projections) == list:
      stage_ids = set(future_projections)
    else:
      projections = future_projections.get_result()
      stage_ids = set(proj.stage_id for proj in projections)
    if not stage_ids:
      return GetGateResponse.from_dict({'gates': []}).to_dict()

    # 2. Fetch all the gates on those stages.
    gates: list[Gate] = Gate.query(Gate.stage_id.IN(stage_ids)).fetch()

    # 3. Convert to dicts and add possible assignees.
    dicts = [converters.gate_value_to_json_dict(g) for g in gates]
    for g in dicts:
      g['possible_assignee_emails'] = prefetched_approvers.get(g['gate_type'], [])

    return GetGateResponse.from_dict({'gates': dicts}).to_dict()


class XfnGatesAPI(basehandlers.APIHandler):

  def do_get(self, **kwargs):
    """Reject unneeded GET requests without triggering Error Reporting."""
    self.abort(405, valid_methods=['POST'])

  def do_post(self, **kwargs) -> dict[str, str]:
    """Add a full set of cross-functional gates to a stage."""
    feature_id: int = kwargs['feature_id']
    fe: FeatureEntry | None = self.get_specified_feature(feature_id=feature_id)
    if fe is None:
      self.abort(404, msg=f'Feature {feature_id} not found')
    stage_id: int = kwargs['stage_id']
    stage: Stage | None = Stage.get_by_id(stage_id)
    if stage is None:
      self.abort(404, msg=f'Stage {stage_id} not found')

    user: User = self.get_current_user(required=True)
    is_editor = fe and permissions.can_edit_feature(user, fe.key.integer_id())
    is_approver = approval_defs.fields_approvable_by(user)
    if not is_editor and not is_approver:
      self.abort(403, msg='User lacks permission to create gates')

    count = self.create_xfn_gates(feature_id, stage_id)
    return SuccessMessage(message=f'Created {count} gates').to_dict()

  def get_needed_gate_types(self) -> list[int]:
    """Return a list of gate types normally used to ship a new feature."""
    needed_gate_tuples = STAGES_AND_GATES_BY_FEATURE_TYPE[
        FEATURE_TYPE_INCUBATE_ID]
    for stage_type, gate_types in needed_gate_tuples:
      if stage_type == STAGE_BLINK_SHIPPING:
        return gate_types
    raise ValueError('Could not find expected list of gate types')

  def create_xfn_gates(self, feature_id, stage_id) -> int:
    """Create all new incubation gates on a PSA stage"""
    logging.info('Creating xfn gates')
    existing_gates = Gate.query(
        Gate.feature_id == feature_id, Gate.stage_id == stage_id).fetch()
    existing_gate_types = set([eg.gate_type for eg in existing_gates])
    logging.info('Found existing: %r', existing_gate_types)
    new_gates = []
    for gate_type in self.get_needed_gate_types():
      if gate_type not in existing_gate_types:
        logging.info(f'Creating gate type {gate_type}')
        gate = Gate(
            feature_id=feature_id, stage_id=stage_id, gate_type=gate_type,
            state=Gate.PREPARING)
        new_gates.append(gate)

    ndb.put_multi(new_gates)
    num_new = len(new_gates)
    logging.info(f'Created {num_new} gates')
    return num_new
