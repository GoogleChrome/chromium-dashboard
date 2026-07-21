# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
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

"""Form field specifications copied from client-side code.

Only type and label attributes are copied as requested.
"""

from typing import TypedDict


class FieldSpec(TypedDict):
    """Specification for a single form field, including its type and display label."""

    type: str
    label: str


ALL_FIELDS: dict[str, FieldSpec] = {
    'name': {
        'type': 'input',
        'label': 'Feature name',
    },
    'summary': {
        'type': 'textarea',
        'label': 'Summary',
    },
    'owner': {
        'type': 'input',
        'label': 'Feature owners',
    },
    'editors': {
        'type': 'input',
        'label': 'Feature editors',
    },
    'cc_recipients': {
        'type': 'input',
        'label': 'CC',
    },
    'unlisted': {
        'type': 'checkbox',
        'label': 'Unlisted',
    },
    'blink_components': {
        'type': 'datalist',
        'label': 'Blink component',
    },
    'web_feature': {
        'type': 'datalist',
        'label': 'Web Feature ID',
    },
    'category': {
        'type': 'select',
        'label': 'Category',
    },
    'enterprise_product_category': {
        'type': 'radios',
        'label': 'Enterprise product category',
    },
    'feature_type': {
        'type': 'select',
        'label': 'Feature type',
    },
    'active_stage_id': {
        'type': 'select',
        'label': 'Active stage',
    },
    'search_tags': {
        'type': 'input',
        'label': 'Search tags',
    },
    'bug_url': {
        'type': 'input',
        'label': 'Tracking bug URL',
    },
    'launch_bug_url': {
        'type': 'input',
        'label': 'Launch URL',
    },
    'screenshot_links': {
        'type': 'attachments',
        'label': 'Screenshot link(s)',
    },
    'first_enterprise_notification_milestone': {
        'type': 'input',
        'label': 'First notification milestone',
    },
    'motivation': {
        'type': 'textarea',
        'label': 'Motivation',
    },
    'deprecation_motivation': {
        'type': 'textarea',
        'label': 'Motivation',
    },
    'initial_public_proposal_url': {
        'type': 'input',
        'label': 'Initial public proposal URL',
    },
    'explainer_links': {
        'type': 'textarea',
        'label': 'Explainer link(s)',
    },
    'spec_link': {
        'type': 'input',
        'label': 'Spec link',
    },
    'comments': {
        'type': 'textarea',
        'label': 'Comments',
    },
    'standard_maturity': {
        'type': 'select',
        'label': 'Standard maturity',
    },
    'api_spec': {
        'type': 'checkbox',
        'label': 'API spec',
    },
    'automation_spec': {
        'type': 'checkbox',
        'label': 'Automation spec',
    },
    'spec_mentors': {
        'type': 'input',
        'label': 'Spec mentors',
    },
    'intent_to_implement_url': {
        'type': 'input',
        'label': 'Intent to Prototype link',
    },
    'intent_to_deprecate_url': {
        'type': 'input',
        'label': 'Intent to Deprecate and Remove link',
    },
    'doc_links': {
        'type': 'textarea',
        'label': 'Doc link(s)',
    },
    'measurement': {
        'type': 'textarea',
        'label': 'Measurement',
    },
    'availability_expectation': {
        'type': 'textarea',
        'label': 'Availability expectation',
    },
    'adoption_expectation': {
        'type': 'textarea',
        'label': 'Adoption expectation',
    },
    'adoption_plan': {
        'type': 'textarea',
        'label': 'Adoption plan',
    },
    'security_review_status': {
        'type': 'select',
        'label': 'Security review status',
    },
    'privacy_review_status': {
        'type': 'select',
        'label': 'Privacy review status',
    },
    'tag_review': {
        'type': 'textarea',
        'label': 'TAG specification review',
    },
    'tag_review_status': {
        'type': 'select',
        'label': 'TAG specification review status',
    },
    'intent_to_ship_url': {
        'type': 'input',
        'label': 'Intent to Ship link',
    },
    'announcement_url': {
        'type': 'input',
        'label': 'Ready for Developer Testing link',
    },
    'intent_to_experiment_url': {
        'type': 'input',
        'label': 'Intent to Experiment link',
    },
    'intent_to_extend_experiment_url': {
        'type': 'input',
        'label': 'Intent to Extend Experiment link',
    },
    'r4dt_url': {
        'type': 'input',
        'label': 'Request for Deprecation Trial link',
    },
    'interop_compat_risks': {
        'type': 'textarea',
        'label': 'Interoperability and compatibility risks',
    },
    'safari_views': {
        'type': 'select',
        'label': 'WebKit views',
    },
    'safari_views_link': {
        'type': 'input',
        'label': 'WebKit views link',
    },
    'safari_views_notes': {
        'type': 'textarea',
        'label': 'WebKit views notes',
    },
    'ff_views': {
        'type': 'select',
        'label': 'Firefox views',
    },
    'ff_views_link': {
        'type': 'input',
        'label': 'Firefox views link',
    },
    'ff_views_notes': {
        'type': 'textarea',
        'label': 'Firefox views notes',
    },
    'web_dev_views': {
        'type': 'select',
        'label': 'Web / Framework developer views',
    },
    'web_dev_views_link': {
        'type': 'input',
        'label': 'Web / Framework developer views link',
    },
    'web_dev_views_notes': {
        'type': 'textarea',
        'label': 'Web / Framework developer views notes',
    },
    'other_views_notes': {
        'type': 'textarea',
        'label': 'Other views',
    },
    'ergonomics_risks': {
        'type': 'textarea',
        'label': 'Ergonomics risks',
    },
    'activation_risks': {
        'type': 'textarea',
        'label': 'Activation risks',
    },
    'security_risks': {
        'type': 'textarea',
        'label': 'Security Risks',
    },
    'webview_risks': {
        'type': 'textarea',
        'label': 'WebView application risks',
    },
    'experiment_goals': {
        'type': 'textarea',
        'label': 'Experiment goals',
    },
    'experiment_timeline': {
        'type': 'textarea',
        'label': 'Experiment timeline',
    },
    'ot_milestone_desktop_start': {
        'type': 'input',
        'label': 'OT desktop start',
    },
    'ot_milestone_desktop_end': {
        'type': 'input',
        'label': 'OT desktop end',
    },
    'ot_milestone_android_start': {
        'type': 'input',
        'label': 'OT Android start',
    },
    'ot_milestone_android_end': {
        'type': 'input',
        'label': 'OT Android end',
    },
    'ot_milestone_webview_start': {
        'type': 'input',
        'label': 'OT WebView start',
    },
    'ot_milestone_webview_end': {
        'type': 'input',
        'label': 'OT WebView end',
    },
    'experiment_risks': {
        'type': 'textarea',
        'label': 'Experiment risks',
    },
    'experiment_extension_reason': {
        'type': 'textarea',
        'label': 'Experiment extension reason',
    },
    'extension_desktop_last': {
        'type': 'input',
        'label': 'Trial extension end milestone',
    },
    'ongoing_constraints': {
        'type': 'textarea',
        'label': 'Ongoing Constraints',
    },
    'rollout_plan': {
        'type': 'select',
        'label': 'Rollout plan',
    },
    'origin_trial_feedback_url': {
        'type': 'input',
        'label': 'Origin trial feedback summary',
    },
    'ot_documentation_url': {
        'type': 'input',
        'label': 'Documentation link',
    },
    'anticipated_spec_changes': {
        'type': 'textarea',
        'label': 'Anticipated spec changes',
    },
    'finch_url': {
        'type': 'input',
        'label': 'Finch experiment',
    },
    'i2e_lgtms': {
        'type': 'input',
        'label': 'Intent to Experiment LGTM by',
    },
    'i2s_lgtms': {
        'type': 'input',
        'label': 'Intent to Ship LGTMs by',
    },
    'r4dt_lgtms': {
        'type': 'input',
        'label': 'Request for Deprecation Trial LGTM by',
    },
    'debuggability': {
        'type': 'textarea',
        'label': 'Debuggability',
    },
    'all_platforms': {
        'type': 'checkbox',
        'label': 'Supported on all platforms?',
    },
    'all_platforms_descr': {
        'type': 'textarea',
        'label': 'Platform support explanation',
    },
    'wpt': {
        'type': 'checkbox',
        'label': 'Web Platform Tests',
    },
    'wpt_descr': {
        'type': 'textarea',
        'label': 'Web Platform Tests or other automated test description',
    },
    'sample_links': {
        'type': 'textarea',
        'label': 'Demo and sample links',
    },
    'non_oss_deps': {
        'type': 'textarea',
        'label': 'Non-OSS dependencies',
    },
    'devrel': {
        'type': 'input',
        'label': 'Developer relations emails',
    },
    'shipped_milestone': {
        'type': 'input',
        'label': 'Chrome for desktop',
    },
    'shipped_android_milestone': {
        'type': 'input',
        'label': 'Chrome for Android',
    },
    'shipped_ios_milestone': {
        'type': 'input',
        'label': 'Chrome for iOS (RARE)',
    },
    'shipped_webview_milestone': {
        'type': 'input',
        'label': 'Android Webview',
    },
    'requires_embedder_support': {
        'type': 'checkbox',
        'label': 'Requires embedder support',
    },
    'devtrial_instructions': {
        'type': 'input',
        'label': 'DevTrial instructions',
    },
    'dt_milestone_desktop_start': {
        'type': 'input',
        'label': 'DevTrial on desktop',
    },
    'dt_milestone_android_start': {
        'type': 'input',
        'label': 'DevTrial on Android',
    },
    'dt_milestone_ios_start': {
        'type': 'input',
        'label': 'DevTrial on iOS (RARE)',
    },
    'flag_name': {
        'type': 'input',
        'label': 'Flag name on about://flags',
    },
    'finch_name': {
        'type': 'input',
        'label': 'Finch feature name',
    },
    'non_finch_justification': {
        'type': 'textarea',
        'label': 'Non-finch justification',
    },
    'prefixed': {
        'type': 'checkbox',
        'label': 'Prefixed?',
    },
    'display_name': {
        'type': 'input',
        'label': 'Stage display name',
    },
    'shipping_year': {
        'type': 'input',
        'label': 'Estimated shipping year',
    },
    'enterprise_policies': {
        'type': 'input',
        'label': 'Enterprise policies',
    },
    'enterprise_feature_categories': {
        'type': 'multiselect',
        'label': 'Enterprise feature categories',
    },
    'enterprise_impact': {
        'type': 'select',
        'label': 'Enterprise impact / risk',
    },
    'rollout_milestone': {
        'type': 'input',
        'label': 'Chrome milestone',
    },
    'rollout_platforms': {
        'type': 'multiselect',
        'label': 'Rollout platforms',
    },
    'rollout_details': {
        'type': 'textarea',
        'label': 'Rollout details (optional)',
    },
    'rollout_stage_plan': {
        'type': 'select',
        'label': 'Rollout plan',
    },
    'confidential': {
        'type': 'checkbox',
        'label': 'Confidential',
    },
}
