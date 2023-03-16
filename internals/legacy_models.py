# -*- coding: utf-8 -*-
# Copyright 2023 Google Inc.
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
from typing import Any

from google.cloud import ndb  # type: ignore

from framework import rediscache
from internals.core_enums import *
from internals import fetchchannels
import settings


##################################
###     Legacy core models     ###
##################################
SIMPLE_TYPES = (int, float, bool, dict, str, list)

class DictModel(ndb.Model):
  # def to_dict(self):
  #   return dict([(p, str(getattr(self, p))) for p in self.properties()])

  def is_saved(self):
    if self.key:
      return True
    return False

  def to_dict(self):
    output = {}

    for key, prop in self._properties.items():
      # Skip obsolete values that are still in our datastore
      if not hasattr(self, key):
        continue

      value = getattr(self, key)

      if value is None or isinstance(value, SIMPLE_TYPES):
        output[key] = value
      elif isinstance(value, datetime.date):
        # Convert date/datetime to ms-since-epoch ("new Date()").
        #ms = time.mktime(value.utctimetuple())
        #ms += getattr(value, 'microseconds', 0) / 1000
        #output[key] = int(ms)
        output[key] = str(value)
      elif isinstance(value, ndb.GeoPt):
        output[key] = {'lat': value.lat, 'lon': value.lon}
      elif isinstance(value, ndb.Model):
        output[key] = value.to_dict()
      elif isinstance(value, ndb.model.User):
        output[key] = value.email()
      else:
        raise ValueError('cannot encode ' + repr(prop))

    return output


class Feature(DictModel):
  """Container for a feature."""

  DEFAULT_CACHE_KEY = 'features'

  def __init__(self, *args, **kwargs):
    # Initialise Feature.blink_components with a default value.  If
    # name is present in kwargs then it would mean constructor is
    # being called for creating a new feature rather than for fetching
    # an existing feature.
    if 'name' in kwargs:
      if 'blink_components' not in kwargs:
        kwargs['blink_components'] = [settings.DEFAULT_COMPONENT]

    super(Feature, self).__init__(*args, **kwargs)

  @classmethod
  def feature_cache_key(cls, cache_key, feature_id):
    return '%s|%s' % (cache_key, feature_id)

  @classmethod
  def feature_cache_prefix(cls):
    return '%s|*' % (Feature.DEFAULT_CACHE_KEY)

  @classmethod
  def _first_of_milestone_v2(self, feature_list, milestone, start=0):
    for i in range(start, len(feature_list)):
      f = feature_list[i]
      desktop_milestone = f['browsers']['chrome'].get('desktop', None)
      android_milestone = f['browsers']['chrome'].get('android', None)
      status = f['browsers']['chrome']['status'].get('text', None)

      if (str(desktop_milestone) == str(milestone) or status == str(milestone)):
        return i
      elif (desktop_milestone == None and
            str(android_milestone) == str(milestone)):
        return i

    return -1

  @classmethod
  def _annotate_first_of_milestones(self, feature_list):
    try:
      omaha_data = fetchchannels.get_omaha_data()

      win_versions = omaha_data[0]['versions']

      # Find the latest canary major version from the list of windows versions.
      canary_versions = [
          x for x in win_versions
          if x.get('channel') and x.get('channel').startswith('canary')]
      LATEST_VERSION = int(canary_versions[0].get('version').split('.')[0])

      milestones = list(range(1, LATEST_VERSION + 1))
      milestones.reverse()
      versions = [
        IMPLEMENTATION_STATUS[PROPOSED],
        IMPLEMENTATION_STATUS[IN_DEVELOPMENT],
        IMPLEMENTATION_STATUS[DEPRECATED],
        ]
      versions.extend(milestones)
      versions.append(IMPLEMENTATION_STATUS[NO_ACTIVE_DEV])
      versions.append(IMPLEMENTATION_STATUS[NO_LONGER_PURSUING])

      last_good_idx = 0
      for i, ver in enumerate(versions):
        idx = Feature._first_of_milestone_v2(
            feature_list, ver, start=last_good_idx)
        if idx != -1:
          feature_list[idx]['first_of_milestone'] = True
          last_good_idx = idx
    except Exception as e:
      logging.error(e)

  def put(self, **kwargs) -> Any:
    key = super(Feature, self).put(**kwargs)
    # Invalidate rediscache for the individual feature view.
    cache_key = Feature.feature_cache_key(
        Feature.DEFAULT_CACHE_KEY, self.key.integer_id())
    rediscache.delete(cache_key)

    return key

  # Metadata.
  created = ndb.DateTimeProperty(auto_now_add=True)
  updated = ndb.DateTimeProperty(auto_now=True)
  accurate_as_of = ndb.DateTimeProperty(auto_now=False)
  updated_by = ndb.UserProperty()
  created_by = ndb.UserProperty()

  # General info.
  category = ndb.IntegerProperty(required=True)
  creator = ndb.StringProperty()
  name = ndb.StringProperty(required=True)
  feature_type = ndb.IntegerProperty(default=FEATURE_TYPE_INCUBATE_ID)
  intent_stage = ndb.IntegerProperty(default=INTENT_NONE)
  summary = ndb.StringProperty(required=True)
  unlisted = ndb.BooleanProperty(default=False)
  enterprise_feature_categories = ndb.StringProperty(repeated=True)
  # TODO(jrobbins): Add an entry_state enum to track app-specific lifecycle
  # info for a feature entry as distinct from process-specific stage.
  deleted = ndb.BooleanProperty(default=False)
  motivation = ndb.StringProperty()
  star_count = ndb.IntegerProperty(default=0)
  search_tags = ndb.StringProperty(repeated=True)
  comments = ndb.StringProperty()
  owner = ndb.StringProperty(repeated=True)
  editors = ndb.StringProperty(repeated=True)
  cc_recipients = ndb.StringProperty(repeated=True)
  footprint = ndb.IntegerProperty()  # Deprecated
  breaking_change = ndb.BooleanProperty(default=False)

  # Tracability to intent discussion threads
  intent_to_implement_url = ndb.StringProperty()
  intent_to_implement_subject_line = ndb.StringProperty()
  intent_to_ship_url = ndb.StringProperty()
  intent_to_ship_subject_line = ndb.StringProperty()
  ready_for_trial_url = ndb.StringProperty()
  intent_to_experiment_url = ndb.StringProperty()
  intent_to_experiment_subject_line = ndb.StringProperty()
  intent_to_extend_experiment_url = ndb.StringProperty()
  intent_to_extend_experiment_subject_line = ndb.StringProperty()
  # Currently, only one is needed.
  i2e_lgtms = ndb.StringProperty(repeated=True)
  i2s_lgtms = ndb.StringProperty(repeated=True)

  # Chromium details.
  bug_url = ndb.StringProperty()
  launch_bug_url = ndb.StringProperty()
  initial_public_proposal_url = ndb.StringProperty()
  blink_components = ndb.StringProperty(repeated=True)
  devrel = ndb.StringProperty(repeated=True)

  impl_status_chrome = ndb.IntegerProperty(required=True, default=NO_ACTIVE_DEV)
  shipped_milestone = ndb.IntegerProperty()
  shipped_android_milestone = ndb.IntegerProperty()
  shipped_ios_milestone = ndb.IntegerProperty()
  shipped_webview_milestone = ndb.IntegerProperty()
  requires_embedder_support = ndb.BooleanProperty(default=False)

  # DevTrial details.
  devtrial_instructions = ndb.StringProperty()
  flag_name = ndb.StringProperty()
  interop_compat_risks = ndb.StringProperty()
  ergonomics_risks = ndb.StringProperty()
  activation_risks = ndb.StringProperty()
  security_risks = ndb.StringProperty()
  webview_risks = ndb.StringProperty()
  debuggability = ndb.StringProperty()
  all_platforms = ndb.BooleanProperty()
  all_platforms_descr = ndb.StringProperty()
  wpt = ndb.BooleanProperty()
  wpt_descr = ndb.StringProperty()
  dt_milestone_desktop_start = ndb.IntegerProperty()
  dt_milestone_android_start = ndb.IntegerProperty()
  dt_milestone_ios_start = ndb.IntegerProperty()
  # Webview DT is currently not offered in the UI because there is no way
  # to set flags.
  dt_milestone_webview_start = ndb.IntegerProperty()
  # Note: There are no dt end milestones because a dev trail implicitly
  # ends when the feature ships or is abandoned.

  visibility = ndb.IntegerProperty(required=False, default=1)  # Deprecated

  # Standards details.
  standardization = ndb.IntegerProperty(required=True,
      default=EDITORS_DRAFT)  # Deprecated
  standard_maturity = ndb.IntegerProperty(required=True, default=UNSET_STD)
  spec_link = ndb.StringProperty()
  api_spec = ndb.BooleanProperty(default=False)
  spec_mentors = ndb.StringProperty(repeated=True)

  security_review_status = ndb.IntegerProperty(default=REVIEW_PENDING)
  privacy_review_status = ndb.IntegerProperty(default=REVIEW_PENDING)

  tag_review = ndb.StringProperty()
  tag_review_status = ndb.IntegerProperty(default=REVIEW_PENDING)

  prefixed = ndb.BooleanProperty()

  explainer_links = ndb.StringProperty(repeated=True)

  ff_views = ndb.IntegerProperty(required=True, default=NO_PUBLIC_SIGNALS)
  # Deprecated
  ie_views = ndb.IntegerProperty(required=True, default=NO_PUBLIC_SIGNALS)
  safari_views = ndb.IntegerProperty(required=True, default=NO_PUBLIC_SIGNALS)
  web_dev_views = ndb.IntegerProperty(required=True, default=DEV_NO_SIGNALS)

  ff_views_link = ndb.StringProperty()
  ie_views_link = ndb.StringProperty()  # Deprecated
  safari_views_link = ndb.StringProperty()
  web_dev_views_link = ndb.StringProperty()

  ff_views_notes = ndb.StringProperty()
  ie_views_notes = ndb.StringProperty()  # Deprecated
  safari_views_notes = ndb.StringProperty()
  web_dev_views_notes = ndb.StringProperty()
  other_views_notes = ndb.StringProperty()

  doc_links = ndb.StringProperty(repeated=True)
  measurement = ndb.StringProperty()
  availability_expectation = ndb.TextProperty()
  adoption_expectation = ndb.TextProperty()
  adoption_plan = ndb.TextProperty()
  sample_links = ndb.StringProperty(repeated=True)
  non_oss_deps = ndb.StringProperty()

  experiment_goals = ndb.StringProperty()
  experiment_timeline = ndb.StringProperty()
  ot_milestone_desktop_start = ndb.IntegerProperty()
  ot_milestone_desktop_end = ndb.IntegerProperty()
  ot_milestone_android_start = ndb.IntegerProperty()
  ot_milestone_android_end = ndb.IntegerProperty()
  ot_milestone_webview_start = ndb.IntegerProperty()
  ot_milestone_webview_end = ndb.IntegerProperty()
  experiment_risks = ndb.StringProperty()
  experiment_extension_reason = ndb.StringProperty()
  ongoing_constraints = ndb.StringProperty()
  origin_trial_feedback_url = ndb.StringProperty()
  anticipated_spec_changes = ndb.StringProperty()

  finch_url = ndb.StringProperty()

  # Flag set to avoid migrating data that has already been migrated.
  stages_migrated = ndb.BooleanProperty(default=False)


####################################
###     Legacy review models     ###
####################################
class Approval(ndb.Model):
  """Describes the current state of one approval on a feature."""

  # Not used: PREPARING = 0
  NA = 1
  REVIEW_REQUESTED = 2
  REVIEW_STARTED = 3
  NEEDS_WORK = 4
  APPROVED = 5
  DENIED = 6
  NO_RESPONSE = 7
  INTERNAL_REVIEW = 8
  APPROVAL_VALUES = {
      # Not used: PREPARING: 'preparing',
      NA: 'na',
      REVIEW_REQUESTED: 'review_requested',
      REVIEW_STARTED: 'review_started',
      NEEDS_WORK: 'needs_work',
      APPROVED: 'approved',
      DENIED: 'denied',
      NO_RESPONSE: 'no_response',
      INTERNAL_REVIEW: 'internal_review',
  }

  FINAL_STATES = [NA, APPROVED, DENIED]

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
      return

    new_appr = Approval(
        feature_id=feature_id, field_id=field_id, state=new_state,
        set_on=now, set_by=set_by_email)
    new_appr.put()
    logging.info('new_appr is %r', new_appr.key.integer_id())

  @classmethod
  def clear_request(cls, feature_id, field_id):
    """After the review requirement has been satisfied, remove the request."""
    review_requests = cls.get_approvals(
        feature_id=feature_id, field_id=field_id, states=[cls.REVIEW_REQUESTED])
    for rr in review_requests:
      rr.key.delete()

    # Note: We keep REVIEW_REQUEST Vote entities.


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
