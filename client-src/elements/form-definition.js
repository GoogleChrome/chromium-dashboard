import {
  FEATURE_TYPES,
  INTENT_STAGES,
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
 * The following arrays define the list of fields for each guide form.
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
      sections: ['requires_embedder_support']
    },
  ],
};

// All fields relevant to the implement/prototyping stage.
const FLAT_IMPLEMENT_FIELDS = {
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
  name: 'Dev trial',
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
    {
      name: 'Implementation in Chromium',
      fields: [
        'flag_name',
        'dt_milestone_desktop_start',
        'dt_milestone_android_start',
        'dt_milestone_ios_start',
        'ready_for_trial_url',
      ],
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
        'tag_review',
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
    },
  ],
};


// All fields relevant to the enterprise prepare to ship stage.
export const FLAT_ENTERPRISE_PREPARE_TO_SHIP = {
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

// Forms to be used on the "Edit all" page that shows a flat list of fields.
// [[sectionName, flatFormFields]].
export const FLAT_FORMS = [
  ['Feature metadata', FLAT_METADATA_FIELDS],
  ['Identify the need', FLAT_INCUBATE_FIELDS],
  ['Prototype a solution', FLAT_IMPLEMENT_FIELDS],
  ['Dev trial', FLAT_DEV_TRIAL_FIELDS],
  ['Origin trial', FLAT_ORIGIN_TRIAL_FIELDS],
  ['Prepare to ship', FLAT_PREPARE_TO_SHIP_FIELDS],
];


export const FLAT_FORMS_BY_FEATURE_TYPE = {
  [FEATURE_TYPES.FEATURE_TYPE_INCUBATE_ID[0]]: FLAT_FORMS,
  [FEATURE_TYPES.FEATURE_TYPE_EXISTING_ID[0]]: FLAT_FORMS,
  [FEATURE_TYPES.FEATURE_TYPE_CODE_CHANGE_ID[0]]: [
    ['Feature metadata', FLAT_METADATA_FIELDS],
    ['Dev trial', FLAT_DEV_TRIAL_FIELDS],
    ['Prepare to ship', FLAT_PREPARE_TO_SHIP_FIELDS],
  ],
  [FEATURE_TYPES.FEATURE_TYPE_DEPRECATION_ID[0]]: [
    ['Feature metadata', FLAT_METADATA_FIELDS],
    ['Dev trial', FLAT_DEV_TRIAL_FIELDS],
    ['Origin trial', FLAT_ORIGIN_TRIAL_FIELDS],
    ['Prepare to ship', FLAT_PREPARE_TO_SHIP_FIELDS],
  ],
  [FEATURE_TYPES.FEATURE_TYPE_ENTERPRISE_ID[0]]: [
    ['Feature metadata', FLAT_METADATA_FIELDS],
    ['Start feature rollout', FLAT_ENTERPRISE_PREPARE_TO_SHIP],
  ],
};

const NEWFEATURE_INCUBATE = [
  'motivation', 'initial_public_proposal_url', 'explainer_links',
];

const IMPLSTATUS_INCUBATE = ['requires_embedder_support'];

const NEWFEATURE_PROTOTYPE = [
  'spec_link', 'standard_maturity', 'api_spec', 'spec_mentors',
  'intent_to_implement_url',
];
// TODO(jrobbins): advise user to request a tag review

const ANY_DEVTRIAL = [
  'devtrial_instructions', 'doc_links',
  'interop_compat_risks',
  'safari_views', 'safari_views_link', 'safari_views_notes',
  'ff_views', 'ff_views_link', 'ff_views_notes',
  'web_dev_views', 'web_dev_views_link', 'web_dev_views_notes',
  'other_views_notes',
  'security_review_status', 'privacy_review_status',
  'ergonomics_risks', 'activation_risks', 'security_risks', 'debuggability',
  'all_platforms', 'all_platforms_descr', 'wpt', 'wpt_descr',
  'sample_links', 'devrel', 'ready_for_trial_url',
];
// TODO(jrobbins): api overview link

const IMPLSTATUS_DEVTRIAL = [
  'dt_milestone_desktop_start', 'dt_milestone_android_start',
  'dt_milestone_ios_start', 'flag_name',
];

const NEWFEATURE_EVALREADINESSTOSHIP = ['prefixed'];

const IMPLSTATUS_ALLMILESTONES = [
  'shipped_milestone', 'shipped_android_milestone',
  'shipped_ios_milestone', 'shipped_webview_milestone',
];

const IMPLSTATUS_EVALREADINESSTOSHIP = [];

const NEWFEATURE_ORIGINTRIAL = [
  'experiment_goals', 'experiment_risks',
  'experiment_extension_reason', 'ongoing_constraints',
  'origin_trial_feedback_url', 'intent_to_experiment_url',
  'intent_to_extend_experiment_url', 'i2e_lgtms',
];

const IMPLSTATUS_ORIGINTRIAL = [
  'ot_milestone_desktop_start', 'ot_milestone_desktop_end',
  'ot_milestone_android_start', 'ot_milestone_android_end',
  'ot_milestone_webview_start', 'ot_milestone_webview_end',
  'experiment_timeline', // deprecated
];

const MOST_PREPARETOSHIP = [
  'tag_review', 'tag_review_status', 'non_oss_deps',
  'webview_risks', 'anticipated_spec_changes', 'measurement',
  'intent_to_ship_url', 'i2s_lgtms', 'finch_url',
];

const ANY_SHIP = ['launch_bug_url', 'finch_url'];

const EXISTING_PROTOTYPE = [
  'explainer_links', 'spec_link', 'standard_maturity', 'api_spec',
  'intent_to_implement_url',
];

const EXISTING_ORIGINTRIAL = [
  'experiment_goals', 'experiment_risks',
  'experiment_extension_reason', 'ongoing_constraints',
  'intent_to_experiment_url', 'intent_to_extend_experiment_url',
  'i2e_lgtms', 'origin_trial_feedback_url',
];

const PSA_IMPLEMENT = ['spec_link', 'standard_maturity'];
// TODO(jrobbins): advise user to request a tag review

const PSA_PREPARETOSHIP = [
  'tag_review', 'intent_to_ship_url',
];

// Note: Even though this is similar to another form, it is likely to change.
// const DEPRECATION_PREPARETOSHIP = [
//   'impl_status_chrome', 'tag_review',
//   'webview_risks',
//   'intent_to_implement_url', 'origin_trial_feedback_url',
// ];

// Note: Even though this is similar to another form, it is likely to change.
const DEPRECATION_DEPRECATIONTRIAL = [
  'experiment_goals', 'experiment_risks',
  'ot_milestone_desktop_start', 'ot_milestone_desktop_end',
  'ot_milestone_android_start', 'ot_milestone_android_end',
  'ot_milestone_webview_start', 'ot_milestone_webview_end',
  'experiment_timeline', // deprecated
  'experiment_extension_reason', 'ongoing_constraints',
  'r4dt_url', // map to name="intent_to_experiment_url" field upon form submission
  'intent_to_extend_experiment_url',
  'r4dt_lgtms', // map to name="i2e_lgtms" field upon form submission
  'origin_trial_feedback_url',
];

// Note: Even though this is similar to another form, it is likely to change.
const DEPRECATION_PREPARETOSHIP = [
  'impl_status_chrome', 'intent_to_ship_url', 'i2s_lgtms',
];

const DEPRECATION_REMOVED = [];

const ENTERPRISE_PREPARE_TO_SHIP = [
  'rollout_milestone', 'rollout_platforms', 'rollout_details',
  'enterprise_policies',
];

// Forms to be used for each stage of each process.
// { feature_type_id: { stage_id: stage_specific_form} }
export const STAGE_FORMS = {
  [FEATURE_TYPES.FEATURE_TYPE_INCUBATE_ID[0]]: {
    [INTENT_STAGES.INTENT_INCUBATE[0]]: NEWFEATURE_INCUBATE,
    [INTENT_STAGES.INTENT_IMPLEMENT[0]]: NEWFEATURE_PROTOTYPE,
    [INTENT_STAGES.INTENT_EXPERIMENT[0]]: ANY_DEVTRIAL,
    [INTENT_STAGES.INTENT_IMPLEMENT_SHIP[0]]: NEWFEATURE_EVALREADINESSTOSHIP,
    [INTENT_STAGES.INTENT_EXTEND_TRIAL[0]]: NEWFEATURE_ORIGINTRIAL,
    [INTENT_STAGES.INTENT_SHIP[0]]: MOST_PREPARETOSHIP,
    [INTENT_STAGES.INTENT_ROLLOUT[0]]: ENTERPRISE_PREPARE_TO_SHIP,
    [INTENT_STAGES.INTENT_SHIPPED[0]]: ANY_SHIP,
  },

  [FEATURE_TYPES.FEATURE_TYPE_EXISTING_ID[0]]: {
    [INTENT_STAGES.INTENT_IMPLEMENT[0]]: EXISTING_PROTOTYPE,
    [INTENT_STAGES.INTENT_EXPERIMENT[0]]: ANY_DEVTRIAL,
    [INTENT_STAGES.INTENT_EXTEND_TRIAL[0]]: EXISTING_ORIGINTRIAL,
    [INTENT_STAGES.INTENT_SHIP[0]]: MOST_PREPARETOSHIP,
    [INTENT_STAGES.INTENT_ROLLOUT[0]]: ENTERPRISE_PREPARE_TO_SHIP,
    [INTENT_STAGES.INTENT_SHIPPED[0]]: ANY_SHIP,
  },

  [FEATURE_TYPES.FEATURE_TYPE_CODE_CHANGE_ID[0]]: {
    [INTENT_STAGES.INTENT_IMPLEMENT[0]]: PSA_IMPLEMENT,
    [INTENT_STAGES.INTENT_EXPERIMENT[0]]: ANY_DEVTRIAL,
    [INTENT_STAGES.INTENT_SHIP[0]]: PSA_PREPARETOSHIP,
    [INTENT_STAGES.INTENT_ROLLOUT[0]]: ENTERPRISE_PREPARE_TO_SHIP,
    [INTENT_STAGES.INTENT_SHIPPED[0]]: ANY_SHIP,
  },

  [FEATURE_TYPES.FEATURE_TYPE_DEPRECATION_ID[0]]: {
    [INTENT_STAGES.INTENT_EXPERIMENT[0]]: ANY_DEVTRIAL,
    [INTENT_STAGES.INTENT_EXTEND_TRIAL[0]]: DEPRECATION_DEPRECATIONTRIAL,
    [INTENT_STAGES.INTENT_SHIP[0]]: DEPRECATION_PREPARETOSHIP,
    [INTENT_STAGES.INTENT_ROLLOUT[0]]: ENTERPRISE_PREPARE_TO_SHIP,
    [INTENT_STAGES.INTENT_REMOVED[0]]: DEPRECATION_REMOVED,
  },

  [FEATURE_TYPES.FEATURE_TYPE_ENTERPRISE_ID[0]]: {
    [INTENT_STAGES.INTENT_ROLLOUT[0]]: ENTERPRISE_PREPARE_TO_SHIP,
    [INTENT_STAGES.INTENT_SHIPPED[0]]: ANY_SHIP,
  },
};

export const IMPL_STATUS_FORMS = {
  [INTENT_STAGES.INTENT_INCUBATE[0]]:
    ['', IMPLSTATUS_INCUBATE],
  [INTENT_STAGES.INTENT_EXPERIMENT[0]]:
    [IMPLEMENTATION_STATUS.BEHIND_A_FLAG[0], IMPLSTATUS_DEVTRIAL],
  [INTENT_STAGES.INTENT_EXTEND_TRIAL[0]]:
    [IMPLEMENTATION_STATUS.ORIGIN_TRIAL[0], IMPLSTATUS_ORIGINTRIAL],
  [INTENT_STAGES.INTENT_IMPLEMENT_SHIP[0]]:
    ['', IMPLSTATUS_EVALREADINESSTOSHIP],
  [INTENT_STAGES.INTENT_SHIP[0]]:
    [IMPLEMENTATION_STATUS.ENABLED_BY_DEFAULT[0], IMPLSTATUS_ALLMILESTONES],
  [INTENT_STAGES.INTENT_ROLLOUT[0]]:
    [IMPLEMENTATION_STATUS.ENABLED_BY_DEFAULT[0], IMPLSTATUS_ALLMILESTONES],
  [INTENT_STAGES.INTENT_SHIPPED[0]]:
    [IMPLEMENTATION_STATUS.ENABLED_BY_DEFAULT[0], IMPLSTATUS_ALLMILESTONES],
  [INTENT_STAGES.INTENT_REMOVED[0]]:
    [IMPLEMENTATION_STATUS.REMOVED[0], IMPLSTATUS_ALLMILESTONES],
};
