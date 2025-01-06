import {html, TemplateResult} from 'lit';
import {Feature, StageDict} from '../js-src/cs-client';
import * as enums from './form-field-enums';

export interface FormattedFeature {
  category: number;
  enterprise_feature_categories: string[];
  enterprise_product_category: number;
  feature_type: number;
  intent_stage: number;
  accurate_as_of: boolean;
  spec_link?: string;
  standard_maturity: number;
  tag_review_status?: number;
  security_review_status?: number;
  privacy_review_status?: number;
  sample_links: string[];
  doc_links: string[];
  search_tags: string[];
  blink_components?: string;
  bug_url?: string;
  devrel?: string[];
  owner?: string[];
  prefixed?: boolean;
  impl_status_chrome?: string;
  shipped_milestone?: number;
  shipped_android_milestone?: number;
  shipped_webview_milestone?: number;
  shipped_ios_milestone?: number;
  ff_views?: number;
  ff_views_link?: string;
  ff_views_notes?: string;
  safari_views?: number;
  safari_views_link?: string;
  safari_views_notes?: string;
  web_dev_views?: number;
  web_dev_views_link?: string;
  web_dev_views_notes?: string;
  other_views_notes?: string;
  stages: StageDict[];
  [key: string]: any; // Allow additional properties
}

interface Section {
  name?: string;
  fields: string[];
  isImplementationSection?: boolean;
  implStatusValue?: number | null;
}

export interface MetadataFields {
  name: string;
  sections: Section[];
}

const COMMA_SEPARATED_FIELDS = [
  'owner',
  'editors',
  'cc_recipients',
  'spec_mentors',
  'search_tags',
  'devrel',
  'i2e_lgtms',
  'i2s_lgtms',
];

const LINE_SEPARATED_FIELDS = [
  'explainer_links',
  'doc_links',
  'sample_links',
  'screenshot_links',
];

/* Convert the format of feature object fetched from API into those for edit.
 * The feature object from API is formatted by the feature_to_legacy_json
 * function in internals/feature_helpers.py
 */
export function formatFeatureForEdit(feature: Feature): FormattedFeature {
  const formattedFeature: FormattedFeature = {
    ...feature,
    category: feature.category_int,
    enterprise_feature_categories: Array.from(
      new Set(feature.enterprise_feature_categories || [])
    ).map(x => parseInt(x).toString()),
    enterprise_product_category: feature.enterprise_product_category,
    feature_type: feature.feature_type_int,
    intent_stage: feature.intent_stage_int,

    // accurate_as_of field should always be checked, regardless of
    // the current value. This is only necessary if the feature
    // has been created before this field was added.
    accurate_as_of: true,

    // from feature.standards
    spec_link: feature.standards.spec,
    standard_maturity: feature.standards.maturity.val,

    tag_review_status: feature.tag_review_status_int,
    security_review_status: feature.security_review_status_int,
    privacy_review_status: feature.privacy_review_status_int,

    // from feature.resources
    sample_links: feature.resources.samples,
    doc_links: feature.resources.docs,

    search_tags: feature.tags,

    // from feature.browsers.chrome
    blink_components: feature.browsers.chrome.blink_components?.[0],

    bug_url: feature.browsers.chrome.bug,
    devrel: feature.browsers.chrome.devrel,
    owner: feature.browsers.chrome.owners,
    prefixed: feature.browsers.chrome.prefixed,
    impl_status_chrome: feature.browsers.chrome.status.val,
    shipped_milestone: feature.browsers.chrome.desktop,
    shipped_android_milestone: feature.browsers.chrome.android,
    shipped_webview_milestone: feature.browsers.chrome.webview,
    shipped_ios_milestone: feature.browsers.chrome.ios,

    // from feature.browsers.ff
    ff_views: feature.browsers.ff.view?.val,
    ff_views_link: feature.browsers.ff.view?.url,
    ff_views_notes: feature.browsers.ff.view?.notes,

    // from feature.browsers.safari
    safari_views: feature.browsers.safari.view?.val,
    safari_views_link: feature.browsers.safari.view?.url,
    safari_views_notes: feature.browsers.safari.view?.notes,

    // from feature.browsers.webdev
    web_dev_views: feature.browsers.webdev.view?.val,
    web_dev_views_link: feature.browsers.webdev.view?.url,
    web_dev_views_notes: feature.browsers.webdev.view?.notes,

    // from feature.browsers.other
    other_views_notes: feature.browsers.other.view?.notes,
  };

  COMMA_SEPARATED_FIELDS.map(field => {
    if (formattedFeature[field])
      formattedFeature[field] = formattedFeature[field].join(', ');
  });

  LINE_SEPARATED_FIELDS.map(field => {
    if (formattedFeature[field])
      formattedFeature[field] = formattedFeature[field].join('\r\n');
  });

  return formattedFeature;
}

/**
 *
 * The following objects define the list of fields for each guide form.
 *
 * Most stages have flat form definitions, with overriding definitions
 * for stages that display differently than their flat definitions.
 */

// The fields shown to the user when first creating a new feature.
// Note: feature_type is done with custom HTML in chromedash-guide-new-page
export const NEW_FEATURE_FORM_FIELDS = [
  'name',
  'summary',
  'unlisted',
  'enterprise_impact',
  'shipping_year',
  'owner',
  'editors',
  'cc_recipients',
  'blink_components',
  'category',
  'web_feature',
];

export const ENTERPRISE_NEW_FEATURE_FORM_FIELDS = [
  'name',
  'summary',
  'owner',
  'editors',
  'enterprise_feature_categories',
  'enterprise_product_category',
  'first_enterprise_notification_milestone',
  'enterprise_impact',
  'confidential',
];

// The fields that are available to every feature.
export const FLAT_METADATA_FIELDS: MetadataFields = {
  name: 'Feature metadata',
  sections: [
    // Standardizaton
    {
      name: 'Feature metadata',
      fields: [
        'name',
        'summary',
        'unlisted',
        'enterprise_impact',
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
    // Implementation
    {
      name: 'Implementation in Chromium',
      fields: [
        'impl_status_chrome',
        'blink_components',
        'bug_url',
        'launch_bug_url',
        'comments',
      ],
      isImplementationSection: true,
    },
  ],
};

// The fields that are available to every enterprise feature.
export const FLAT_ENTERPRISE_METADATA_FIELDS: MetadataFields = {
  name: 'Feature metadata',
  sections: [
    // Standardizaton
    {
      name: 'Feature metadata',
      fields: [
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
};

// All fields relevant to the incubate/planning stage.
const FLAT_INCUBATE_FIELDS: MetadataFields = {
  name: 'Identify the need',
  sections: [
    // Standardization
    {
      name: 'Identify the need',
      fields: ['motivation', 'initial_public_proposal_url', 'explainer_links'],
    },
    // Implementation
    {
      name: 'Implementation in Chromium',
      fields: ['requires_embedder_support'],
      isImplementationSection: true,
      implStatusValue: null,
    },
  ],
};

// All fields relevant to the implement/prototyping stage.
// TODO(jrobbins): advise user to request a tag review
// TODO(jrobbins): api overview link
const FLAT_PROTOTYPE_FIELDS: MetadataFields = {
  name: 'Prototype a solution',
  sections: [
    // Standardization
    {
      name: 'Prototype a solution',
      fields: [
        'motivation',
        'spec_link',
        'standard_maturity',
        'api_spec',
        'spec_mentors',
        'intent_to_implement_url',
      ],
    },
  ],
};

// All fields relevant to the dev trials stage.
const FLAT_DEV_TRIAL_FIELDS: MetadataFields = {
  name: 'Dev trials and iterate on design',
  sections: [
    // Standardizaton
    {
      name: 'Dev trial',
      fields: [
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
    // Implementation
    {
      name: 'Implementation in Chromium',
      fields: [
        'flag_name',
        'finch_name',
        'non_finch_justification',
        'dt_milestone_desktop_start',
        'dt_milestone_android_start',
        'dt_milestone_ios_start',
        'announcement_url',
      ],
      isImplementationSection: true,
      implStatusValue: enums.IMPLEMENTATION_STATUS.BEHIND_A_FLAG[0],
    },
  ],
};
// TODO(jrobbins): UA support signals section
// TODO(jrobbins): api overview link

// All fields relevant to the origin trial stage.
const FLAT_ORIGIN_TRIAL_FIELDS: MetadataFields = {
  name: 'Origin trial',
  sections: [
    // Standardization
    {
      name: 'Origin trial',
      fields: [
        'display_name',
        'experiment_goals',
        'experiment_risks',
        'ongoing_constraints',
        // TODO(jrobbins): display r4dt_url instead when deprecating.
        'i2e_lgtms',
        'ot_documentation_url',
        'intent_to_experiment_url',
        'origin_trial_feedback_url',
      ],
    },
    // Implementation
    {
      name: 'Implementation in Chromium',
      fields: [
        'ot_milestone_desktop_start',
        'ot_milestone_desktop_end',
        'ot_milestone_android_start',
        'ot_milestone_android_end',
        'ot_milestone_webview_start',
        'ot_milestone_webview_end',
        'experiment_timeline', // deprecated
      ],
      isImplementationSection: true,
      implStatusValue: enums.IMPLEMENTATION_STATUS.ORIGIN_TRIAL[0],
    },
  ],
};

export const FLAT_TRIAL_EXTENSION_FIELDS: MetadataFields = {
  name: 'Trial extension',
  sections: [
    {
      name: 'Trial extension',
      fields: [
        'experiment_extension_reason',
        'intent_to_extend_experiment_url',
        'extension_desktop_last',
      ],
    },
  ],
};

const FLAT_EVAL_READINESS_TO_SHIP_FIELDS: MetadataFields = {
  name: 'Evaluate readiness to ship',
  sections: [
    {
      name: 'Evaluate readiness to ship',
      fields: ['prefixed', 'tag_review'],
    },
  ],
};

// All fields relevant to the prepare to ship stage.
const FLAT_PREPARE_TO_SHIP_FIELDS: MetadataFields = {
  name: 'Prepare to ship',
  sections: [
    {
      name: 'Prepare to ship',
      fields: [
        'display_name',
        // Standardization
        'tag_review_status',
        'webview_risks',
        'anticipated_spec_changes',
        'i2s_lgtms',
        'availability_expectation',
        'adoption_expectation',
        'adoption_plan',
        // Implementation
        'non_oss_deps',

        // Stage-specific fields
        'finch_url',
        'intent_to_ship_url',
      ],
    },
    {
      name: 'Implementation in Chromium',
      fields: [
        'shipped_milestone',
        'shipped_android_milestone',
        'shipped_ios_milestone',
        'shipped_webview_milestone',
      ],
      isImplementationSection: true,
      implStatusValue: enums.IMPLEMENTATION_STATUS.ENABLED_BY_DEFAULT[0],
    },
  ],
};

// All fields relevant to the enterprise prepare to ship stage.
export const FLAT_ENTERPRISE_PREPARE_TO_SHIP_FIELDS: MetadataFields = {
  name: 'Rollout step',
  sections: [
    {
      name: 'Rollout step',
      fields: [
        'rollout_milestone',
        'rollout_platforms',
        'rollout_details',
        'enterprise_policies',
      ],
    },
  ],
};

/**
 * The following definitions override the flat form definitions for
 * specific stage types.
 */

const PSA_IMPLEMENT_FIELDS: MetadataFields = {
  name: 'Start prototyping',
  sections: [
    // Standardization
    {
      name: 'Start prototyping',
      fields: ['motivation', 'spec_link', 'standard_maturity'],
    },
  ],
};

const PSA_PREPARE_TO_SHIP_FIELDS: MetadataFields = {
  name: 'Prepare to ship',
  sections: [
    // Standardization
    {
      name: 'Prepare to ship',
      fields: ['intent_to_ship_url'],
    },
    // Implementation
    {
      name: 'Implementation in Chromium',
      fields: [
        'shipped_milestone',
        'shipped_android_milestone',
        'shipped_ios_milestone',
        'shipped_webview_milestone',
      ],
      isImplementationSection: true,
      implStatusValue: enums.IMPLEMENTATION_STATUS.ENABLED_BY_DEFAULT[0],
    },
  ],
};

const DEPRECATION_PLAN_FIELDS: MetadataFields = {
  name: 'Write up deprecation plan',
  sections: [
    {
      name: 'Write up deprecation plan',
      fields: ['motivation', 'spec_link'],
    },
  ],
};

const DEPRECATION_DEV_TRIAL_FIELDS: MetadataFields = {
  name: 'Dev trial of deprecation',
  sections: [
    // Standardizaton
    {
      name: 'Dev trial of deprecation',
      fields: [
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
    // Implementation
    {
      name: 'Implementation in Chromium',
      fields: [
        'flag_name',
        'finch_name',
        'non_finch_justification',
        'dt_milestone_desktop_start',
        'dt_milestone_android_start',
        'dt_milestone_ios_start',
        'announcement_url',
      ],
      isImplementationSection: true,
      implStatusValue: enums.IMPLEMENTATION_STATUS.BEHIND_A_FLAG[0],
    },
  ],
};

export const ORIGIN_TRIAL_CREATION_FIELDS: MetadataFields = {
  name: 'Origin trial creation',
  sections: [
    {
      fields: [
        'ot_display_name',
        'ot_description',
        'ot_owner_email',
        'ot_emails',
        'ot_creation__milestone_desktop_first',
        'ot_creation__milestone_desktop_last',
        'ot_creation__intent_to_experiment_url',
        'ot_creation__ot_documentation_url',
        'ot_feedback_submission_url',
        'ot_chromium_trial_name',
        'ot_is_deprecation_trial',
        'ot_webfeature_use_counter',
        'ot_has_third_party_support',
        'ot_is_critical_trial',
        'ot_require_approvals',
      ],
    },
  ],
};

export const ORIGIN_TRIAL_EXTENSION_FIELDS: MetadataFields = {
  name: 'Origin trial extension',
  sections: [
    {
      fields: [
        'ot_extension__milestone_desktop_last',
        'experiment_extension_reason',
      ],
    },
  ],
};

// Note: Even though this is similar to another form, it is likely to change.
const DEPRECATION_ORIGIN_TRIAL_FIELDS: MetadataFields = {
  name: 'Prepare for Deprecation Trial',
  sections: [
    {
      name: 'Prepare for Deprecation Trial',
      fields: [
        'display_name',
        'experiment_goals',
        'experiment_risks',
        'ongoing_constraints',
        'r4dt_url', // map to name="intent_to_experiment_url" field upon form submission
        'r4dt_lgtms', // map to name="i2e_lgtms" field upon form submission
        'origin_trial_feedback_url',
      ],
    },
    // Implementation
    {
      name: 'Implementation in Chromium',
      fields: [
        'ot_milestone_desktop_start',
        'ot_milestone_desktop_end',
        'ot_milestone_android_start',
        'ot_milestone_android_end',
        'ot_milestone_webview_start',
        'ot_milestone_webview_end',
        'experiment_timeline', // deprecated
      ],
      isImplementationSection: true,
      implStatusValue: enums.IMPLEMENTATION_STATUS.ORIGIN_TRIAL[0],
    },
  ],
};

// Note: Even though this is similar to another form, it is likely to change.
const DEPRECATION_PREPARE_TO_SHIP_FIELDS: MetadataFields = {
  name: 'Prepare to ship',
  sections: [
    // Standardization
    {
      name: 'Prepare to ship',
      fields: ['display_name', 'intent_to_ship_url', 'i2s_lgtms'],
    },
    // Implementation
    {
      name: 'Implementation in Chromium',
      fields: [
        'shipped_milestone',
        'shipped_android_milestone',
        'shipped_ios_milestone',
        'shipped_webview_milestone',
      ],
      isImplementationSection: true,
      implStatusValue: enums.IMPLEMENTATION_STATUS.ENABLED_BY_DEFAULT[0],
    },
  ],
};

// ****************************
// ** Verify Accuracy fields **
// ****************************
// The fields shown to the user when verifying the accuracy of a feature.
// Only one stage can be used for each definition object, so
// multiple definitions exist for each stage that might be updated.
export const VERIFY_ACCURACY_METADATA_FIELDS: MetadataFields = {
  name: 'Feature Metadata',
  sections: [
    {
      name: 'Feature Metadata',
      fields: [
        'summary',
        'owner',
        'editors',
        'cc_recipients',
        'impl_status_chrome',
      ],
    },
  ],
};

const VERIFY_ACCURACY_DEV_TRIAL_FIELDS: MetadataFields = {
  name: 'Dev trials and iterate on design',
  sections: [
    {
      name: 'Dev trials milestones',
      fields: [
        'dt_milestone_desktop_start',
        'dt_milestone_android_start',
        'dt_milestone_ios_start',
      ],
    },
  ],
};

const VERIFY_ACCURACY_ORIGIN_TRIAL_FIELDS: MetadataFields = {
  name: 'Origin trial',
  sections: [
    {
      name: 'Origin trial milestones',
      fields: [
        'ot_milestone_desktop_start',
        'ot_milestone_desktop_end',
        'ot_milestone_android_start',
        'ot_milestone_android_end',
        'ot_milestone_webview_start',
        'ot_milestone_webview_end',
      ],
    },
  ],
};

export const VERIFY_ACCURACY_TRIAL_EXTENSION_FIELDS: MetadataFields = {
  name: 'Trial extension',
  sections: [
    {
      name: 'Trial extension milestones',
      fields: [
        'extension_android_last',
        'extension_desktop_last',
        'extension_webview_last',
      ],
    },
  ],
};

const VERIFY_ACCURACY_PREPARE_TO_SHIP_FIELDS: MetadataFields = {
  name: 'Prepare to ship',
  sections: [
    {
      name: 'Shipping milestones',
      fields: [
        'shipped_milestone',
        'shipped_android_milestone',
        'shipped_ios_milestone',
        'shipped_webview_milestone',
      ],
    },
  ],
};

const VERIFY_ACCURACY_ENTERPRISE_PREPARE_TO_SHIP_FIELDS: MetadataFields = {
  name: 'Rollout step',
  sections: [
    {
      name: 'Rollout milestones',
      fields: [
        'rollout_milestone',
        'rollout_platforms',
        'rollout_details',
        'enterprise_policies',
      ],
    },
  ],
};

// A single form to display the checkbox for verifying accuracy at the end.
export const VERIFY_ACCURACY_CONFIRMATION_FIELD: MetadataFields = {
  name: 'Verify Accuracy',
  sections: [
    {
      name: 'Verify Accuracy',
      fields: ['accurate_as_of'],
    },
  ],
};

export const FORMS_BY_STAGE_TYPE: Record<number, MetadataFields> = {
  [enums.STAGE_BLINK_INCUBATE]: FLAT_INCUBATE_FIELDS,
  [enums.STAGE_BLINK_PROTOTYPE]: FLAT_PROTOTYPE_FIELDS,
  [enums.STAGE_BLINK_DEV_TRIAL]: FLAT_DEV_TRIAL_FIELDS,
  [enums.STAGE_BLINK_EVAL_READINESS]: FLAT_EVAL_READINESS_TO_SHIP_FIELDS,
  [enums.STAGE_BLINK_ORIGIN_TRIAL]: FLAT_ORIGIN_TRIAL_FIELDS,
  [enums.STAGE_BLINK_EXTEND_ORIGIN_TRIAL]: FLAT_TRIAL_EXTENSION_FIELDS,
  [enums.STAGE_BLINK_SHIPPING]: FLAT_PREPARE_TO_SHIP_FIELDS,

  [enums.STAGE_FAST_PROTOTYPE]: FLAT_PROTOTYPE_FIELDS,
  [enums.STAGE_FAST_DEV_TRIAL]: FLAT_DEV_TRIAL_FIELDS,
  [enums.STAGE_FAST_ORIGIN_TRIAL]: FLAT_ORIGIN_TRIAL_FIELDS,
  [enums.STAGE_FAST_EXTEND_ORIGIN_TRIAL]: FLAT_TRIAL_EXTENSION_FIELDS,
  [enums.STAGE_FAST_SHIPPING]: FLAT_PREPARE_TO_SHIP_FIELDS,

  [enums.STAGE_PSA_IMPLEMENT_FIELDS]: PSA_IMPLEMENT_FIELDS,
  [enums.STAGE_PSA_DEV_TRIAL]: FLAT_DEV_TRIAL_FIELDS,
  [enums.STAGE_PSA_SHIPPING]: PSA_PREPARE_TO_SHIP_FIELDS,

  [enums.STAGE_DEP_PLAN]: DEPRECATION_PLAN_FIELDS,
  [enums.STAGE_DEP_DEV_TRIAL]: DEPRECATION_DEV_TRIAL_FIELDS,
  [enums.STAGE_DEP_DEPRECATION_TRIAL]: DEPRECATION_ORIGIN_TRIAL_FIELDS,
  [enums.STAGE_DEP_EXTEND_DEPRECATION_TRIAL]: FLAT_TRIAL_EXTENSION_FIELDS,
  [enums.STAGE_DEP_SHIPPING]: DEPRECATION_PREPARE_TO_SHIP_FIELDS,

  [enums.STAGE_ENT_ROLLOUT]: FLAT_ENTERPRISE_PREPARE_TO_SHIP_FIELDS,
  [enums.STAGE_ENT_SHIPPED]: FLAT_PREPARE_TO_SHIP_FIELDS,
};

export const CREATEABLE_STAGES: Record<number, number[]> = {
  [enums.FEATURE_TYPES.FEATURE_TYPE_INCUBATE_ID[0]]: [
    enums.STAGE_BLINK_ORIGIN_TRIAL,
    enums.STAGE_BLINK_SHIPPING,
    enums.STAGE_ENT_ROLLOUT,
  ],
  [enums.FEATURE_TYPES.FEATURE_TYPE_EXISTING_ID[0]]: [
    enums.STAGE_FAST_ORIGIN_TRIAL,
    enums.STAGE_FAST_SHIPPING,
    enums.STAGE_ENT_ROLLOUT,
  ],
  [enums.FEATURE_TYPES.FEATURE_TYPE_CODE_CHANGE_ID[0]]: [
    enums.STAGE_PSA_SHIPPING,
    enums.STAGE_ENT_ROLLOUT,
  ],
  [enums.FEATURE_TYPES.FEATURE_TYPE_DEPRECATION_ID[0]]: [
    enums.STAGE_DEP_DEPRECATION_TRIAL,
    enums.STAGE_DEP_SHIPPING,
    enums.STAGE_ENT_ROLLOUT,
  ],
  [enums.FEATURE_TYPES.FEATURE_TYPE_ENTERPRISE_ID[0]]: [
    enums.STAGE_ENT_ROLLOUT,
  ],
};

export const VERIFY_ACCURACY_FORMS_BY_STAGE_TYPE: Record<
  number,
  MetadataFields
> = {
  [enums.STAGE_BLINK_DEV_TRIAL]: VERIFY_ACCURACY_DEV_TRIAL_FIELDS,
  [enums.STAGE_BLINK_ORIGIN_TRIAL]: VERIFY_ACCURACY_ORIGIN_TRIAL_FIELDS,
  [enums.STAGE_BLINK_SHIPPING]: VERIFY_ACCURACY_PREPARE_TO_SHIP_FIELDS,

  [enums.STAGE_FAST_DEV_TRIAL]: VERIFY_ACCURACY_DEV_TRIAL_FIELDS,
  [enums.STAGE_FAST_ORIGIN_TRIAL]: VERIFY_ACCURACY_ORIGIN_TRIAL_FIELDS,
  [enums.STAGE_FAST_SHIPPING]: VERIFY_ACCURACY_PREPARE_TO_SHIP_FIELDS,

  [enums.STAGE_PSA_DEV_TRIAL]: VERIFY_ACCURACY_DEV_TRIAL_FIELDS,
  [enums.STAGE_PSA_SHIPPING]: VERIFY_ACCURACY_PREPARE_TO_SHIP_FIELDS,

  [enums.STAGE_DEP_DEV_TRIAL]: VERIFY_ACCURACY_DEV_TRIAL_FIELDS,
  [enums.STAGE_DEP_DEPRECATION_TRIAL]: VERIFY_ACCURACY_ORIGIN_TRIAL_FIELDS,
  [enums.STAGE_DEP_SHIPPING]: VERIFY_ACCURACY_PREPARE_TO_SHIP_FIELDS,

  [enums.STAGE_ENT_ROLLOUT]: VERIFY_ACCURACY_ENTERPRISE_PREPARE_TO_SHIP_FIELDS,
  [enums.STAGE_ENT_SHIPPED]: VERIFY_ACCURACY_PREPARE_TO_SHIP_FIELDS,
};
