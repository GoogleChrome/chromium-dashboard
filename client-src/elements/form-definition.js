import {html} from 'lit';
import {
  FEATURE_TYPES,
  IMPLEMENTATION_STATUS,
  GATE_TYPES,
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
    enterprise_feature_categories: Array.from(new Set(feature.enterprise_feature_categories || []))
      .map(x => parseInt(x).toString()),
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

export const ENTERPRISE_NEW_FEATURE_FORM_FIELDS = [
  'name',
  'summary',
  'owner',
  'editors',
  'launch_bug_url',
  'enterprise_feature_categories',
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
        'devrel',
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

// The fields that are available to every enterprise feature.
export const FLAT_ENTERPRISE_METADATA_FIELDS = {
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
        'breaking_change',
      ],
    },
    // Implementation
    {
      name: 'Implementation in Chromium',
      fields: [
        'launch_bug_url',
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
        'announcement_url',
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
        'display_name',
        'experiment_goals',
        'experiment_risks',
        'ongoing_constraints',
        // TODO(jrobbins): display r4dt_url instead when deprecating.
        'i2e_lgtms',
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
      implStatusValue: IMPLEMENTATION_STATUS.ORIGIN_TRIAL[0],
    },
  ],
};

export const FLAT_TRIAL_EXTENSION_FIELDS = {
  name: 'Trial extension',
  sections: [
    {
      name: 'Trial extension',
      fields: [
        'experiment_extension_reason',
        'intent_to_extend_experiment_url',
        'extension_desktop_last',
        'extension_android_last',
        'extension_webview_last',
      ],
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
        'rollout_impact',
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

const DEPRECATION_PLAN_FIELDS = {
  name: 'Write up motivation',
  sections: [
    {
      name: 'Write up motivation',
      fields: [
        'motivation',
        'spec_link',
      ],
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
        'announcement_url',
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
        'display_name',
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

// ****************************
// ** Verify Accuracy fields **
// ****************************
// The fields shown to the user when verifying the accuracy of a feature.
// Only one stage can be used for each definition object, so
// multiple definitions exist for each stage that might be updated.
export const VERIFY_ACCURACY_METADATA_FIELDS = {
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

const VERIFY_ACCURACY_DEV_TRIAL_FIELDS = {
  name: 'Dev trials and iterate on design',
  sections: [
    {
      name: 'Dev trials milestones',
      fields: [
        'dt_milestone_android_start',
        'dt_milestone_desktop_start',
        'dt_milestone_ios_start',
      ],
    },
  ],
};

const VERIFY_ACCURACY_ORIGIN_TRIAL_FIELDS = {
  name: 'Origin trial',
  sections: [
    {
      name: 'Origin trial milestones',
      fields: [
        'ot_milestone_android_start',
        'ot_milestone_android_end',
        'ot_milestone_desktop_start',
        'ot_milestone_desktop_end',
        'ot_milestone_webview_start',
        'ot_milestone_webview_end',
      ],
    },
  ],
};

export const VERIFY_ACCURACY_TRIAL_EXTENSION_FIELDS = {
  name: 'Trial extension',
  sections: [
    {
      name: 'Trial extension milestones',
      fields: [
        'extension_desktop_last',
        'extension_android_last',
        'extension_webview_last',
      ],
    },
  ],
};

const VERIFY_ACCURACY_PREPARE_TO_SHIP_FIELDS = {
  name: 'Prepare to ship',
  sections: [
    {
      name: 'Shipping milestones',
      fields: [
        'shipped_android_milestone',
        'shipped_ios_milestone',
        'shipped_milestone',
        'shipped_webview_milestone',
      ],
    },
  ],
};

// A single form to display the checkbox for verifying accuracy at the end.
export const VERIFY_ACCURACY_CONFIRMATION_FIELD = {
  name: 'Verify Accuracy',
  sections: [
    {
      name: 'Verify Accuracy',
      fields: [
        'accurate_as_of',
      ],
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
const STAGE_BLINK_EXTEND_ORIGIN_TRIAL = 151;
const STAGE_BLINK_SHIPPING = 160;
// Note: We might define post-ship support stage(s) later.

// For implementing existing standards: the "fast track" process.
const STAGE_FAST_PROTOTYPE = 220;
const STAGE_FAST_DEV_TRIAL = 230;
const STAGE_FAST_ORIGIN_TRIAL = 250;
const STAGE_FAST_EXTEND_ORIGIN_TRIAL = 251;
const STAGE_FAST_SHIPPING = 260;

// For developer-facing code changes not impacting a standard: the "PSA" process.
const STAGE_PSA_IMPLEMENT_FIELDS = 320;
const STAGE_PSA_DEV_TRIAL = 330;
const STAGE_PSA_SHIPPING = 360;

// For deprecating a feature: the "DEP" process.
const STAGE_DEP_PLAN = 410;
const STAGE_DEP_DEV_TRIAL = 430;
const STAGE_DEP_DEPRECATION_TRIAL = 450;
const STAGE_DEP_EXTEND_DEPRECATION_TRIAL = 451;
const STAGE_DEP_SHIPPING = 460;
// const STAGE_DEP_REMOVE_CODE = 470;

// Note STAGE_* enum values 500-999 are reseverd for future WP processes.

// Define enterprise feature processes.
// Note: This stage can ge added to any feature that is following any process.
export const STAGE_ENT_ROLLOUT = 1061;
const STAGE_ENT_SHIPPED = 1070;

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

  [STAGE_DEP_PLAN]: DEPRECATION_PLAN_FIELDS,
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
  ],
};

export const STAGE_TYPES_ORIGIN_TRIAL = new Set([
  STAGE_BLINK_ORIGIN_TRIAL,
  STAGE_FAST_ORIGIN_TRIAL,
  STAGE_DEP_DEPRECATION_TRIAL,
]);

export const VERIFY_ACCURACY_FORMS_BY_STAGE_TYPE = {
  [STAGE_BLINK_DEV_TRIAL]: VERIFY_ACCURACY_DEV_TRIAL_FIELDS,
  [STAGE_BLINK_ORIGIN_TRIAL]: VERIFY_ACCURACY_ORIGIN_TRIAL_FIELDS,
  [STAGE_BLINK_SHIPPING]: VERIFY_ACCURACY_PREPARE_TO_SHIP_FIELDS,

  [STAGE_FAST_DEV_TRIAL]: VERIFY_ACCURACY_DEV_TRIAL_FIELDS,
  [STAGE_FAST_ORIGIN_TRIAL]: VERIFY_ACCURACY_ORIGIN_TRIAL_FIELDS,
  [STAGE_FAST_SHIPPING]: VERIFY_ACCURACY_PREPARE_TO_SHIP_FIELDS,

  [STAGE_PSA_DEV_TRIAL]: VERIFY_ACCURACY_DEV_TRIAL_FIELDS,
  [STAGE_PSA_SHIPPING]: VERIFY_ACCURACY_PREPARE_TO_SHIP_FIELDS,

  [STAGE_DEP_DEV_TRIAL]: VERIFY_ACCURACY_DEV_TRIAL_FIELDS,
  [STAGE_DEP_DEPRECATION_TRIAL]: VERIFY_ACCURACY_ORIGIN_TRIAL_FIELDS,
  [STAGE_DEP_SHIPPING]: VERIFY_ACCURACY_PREPARE_TO_SHIP_FIELDS,

  [STAGE_ENT_SHIPPED]: VERIFY_ACCURACY_PREPARE_TO_SHIP_FIELDS,
};

// key: Origin trial stage types,
// value: extension stage type associated with the origin trial type.
export const OT_EXTENSION_STAGE_MAPPING = {
  [STAGE_BLINK_ORIGIN_TRIAL]: STAGE_BLINK_EXTEND_ORIGIN_TRIAL,
  [STAGE_FAST_ORIGIN_TRIAL]: STAGE_FAST_EXTEND_ORIGIN_TRIAL,
  [STAGE_DEP_DEPRECATION_TRIAL]: STAGE_DEP_EXTEND_DEPRECATION_TRIAL,
};


export const STAGE_SHORT_NAMES = {
  [STAGE_BLINK_INCUBATE]: 'Incubate',
  [STAGE_BLINK_PROTOTYPE]: 'Prototype',
  [STAGE_BLINK_DEV_TRIAL]: 'DevTrial',
  [STAGE_BLINK_EVAL_READINESS]: 'Eval readiness',
  [STAGE_BLINK_ORIGIN_TRIAL]: 'OT',
  [STAGE_BLINK_EXTEND_ORIGIN_TRIAL]: 'Extend OT',
  [STAGE_BLINK_SHIPPING]: 'Ship',

  [STAGE_FAST_PROTOTYPE]: 'Prototype',
  [STAGE_FAST_DEV_TRIAL]: 'DevTrial',
  [STAGE_FAST_ORIGIN_TRIAL]: 'OT',
  [STAGE_FAST_EXTEND_ORIGIN_TRIAL]: 'Extend OT',
  [STAGE_FAST_SHIPPING]: 'Ship',

  [STAGE_PSA_IMPLEMENT_FIELDS]: 'Implement',
  [STAGE_PSA_DEV_TRIAL]: 'DevTrial',
  [STAGE_PSA_SHIPPING]: 'Ship',

  [STAGE_DEP_PLAN]: 'Plan',
  [STAGE_DEP_DEV_TRIAL]: 'DevTrial',
  [STAGE_DEP_DEPRECATION_TRIAL]: 'Dep Trial',
  [STAGE_DEP_EXTEND_DEPRECATION_TRIAL]: 'Extend Dep Trial',
  [STAGE_DEP_SHIPPING]: 'Ship',

  [STAGE_ENT_ROLLOUT]: 'Rollout',
  [STAGE_ENT_SHIPPED]: 'Ship',
};


const BLINK_GENERIC_QUESTIONNAIRE = (
  'To request a review, use the "Draft intent..." button ' +
  'above to generate an intent messsage, ' +
  'and then post that message to blink-dev@chromium.org.\n' +
  '\n' +
  'Be sure to update your feature entry in response to ' +
  'any suggestions on that email thread.'
);

const PRIVACY_GENERIC_QUESTIONNAIRE = (
  `To request a review, use the "Request review" button above.`
);

const SECURITY_GENERIC_QUESTIONNAIRE = (
  `To request a review, use the "Request review" button above.`
);

const ENTERPRISE_SHIP_QUESTIONNAIRE = (
  html`<b>(1) Does this launch include a breaking change?</b>
Does this launch remove or modify existing behavior or does it interrupt an existing user flow? (e.g. removing or restricting an API, or significant UI change). Answer with one of the following options, and/or describe anything you're unsure about:
<ul>
<li>No. There's no change visible to users, developers, or IT admins (e.g. internal refactoring)
<li>No. This launch is strictly additive functionality
<li>Yes. Something that exists is changing or being removed (even if usage is very small)
<li>I don't know. Enterprise reviewers, please help me decide. The relevant information is: ______
</ul>
<b>(2) Is there any other reason you expect that enterprises will care about this launch?</b>
(e.g. they may perceive a risk of data leaks if the browser is uploading new information, or it may be a surprise to employees resulting in them calling their help desk). Answer with one of the following options, and/or describe anything you're unsure about:
<ul>
<li>No. Enterprises won't care about this
<li>Yes. They'll probably care because ______
<li>I don't know. Enterprise reviewers, please help me decide. The relevant information is: ______
</ul>
<b>(3) Does your launch have an enterprise policy to control it, and will it be available when this rolls out to stable (even to 1%)?</b>
Only required if you answered Yes to either of the first 2 questions. Answer with one of the following options, and/or describe anything you're unsure about:
<ul>
<li>Yes. It's called ______. It will be a permanent policy, and it will be available when stable rollout starts
<li>Yes. It's called ______. This is a temporary transition period, so the policy will stop working on milestone ___. It will be available when stable rollout starts
<li>No. A policy is infeasible because ______ (e.g. this launch is a change in how we compile Chrome)
<li>No. A policy isn't necessary because ______ (e.g. there's a better method of control available to admins)
</ul>
<b>(4) Provide a brief title and description of this launch, which can be shared with enterprises.</b>
Only required if you answered Yes to either of the first 2 questions. This may be added to browser release notes. Where applicable, explain the benefit to users, and describe the policy to control it.
`
);

const DEBUGGABILITY_ORIGIN_TRIAL_QUESTIONNAIRE = (
    `(1) Does the introduction of the new Web Platform feature break Chrome DevTools' existing developer experience?

(2) Does Chrome DevTools' existing set of tooling features interact with the new Web Platform feature in an expected way?

(3) Would the new Web Platform feature's acceptance and/or adoption benefit from adding a new developer workflow to Chrome DevTools?

When in doubt, please check out https://goo.gle/devtools-checklist for details!
`
);

const DEBUGGABILITY_SHIP_QUESTIONNAIRE = DEBUGGABILITY_ORIGIN_TRIAL_QUESTIONNAIRE;

const TESTING_SHIP_QUESTIONNAIRE = (
  'See http://go/chrome-wp-test-survey.'
);


export const GATE_QUESTIONNAIRES = {
  [GATE_TYPES.API_PROTOTYPE]: BLINK_GENERIC_QUESTIONNAIRE,
  [GATE_TYPES.API_ORIGIN_TRIAL]: BLINK_GENERIC_QUESTIONNAIRE,
  [GATE_TYPES.API_EXTEND_ORIGIN_TRIAL]: BLINK_GENERIC_QUESTIONNAIRE,
  [GATE_TYPES.API_SHIP]: BLINK_GENERIC_QUESTIONNAIRE,
  [GATE_TYPES.PRIVACY_ORIGIN_TRIAL]: PRIVACY_GENERIC_QUESTIONNAIRE,
  [GATE_TYPES.PRIVACY_SHIP]: PRIVACY_GENERIC_QUESTIONNAIRE,
  [GATE_TYPES.SECURITY_ORIGIN_TRIAL]: SECURITY_GENERIC_QUESTIONNAIRE,
  [GATE_TYPES.SECURITY_SHIP]: SECURITY_GENERIC_QUESTIONNAIRE,
  [GATE_TYPES.ENTERPRISE_SHIP]: ENTERPRISE_SHIP_QUESTIONNAIRE,
  [GATE_TYPES.DEBUGGABILITY_ORIGIN_TRIAL]:
      DEBUGGABILITY_ORIGIN_TRIAL_QUESTIONNAIRE,
  [GATE_TYPES.DEBUGGABILITY_SHIP]: DEBUGGABILITY_SHIP_QUESTIONNAIRE,
  [GATE_TYPES.TESTING_SHIP]: TESTING_SHIP_QUESTIONNAIRE,
};
