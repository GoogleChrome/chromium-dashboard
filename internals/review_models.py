# Copyright 2020 Google Inc.
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

# Import needed to reference a class within its own class method.
# https://stackoverflow.com/a/33533514
from __future__ import annotations
import collections

import datetime
import logging
from typing import Optional
from google.cloud import ndb  # type: ignore


class OwnersFile(ndb.Model):
  """Describes the properties to store raw API_OWNERS content."""
  url = ndb.StringProperty(required=True)
  raw_content = ndb.TextProperty(required=True)
  created_on = ndb.DateTimeProperty(auto_now_add=True)

  def add_owner_file(self):
    """Add the owner file's content in ndb and delete all other entities."""
    # Delete all other entities.
    ndb.delete_multi(OwnersFile.query(
        OwnersFile.url == self.url).fetch(keys_only=True))
    return self.put()

  @classmethod
  def get_raw_owner_file(cls, url) -> OwnersFile | None:
    """Retrieve raw the owner file's content, if it is created with an hour."""
    q = cls.query()
    q = q.filter(cls.url == url)
    owners_file_list = q.fetch(1)
    if not owners_file_list:
      logging.info('API_OWNERS content does not exist for URL %s.' % (url))
      return None

    return owners_file_list[0]

  def is_fresh(self) -> bool:
    """Check if it was created within the past hour."""
    an_hour_before = datetime.datetime.now() - datetime.timedelta(hours=1)
    return self.created_on > an_hour_before


class GateDef(ndb.Model):
  """Configuration for a review gate."""
  gate_type = ndb.IntegerProperty(required=True)
  approvers = ndb.StringProperty(repeated=True)
  rotation_url = ndb.StringProperty()

  # TODO(jrobbins): Use these and phase out approval_devs.ApprovalFieldDef.
  name = ndb.StringProperty()
  description = ndb.StringProperty()
  rule = ndb.StringProperty()
  team_name = ndb.StringProperty()
  slo_initial_response = ndb.IntegerProperty()

  @classmethod
  def get_gate_def(cls, gate_type: int) -> GateDef:
    """Load an existing GateDef and or create a new one."""
    query: ndb.Query = GateDef.query(GateDef.gate_type == gate_type)
    gate_defs = query.fetch(1)
    if gate_defs:
      gate_def = gate_defs[0]
    else:
      logging.info(f'Creating empty GateDef for {gate_type}')
      gate_def = GateDef(gate_type=gate_type)
      gate_def.put()

    return gate_def


class Vote(ndb.Model):
  """One approver's vote on what the state of a gate should be."""

  # Not used: PREPARING = 0
  NA = 1
  REVIEW_REQUESTED = 2
  REVIEW_STARTED = 3
  NEEDS_WORK = 4
  APPROVED = 5
  DENIED = 6
  NO_RESPONSE = 7
  INTERNAL_REVIEW = 8
  NA_REQUESTED = 9
  NA_SELF = 10
  NA_VERIFIED = 11
  VOTE_VALUES = {
      # Not used: PREPARING: 'preparing',
      NA: 'na',
      REVIEW_REQUESTED: 'review_requested',
      REVIEW_STARTED: 'review_started',
      NEEDS_WORK: 'needs_work',
      APPROVED: 'approved',
      DENIED: 'denied',
      NO_RESPONSE: 'no_response',
      INTERNAL_REVIEW: 'internal_review',
      NA_REQUESTED: 'na_requested',
      NA_SELF: 'na (self-certified)',
      NA_VERIFIED: 'na (verified)',
  }

  REQUESTING_STATES = [REVIEW_REQUESTED, NA_REQUESTED, NA_SELF]
  RESPONSE_STATES = [
      NA, APPROVED, DENIED, REVIEW_STARTED, NEEDS_WORK, INTERNAL_REVIEW,
      NA_SELF]

  feature_id = ndb.IntegerProperty(required=True)
  gate_id = ndb.IntegerProperty(required=True)
  gate_type = ndb.IntegerProperty()
  state = ndb.IntegerProperty(required=True)
  set_on = ndb.DateTimeProperty(required=True)
  set_by = ndb.StringProperty(required=True)

  @classmethod
  def get_votes(
      cls, feature_id: Optional[int]=None, gate_id: Optional[int]=None,
      gate_type: Optional[int]=None, states: Optional[list[int]]=None,
      set_by: Optional[str]=None, limit=None) -> list[Vote]:
    """Return the requested approvals."""
    query: ndb.Query = Vote.query().order(Vote.set_on)
    if feature_id is not None:
      query = query.filter(Vote.feature_id == feature_id)
    if gate_id is not None:
      query = query.filter(Vote.gate_id == gate_id)
    if gate_type is not None:
      query = query.filter(Vote.gate_type == gate_type)
    if states is not None:
      query = query.filter(Vote.state.IN(states))
    if set_by is not None:
      query = query.filter(Vote.set_by == set_by)
    logging.info('query is %r', query)
    # Query with STRONG consistency because ndb defaults to
    # EVENTUAL consistency and we run this query immediately after
    # saving the user's change that we want included in the query.
    votes: list[Vote] = query.fetch(limit, read_consistency=ndb.STRONG)
    logging.info('found %r Votes', len(votes))
    return votes

  @classmethod
  def is_valid_state(cls, new_state: int) -> bool:
    """Return true if new_state is valid."""
    return new_state in cls.VOTE_VALUES

  # Note: set_vote() moved to approval_defs.py


class SurveyAnswers(ndb.Model):
  """Surveys allow for self-certification of some gates."""

  # Questions from the privacy team.
  is_language_polyfill = ndb.BooleanProperty(default=False)
  is_api_polyfill = ndb.BooleanProperty(default=False)
  is_same_origin_css = ndb.BooleanProperty(default=False)

  # Questions that are potentially useful to several teams.
  launch_or_contact = ndb.StringProperty()  # URL or email for more info.
  explanation = ndb.StringProperty()  # Explain why you chose those answers.


class Gate(ndb.Model):
  """Gates regulate the completion of a stage."""

  PREPARING = 0
  PENDING_STATES = [
      Vote.REVIEW_REQUESTED, Vote.REVIEW_STARTED, Vote.NEEDS_WORK,
      Vote.INTERNAL_REVIEW, Vote.NA_REQUESTED]
  FINAL_STATES = [Vote.NA, Vote.APPROVED, Vote.DENIED, Vote.NA_SELF,
                  Vote.NA_VERIFIED]
  APPROVED_STATES = [Vote.NA, Vote.APPROVED, Vote.NA_SELF, Vote.NA_VERIFIED]

  feature_id = ndb.IntegerProperty(required=True)
  stage_id = ndb.IntegerProperty(required=True)
  gate_type = ndb.IntegerProperty(required=True)  # copy from field_id

  # Calculated from Vote states.  Can be one of Vote states or PREPARING.
  state = ndb.IntegerProperty(required=True)
  # The datetime of the first vote on this gate.
  requested_on = ndb.DateTimeProperty()
  # The first comment or vote on this gate from a reviewer after the request.
  responded_on = ndb.DateTimeProperty()
  # The time at which the gate first enters a final state.
  resolved_on = ndb.DateTimeProperty()
  # The time at which the gate most recently entered the NEEDS_WORK state.
  needs_work_started_on = ndb.DateTimeProperty()
  # The cumulative number of weekdays spent in the NEEDS_WORK state.
  # It can add up if the the review is sent back multiple times.
  needs_work_elapsed = ndb.IntegerProperty()

  assignee_emails = ndb.StringProperty(repeated=True)
  next_action = ndb.DateProperty()
  additional_review = ndb.BooleanProperty(default=False)

  survey_answers = ndb.StructuredProperty(SurveyAnswers)

  @classmethod
  def get_feature_gates(cls, feature_id: int) -> dict[int, list[Gate]]:
    """Return a dictionary of stages associated with a given feature."""
    gates: list[Gate] = Gate.query(Gate.feature_id == feature_id).fetch()
    gates_dict = collections.defaultdict(list)
    for gate in gates:
      gates_dict[gate.gate_type].append(gate)
    return gates_dict


class Amendment(ndb.Model):
  """Activity log entries can record changes to fields."""
  field_name = ndb.StringProperty()  # from QUERIABLE_FIELDS
  old_value = ndb.TextProperty()
  new_value = ndb.TextProperty()


class Activity(ndb.Model):
  """An activity log entry (comment + amendments) on a gate or feature."""
  feature_id = ndb.IntegerProperty(required=True)
  gate_id = ndb.IntegerProperty()  # The gate commented on, or general comment.
  created = ndb.DateTimeProperty(auto_now_add=True)
  author = ndb.StringProperty()
  content = ndb.TextProperty()
  deleted_by = ndb.StringProperty()

  amendments = ndb.StructuredProperty(Amendment, repeated=True)

  @classmethod
  def get_activities(cls, feature_id: int, gate_id: Optional[int]=None,
      comments_only: bool=False) -> list[Activity]:
    """Return all actitivies for a feature, or a specific gate."""
    query = Activity.query().order(Activity.created)
    query = query.filter(Activity.feature_id == feature_id)
    if gate_id:
      query = query.filter(Activity.gate_id == gate_id)
    acts = query.fetch(None)
    if comments_only:
      return [act for act in acts if act.content]
    return acts
