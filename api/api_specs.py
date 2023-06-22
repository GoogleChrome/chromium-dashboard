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

# Data type for lists defining field data type information.
FIELD_INFO_DATA_TYPE = list[tuple[str, str]]

# List with fields that can be edited on feature create/update
# and their data types.
# Field name, data type
FEATURE_FIELD_DATA_TYPES: FIELD_INFO_DATA_TYPE = [
  ('activation_risks', 'str'),
  ('active_stage_id', 'int'),
  ('adoption_expectation', 'str'),
  ('adoption_plan', 'str'),
  ('all_platforms', 'bool'),
  ('all_platforms_descr', 'str'),
  ('anticipated_spec_changes', 'str'),
  ('api_spec', 'bool'),
  ('availability_expectation', 'str'),
  ('blink_components', 'split_str'),
  ('breaking_change', 'bool'),
  ('bug_url', 'link'),
  ('category', 'int'),
  ('cc_emails', 'emails'),
  ('comments', 'str'),
  ('debuggability', 'str'),
  ('devrel_emails', 'emails'),
  ('devtrial_instructions', 'link'),
  ('doc_links', 'links'),
  ('editor_emails', 'emails'),
  ('enterprise_feature_categories', 'split_str'),
  ('ergonomics_risks', 'str'),
  ('explainer_links', 'links'),
  ('feature_type', 'int'),
  ('ff_views', 'int'),
  ('ff_views_link', 'link'),
  ('ff_views_notes', 'str'),
  ('flag_name', 'str'),
  ('finch_name', 'str'),
  ('non_finch_justification', 'str'),
  ('impl_status_chrome', 'int'),
  ('initial_public_proposal_url', 'str'),
  ('intent_stage', 'int'),
  ('interop_compat_risks', 'str'),
  ('launch_bug_url', 'link'),
  ('screenshot_links', 'links'),
  ('measurement', 'str'),
  ('motivation', 'str'),
  ('name', 'str'),
  ('non_oss_deps', 'str'),
  ('ongoing_constraints', 'str'),
  ('other_views_notes', 'str'),
  ('owner_emails', 'emails'),
  ('prefixed', 'bool'),
  ('privacy_review_status', 'int'),
  ('requires_embedder_support', 'bool'),
  ('safari_views', 'int'),
  ('safari_views_link', 'link'),
  ('safari_views_notes', 'str'),
  ('sample_links', 'links'),
  ('search_tags', 'split_str'),
  ('security_review_status', 'int'),
  ('security_risks', 'str'),
  ('spec_link', 'link'),
  ('spec_mentor_emails', 'emails'),
  ('standard_maturity', 'int'),
  ('summary', 'str'),
  ('tag_review', 'str'),
  ('tag_review_status', 'int'),
  ('unlisted', 'bool'),
  ('web_dev_views', 'int'),
  ('web_dev_views_link', 'link'),
  ('web_dev_views_notes', 'str'),
  ('webview_risks', 'str'),
  ('wpt', 'bool'),
  ('wpt_descr', 'str'),
]

# List with stage fields that can be edited on feature create/update
# and their data types.
# Field name, data type
STAGE_FIELD_DATA_TYPES: FIELD_INFO_DATA_TYPE = [
  ('announcement_url', 'link'),
  ('browser', 'str'),
  ('display_name', 'str'),
  ('enterprise_policies', 'split_str'),
  ('finch_url', 'link'),
  ('experiment_goals', 'str'),
  ('experiment_risks', 'str'),
  ('experiment_extension_reason', 'str'),
  ('intent_thread_url', 'link'),
  ('origin_trial_feedback_url', 'link'),
  ('rollout_impact', 'int'),
  ('rollout_milestone', 'int'),
  ('rollout_platforms', 'split_str'),
  ('rollout_details', 'str'),
]

MILESTONESET_FIELD_DATA_TYPES: FIELD_INFO_DATA_TYPE = [
  ('desktop_first', 'int'),
  ('desktop_last', 'int'),
  ('android_first', 'int'),
  ('android_last', 'int'),
  ('ios_first', 'int'),
  ('ios_last', 'int'),
  ('webview_first', 'int'),
  ('webview_last', 'int'),
]
