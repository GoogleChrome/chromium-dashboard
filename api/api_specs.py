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
  ('adoption_expectation', 'str'),
  ('adoption_plan', 'str'),
  ('all_platforms', 'bool'),
  ('all_platforms_descr', 'str'),
  ('anticipated_spec_changes', 'str'),
  ('api_spec', 'bool'),
  ('availability_expectation', 'str'),
  ('blink_components', 'list'),
  ('breaking_change', 'bool'),
  ('bug_url', 'str'),
  ('category', 'int'),
  ('cc_emails', 'list'),
  ('comments', 'str'),
  ('debuggability', 'str'),
  ('devrel', 'list'),
  ('devtrial_instructions', 'str'),
  ('doc_links', 'list'),
  ('editor_emails', 'list'),
  ('enterprise_feature_categories', 'list'),
  ('ergonomics_risks', 'str'),
  ('explainer_links', 'list'),
  ('feature_type', 'int'),
  ('ff_views', 'int'),
  ('ff_views_link', 'str'),
  ('ff_views_notes', 'str'),
  ('flag_name', 'str'),
  ('impl_status_chrome', 'int'),
  ('initial_public_proposal_url', 'str'),
  ('intent_stage', 'int'),
  ('interop_compat_risks', 'str'),
  ('launch_bug_url', 'str'),
  ('screenshot_links', 'list'),
  ('measurement', 'str'),
  ('motivation', 'str'),
  ('name', 'str'),
  ('non_oss_deps', 'str'),
  ('ongoing_constraints', 'str'),
  ('other_views_notes', 'str'),
  ('owner_emails', 'list'),
  ('prefixed', 'bool'),
  ('privacy_review_status', 'int'),
  ('requires_embedder_support', 'bool'),
  ('safari_views', 'int'),
  ('safari_views_link', 'str'),
  ('safari_views_notes', 'str'),
  ('sample_links', 'list'),
  ('search_tags', 'list'),
  ('security_review_status', 'int'),
  ('security_risks', 'str'),
  ('spec_link', 'str'),
  ('spec_mentors', 'list'),
  ('standard_maturity', 'int'),
  ('summary', 'str'),
  ('tag_review', 'str'),
  ('tag_review_status', 'int'),
  ('unlisted', 'bool'),
  ('web_dev_views', 'int'),
  ('web_dev_views_link', 'str'),
  ('web_dev_views_notes', 'str'),
  ('webview_risks', 'str'),
  ('wpt', 'bool'),
  ('wpt_descr', 'str'),
]

# List with stage fields that can be edited on feature create/update
# and their data types.
# Field name, data type
STAGE_FIELD_DATA_TYPES: FIELD_INFO_DATA_TYPE = [
  ('display_name', 'str'),
  ('browser', 'str'),
  ('experiment_goals', 'str'),
  ('experiment_risks', 'str'),
  ('experiment_extension_reason', 'str'),
  ('intent_thread_url', 'str'),
  ('origin_trial_feedback_url', 'str'),
  ('announcement_url', 'str'),
  ('rollout_impact', 'int'),
  ('rollout_milestone', 'int'),
  ('rollout_platforms', 'list'),
  ('rollout_details', 'str'),
  ('enterprise_policies', 'str'),
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
