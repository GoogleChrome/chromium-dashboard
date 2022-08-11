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

from google.cloud import ndb


class Vote(ndb.Model):  # copy from Approval
  """One approver's vote on what the state of a gate should be."""

  # Not used: NEEDS_REVIEW = 0
  NA = 1
  REVIEW_REQUESTED = 2
  REVIEW_STARTED = 3
  NEED_INFO = 4
  APPROVED = 5
  NOT_APPROVED = 6
  APPROVAL_VALUES = {
      # Not used: NEEDS_REVIEW: 'needs_review',
      NA: 'na',
      REVIEW_REQUESTED: 'review_requested',
      REVIEW_STARTED: 'review_started',
      NEED_INFO: 'need_info',
      APPROVED: 'approved',
      NOT_APPROVED: 'not_approved',
  }

  PENDING_STATES = [REVIEW_REQUESTED, REVIEW_STARTED, NEED_INFO]
  FINAL_STATES = [NA, APPROVED, NOT_APPROVED]

  feature_id = ndb.IntegerProperty(required=True)
  field_id = ndb.IntegerProperty(required=True)
  state = ndb.IntegerProperty(required=True)
  set_on = ndb.DateTimeProperty(required=True)
  set_by = ndb.StringProperty(required=True)

  @classmethod
  def get_approvals(
      cls, feature_id=None, field_id=None, states=None, set_by=None,
      limit=None):
    """Return the requested approvals."""
    query = ApprovalVote.query()
    if feature_id is not None:
      query = query.filter(ApprovalVote.feature_id == feature_id)
    if field_id is not None:
      query = query.filter(ApprovalVote.field_id == field_id)
    if states is not None:
      query = query.filter(ApprovalVote.state.IN(states))
    if set_by is not None:
      query = query.filter(ApprovalVote.set_by == set_by)
    approvals = query.fetch(limit)
    return approvals

  @classmethod
  def sorted_by_pending_request_date(cls, descending):
    """Return feature_ids of pending approvals sorted by request date."""
    query = ApprovalVote.query(
        ApprovalVote.state == ApprovalVote.REVIEW_REQUESTED)
    if descending:
      query = query.order(-ApprovalVote.set_on)
    else:
      query = query.order(ApprovalVote.set_on)

    pending_approvals = query.fetch(projection=['feature_id'])
    feature_ids = utils.dedupe(pa.feature_id for pa in pending_approvals)
    return feature_ids

  @classmethod
  def sorted_by_review_date(cls, descending):
    """Return feature_ids of reviewed approvals sorted by last review."""
    query = ApprovalVote.query(ApprovalVote.state.IN(ApprovalVote.FINAL_STATES))
    if descending:
      query = query.order(-ApprovalVote.set_on)
    else:
      query = query.order(ApprovalVote.set_on)
    recent_approvals = query.fetch(projection=['feature_id'])

    feature_ids = utils.dedupe(ra.feature_id for ra in recent_approvals)
    return feature_ids

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
      return

    new_appr = Approval(
        feature_id=feature_id, field_id=field_id, state=new_state,
        set_on=now, set_by=set_by_email)
    new_appr.put()

  @classmethod
  def clear_request(cls, feature_id, field_id):
    """After the review requirement has been satisfied, remove the request."""
    review_requests = cls.get_approvals(
        feature_id=feature_id, field_id=field_id, states=[cls.REVIEW_REQUESTED])
    for rr in review_requests:
      rr.key.delete()


class Amendment(ndb.Model):
  """Comments can log changes to other fields of the feature."""
  field_name = ndb.StringProperty()  # from QUERIABLE_FIELDS
  old_value = ndb.TextProperty()
  new_value = ndb.TextProperty()


class ReviewComment(ndb.Model):  # copy from Comment
  """A review comment on a gate or a general comment on a feature."""
  feature_id = ndb.IntegerProperty(required=True)
  gate_id = ndb.IntegerProperty()  # The gate commented on, or general comment.
  created = ndb.DateTimeProperty(auto_now=True)
  author = ndb.StringProperty()
  content = ndb.TextProperty()
  deleted_by = ndb.StringProperty()

  amendments = ndb.StructuredProperty(Amendment, repeated=True)

  @classmethod
  def get_comments(cls, feature_id, field_id=None):
    """Return review comments for an approval."""
    query = Comment.query().order(Comment.created)
    query = query.filter(Comment.feature_id == feature_id)
    if field_id:
      query = query.filter(Comment.field_id == field_id)
    comments = query.fetch(None)
    return comments
