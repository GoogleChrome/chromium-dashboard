# -*- coding: utf-8 -*-
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

from typing import Any, TypedDict

from google.cloud import ndb  # type: ignore

from framework import rediscache
from internals.core_enums import *
import settings


class UserEditInfo(TypedDict):
  by: str | None
  when: str | None 

class FeatureResourceInfo(TypedDict):
  samples: list[str]
  docs: list[str]


class StandardsInfo(TypedDict):
  spec: str | None
  maturity: MaturityInfo


class MaturityInfo(TypedDict):
  text: str | None
  short_text: str | None
  val: int


class BrowserStatus(TypedDict):
  text: str | None
  val: str | None
  milestone_str: str | None


class ViewInfo(TypedDict):
  text: str | None
  val: int | None
  url: str | None
  notes: str | None

class ChromeBrowserInfo(TypedDict):
  bug: str | None
  blink_components: list[str] | None
  devrel: list[str] | None
  owners: list[str] | None
  origintrial: bool | None
  intervention: bool | None
  prefixed: bool | None
  flag: bool | None
  status: BrowserStatus
  desktop: int | None
  android: int | None
  webview: int | None
  ios: int | None


class SingleBrowserInfo(TypedDict):
  view: ViewInfo | None


class FeatureBrowsersInfo(TypedDict):
  chrome: ChromeBrowserInfo
  ff: SingleBrowserInfo
  safari: SingleBrowserInfo
  webdev: SingleBrowserInfo
  other: SingleBrowserInfo


class StageDict(TypedDict):
  id: int
  feature_id: int
  stage_type: int
  intent_stage: int
  intent_thread_url: str | None

  # Dev trial specific fields.
  ready_for_trial_url: str | None
  announcement_url: str | None

  
  # Origin trial specific fields.
  experiment_goals: str | None
  experiment_risks: str | None
  extensions: list[StageDict]  # type: ignore
  origin_trial_feedback_url: str | None
  
  # Trial extension specific fields.
  ot_stage_id: int | None
  experiment_extension_reason: str | None

  # Ship specific fields
  finch_url: str | None

  # Enterprise specific fields
  rollout_milestone: int | None
  rollout_platforms: list[str]
  rollout_details: list[str]
  enterprise_policies: list[str]

  # Email information
  pm_emails: list[str]
  tl_emails: list[str]
  ux_emails: list[str]
  te_emails: list[str]

  # Milestone fields
  desktop_first: int | None
  android_first: int | None
  ios_first: int | None
  webview_first: int | None
  desktop_last: int | None
  android_last: int | None
  ios_last: int | None
  webview_last: int | None

  # Legacy fields or fields that now live on stage entities.
  # TODO(danielrsmith): stop representing these on the feature dict
  # and references them direct from stage entities.
  intent_to_implement_url: str | None
  intent_to_experiment_url: str  | None
  intent_to_extend_experiment_url: str | None
  intent_to_ship_url: str | None

  # Legacy milestone fields that now live on stage entities.
  dt_milestone_desktop_start: int | None
  dt_milestone_android_start: int | None
  dt_milestone_ios_start: int | None
  dt_milestone_webview_start: int | None
  ot_milestone_desktop_start: int | None
  ot_milestone_android_start: int | None
  ot_milestone_webview_start: int | None
  ot_milestone_desktop_end: int | None
  ot_milestone_android_end: int | None
  ot_milestone_webview_end: int | None
  shipped_milestone: int | None
  shipped_android_milestone: int | None
  shipped_ios_milestone: int | None
  shipped_webview_milestone: int | None


class VerboseFeatureDict(TypedDict):

  # Metadata: Creation and updates.
  id: int
  created: UserEditInfo
  updated: UserEditInfo
  accurate_as_of: str | None
  creator_email: str | None
  updater_email: str | None

  # Metadata: Access controls
  owner_emails: list[str]
  editor_emails: list[str]
  cc_emails: list[str]
  spec_mentor_emails: list[str]
  unlisted: bool
  deleted: bool

  # Renamed metadata fields
  editors: list[str]
  cc_recipients: list[str]
  spec_mentors: list[str]
  creator: str | None

  # Descriptive info.
  name: str
  summary: str
  category: str
  category_int: int
  blink_components: list[str]
  star_count: int
  search_tags: list[str]
  feature_notes: str | None
  enterprise_feature_categories: list[str]

  # Metadata: Process information
  feature_type: str
  feature_type_int: int
  intent_stage: str
  intent_stage_int: int
  active_stage_id: int | None
  bug_url: str | None
  launch_bug_url: str | None
  breaking_change: bool

  # Implementation in Chrome
  flag_name: str | None
  ongoing_constraints: str | None

  # Topic: Adoption
  motivation: str | None
  devtrial_instructions: str | None
  activation_risks: str | None
  measurement: str | None
  availability_expectation: str | None
  adoption_expectation: str | None
  adoption_plan: str | None

  # Gate: Standardization and Interop
  initial_public_proposal_url: str | None
  explainer_links: list[str]
  requires_embedder_support: bool
  spec_link: str | None
  api_spec: str | None
  prefixed: bool | None
  interop_compat_risks: str | None
  all_platforms: bool | None
  all_platforms_descr: bool | None
  tag_review: str | None
  non_oss_deps: str | None
  anticipated_spec_changes: str | None

  # Gate: Security & Privacy
  security_risks: str | None
  tags: list[str]
  tag_review_status: str
  tag_review_status_int: int | None
  security_review_status: str
  security_review_status_int: int | None
  privacy_review_status: str
  privacy_review_status_int: int | None

  # Gate: Testing / Regressions
  ergonomics_risks: str | None
  wpt: bool | None
  wpt_descr: str | None
  webview_risks: str | None

  # Gate: Devrel & Docs
  devrel_emails: list[str]
  debuggability: str | None
  doc_links: list[str]
  sample_links: list[str]

  stages: list[StageDict]

  # Legacy fields or fields that now live on stage entities.
  # TODO(danielrsmith): stop representing these on the feature dict
  # and references them direct from stage entities.
  intent_to_implement_url: str | None
  intent_to_experiment_url: str  | None
  intent_to_extend_experiment_url: str | None
  intent_to_ship_url: str | None
  ready_for_trial_url: str | None
  origin_trial_feeback_url: str | None
  experiment_goals: str | None
  experiment_risks: str | None
  announcement_url: str | None
  experiment_extension_reason: str | None
  rollout_milestone: int | None
  rollout_details: str | None
  experiment_timeline: str | None
  resources: FeatureResourceInfo
  comments: str | None  # feature_notes

  # Repeated in 'browsers' section. TODO(danielrsmith): delete these?
  ff_views: int
  safari_views: int
  web_dev_views: int

  browsers: FeatureBrowsersInfo

  # Legacy milestone fields that now live on stage entities.
  dt_milestone_desktop_start: int | None
  dt_milestone_android_start: int | None
  dt_milestone_ios_start: int | None
  dt_milestone_webview_start: int | None
  ot_milestone_desktop_start: int | None
  ot_milestone_android_start: int | None
  ot_milestone_webview_start: int | None
  ot_milestone_desktop_end: int | None
  ot_milestone_android_end: int | None
  ot_milestone_webview_end: int | None

  finch_url: str | None

  standards: StandardsInfo
  is_released: bool
  is_enterprise_feature: bool
  updated_display: str | None
  new_crbug_url: str | None


class FeatureEntry(ndb.Model):  # Copy from Feature
  """This is the main representation of a feature that we are tracking."""

  # Metadata: Creation and updates.
  created = ndb.DateTimeProperty(auto_now_add=True)
  updated = ndb.DateTimeProperty(auto_now_add=True)
  accurate_as_of = ndb.DateTimeProperty()
  outstanding_notifications = ndb.IntegerProperty(default=0)
  creator_email = ndb.StringProperty()
  updater_email = ndb.StringProperty()

  # Metadata: Access controls
  owner_emails = ndb.StringProperty(repeated=True)  # copy from owner
  editor_emails = ndb.StringProperty(repeated=True)
  cc_emails = ndb.StringProperty(repeated=True)
  unlisted = ndb.BooleanProperty(default=False)
  deleted = ndb.BooleanProperty(default=False)

  # Descriptive info.
  name = ndb.StringProperty(required=True)
  summary = ndb.TextProperty(required=True)
  category = ndb.IntegerProperty(required=True)
  enterprise_feature_categories = ndb.StringProperty(repeated=True)
  blink_components = ndb.StringProperty(repeated=True)
  star_count = ndb.IntegerProperty(default=0)
  search_tags = ndb.StringProperty(repeated=True)
  feature_notes = ndb.TextProperty()  # copy from comments

  # Metadata: Process information
  feature_type = ndb.IntegerProperty(required=True, default=FEATURE_TYPE_INCUBATE_ID)
  intent_stage = ndb.IntegerProperty(default=INTENT_NONE)
  active_stage_id = ndb.IntegerProperty()
  bug_url = ndb.StringProperty()  # Tracking bug
  launch_bug_url = ndb.StringProperty()  # FLT or go/launch
  breaking_change = ndb.BooleanProperty(default=False)

  # Implementation in Chrome
  impl_status_chrome = ndb.IntegerProperty(required=True, default=NO_ACTIVE_DEV)
  flag_name = ndb.StringProperty()
  ongoing_constraints = ndb.TextProperty()

  # Topic: Adoption (reviewed by API Owners.  Auto-approved gate later?)
  motivation = ndb.TextProperty()
  devtrial_instructions = ndb.TextProperty()
  activation_risks = ndb.TextProperty()
  measurement = ndb.TextProperty()
  availability_expectation = ndb.TextProperty()
  adoption_expectation = ndb.TextProperty()
  adoption_plan = ndb.TextProperty()

  # Gate: Standardization & Interop
  initial_public_proposal_url = ndb.StringProperty()
  explainer_links = ndb.StringProperty(repeated=True)
  requires_embedder_support = ndb.BooleanProperty(default=False)
  standard_maturity = ndb.IntegerProperty(required=True, default=UNSET_STD)
  spec_link = ndb.StringProperty()
  api_spec = ndb.BooleanProperty(default=False)
  spec_mentor_emails = ndb.StringProperty(repeated=True)
  interop_compat_risks = ndb.TextProperty()
  prefixed = ndb.BooleanProperty()
  all_platforms = ndb.BooleanProperty()
  all_platforms_descr = ndb.TextProperty()
  tag_review = ndb.StringProperty()
  tag_review_status = ndb.IntegerProperty(default=REVIEW_PENDING)
  non_oss_deps = ndb.TextProperty()
  anticipated_spec_changes = ndb.TextProperty()

  ff_views = ndb.IntegerProperty(required=True, default=NO_PUBLIC_SIGNALS)
  safari_views = ndb.IntegerProperty(required=True, default=NO_PUBLIC_SIGNALS)
  web_dev_views = ndb.IntegerProperty(required=True, default=DEV_NO_SIGNALS)
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
  devrel_emails = ndb.StringProperty(repeated=True)
  debuggability = ndb.TextProperty()
  doc_links = ndb.StringProperty(repeated=True)
  sample_links = ndb.StringProperty(repeated=True)

  # Legacy fields that we display on old entries, but don't allow editing.
  experiment_timeline = ndb.TextProperty()  # Display-only

  DEFAULT_CACHE_KEY = 'FeatureEntries'

  def __init__(self, *args, **kwargs):
    # Initialise Feature.blink_components with a default value.  If
    # name is present in kwargs then it would mean constructor is
    # being called for creating a new feature rather than for fetching
    # an existing feature.
    if 'name' in kwargs:
      if 'blink_components' not in kwargs:
        kwargs['blink_components'] = [settings.DEFAULT_COMPONENT]

    super(FeatureEntry, self).__init__(*args, **kwargs)

  @classmethod
  def feature_cache_key(cls, cache_key, feature_id):
    return '%s|%s' % (cache_key, feature_id)

  @classmethod
  def feature_cache_prefix(cls):
    return '%s|*' % (cls.DEFAULT_CACHE_KEY)

  def put(self, **kwargs) -> Any:
    key = super(FeatureEntry, self).put(**kwargs)
    # Invalidate rediscache for the individual feature view.
    cache_key = FeatureEntry.feature_cache_key(
        FeatureEntry.DEFAULT_CACHE_KEY, self.key.integer_id())
    rediscache.delete(cache_key)

    return key

  # Note: get_in_milestone will be in a new file legacy_queries.py.


class MilestoneSet(ndb.Model):  # copy from milestone fields of Feature
  """Range of milestones during which a feature will be in a certain stage."""

  # Mapping of old milestone fields to the new fields they should use
  # in the MilestoneSet kind.
  MILESTONE_FIELD_MAPPING = {
      'shipped_milestone': 'desktop_first',
      'shipped_android_milestone': 'android_first',
      'shipped_ios_milestone': 'ios_first',
      'shipped_webview_milestone': 'webview_first',
      'ot_milestone_desktop_start': 'desktop_first',
      'ot_milestone_desktop_end': 'desktop_last',
      'ot_milestone_android_start': 'android_first',
      'ot_milestone_android_end': 'android_last',
      'ot_milestone_webview_start': 'webview_first',
      'ot_milestone_webview_end': 'webview_last',
      'dt_milestone_desktop_start': 'desktop_first',
      'dt_milestone_android_start': 'android_first',
      'dt_milestone_ios_start': 'ios_first',
      'dt_milestone_webview_start': 'webview_first',
    }

  # List of milestone fields relevant to the origin trial stage types.
  OT_MILESTONE_FIELD_NAMES = [
    {'old': 'ot_milestone_desktop_start', 'new': 'desktop_first'},
    {'old': 'ot_milestone_desktop_end', 'new': 'desktop_last'},
    {'old': 'ot_milestone_android_start', 'new': 'android_first'},
    {'old': 'ot_milestone_android_end', 'new': 'android_last'},
    {'old': 'ot_milestone_webview_start', 'new': 'webview_first'},
    {'old': 'ot_milestone_webview_end', 'new': 'webview_last'},
  ]

  OT_EXTENSION_MILESTONE_FIELD_NAMES = [
    {'old': 'extension_desktop_last', 'new': 'desktop_last'},
    {'old': 'extension_android_last', 'new': 'android_last'},
    {'old': 'extension_webview_last', 'new': 'webview_last'},
  ]

  # List of milestone fields relevant to the dev trial stage types.
  DEV_TRIAL_MILESTONE_FIELD_NAMES = [
    {'old': 'dt_milestone_desktop_start', 'new': 'desktop_first'},
    {'old': 'dt_milestone_android_start', 'new': 'android_first'},
    {'old': 'dt_milestone_ios_start', 'new': 'ios_first'},
    {'old': 'dt_milestone_webview_start', 'new': 'webview_first'},
  ]

  # List of milestone fields relevant to the shipping stage types.
  SHIPPING_MILESTONE_FIELD_NAMES = [
    {'old': 'shipped_milestone', 'new': 'desktop_first'},
    {'old': 'shipped_android_milestone', 'new': 'android_first'},
    {'old': 'shipped_ios_milestone', 'new': 'ios_first'},
    {'old': 'shipped_webview_milestone', 'new': 'webview_first'},
  ]

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
  experiment_goals = ndb.TextProperty()
  experiment_risks = ndb.TextProperty()
  experiment_extension_reason = ndb.TextProperty()
  intent_thread_url = ndb.StringProperty()
  intent_subject_line = ndb.StringProperty()
  origin_trial_feedback_url = ndb.StringProperty()
  announcement_url = ndb.StringProperty()
  # Origin trial stage id that this stage extends, if trial extension stage.
  ot_stage_id = ndb.IntegerProperty()

  #Enterprise
  rollout_milestone = ndb.IntegerProperty()
  rollout_platforms = ndb.StringProperty(repeated=True)
  rollout_details = ndb.TextProperty()
  enterprise_policies = ndb.StringProperty(repeated=True)

  archived = ndb.BooleanProperty(default=False)
