import {
  FEATURE_TYPES,
  IMPLEMENTATION_STATUS,
} from './form-field-enums';


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
];

/* Convert the format of feature object fetched from API into those for edit.
 * The feature object from API is formatted by the feature_to_legacy_json
 * function in internals/feature_helpers.py
 */
export function formatFeatureForEdit(feature) {
  const formattedFeature = {
    ...feature,
    category: feature.category_int,
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
    privacy_review_status: feature.security_review_status_int,

    // from feature.resources
    sample_links: feature.resources.samples,
    doc_links: feature.resources.docs,

    search_tags: feature.tags,

    // from feature.browsers.chrome
    blink_components: feature.browsers.chrome.blink_components[0],
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
    ff_views: feature.browsers.ff.view.val,
    ff_views_link: feature.browsers.ff.view.url,
    ff_views_notes: feature.browsers.ff.view.notes,

    // from feature.browsers.safari
    safari_views: feature.browsers.safari.view.val,
    safari_views_link: feature.browsers.safari.view.url,
    safari_views_notes: feature.browsers.safari.view.notes,

    // from feature.browsers.webdev
    web_dev_views: feature.browsers.webdev.view.val,
    web_dev_views_link: feature.browsers.webdev.view.url,
    web_dev_views_notes: feature.browsers.webdev.view.notes,

    // from feature.browsers.other
    other_views_notes: feature.browsers.other.view.notes,

    rollout_platforms: Array.from(new Set((feature.rollout_platforms || [])
      .map(x => parseInt(x).toString()))),
  };

  COMMA_SEPARATED_FIELDS.map((field) => {
    if (formattedFeature[field]) formattedFeature[field] = formattedFeature[field].join(', ');
  });

  LINE_SEPARATED_FIELDS.map((field) => {
    if (formattedFeature[field]) formattedFeature[field] = formattedFeature[field].join('\r\n');
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
  'breaking_change',
  'owner',
  'editors',
  'cc_recipients',
  'blink_components',
  'category',
];

// The fields shown to the user when verifying the accuracy of a feature.
export const VERIFY_ACCURACY_FORM_FIELDS = [
  'summary',
  'owner',
  'editors',
  'cc_recipients',
  'impl_status_chrome',
  'dt_milestone_android_start',
  'dt_milestone_desktop_start',
  'dt_milestone_ios_start',
  'ot_milestone_android_start',
  'ot_milestone_android_end',
  'ot_milestone_desktop_start',
  'ot_milestone_desktop_end',
  'ot_milestone_webview_start',
  'ot_milestone_webview_end',
  'shipped_android_milestone',
  'shipped_ios_milestone',
  'shipped_milestone',
  'shipped_webview_milestone',
  'accurate_as_of',
];

// The fields that are available to every feature.
export const FLAT_METADATA_FIELDS = {
  name: 'Feature metadata',
  sections: [
    // Standardizaton
    {
      name: 'Feature metadata',
      fields: [
        'name',
        'summary',
        'unlisted',
        'breaking_change',
        'owner',
        'editors',
        'cc_recipients',
        'category',
        'feature_type',
        'search_tags',
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

// All fields relevant to the incubate/planning stage.
const FLAT_INCUBATE_FIELDS = {
  name: 'Identify the need',
  sections: [
    // Standardization
    {
      name: 'Identify the need',
      fields: [
        'motivation',
        'initial_public_proposal_url',
        'explainer_links',
      ],
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
const FLAT_PROTOTYPE_FIELDS = {
  name: 'Prototype a solution',
  sections: [
    // Standardization
    {
      name: 'Prototype a solution',
      fields: [
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
const FLAT_DEV_TRIAL_FIELDS = {
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
        'all_platforms',
        'all_platforms_descr',
        'wpt',
        'wpt_descr',
        'sample_links',
        'devrel',
      ],
    },
    // Implementation
    {
      name: 'Implementation in Chromium',
      fields: [
        'flag_name',
        'dt_milestone_desktop_start',
        'dt_milestone_android_start',
        'dt_milestone_ios_start',
        'ready_for_trial_url',
      ],
      isImplementationSection: true,
      implStatusValue: IMPLEMENTATION_STATUS.BEHIND_A_FLAG[0],
    },
  ],
};
// TODO(jrobbins): UA support signals section
// TODO(jrobbins): api overview link

// All fields relevant to the origin trial stage.
const FLAT_ORIGIN_TRIAL_FIELDS = {
  name: 'Origin trial',
  sections: [
    // Standardization
    {
      name: 'Origin trial',
      fields: [
        'experiment_goals',
        'experiment_risks',
        'ongoing_constraints',
        // TODO(jrobbins): display r4dt_url instead when deprecating.
        'i2e_lgtms',
        'intent_to_experiment_url',
        'origin_trial_feedback_url',

        // Extension stage-specific fields
        'experiment_extension_reason',
        'intent_to_extend_experiment_url',
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
      implStatusValue: IMPLEMENTATION_STATUS.ORIGIN_TRIAL[0],
    },
  ],
};

const FLAT_EVAL_READINESS_TO_SHIP_FIELDS = {
  name: 'Evaluate readiness to ship',
  sections: [
    {
      name: 'Evaluate readiness to ship',
      fields: [
        'prefixed',
        'tag_review',
      ],
    },
  ],
};

// All fields relevant to the prepare to ship stage.
const FLAT_PREPARE_TO_SHIP_FIELDS = {
  name: 'Prepare to ship',
  sections: [
    {
      name: 'Prepare to ship',
      fields: [
        // Standardization
        'tag_review_status',
        'webview_risks',
        'anticipated_spec_changes',
        'i2s_lgtms',
        // Implementation
        'measurement',
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
      implStatusValue: IMPLEMENTATION_STATUS.ENABLED_BY_DEFAULT[0],
    },
  ],
};

// All fields relevant to the enterprise prepare to ship stage.
export const FLAT_ENTERPRISE_PREPARE_TO_SHIP_FIELDS = {
  name: 'Start feature rollout',
  sections: [
    {
      name: 'Start feature rollout',
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


const PSA_IMPLEMENT_FIELDS = {
  name: 'Start prototyping',
  sections: [
    // Standardization
    {
      name: 'Start prototyping',
      fields: [
        'spec_link',
        'standard_maturity',
      ],
    },
  ],
};

const PSA_PREPARE_TO_SHIP_FIELDS = {
  name: 'Prepare to ship',
  sections: [
    // Standardization
    {
      name: 'Prepare to ship',
      fields: [
        'intent_to_ship_url',
      ],
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
      implStatusValue: IMPLEMENTATION_STATUS.ENABLED_BY_DEFAULT[0],
    },
  ],
};

const DEPRECATION_DEV_TRIAL_FIELDS = {
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
        'debuggability',
        'all_platforms',
        'all_platforms_descr',
        'wpt',
        'wpt_descr',
        'sample_links',
        'devrel',
      ],
    },
    // Implementation
    {
      name: 'Implementation in Chromium',
      fields: [
        'flag_name',
        'dt_milestone_desktop_start',
        'dt_milestone_android_start',
        'dt_milestone_ios_start',
        'ready_for_trial_url',
      ],
      isImplementationSection: true,
      implStatusValue: IMPLEMENTATION_STATUS.BEHIND_A_FLAG[0],
    },
  ],
};

// Note: Even though this is similar to another form, it is likely to change.
const DEPRECATION_ORIGIN_TRIAL_FIELDS = {
  name: 'Origin trial',
  sections: [
    {
      name: 'Origin trial',
      fields: [
        'experiment_goals',
        'experiment_risks',
        'experiment_extension_reason',
        'ongoing_constraints',
        'r4dt_url', // map to name="intent_to_experiment_url" field upon form submission
        'intent_to_extend_experiment_url',
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
      implStatusValue: IMPLEMENTATION_STATUS.ORIGIN_TRIAL[0],
    },
  ],
};

// Note: Even though this is similar to another form, it is likely to change.
const DEPRECATION_PREPARE_TO_SHIP_FIELDS = {
  name: 'Prepare to ship',
  sections: [
    // Standardization
    {
      name: 'Prepare to ship',
      fields: [
        'intent_to_ship_url',
        'i2s_lgtms',
      ],
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
      implStatusValue: IMPLEMENTATION_STATUS.ENABLED_BY_DEFAULT[0],
    },
  ],
};


// Stage_type values for each process.  Even though some of the stages
// in these processes are similar to each other, they have distinct enum
// values so that they can have different gates.

// For incubating new standard features: the "blink" process.
const STAGE_BLINK_INCUBATE = 110;
const STAGE_BLINK_PROTOTYPE = 120;
const STAGE_BLINK_DEV_TRIAL = 130;
const STAGE_BLINK_EVAL_READINESS = 140;
const STAGE_BLINK_ORIGIN_TRIAL = 150;
// const STAGE_BLINK_EXTEND_ORIGIN_TRIAL = 151;
const STAGE_BLINK_SHIPPING = 160;
// Note: We might define post-ship support stage(s) later.

// For implementing existing standards: the "fast track" process.
const STAGE_FAST_PROTOTYPE = 220;
const STAGE_FAST_DEV_TRIAL = 230;
const STAGE_FAST_ORIGIN_TRIAL = 250;
// const STAGE_FAST_EXTEND_ORIGIN_TRIAL = 251;
const STAGE_FAST_SHIPPING = 260;

// For developer-facing code changes not impacting a standard: the "PSA" process.
const STAGE_PSA_IMPLEMENT_FIELDS = 320;
const STAGE_PSA_DEV_TRIAL = 330;
const STAGE_PSA_SHIPPING = 360;

// For deprecating a feature: the "DEP" process.
// const STAGE_DEP_PLAN = 410;
const STAGE_DEP_DEV_TRIAL = 430;
const STAGE_DEP_DEPRECATION_TRIAL = 450;
// const STAGE_DEP_EXTEND_DEPRECATION_TRIAL = 451;
const STAGE_DEP_SHIPPING = 460;
// const STAGE_DEP_REMOVE_CODE = 470;

// Note STAGE_* enum values 500-999 are reseverd for future WP processes.

// Define enterprise feature processes.
// Note: This stage can ge added to any feature that is following any process.
const STAGE_ENT_ROLLOUT = 1061;
const STAGE_ENT_SHIPPED = 1070;

// TODO(danielrsmith): Differentiate origin trial and trial extension fields.
export const FORMS_BY_STAGE_TYPE = {
  [STAGE_BLINK_INCUBATE]: FLAT_INCUBATE_FIELDS,
  [STAGE_BLINK_PROTOTYPE]: FLAT_PROTOTYPE_FIELDS,
  [STAGE_BLINK_DEV_TRIAL]: FLAT_DEV_TRIAL_FIELDS,
  [STAGE_BLINK_EVAL_READINESS]: FLAT_EVAL_READINESS_TO_SHIP_FIELDS,
  [STAGE_BLINK_ORIGIN_TRIAL]: FLAT_ORIGIN_TRIAL_FIELDS,
  [STAGE_BLINK_SHIPPING]: FLAT_PREPARE_TO_SHIP_FIELDS,

  [STAGE_FAST_PROTOTYPE]: FLAT_PROTOTYPE_FIELDS,
  [STAGE_FAST_DEV_TRIAL]: FLAT_DEV_TRIAL_FIELDS,
  [STAGE_FAST_ORIGIN_TRIAL]: FLAT_ORIGIN_TRIAL_FIELDS,
  [STAGE_FAST_SHIPPING]: FLAT_PREPARE_TO_SHIP_FIELDS,

  [STAGE_PSA_IMPLEMENT_FIELDS]: PSA_IMPLEMENT_FIELDS,
  [STAGE_PSA_DEV_TRIAL]: FLAT_DEV_TRIAL_FIELDS,
  [STAGE_PSA_SHIPPING]: PSA_PREPARE_TO_SHIP_FIELDS,

  [STAGE_DEP_DEV_TRIAL]: DEPRECATION_DEV_TRIAL_FIELDS,
  [STAGE_DEP_DEPRECATION_TRIAL]: DEPRECATION_ORIGIN_TRIAL_FIELDS,
  [STAGE_DEP_SHIPPING]: DEPRECATION_PREPARE_TO_SHIP_FIELDS,

  [STAGE_ENT_ROLLOUT]: FLAT_ENTERPRISE_PREPARE_TO_SHIP_FIELDS,
  [STAGE_ENT_SHIPPED]: FLAT_PREPARE_TO_SHIP_FIELDS,
};

export const CREATEABLE_STAGES = {
  [FEATURE_TYPES.FEATURE_TYPE_INCUBATE_ID[0]]: [
    STAGE_BLINK_ORIGIN_TRIAL,
    STAGE_BLINK_SHIPPING,
    STAGE_ENT_ROLLOUT,
  ],
  [FEATURE_TYPES.FEATURE_TYPE_EXISTING_ID[0]]: [
    STAGE_FAST_ORIGIN_TRIAL,
    STAGE_FAST_SHIPPING,
    STAGE_ENT_ROLLOUT,
  ],
  [FEATURE_TYPES.FEATURE_TYPE_CODE_CHANGE_ID[0]]: [
    STAGE_PSA_SHIPPING,
    STAGE_ENT_ROLLOUT,
  ],
  [FEATURE_TYPES.FEATURE_TYPE_DEPRECATION_ID[0]]: [
    STAGE_DEP_DEPRECATION_TRIAL,
    STAGE_DEP_SHIPPING,
    STAGE_ENT_ROLLOUT,
  ],
  [FEATURE_TYPES.FEATURE_TYPE_ENTERPRISE_ID[0]]: [
    STAGE_ENT_ROLLOUT,
    STAGE_ENT_SHIPPED,
  ],
};
