import {html} from 'lit';
import * as enums from './form-field-enums';

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
export function formatFeatureForEdit(feature) {
  const formattedFeature = {
    ...feature,
    category: feature.category_int,
    enterprise_feature_categories: Array.from(
      new Set(feature.enterprise_feature_categories || [])
    ).map(x => parseInt(x).toString()),
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
  'enterprise_feature_categories',
  'first_enterprise_notification_milestone',
  'enterprise_impact',
  'screenshot_links',
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
        'enterprise_impact',
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
        'enterprise_impact',
        'first_enterprise_notification_milestone',
        'screenshot_links',
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
const FLAT_PROTOTYPE_FIELDS = {
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
      implStatusValue: enums.IMPLEMENTATION_STATUS.ORIGIN_TRIAL[0],
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
      ],
    },
  ],
};

const FLAT_EVAL_READINESS_TO_SHIP_FIELDS = {
  name: 'Evaluate readiness to ship',
  sections: [
    {
      name: 'Evaluate readiness to ship',
      fields: ['prefixed', 'tag_review'],
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
      implStatusValue: enums.IMPLEMENTATION_STATUS.ENABLED_BY_DEFAULT[0],
    },
  ],
};

// All fields relevant to the enterprise prepare to ship stage.
export const FLAT_ENTERPRISE_PREPARE_TO_SHIP_FIELDS = {
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

const PSA_IMPLEMENT_FIELDS = {
  name: 'Start prototyping',
  sections: [
    // Standardization
    {
      name: 'Start prototyping',
      fields: ['motivation', 'spec_link', 'standard_maturity'],
    },
  ],
};

const PSA_PREPARE_TO_SHIP_FIELDS = {
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

const DEPRECATION_PLAN_FIELDS = {
  name: 'Write up motivation',
  sections: [
    {
      name: 'Write up motivation',
      fields: ['motivation', 'spec_link'],
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
        'webview_risks',
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

export const ORIGIN_TRIAL_CREATION_FIELDS = {
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
        'ot_documentation_url',
        'ot_feedback_submission_url',
        'ot_chromium_trial_name',
        'ot_is_deprecation_trial',
        'ot_webfeature_use_counter',
        'ot_has_third_party_support',
        'ot_is_critical_trial',
        'ot_require_approvals',
        'ot_request_note',
      ],
    },
  ],
};

export const ORIGIN_TRIAL_EXTENSION_FIELDS = {
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
      implStatusValue: enums.IMPLEMENTATION_STATUS.ORIGIN_TRIAL[0],
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
        'dt_milestone_desktop_start',
        'dt_milestone_android_start',
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

export const VERIFY_ACCURACY_TRIAL_EXTENSION_FIELDS = {
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

const VERIFY_ACCURACY_PREPARE_TO_SHIP_FIELDS = {
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

const VERIFY_ACCURACY_ENTERPRISE_PREPARE_TO_SHIP_FIELDS = {
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
export const VERIFY_ACCURACY_CONFIRMATION_FIELD = {
  name: 'Verify Accuracy',
  sections: [
    {
      name: 'Verify Accuracy',
      fields: ['accurate_as_of'],
    },
  ],
};

export const FORMS_BY_STAGE_TYPE = {
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

export const CREATEABLE_STAGES = {
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

export const VERIFY_ACCURACY_FORMS_BY_STAGE_TYPE = {
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

const BLINK_GENERIC_QUESTIONNAIRE = html` <p>
    To request a review, use the "Draft intent..." button above to generate an
    intent messsage, and then post that message to blink-dev@chromium.org.
  </p>
  <p>
    Be sure to update your feature entry in response to any suggestions on that
    email thread.
  </p>`;

const PRIVACY_GENERIC_QUESTIONNAIRE = html` <p>
    <b
      >Please fill out the Security &amp; Privacy self-review questionnaire:
      <a
        href="https://www.w3.org/TR/security-privacy-questionnaire/"
        target="_blank"
        >https://www.w3.org/TR/security-privacy-questionnaire/</a
      ></b
    >
  </p>
  <p>
    Share it as a public document, as a file in your repository, or in any other
    public format of your choice.
  </p>
  <p>
    You can reuse the same filled-out questionnaire in the security review
    below, across all stages of this ChromeStatus entry, and across all entries
    related to the same API. If you updated an existing questionnaire to reflect
    new changes to the API, please highlight them for an easier review.
  </p>
  <p>
    <b>If you believe your feature has no privacy impact</b> and none of the
    questions in the questionnaire apply, you can provide a justification
    instead, e.g. "Removing a prefix from the API, no changes to functionality"
    or "New CSS property that doesn't depend on the user state, therefore
    doesn't reveal any user information". Note that if your reviewer disagrees
    with the justification, they may ask you to fill out the questionnaire
    nevertheless.
  </p>`;

const SECURITY_GENERIC_QUESTIONNAIRE = html` <p>
    <b
      >Please fill out the Security &amp; Privacy self-review questionnaire:
      <a
        href="https://www.w3.org/TR/security-privacy-questionnaire/"
        target="_blank"
        >https://www.w3.org/TR/security-privacy-questionnaire/</a
      ></b
    >
  </p>
  <p>
    Share it as a public document, as a file in your repository, or in any other
    public format of your choice.
  </p>
  <p>
    You can reuse the same filled-out questionnaire in the privacy review above,
    across all stages of this ChromeStatus entry, and across all entries related
    to an API. If you updated an existing questionnaire to reflect new changes
    to the API, please highlight them for an easier review.
  </p>
  <p>
    <b>If you believe your feature has no security impact</b> and none of the
    questions in the questionnaire apply, you can provide a justification
    instead. Note that if your reviewer disagrees with the justification, they
    may ask you to fill out the questionnaire nevertheless.
  </p>`;

const ENTERPRISE_SHIP_QUESTIONNAIRE = html` <p>
    <b>(1) Does this launch include a breaking change?</b> Does this launch
    remove or modify existing behavior or does it interrupt an existing user
    flow? (e.g. removing or restricting an API, or significant UI change).
    Answer with one of the following options, and/or describe anything you're
    unsure about:
  </p>
  <ul>
    <li>
      No. There's no change visible to users, developers, or IT admins (e.g.
      internal refactoring)
    </li>
    <li>No. This launch is strictly additive functionality</li>
    <li>
      Yes. Something that exists is changing or being removed (even if usage is
      very small)
    </li>
    <li>
      I don't know. Enterprise reviewers, please help me decide. The relevant
      information is: ______
    </li>
  </ul>
  <p>
    <b
      >(2) Is there any other reason you expect that enterprises will care about
      this launch?</b
    >
    (e.g. they may perceive a risk of data leaks if the browser is uploading new
    information, or it may be a surprise to employees resulting in them calling
    their help desk). Answer with one of the following options, and/or describe
    anything you're unsure about:
  </p>
  <ul>
    <li>No. Enterprises won't care about this</li>
    <li>Yes. They'll probably care because ______</li>
    <li>
      I don't know. Enterprise reviewers, please help me decide. The relevant
      information is: ______
    </li>
  </ul>
  <p>
    <b
      >(3) Does your launch have an enterprise policy to control it, and will it
      be available when this rolls out to stable (even to 1%)?</b
    >
    Only required if you answered Yes to either of the first 2 questions. Answer
    with one of the following options, and/or describe anything you're unsure
    about:
  </p>
  <ul>
    <li>
      Yes. It's called ______. It will be a permanent policy, and it will be
      available when stable rollout starts
    </li>
    <li>
      Yes. It's called ______. This is a temporary transition period, so the
      policy will stop working on milestone ___. It will be available when
      stable rollout starts
    </li>
    <li>
      No. A policy is infeasible because ______ (e.g. this launch is a change in
      how we compile Chrome)
    </li>
    <li>
      No. A policy isn't necessary because ______ (e.g. there's a better method
      of control available to admins)
    </li>
  </ul>
  <p>
    <b
      >(4) Provide a brief title and description of this launch, which can be
      shared with enterprises.</b
    >
    Only required if you answered Yes to either of the first 2 questions. This
    may be added to browser release notes. Where applicable, explain the benefit
    to users, and describe the policy to control it.
  </p>`;

const DEBUGGABILITY_ORIGIN_TRIAL_QUESTIONNAIRE = html`
  <p>
    (1) Does the introduction of the new Web Platform feature break Chrome
    DevTools' existing developer experience?
  </p>

  <p>
    (2) Does Chrome DevTools' existing set of tooling features interact with the
    new Web Platform feature in an expected way?
  </p>

  <p>
    (3) Would the new Web Platform feature's acceptance and/or adoption benefit
    from adding a new developer workflow to Chrome DevTools?
  </p>

  <p>
    When in doubt, please check out https://goo.gle/devtools-checklist for
    details!
  </p>
`;

const DEBUGGABILITY_SHIP_QUESTIONNAIRE =
  DEBUGGABILITY_ORIGIN_TRIAL_QUESTIONNAIRE;

const TESTING_SHIP_QUESTIONNAIRE = html` <p>
    <b
      >(1) Does your feature have sufficient automated test coverage (Unit
      tests, WPT, browser tests and other integration tests)?</b
    >
    Chrome requires at least 70% automation code coverage (<a
      href="https://analysis.chromium.org/coverage/p/chromium"
      target="_blank"
      >dashboard</a
    >) running on the main/release branch and 70% Changelist
    <a
      href="https://chromium.googlesource.com/chromium/src/+/refs/heads/main/docs/testing/code_coverage_in_gerrit.md"
      target="_blank"
      >code coverage in Gerrit</a
    >? Do the automated tests have more than 93% green (flakiness < 7%) on CQ
    and CI builders?
  </p>
  <ul>
    <li>
      Yes. My feature met the minimum automated test coverage and health
      requirements.
    </li>
    <li>No. My feature does not meet the requirements since __________.</li>
  </ul>
  <p>
    <b>(2) How are performance tests conducted on Chromium builders?</b> List
    links to tests if any.
  </p>
  <p>
    <b
      >(3) Does this feature have non-automatable test cases that require manual
      testing? Do you have a plan to get them tested?</b
    >
  </p>
  <ul>
    <li>No. All feature related test cases are automated.</li>
    <li>
      Yes. There are non-automatable test cases and I have completed test
      execution or allocated resources to ensure the coverage of these test
      cases.
    </li>
    <li>
      Yes. There are non-automatable test cases and my feature impacts Google
      products.
    </li>
  </ul>
  <p>
    <b
      >(4) If your feature impacts Google products, please fill in
      <a href="http://go/chrome-wp-test-survey" target="_blank"
        >go/chrome-wp-test-survey</a
      >.</b
    >
    Make a copy, answer the survey questions, and provide a link to your
    document here.
  </p>`;

export const GATE_QUESTIONNAIRES = {
  [enums.GATE_TYPES.API_PROTOTYPE]: BLINK_GENERIC_QUESTIONNAIRE,
  [enums.GATE_TYPES.API_ORIGIN_TRIAL]: BLINK_GENERIC_QUESTIONNAIRE,
  [enums.GATE_TYPES.API_EXTEND_ORIGIN_TRIAL]: BLINK_GENERIC_QUESTIONNAIRE,
  [enums.GATE_TYPES.API_SHIP]: BLINK_GENERIC_QUESTIONNAIRE,
  [enums.GATE_TYPES.API_PLAN]: BLINK_GENERIC_QUESTIONNAIRE,
  [enums.GATE_TYPES.PRIVACY_ORIGIN_TRIAL]: PRIVACY_GENERIC_QUESTIONNAIRE,
  [enums.GATE_TYPES.PRIVACY_SHIP]: PRIVACY_GENERIC_QUESTIONNAIRE,
  // Note: There is no privacy planning gate.
  [enums.GATE_TYPES.SECURITY_ORIGIN_TRIAL]: SECURITY_GENERIC_QUESTIONNAIRE,
  [enums.GATE_TYPES.SECURITY_SHIP]: SECURITY_GENERIC_QUESTIONNAIRE,
  // Note: There is no security planning gate.
  [enums.GATE_TYPES.ENTERPRISE_SHIP]: ENTERPRISE_SHIP_QUESTIONNAIRE,
  [enums.GATE_TYPES.ENTERPRISE_PLAN]: ENTERPRISE_SHIP_QUESTIONNAIRE,
  [enums.GATE_TYPES.DEBUGGABILITY_ORIGIN_TRIAL]:
    DEBUGGABILITY_ORIGIN_TRIAL_QUESTIONNAIRE,
  [enums.GATE_TYPES.DEBUGGABILITY_SHIP]: DEBUGGABILITY_SHIP_QUESTIONNAIRE,
  [enums.GATE_TYPES.DEBUGGABILITY_PLAN]: DEBUGGABILITY_SHIP_QUESTIONNAIRE,
  [enums.GATE_TYPES.TESTING_SHIP]: TESTING_SHIP_QUESTIONNAIRE,
  [enums.GATE_TYPES.TESTING_PLAN]: TESTING_SHIP_QUESTIONNAIRE,
};
