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

"""Form definitions copied from client-side code.

Includes the list of fields for each guide form stage.
"""

import copy
from typing import NotRequired, TypedDict

from internals import core_enums


class Section(TypedDict):
    """Represents a section in a form definition."""

    name: NotRequired[str]
    fields: list[str]


class FormDef(TypedDict):
    """Represents a form definition with a name and a list of sections."""

    name: str
    sections: list[Section]


# TODO(jrobbins): Consider loading and parsing a shared JSON file
# to avoid code duplication.  See comments on PR #6626.

# The fields relevant to the incubate/planning stage.
FLAT_INCUBATE_FIELDS: FormDef = {
    'name': 'Identify the need',
    'sections': [
        # Standardization
        {
            'name': 'Identify the need',
            'fields': [
                'motivation',
                'initial_public_proposal_url',
                'explainer_links',
            ],
        },
        # Implementation
        {
            'name': 'Implementation in Chromium',
            'fields': ['requires_embedder_support'],
        },
    ],
}

# The fields relevant to the implement/prototyping stage.
FLAT_PROTOTYPE_FIELDS: FormDef = {
    'name': 'Prototype a solution',
    'sections': [
        # Standardization
        {
            'name': 'Prototype a solution',
            'fields': [
                'motivation',
                'explainer_links',
                'spec_link',
                'standard_maturity',
                'api_spec',
                'automation_spec',
                'spec_mentors',
                'intent_to_implement_url',
            ],
        },
    ],
}

# All fields relevant to the dev trials stage.
FLAT_DEV_TRIAL_FIELDS: FormDef = {
    'name': 'Dev trials and iterate on design',
    'sections': [
        # Standardization
        {
            'name': 'Dev trial',
            'fields': [
                'devtrial_instructions',
                'doc_links',
                'interop_compat_risks',
                'safari_views',
                'safari_views_link',
                'safari_views_notes',
                'ff_views',
                'ff_views_link',
                'ff_views_notes',
                'web_dev_views',
                'web_dev_views_link',
                'web_dev_views_notes',
                'other_views_notes',
                'security_review_status',
                'privacy_review_status',
                'ergonomics_risks',
                'activation_risks',
                'security_risks',
                'debuggability',
                'measurement',
                'all_platforms',
                'all_platforms_descr',
                'wpt',
                'wpt_descr',
                'sample_links',
            ],
        },
        # Implementation
        {
            'name': 'Implementation in Chromium',
            'fields': [
                'flag_name',
                'finch_name',
                'non_finch_justification',
                'dt_milestone_desktop_start',
                'dt_milestone_android_start',
                'dt_milestone_ios_start',
                'announcement_url',
            ],
        },
    ],
}

FAST_DEV_TRIAL_FIELDS: FormDef = copy.deepcopy(FLAT_DEV_TRIAL_FIELDS)
FAST_DEV_TRIAL_FIELDS['sections'][0]['fields'].append('tag_review')

# All fields relevant to the origin trial stage.
FLAT_ORIGIN_TRIAL_FIELDS: FormDef = {
    'name': 'Origin trial',
    'sections': [
        # Standardization
        {
            'name': 'Origin trial',
            'fields': [
                'display_name',
                'experiment_goals',
                'experiment_risks',
                'ongoing_constraints',
                'i2e_lgtms',
                'ot_documentation_url',
                'intent_to_experiment_url',
                'origin_trial_feedback_url',
            ],
        },
        # Implementation
        {
            'name': 'Implementation in Chromium',
            'fields': [
                'ot_milestone_desktop_start',
                'ot_milestone_desktop_end',
                'ot_milestone_android_start',
                'ot_milestone_android_end',
                'ot_milestone_webview_start',
                'ot_milestone_webview_end',
                'experiment_timeline',  # deprecated
            ],
        },
    ],
}

FLAT_TRIAL_EXTENSION_FIELDS: FormDef = {
    'name': 'Trial extension',
    'sections': [
        {
            'name': 'Trial extension',
            'fields': [
                'experiment_extension_reason',
                'intent_to_extend_experiment_url',
                'extension_desktop_last',
            ],
        },
    ],
}

FLAT_EVAL_READINESS_TO_SHIP_FIELDS: FormDef = {
    'name': 'Evaluate readiness to ship',
    'sections': [
        {
            'name': 'Evaluate readiness to ship',
            'fields': ['prefixed', 'tag_review'],
        },
    ],
}

# All fields relevant to the prepare to ship stage.
FLAT_PREPARE_TO_SHIP_FIELDS: FormDef = {
    'name': 'Prepare to ship',
    'sections': [
        {
            'name': 'Prepare to ship',
            'fields': [
                'display_name',
                # Standardization
                'tag_review_status',
                'webview_risks',
                'anticipated_spec_changes',
                'i2s_lgtms',
                'availability_expectation',
                'adoption_expectation',
                'adoption_plan',
                # Implementation
                'non_oss_deps',
                # Stage-specific fields
                'finch_url',
                'intent_to_ship_url',
            ],
        },
        {
            'name': 'Implementation in Chromium',
            'fields': [
                'rollout_plan',
                'shipped_milestone',
                'shipped_android_milestone',
                'shipped_ios_milestone',
                'shipped_webview_milestone',
            ],
        },
    ],
}

# All fields relevant to the enterprise prepare to ship stage.
FLAT_ENTERPRISE_PREPARE_TO_SHIP_FIELDS: FormDef = {
    'name': 'Rollout step',
    'sections': [
        {
            'name': 'Rollout step',
            'fields': [
                'rollout_milestone',
                'rollout_platforms',
                'rollout_details',
                'rollout_stage_plan',
                'enterprise_policies',
            ],
        },
    ],
}

PSA_IMPLEMENT_FIELDS: FormDef = {
    'name': 'Start prototyping',
    'sections': [
        # Standardization
        {
            'name': 'Start prototyping',
            'fields': [
                'motivation',
                'explainer_links',
                'spec_link',
                'standard_maturity',
            ],
        },
    ],
}

PSA_PREPARE_TO_SHIP_FIELDS: FormDef = {
    'name': 'Prepare to ship',
    'sections': [
        # Standardization
        {
            'name': 'Prepare to ship',
            'fields': ['intent_to_ship_url'],
        },
        # Implementation
        {
            'name': 'Implementation in Chromium',
            'fields': [
                'rollout_plan',
                'shipped_milestone',
                'shipped_android_milestone',
                'shipped_ios_milestone',
                'shipped_webview_milestone',
            ],
        },
    ],
}

DEPRECATION_PLAN_FIELDS: FormDef = {
    'name': 'Write up deprecation plan',
    'sections': [
        {
            'name': 'Write up deprecation plan',
            'fields': [
                'deprecation_motivation',
                'explainer_links',
                'spec_link',
                'intent_to_deprecate_url',
            ],
        },
    ],
}

DEPRECATION_DEV_TRIAL_FIELDS: FormDef = {
    'name': 'Dev trial of deprecation',
    'sections': [
        # Standardization
        {
            'name': 'Dev trial of deprecation',
            'fields': [
                'devtrial_instructions',
                'doc_links',
                'interop_compat_risks',
                'safari_views',
                'safari_views_link',
                'safari_views_notes',
                'ff_views',
                'ff_views_link',
                'ff_views_notes',
                'web_dev_views',
                'web_dev_views_link',
                'web_dev_views_notes',
                'other_views_notes',
                'security_review_status',
                'privacy_review_status',
                'ergonomics_risks',
                'activation_risks',
                'security_risks',
                'webview_risks',
                'debuggability',
                'measurement',
                'all_platforms',
                'all_platforms_descr',
                'wpt',
                'wpt_descr',
                'sample_links',
            ],
        },
        # Implementation
        {
            'name': 'Implementation in Chromium',
            'fields': [
                'flag_name',
                'finch_name',
                'non_finch_justification',
                'dt_milestone_desktop_start',
                'dt_milestone_android_start',
                'dt_milestone_ios_start',
                'announcement_url',
            ],
        },
    ],
}

DEPRECATION_ORIGIN_TRIAL_FIELDS: FormDef = {
    'name': 'Prepare for Deprecation Trial',
    'sections': [
        {
            'name': 'Prepare for Deprecation Trial',
            'fields': [
                'display_name',
                'experiment_goals',
                'experiment_risks',
                'ongoing_constraints',
                'r4dt_url',  # map to name="intent_to_experiment_url" field upon form submission  # noqa: E501
                'r4dt_lgtms',  # map to name="i2e_lgtms" field upon form submission  # noqa: E501
                'origin_trial_feedback_url',
            ],
        },
        # Implementation
        {
            'name': 'Implementation in Chromium',
            'fields': [
                'ot_milestone_desktop_start',
                'ot_milestone_desktop_end',
                'ot_milestone_android_start',
                'ot_milestone_android_end',
                'ot_milestone_webview_start',
                'ot_milestone_webview_end',
                'experiment_timeline',  # deprecated
            ],
        },
    ],
}

DEPRECATION_PREPARE_TO_SHIP_FIELDS: FormDef = {
    'name': 'Prepare to ship',
    'sections': [
        # Standardization
        {
            'name': 'Prepare to ship',
            'fields': ['display_name', 'intent_to_ship_url', 'i2s_lgtms'],
        },
        # Implementation
        {
            'name': 'Implementation in Chromium',
            'fields': [
                'rollout_plan',
                'shipped_milestone',
                'shipped_android_milestone',
                'shipped_ios_milestone',
                'shipped_webview_milestone',
            ],
        },
    ],
}

# The fields that are available to every feature.
FLAT_METADATA_FIELDS: FormDef = {
    'name': 'Feature metadata',
    'sections': [
        # Standardization
        {
            'name': 'Feature metadata',
            'fields': [
                'name',
                'summary',
                'unlisted',
                'enterprise_impact',
                'enterprise_feature_categories',
                'shipping_year',
                'owner',
                'editors',
                'cc_recipients',
                'devrel',
                'category',
                'feature_type',
                'active_stage_id',
                'search_tags',
                'web_feature',
            ],
        },
        # Implementation
        {
            'name': 'Implementation in Chromium',
            'fields': [
                'blink_components',
                'bug_url',
                'launch_bug_url',
                'comments',
            ],
        },
    ],
}

# The fields that are available to every enterprise feature.
FLAT_ENTERPRISE_METADATA_FIELDS: FormDef = {
    'name': 'Feature metadata',
    'sections': [
        # Standardization
        {
            'name': 'Feature metadata',
            'fields': [
                'name',
                'summary',
                'owner',
                'editors',
                'enterprise_feature_categories',
                'enterprise_product_category',
                'enterprise_impact',
                'confidential',
                'first_enterprise_notification_milestone',
                'screenshot_links',
            ],
        },
    ],
}

FORMS_BY_STAGE_TYPE: dict[int, FormDef] = {
    core_enums.STAGE_BLINK_INCUBATE: FLAT_INCUBATE_FIELDS,
    core_enums.STAGE_BLINK_PROTOTYPE: FLAT_PROTOTYPE_FIELDS,
    core_enums.STAGE_BLINK_DEV_TRIAL: FLAT_DEV_TRIAL_FIELDS,
    core_enums.STAGE_BLINK_EVAL_READINESS: FLAT_EVAL_READINESS_TO_SHIP_FIELDS,
    core_enums.STAGE_BLINK_ORIGIN_TRIAL: FLAT_ORIGIN_TRIAL_FIELDS,
    core_enums.STAGE_BLINK_EXTEND_ORIGIN_TRIAL: FLAT_TRIAL_EXTENSION_FIELDS,
    core_enums.STAGE_BLINK_SHIPPING: FLAT_PREPARE_TO_SHIP_FIELDS,
    core_enums.STAGE_FAST_PROTOTYPE: FLAT_PROTOTYPE_FIELDS,
    core_enums.STAGE_FAST_DEV_TRIAL: FAST_DEV_TRIAL_FIELDS,
    core_enums.STAGE_FAST_ORIGIN_TRIAL: FLAT_ORIGIN_TRIAL_FIELDS,
    core_enums.STAGE_FAST_EXTEND_ORIGIN_TRIAL: FLAT_TRIAL_EXTENSION_FIELDS,
    core_enums.STAGE_FAST_SHIPPING: FLAT_PREPARE_TO_SHIP_FIELDS,
    core_enums.STAGE_PSA_IMPLEMENT: PSA_IMPLEMENT_FIELDS,
    core_enums.STAGE_PSA_DEV_TRIAL: FLAT_DEV_TRIAL_FIELDS,
    core_enums.STAGE_PSA_SHIPPING: PSA_PREPARE_TO_SHIP_FIELDS,
    core_enums.STAGE_DEP_PLAN: DEPRECATION_PLAN_FIELDS,
    core_enums.STAGE_DEP_DEV_TRIAL: DEPRECATION_DEV_TRIAL_FIELDS,
    core_enums.STAGE_DEP_DEPRECATION_TRIAL: DEPRECATION_ORIGIN_TRIAL_FIELDS,
    core_enums.STAGE_DEP_EXTEND_DEPRECATION_TRIAL: FLAT_TRIAL_EXTENSION_FIELDS,
    core_enums.STAGE_DEP_SHIPPING: DEPRECATION_PREPARE_TO_SHIP_FIELDS,
    core_enums.STAGE_ENT_ROLLOUT: FLAT_ENTERPRISE_PREPARE_TO_SHIP_FIELDS,
    core_enums.STAGE_ENT_SHIPPED: FLAT_PREPARE_TO_SHIP_FIELDS,
}
