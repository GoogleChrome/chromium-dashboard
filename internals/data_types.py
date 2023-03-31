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

from typing import TypedDict


# JSON representation of Stage entity data.
class StageDict(TypedDict):
  id: int
  feature_id: int
  stage_type: int
  display_name: str
  intent_stage: int
  intent_thread_url: str | None

  # Dev trial specific fields.
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
  rollout_details: str | None
  rollout_impact: int | None
  rollout_milestone: int | None
  rollout_platforms: list[str]
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


#############################
## FeatureDict definitions ##
#############################
# Nested JSON type definitions.
class FeatureDictInnerResourceInfo(TypedDict):
  samples: list[str]
  docs: list[str]


class FeatureDictInnerStandardsInfo(TypedDict):
  spec: str | None
  maturity: FeatureDictInnerMaturityInfo


class FeatureDictInnerMaturityInfo(TypedDict):
  text: str | None
  short_text: str | None
  val: int


class FeatureDictInnerBrowserStatus(TypedDict):
  text: str | None
  val: str | None
  milestone_str: str | None


class FeatureDictInnerViewInfo(TypedDict):
  text: str | None
  val: int | None
  url: str | None
  notes: str | None


class FeatureDictInnerChromeBrowserInfo(TypedDict):
  bug: str | None
  blink_components: list[str] | None
  devrel: list[str] | None
  owners: list[str] | None
  origintrial: bool | None
  intervention: bool | None
  prefixed: bool | None
  flag: bool | None
  status: FeatureDictInnerBrowserStatus

  # Old representation of ship dates.
  # TODO(danielrsmith): find if needed and remove if unneeded.
  desktop: int | None
  android: int | None
  webview: int | None
  ios: int | None


class FeatureDictInnerSingleBrowserInfo(TypedDict):
  view: FeatureDictInnerViewInfo | None


class FeatureBrowsersInfo(TypedDict):
  chrome: FeatureDictInnerChromeBrowserInfo
  ff: FeatureDictInnerSingleBrowserInfo
  safari: FeatureDictInnerSingleBrowserInfo
  webdev: FeatureDictInnerSingleBrowserInfo
  other: FeatureDictInnerSingleBrowserInfo


# Basic user info displayed for create/update attributes in
# FeatureEntry edit information.
class FeatureDictInnerUserEditInfo(TypedDict):
  by: str | None
  when: str | None


# JSON representation of FeatureEntry entity. Created from
# converters.feature_entry_to_json_verbose().
class VerboseFeatureDict(TypedDict):

  # Metadata: Creation and updates.
  id: int
  created: FeatureDictInnerUserEditInfo
  updated: FeatureDictInnerUserEditInfo
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

  experiment_timeline: str | None
  resources: FeatureDictInnerResourceInfo
  comments: str | None  # feature_notes

  # Repeated in 'browsers' section. TODO(danielrsmith): delete these?
  ff_views: int
  safari_views: int
  web_dev_views: int

  browsers: FeatureBrowsersInfo

  standards: FeatureDictInnerStandardsInfo
  is_released: bool
  is_enterprise_feature: bool
  updated_display: str | None
  new_crbug_url: str | None
