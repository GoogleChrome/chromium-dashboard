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

from typing import Any, Optional

from google.cloud import ndb  # type: ignore

from framework import rediscache
from internals.core_enums import *
import settings


class ReviewResultProperty(ndb.StringProperty):
  """A StringProperty representing the result of an external review.

  These are the values after the `:` in
  https://github.com/mozilla/standards-positions/labels?q=position%3A,
  https://github.com/WebKit/standards-positions/labels?q=position%3A, and
  https://github.com/w3ctag/design-reviews/labels?q=resolution%3A, plus the special value "closed"
  to represent a review that was closed without a position.
  """

  CLOSED_WITHOUT_POSITION = 'closed'


class FeatureEntry(ndb.Model):
  """This is the main representation of a feature that we are tracking."""

  # Fields that should not be mutated by user edit requests.
  FIELDS_IMMUTABLE_BY_USER = frozenset([
    'id',
    'created',
    'creator_email',
    'updated',
    'updater_email',
    'accurate_as_of',
    'outstanding_notifications',
    'deleted',
    'star_count',
    'feature_type',
    'ai_test_eval_report',
    'ai_test_eval_run_status',
    'ai_test_eval_status_timestamp',
  ])

  # All required fields needed upon feature creation.
  REQUIRED_FIELDS = frozenset([
    'feature_type',
    'name',
    'summary',
  ])

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
  markdown_fields = ndb.StringProperty(repeated=True)
  category = ndb.IntegerProperty(required=True)
  enterprise_product_category = ndb.IntegerProperty(required=False, default=ENTERPRISE_PRODUCT_CATEGORY_CHROME_BROWSER_UPDATE)
  enterprise_feature_categories = ndb.StringProperty(repeated=True)
  blink_components = ndb.StringProperty(repeated=True)
  star_count = ndb.IntegerProperty(default=0)
  search_tags = ndb.StringProperty(repeated=True)
  feature_notes = ndb.TextProperty()  # copy from comments
  web_feature = ndb.StringProperty()  # ID from webstatus.dev
  webdx_usecounter_enum = ndb.StringProperty()

  # Metadata: Process information
  feature_type = ndb.IntegerProperty(required=True, default=FEATURE_TYPE_INCUBATE_ID)
  intent_stage = ndb.IntegerProperty(default=INTENT_NONE)
  active_stage_id = ndb.IntegerProperty()
  bug_url = ndb.StringProperty()  # Tracking bug
  launch_bug_url = ndb.StringProperty()  # FLT or go/launch
  screenshot_links = ndb.StringProperty(repeated=True)
  first_enterprise_notification_milestone = ndb.IntegerProperty()
  enterprise_impact = ndb.IntegerProperty(default=ENTERPRISE_IMPACT_NONE)
  is_releasenotes_content_reviewed = ndb.BooleanProperty(default=False)
  is_releasenotes_publish_ready = ndb.BooleanProperty(default=False)
  breaking_change = ndb.BooleanProperty(default=False)
  confidential = ndb.BooleanProperty(default=False)
  shipping_year = ndb.IntegerProperty()

  # Implementation in Chrome
  impl_status_chrome = ndb.IntegerProperty(required=True, default=PROPOSED)
  flag_name = ndb.StringProperty()
  finch_name = ndb.StringProperty()
  non_finch_justification = ndb.TextProperty()
  ongoing_constraints = ndb.TextProperty()
  rollout_plan = ndb.IntegerProperty(required=True, default=ROLLOUT_100)

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
  automation_spec = ndb.BooleanProperty(default=False)
  spec_mentor_emails = ndb.StringProperty(repeated=True)
  interop_compat_risks = ndb.TextProperty()
  prefixed = ndb.BooleanProperty()
  all_platforms = ndb.BooleanProperty()
  all_platforms_descr = ndb.TextProperty()
  tag_review = ndb.StringProperty()
  tag_review_status = ndb.IntegerProperty(default=REVIEW_PENDING)
  tag_review_resolution: Optional[ReviewResultProperty] = ReviewResultProperty()
  non_oss_deps = ndb.TextProperty()
  anticipated_spec_changes = ndb.TextProperty()

  ff_views = ndb.IntegerProperty(required=True, default=NO_PUBLIC_SIGNALS)
  safari_views = ndb.IntegerProperty(required=True, default=NO_PUBLIC_SIGNALS)
  web_dev_views = ndb.IntegerProperty(required=True, default=DEV_NO_SIGNALS)
  ff_views_link = ndb.StringProperty()
  ff_views_link_result: Optional[ReviewResultProperty] = ReviewResultProperty()
  safari_views_link = ndb.StringProperty()
  safari_views_link_result: Optional[ReviewResultProperty] = ReviewResultProperty()
  web_dev_views_link = ndb.StringProperty()
  ff_views_notes = ndb.StringProperty()
  safari_views_notes = ndb.TextProperty()
  web_dev_views_notes = ndb.TextProperty()
  other_views_notes = ndb.TextProperty()

  # AI evaluation fields.
  ai_test_eval_report = ndb.TextProperty(indexed=False)
  ai_test_eval_run_status = ndb.IntegerProperty()
  ai_test_eval_status_timestamp = ndb.DateTimeProperty()

  @ndb.ComputedProperty
  def has_open_tag_review(self):
    return self.tag_review is not None and self.tag_review_resolution is None

  @ndb.ComputedProperty
  def has_open_ff_review(self):
    return (
      self.ff_views not in [IN_DEV, SHIPPED, SIGNALS_NA]
      and self.ff_views_link is not None
      and self.ff_views_link_result is None
    )

  @ndb.ComputedProperty
  def has_open_safari_review(self):
    return (
      self.safari_views not in [IN_DEV, SHIPPED, SIGNALS_NA]
      and self.safari_views_link is not None
      and self.safari_views_link_result is None
    )

  # Gate: Security & Privacy
  security_risks = ndb.TextProperty()
  security_review_status = ndb.IntegerProperty(default=REVIEW_PENDING)
  privacy_review_status = ndb.IntegerProperty(default=REVIEW_PENDING)
  security_continuity_id = ndb.IntegerProperty()
  security_launch_issue_id = ndb.IntegerProperty()

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

  # The prefix of rediscache keys for storing all information
  # about a feature.
  DEFAULT_CACHE_KEY = 'FeatureEntries'
  # The prefix of rediscache keys for storing the feature name
  # of a feature.
  FEATURE_NAME_CACHE_KEY = 'FeatureNames'
  # The prefix used when cacheing entire search results.
  SEARCH_CACHE_KEY = 'FeatureSearch'

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

  def put(self, **kwargs) -> Any:
    key = super(FeatureEntry, self).put(**kwargs)
    # Invalidate rediscache for the individual feature view.
    cache_key = FeatureEntry.feature_cache_key(
        FeatureEntry.DEFAULT_CACHE_KEY, self.key.integer_id())
    rediscache.delete(cache_key)

    # Invalidate rediscache for the individual feature name.
    cache_key = FeatureEntry.feature_cache_key(
        FeatureEntry.FEATURE_NAME_CACHE_KEY, self.key.integer_id())
    rediscache.delete(cache_key)
    rediscache.delete_keys_with_prefix(FeatureEntry.SEARCH_CACHE_KEY)

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
      'rollout_milestone': 'desktop_first',
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
  display_name = ndb.StringProperty()

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
  announcement_url = ndb.StringProperty()
  experiment_extension_reason = ndb.TextProperty()
  intent_thread_url = ndb.StringProperty()
  intent_subject_line = ndb.StringProperty()

  # Origin trial fields
  origin_trial_id = ndb.StringProperty()
  origin_trial_feedback_url = ndb.StringProperty()
  experiment_goals = ndb.TextProperty()
  experiment_risks = ndb.TextProperty()
  ot_action_requested = ndb.BooleanProperty(default=False)
  ot_activation_date = ndb.DateProperty()
  ot_approval_buganizer_component = ndb.IntegerProperty()
  ot_approval_buganizer_custom_field_id = ndb.IntegerProperty()
  ot_approval_criteria_url = ndb.StringProperty()
  ot_approval_group_email = ndb.StringProperty()
  ot_chromium_trial_name = ndb.StringProperty()
  ot_description = ndb.TextProperty()
  ot_display_name = ndb.StringProperty()
  ot_documentation_url = ndb.StringProperty()
  ot_emails = ndb.StringProperty(repeated=True)
  ot_feedback_submission_url = ndb.StringProperty()
  ot_has_third_party_support = ndb.BooleanProperty(default=False)
  ot_is_critical_trial = ndb.BooleanProperty(default=False)
  ot_is_deprecation_trial = ndb.BooleanProperty(default=False)
  ot_owner_email = ndb.StringProperty()
  ot_request_note = ndb.TextProperty()  # Deprecated.
  ot_require_approvals = ndb.BooleanProperty(default=False)
  ot_setup_status = ndb.IntegerProperty()
  ot_use_counter_bucket_number = ndb.IntegerProperty()
  ot_webfeature_use_counter = ndb.StringProperty()

  # Origin trial stage id that this stage extends, if trial extension stage.
  ot_stage_id = ndb.IntegerProperty()

  # Enterprise
  rollout_impact = ndb.IntegerProperty(default=2) # deprecated
  # rollout_milestone will be migrated to milestones.desktop_first as the
  # default "start" milestone.
  rollout_milestone = ndb.IntegerProperty()
  rollout_platforms = ndb.StringProperty(repeated=True)
  rollout_details = ndb.TextProperty()
  enterprise_policies = ndb.StringProperty(repeated=True)

  archived = ndb.BooleanProperty(default=False)
  created = ndb.DateTimeProperty(auto_now_add=True)
