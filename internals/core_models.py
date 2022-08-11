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

# This file defineds NDB models for the core objects of our system:
# FeatureEntry, Stage, MilestoneSet, Gate, ApprovalValue.

import logging

from google.cloud import ndb

from framework import ramcache
from framework import users


class FeatureEntry(ndb.Model):  # Copy from Feature
  """This is the main representation of a feature that we are tracking."""

  # Metadata: Creation and updates.
  created = ndb.DateTimeProperty(auto_now_add=True)
  updated = ndb.DateTimeProperty()
  accurate_as_of = ndb.DateTimeProperty()
  creator = ndb.StringProperty()
  updater = ndb.StringProperty()

  # Metadata: Access controls
  owners = ndb.StringProperty(repeated=True)  # copy from owner
  editors = ndb.StringProperty(repeated=True)
  unlisted = ndb.BooleanProperty(default=False)
  deleted = ndb.BooleanProperty(default=False)

  # Descriptive info.
  name = ndb.StringProperty(required=True)
  summary = ndb.TextProperty(required=True)
  category = ndb.IntegerProperty(required=True)
  blink_components = ndb.StringProperty(repeated=True)
  star_count = ndb.IntegerProperty(default=0)
  search_tags = ndb.StringProperty(repeated=True)
  feature_notes = ndb.TextProperty()  # copy from comments

  # Metadata: Process information
  feature_type = ndb.IntegerProperty(default=FEATURE_TYPE_INCUBATE_ID)
  intent_stage = ndb.IntegerProperty(default=0)
  bug_url = ndb.StringProperty()
  launch_bug_url = ndb.StringProperty()

  # Implementation in Chrome
  impl_status_chrome = ndb.IntegerProperty(required=True)
  flag_name = ndb.StringProperty()
  ongoing_constraints = ndb.TextProperty()

  # Gate: Adoption
  motivation = ndb.TextProperty()
  devtrial_instructions = ndb.TextProperty()
  activation_risks = ndb.textProperty()
  measurement = ndb.TextProperty()

  # Gate: Standardization & Interop
  initial_public_proposal_url = ndb.StringProperty()
  explainer_links = ndb.StringProperty(repeated=True)
  requires_embedder_support = ndb.BooleanProperty(default=False)
  standard_maturity = ndb.IntegerProperty(required=True, default=UNSET_STD)
  spec_link = ndb.StringProperty()
  api_spec = ndb.BooleanProperty(default=False)
  spec_mentors = ndb.StringProperty(repeated=True)
  interop_compat_risks = ndb.TextProperty()
  prefixed = ndb.BooleanProperty()
  all_platforms = ndb.BooleanProperty()
  all_platforms_descr = ndb.TextProperty()
  tag_review = ndb.StringProperty()
  tag_review_status = ndb.IntegerProperty(default=REVIEW_PENDING)
  non_oss_deps = ndb.TextProperty()
  origin_trial_feedback_url = ndb.StringProperty()
  anticipated_spec_changes = ndb.TextProperty()

  ff_views = ndb.IntegerProperty(required=True, default=NO_PUBLIC_SIGNALS)
  safari_views = ndb.IntegerProperty(required=True, default=NO_PUBLIC_SIGNALS)
  web_dev_views = ndb.IntegerProperty(required=True)
  ff_views_link = ndb.StringProperty()
  safari_views_link = ndb.StringProperty()
  web_dev_views_link = ndb.StringProperty()
  ff_views_notes = ndb.StringProperty()
  safari_views_notes = ndb.TextProperty()
  web_dev_views_notes = ndb.TextProperty()
  other_views_notes = ndb.TextProperty()

  # Gate: Security & Privacy
  security_risks = ndb.TextProperty()
  security_review_status = ndb.IntegerProperty(default=REVIEW_PENDING)
  privacy_review_status = ndb.IntegerProperty(default=REVIEW_PENDING)

  # Gate: Testing / Regressions
  ergonomics_risks = ndb.TextProperty()
  wpt = ndb.BooleanProperty()
  wpt_descr = ndb.TextProperty()
  webview_risks = ndb.TextProperty()

  # Gate: Devrel & Docs
  devrel = ndb.StringProperty(repeated=True)
  debuggability = ndb.TextProperty()
  doc_links = ndb.StringProperty(repeated=True)
  sample_links = ndb.StringProperty(repeated=True)

  DEFAULT_CACHE_KEY = 'FeatureEntries'

  def __init__(self, *args, **kwargs):
    # Initialise Feature.blink_components with a default value.  If
    # name is present in kwargs then it would mean constructor is
    # being called for creating a new feature rather than for fetching
    # an existing feature.
    if 'name' in kwargs:
      if 'blink_components' not in kwargs:
        kwargs['blink_components'] = [BlinkComponent.DEFAULT_COMPONENT]

    super(FeatureEntry, self).__init__(*args, **kwargs)


  @classmethod
  def get_feature_entry(self, feature_id, update_cache=False):
    KEY = '%s|%s' % (Feature.DEFAULT_CACHE_KEY, feature_id)
    feature = ramcache.get(KEY)

    if feature is None or update_cache:
      entry = FeatureEntry.get_by_id(feature_id)
      if entry:
        if entry.deleted:
          return None
        ramcache.set(KEY, entry)

    return entry

  @classmethod
  def filter_unlisted(self, entry_list):
    """Filters feature entries to display only features the user should see."""
    user = users.get_current_user()
    email = None
    if user:
      email = user.email()
    allowed_entries = []
    for fe in entry_list:
      # Owners and editors of a feature can see their unlisted features.
      if (not fe.unlisted or
          email in fe.owners or
          email in fe.editors or
          (email is not None and fe.creator == email)):
        allowed_entries.append(fe)

    return allowed_entries

  @classmethod
  def get_by_ids(self, entry_ids, update_cache=False):
    result_dict = {}
    futures = []

    for fe_id in entry_ids:
      lookup_key = '%s|%s' % (FeatureEntry.DEFAULT_CACHE_KEY, fe_id)
      entry = ramcache.get(lookup_key)
      if entry is None or update_cache:
        futures.append(FeatureEntry.get_by_id_async(fe_id))
      else:
        result_dict[fe_id] = entry

    for future in futures:
      entry = future.get_result()
      if entry and not entry.deleted:
        store_key = '%s|%s' % (
            FeatureEntry.DEFAULT_CACHE_KEY, entry.key.integer_id())
        ramcache.set(store_key, entry)
        result_dict[entry.key.integer_id()] = entry

    result_list = [
        result_dict.get(fe_id) for fe_id in entry_ids
        if fe_id in result_dict]
    return result_list

  # Note: get_in_milestone will be in a new file legacy_queries.py.


class MilestoneSet(ndb.Model):  # copy from milestone fields of Feature
  """Range of milestones during which a feature will be in a certain stage."""
  desktop_first = ndb.IntegerProperty()
  desktop_last = ndb.IntegerProperty()
  android_first = ndb.IntegerProperty()
  android_last = ndb.IntegerProperty()
  ios_first = ndb.IntegerProperty()
  ios_last = ndb.IntegerProperty()
  webview_first = ndb.IntegerProperty()
  webview_last = ndb.IntegerProperty()


class Stage(ndb.Model):
  """A stage of a feature's development."""
  # Identifying information: what.
  feature_id = ndb.IntegerProperty(required=True)
  stage_type = ndb.IntegerProperty(required=True)

  # Pragmatic information: where and when.
  browser = ndb.StringProperty()  # Blank or "Chrome" for now.
  milestones = ndb.StructuredProperty(MilestoneSet)
  finch_url = ndb.StringProperty()  # copy from Feature

  # Feature stage launch team
  pm_emails = ndb.StringProperty(repeated=True)
  tl_emails = ndb.StringProperty(repeated=True)
  ux_emails = ndb.StringProperty(repeated=True)
  te_emails = ndb.StringProperty(repeated=True)

  # Gate-related fields that need separate values for repeated stages.
  # copy from Feature.
  experiment_goals = ndb.StringProperty()
  experiment_risks = ndb.StringProperty()
  experiment_extension_reason = ndb.StringProperty()
  intent_thread_url = ndb.StringProperty()


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
