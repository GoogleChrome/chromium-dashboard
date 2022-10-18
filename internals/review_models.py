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

import datetime
import logging
from typing import Optional
from google.cloud import ndb


class Approval(ndb.Model):
  """Describes the current state of one approval on a feature."""

  # Not used: NEEDS_REVIEW = 0
  NA = 1
  REVIEW_REQUESTED = 2
  REVIEW_STARTED = 3
  NEEDS_WORK = 4
  APPROVED = 5
  NOT_APPROVED = 6
  APPROVAL_VALUES = {
      # Not used: NEEDS_REVIEW: 'needs_review',
      NA: 'na',
      REVIEW_REQUESTED: 'review_requested',
      REVIEW_STARTED: 'review_started',
      NEEDS_WORK: 'needs_work',
      APPROVED: 'approved',
      NOT_APPROVED: 'not_approved',
  }

  FINAL_STATES = [NA, APPROVED, NOT_APPROVED]

  feature_id = ndb.IntegerProperty(required=True)
  field_id = ndb.IntegerProperty(required=True)
  state = ndb.IntegerProperty(required=True)
  set_on = ndb.DateTimeProperty(required=True)
  set_by = ndb.StringProperty(required=True)

  @classmethod
  def get_approvals(
      cls, feature_id=None, field_id=None, states=None, set_by=None,
      limit=None) -> list[Approval]:
    """Return the requested approvals."""
    query = Approval.query().order(Approval.set_on)
    if feature_id is not None:
      query = query.filter(Approval.feature_id == feature_id)
    if field_id is not None:
      query = query.filter(Approval.field_id == field_id)
    if states is not None:
      query = query.filter(Approval.state.IN(states))
    if set_by is not None:
      query = query.filter(Approval.set_by == set_by)
    # Query with STRONG consistency because ndb defaults to
    # EVENTUAL consistency and we run this query immediately after
    # saving the user's change that we want included in the query.
    approvals = query.fetch(limit, read_consistency=ndb.STRONG)
    return approvals

  @classmethod
  def is_valid_state(cls, new_state):
    """Return true if new_state is valid."""
    return new_state in cls.APPROVAL_VALUES

  @classmethod
  def set_approval(cls, feature_id, field_id, new_state, set_by_email):
    """Add or update an approval value."""
    if not cls.is_valid_state(new_state):
      raise ValueError('Invalid approval state')

    now = datetime.datetime.now()
    existing_list = cls.get_approvals(
        feature_id=feature_id, field_id=field_id, set_by=set_by_email)
    if existing_list:
      existing = existing_list[0]
      existing.set_on = now
      existing.state = new_state
      existing.put()
      logging.info('existing approval is %r', existing.key.integer_id())

      # Write for existing Vote entity.
      existing_votes = Vote.get_votes(
          feature_id=feature_id, gate_id=field_id, set_by=set_by_email)
      if existing_votes:
        vote = existing_votes[0]
        vote.set_on = now
        vote.state = new_state
        vote.put()
        logging.info('existing vote is %r', existing.key.integer_id())
      return

    new_appr = Approval(
        feature_id=feature_id, field_id=field_id, state=new_state,
        set_on=now, set_by=set_by_email)
    new_appr.put()
    logging.info('new_appr is %r', new_appr.key.integer_id())

    # Write for new Vote entity.
    new_vote = Vote(
        id=new_appr.key.integer_id(), feature_id=feature_id, gate_id=field_id,
        state=new_state, set_on=now, set_by=set_by_email)
    new_vote.put()
    logging.info('new_vote is %r', new_vote.key.integer_id())

  @classmethod
  def clear_request(cls, feature_id, field_id):
    """After the review requirement has been satisfied, remove the request."""
    review_requests = cls.get_approvals(
        feature_id=feature_id, field_id=field_id, states=[cls.REVIEW_REQUESTED])
    for rr in review_requests:
      rr.key.delete()
    
    # Delete associated Vote entities as well.
    requested_votes = Vote.get_votes(feature_id=feature_id,
        gate_id=field_id, states=[Vote.REVIEW_REQUESTED])
    for vote in requested_votes:
      vote.key.delete()


class ApprovalConfig(ndb.Model):
  """Allows customization of an approval field for one feature."""

  feature_id = ndb.IntegerProperty(required=True)
  field_id = ndb.IntegerProperty(required=True)
  owners = ndb.StringProperty(repeated=True)
  next_action = ndb.DateProperty()
  additional_review = ndb.BooleanProperty(default=False)

  @classmethod
  def get_configs(cls, feature_id):
    """Return approval configs for all approval fields."""
    query = ApprovalConfig.query(ApprovalConfig.feature_id == feature_id)
    configs = query.fetch(None)
    return configs

  @classmethod
  def set_config(
      cls, feature_id, field_id, owners, next_action, additional_review):
    """Add or update an approval config object."""
    config = ApprovalConfig(feature_id=feature_id, field_id=field_id)
    for existing in cls.get_configs(feature_id):
      if existing.field_id == field_id:
        config = existing

    config.owners = owners or []
    config.next_action = next_action
    config.additional_review = additional_review
    config.put()


class Comment(ndb.Model):
  """A review comment on a feature."""
  feature_id = ndb.IntegerProperty(required=True)
  field_id = ndb.IntegerProperty()  # The approval field_id, or general comment.
  created = ndb.DateTimeProperty(auto_now_add=True)
  author = ndb.StringProperty()
  content = ndb.StringProperty()
  deleted_by = ndb.StringProperty()
  migrated = ndb.BooleanProperty()
  # If the user set an approval value, we capture that here so that we can
  # display a change log.  This could be generalized to a list of separate
  # Amendment entities, but that complexity is not needed yet.
  old_approval_state = ndb.IntegerProperty()
  new_approval_state = ndb.IntegerProperty()

  @classmethod
  def get_comments(cls, feature_id, field_id=None):
    """Return review comments for an approval."""
    query = Comment.query().order(Comment.created)
    query = query.filter(Comment.feature_id == feature_id)
    if field_id:
      query = query.filter(Comment.field_id == field_id)
    comments = query.fetch(None)
    return comments


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
  def get_raw_owner_file(cls, url):
    """Retrieve raw the owner file's content, if it is created with an hour."""
    q = cls.query()
    q = q.filter(cls.url == url)
    owners_file_list = q.fetch(1)
    if not owners_file_list:
      logging.info('API_OWNERS content does not exist for URL %s.' % (url))
      return None

    owners_file = owners_file_list[0]
    # Check if it is created within an hour.
    an_hour_before = datetime.datetime.now() - datetime.timedelta(hours=1)
    if owners_file.created_on < an_hour_before:
      return None

    return owners_file.raw_content


# Note: This class is not used yet.
class Gate(ndb.Model):  # copy from ApprovalConfig
  """Gates regulate the completion of a stage."""
  feature_id = ndb.IntegerProperty(required=True)
  stage_id = ndb.IntegerProperty(required=True)
  gate_type = ndb.IntegerProperty(required=True)  # copy from field_id

  # Can be REVIEW_REQUESTED or one of ApprovalValue states
  state = ndb.IntegerProperty(required=True)  # calc from Approval

  owners = ndb.StringProperty(repeated=True)
  next_action = ndb.DateProperty()
  additional_review = ndb.BooleanProperty(default=False)

  # TODO(jrobbins): implement request_review()

  def clear_request(self) -> None:
    """After the review requirement has been satisfied, remove the request."""
    votes_requested = Vote.get_votes(feature_id=self.feature_id,
        gate_id=self.key.integer_id(), states=[Vote.REVIEW_REQUESTED])
    for vote in votes_requested:
      vote.key.delete()

  def is_resolved(self) -> bool:
    """Return if the Gate's outcome has been decided."""
    return self.state == Vote.APPROVED or self.state == Vote.NOT_APPROVED

  def is_approved(self) -> bool:
    """Return if the Gate approval requirements have been met."""
    return self.state == Vote.APPROVED


# Note: This class is not used yet.
class Vote(ndb.Model):  # copy from Approval
  """One approver's vote on what the state of a gate should be."""

  # Not used: NEEDS_REVIEW = 0
  NA = 1
  REVIEW_REQUESTED = 2
  REVIEW_STARTED = 3
  NEEDS_WORK = 4
  APPROVED = 5
  NOT_APPROVED = 6
  VOTE_VALUES = {
      # Not used: NEEDS_REVIEW: 'needs_review',
      NA: 'na',
      REVIEW_REQUESTED: 'review_requested',
      REVIEW_STARTED: 'review_started',
      NEEDS_WORK: 'needs_work',
      APPROVED: 'approved',
      NOT_APPROVED: 'not_approved',
  }

  FINAL_STATES = [NA, APPROVED, NOT_APPROVED]

  feature_id = ndb.IntegerProperty(required=True)
  gate_id = ndb.IntegerProperty(required=True)
  state = ndb.IntegerProperty(required=True)
  set_on = ndb.DateTimeProperty(required=True)
  set_by = ndb.StringProperty(required=True)

  @classmethod
  def get_votes(
      cls, feature_id=None, gate_id=None, states=None, set_by=None,
      limit=None):
    """Return the requested approvals."""
    query = Vote.query().order(Approval.set_on)
    if feature_id is not None:
      query = query.filter(Vote.feature_id == feature_id)
    if gate_id is not None:
      query = query.filter(Vote.gate_id == gate_id)
    if states is not None:
      query = query.filter(Vote.state.IN(states))
    if set_by is not None:
      query = query.filter(Vote.set_by == set_by)
    # Query with STRONG consistency because ndb defaults to
    # EVENTUAL consistency and we run this query immediately after
    # saving the user's change that we want included in the query.
    votes = query.fetch(limit, read_consistency=ndb.STRONG)
    return votes

  @classmethod
  def is_valid_state(cls, new_state):
    """Return true if new_state is valid."""
    return new_state in cls.VOTE_VALUES

  # Note: set_vote() moved to approval_defs.py

  # Note: clear_request() moved to Gate


# Note: This class is not used yet.
class Amendment(ndb.Model):
  """Activity log entries can record changes to fields."""
  field_name = ndb.StringProperty()  # from QUERIABLE_FIELDS
  old_value = ndb.TextProperty()
  new_value = ndb.TextProperty()


# Note: This class is not used yet.
# TODO(jrobbins): Decide on either copying to this new class or adding
# and removing fields from the existing Comment class.
class Activity(ndb.Model):  # copy from Comment
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
    """Return actitivies for an approval."""
    query = Activity.query().order(Activity.created)
    query = query.filter(Activity.feature_id == feature_id)
    if gate_id:
      query = query.filter(Activity.gate_id == gate_id)
    acts = query.fetch(None)
    if comments_only:
      return [act for act in acts if act.content]
    return acts
