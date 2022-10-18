import {
  FEATURE_TYPES,
  INTENT_STAGES,
  IMPLEMENTATION_STATUS,
} from './form-field-enums';


const COMMA_SEPARATED_FIELDS = ['owner', 'editors', 'cc_recipients',
  'spec_mentors', 'search_tags', 'devrel', 'i2e_lgtms', 'i2s_lgtms'];

const LINE_SEPARATED_FIELDS = ['explainer_links', 'doc_links', 'sample_links'];

/* Convert the format of feature object fetched from API into those for edit.
 * The feature object from API is formatted by the format_for_template method of
 * the Feature class in internals/core_models.py
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
    standardization: feature.standards.status.val,
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
  };

  COMMA_SEPARATED_FIELDS.map((field) => {
    if (formattedFeature[field]) formattedFeature[field] = formattedFeature[field].join(', ');
  });

  LINE_SEPARATED_FIELDS.map((field) => {
    if (formattedFeature[field]) formattedFeature[field] = formattedFeature[field].join('\r\n');
  });

  return formattedFeature;
}

// The following arrays define the list of fields for each guide form.

export const NEW_FEATURE_FORM_FIELDS = [
  'name', 'summary', 'unlisted', 'owner',
  'editors', 'cc_recipients', 'blink_components', 'category',
];
// Note: feature_type is done with custom HTML in chromedash-guide-new-page

export const METADATA_FORM_FIELDS = [
  'name', 'summary', 'unlisted', 'owner',
  'editors', 'cc_recipients', 'category',
  'feature_type', 'intent_stage',
  'search_tags',
  // Implemention
  'impl_status_chrome',
  'blink_components',
  'bug_url', 'launch_bug_url',
];

export const VERIFY_ACCURACY_FORM_FIELDS = [
  'summary', 'owner', 'editors', 'cc_recipients', 'impl_status_chrome', 'intent_stage',
  'dt_milestone_android_start', 'dt_milestone_desktop_start',
  'dt_milestone_ios_start', 'ot_milestone_android_start',
  'ot_milestone_android_end', 'ot_milestone_desktop_start',
  'ot_milestone_desktop_end', 'ot_milestone_webview_start',
  'ot_milestone_webview_end', 'shipped_android_milestone',
  'shipped_ios_milestone', 'shipped_milestone', 'shipped_webview_milestone',
  'accurate_as_of',
];

const FLAT_METADATA_FIELDS = [
  // Standardizaton
  'name', 'summary', 'unlisted', 'owner',
  'editors', 'cc_recipients', 'category',
  'feature_type', 'intent_stage',
  'search_tags',
  // Implementtion
  'impl_status_chrome',
  'blink_components',
  'bug_url', 'launch_bug_url',
  'comments',
];

const FLAT_IDENTIFY_FIELDS = [
  // Standardization
  // TODO(jrobbins): display deprecation_motivation instead when deprecating.
  'motivation', 'initial_public_proposal_url', 'explainer_links',
  // Implementtion
  'requires_embedder_support',
];


const FLAT_IMPLEMENT_FIELDS = [
  // Standardization
  'spec_link', 'standard_maturity', 'api_spec', 'spec_mentors',
  'intent_to_implement_url',
];


const FLAT_DEV_TRAIL_FIELDS = [
  // Standardizaton
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

  // TODO(jrobbins): UA support signals section

  // Implementation
  'dt_milestone_desktop_start', 'dt_milestone_android_start',
  'dt_milestone_ios_start',
  'flag_name',
];
// TODO(jrobbins): api overview link


const FLAT_ORIGIN_TRIAL_FIELDS = [
  // Standardization
  'experiment_goals',
  'experiment_risks',
  'experiment_extension_reason', 'ongoing_constraints',
  // TODO(jrobbins): display r4dt_url instead when deprecating.
  'intent_to_experiment_url', 'intent_to_extend_experiment_url',
  'i2e_lgtms',
  'origin_trial_feedback_url',

  // Implementation
  'ot_milestone_desktop_start', 'ot_milestone_desktop_end',
  'ot_milestone_android_start', 'ot_milestone_android_end',
  'ot_milestone_webview_start', 'ot_milestone_webview_end',
  'experiment_timeline', // deprecated
];


const FLAT_PREPARE_TO_SHIP_FIELDS = [
  // Standardization
  'tag_review', 'tag_review_status',
  'webview_risks', 'anticipated_spec_changes',
  'intent_to_ship_url', 'i2s_lgtms',
  // Implementation
  'measurement',
  'non_oss_deps',
];


const FLAT_SHIP_FIELDS = [
  // Implementation
  'finch_url',
  'shipped_milestone', 'shipped_android_milestone',
  'shipped_ios_milestone', 'shipped_webview_milestone',
];

// Forms to be used on the "Edit all" page that shows a flat list of fields.
// [[sectionName, flatFormFields]].
export const FLAT_FORMS = [
  ['Feature metadata', FLAT_METADATA_FIELDS],
  ['Identify the need', FLAT_IDENTIFY_FIELDS],
  ['Prototype a solution', FLAT_IMPLEMENT_FIELDS],
  ['Dev trial', FLAT_DEV_TRAIL_FIELDS],
  ['Origin trial', FLAT_ORIGIN_TRIAL_FIELDS],
  ['Prepare to ship', FLAT_PREPARE_TO_SHIP_FIELDS],
  ['Ship', FLAT_SHIP_FIELDS],
];


const NEWFEATURE_INCUBATE = [
  'motivation', 'initial_public_proposal_url', 'explainer_links',
  'bug_url', 'launch_bug_url', 'comments',
];

const IMPLSTATUS_INCUBATE = ['requires_embedder_support'];

const NEWFEATURE_PROTOTYPE = [
  'spec_link', 'standard_maturity', 'api_spec', 'spec_mentors',
  'intent_to_implement_url', 'comments',
];
// TODO(jrobbins): advise user to request a tag review

const ANY_DEVTRIAL = [
  'bug_url', 'devtrial_instructions', 'doc_links',
  'interop_compat_risks',
  'safari_views', 'safari_views_link', 'safari_views_notes',
  'ff_views', 'ff_views_link', 'ff_views_notes',
  'web_dev_views', 'web_dev_views_link', 'web_dev_views_notes',
  'other_views_notes',
  'security_review_status', 'privacy_review_status',
  'ergonomics_risks', 'activation_risks', 'security_risks', 'debuggability',
  'all_platforms', 'all_platforms_descr', 'wpt', 'wpt_descr',
  'sample_links', 'devrel', 'ready_for_trial_url', 'comments',
];
// TODO(jrobbins): api overview link

const IMPLSTATUS_DEVTRIAL = [
  'dt_milestone_desktop_start', 'dt_milestone_android_start',
  'dt_milestone_ios_start',
  'flag_name',
];

const NEWFEATURE_EVALREADINESSTOSHIP = [
  'doc_links', 'tag_review', 'spec_link',
  'standard_maturity', 'interop_compat_risks',
  'safari_views', 'safari_views_link', 'safari_views_notes',
  'ff_views', 'ff_views_link', 'ff_views_notes',
  'web_dev_views', 'web_dev_views_link', 'web_dev_views_notes',
  'other_views_notes',
  'prefixed', 'non_oss_deps', 'comments',
];

const IMPLSTATUS_ALLMILESTONES = [
  'shipped_milestone', 'shipped_android_milestone',
  'shipped_ios_milestone', 'shipped_webview_milestone',
];

const IMPLSTATUS_EVALREADINESSTOSHIP = [
  'shipped_milestone', 'shipped_android_milestone',
  'shipped_ios_milestone', 'shipped_webview_milestone',
  'measurement',
];

const NEWFEATURE_ORIGINTRIAL = [
  'experiment_goals', 'experiment_risks',
  'experiment_extension_reason', 'ongoing_constraints',
  'origin_trial_feedback_url', 'intent_to_experiment_url',
  'intent_to_extend_experiment_url',
  'i2e_lgtms', 'comments',
];

const IMPLSTATUS_ORIGINTRIAL = [
  'ot_milestone_desktop_start', 'ot_milestone_desktop_end',
  'ot_milestone_android_start', 'ot_milestone_android_end',
  'ot_milestone_webview_start', 'ot_milestone_webview_end',
  'experiment_timeline', // deprecated
];

const MOST_PREPARETOSHIP = [
  'tag_review', 'tag_review_status', 'non_oss_deps',
  'webview_risks', 'anticipated_spec_changes', 'origin_trial_feedback_url',
  'launch_bug_url', 'intent_to_ship_url', 'i2s_lgtms', 'comments',
];

const ANY_SHIP = ['launch_bug_url', 'finch_url', 'comments'];

const EXISTING_PROTOTYPE = [
  'owner', 'editors', 'cc_recipients', 'blink_components', 'motivation',
  'explainer_links', 'spec_link', 'standard_maturity', 'api_spec', 'bug_url',
  'launch_bug_url', 'intent_to_implement_url', 'comments',
];

const EXISTING_ORIGINTRIAL = [
  'experiment_goals', 'experiment_risks',
  'experiment_extension_reason', 'ongoing_constraints',
  'intent_to_experiment_url', 'intent_to_extend_experiment_url',
  'i2e_lgtms', 'origin_trial_feedback_url', 'comments',
];

const PSA_IMPLEMENT = ['motivation', 'spec_link', 'standard_maturity', 'comments'];
// TODO(jrobbins): advise user to request a tag review

const PAS_PREPARETOSHIP = [
  'tag_review', 'intent_to_implement_url', 'origin_trial_feedback_url',
  'launch_bug_url', 'intent_to_ship_url', 'comments',
];

const DEPRECATION_IMPLEMENT = [
  'deprecation_motivation', // map to name="motivation" field upon form submission
  'spec_link', 'comments',
];

// Note: Even though this is similar to another form, it is likely to change.
// const DEPRECATION_PREPARETOSHIP = [
//   'impl_status_chrome', 'tag_review',
//   'webview_risks',
//   'intent_to_implement_url', 'origin_trial_feedback_url',
//   'launch_bug_url', 'comments'
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
  'origin_trial_feedback_url', 'comments',
];

// Note: Even though this is similar to another form, it is likely to change.
const DEPRECATION_PREPARETOSHIP = [
  'impl_status_chrome', 'intent_to_ship_url', 'i2s_lgtms',
  'launch_bug_url', 'comments',
];

const DEPRECATION_REMOVED = ['comments'];

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
    [INTENT_STAGES.INTENT_SHIPPED[0]]: ANY_SHIP,
  },

  [FEATURE_TYPES.FEATURE_TYPE_EXISTING_ID[0]]: {
    [INTENT_STAGES.INTENT_IMPLEMENT[0]]: EXISTING_PROTOTYPE,
    [INTENT_STAGES.INTENT_EXPERIMENT[0]]: ANY_DEVTRIAL,
    [INTENT_STAGES.INTENT_EXTEND_TRIAL[0]]: EXISTING_ORIGINTRIAL,
    [INTENT_STAGES.INTENT_SHIP[0]]: MOST_PREPARETOSHIP,
    [INTENT_STAGES.INTENT_SHIPPED[0]]: ANY_SHIP,
  },

  [FEATURE_TYPES.FEATURE_TYPE_CODE_CHANGE_ID[0]]: {
    [INTENT_STAGES.INTENT_IMPLEMENT[0]]: PSA_IMPLEMENT,
    [INTENT_STAGES.INTENT_EXPERIMENT[0]]: ANY_DEVTRIAL,
    [INTENT_STAGES.INTENT_SHIP[0]]: PAS_PREPARETOSHIP,
    [INTENT_STAGES.INTENT_SHIPPED[0]]: ANY_SHIP,
  },

  [FEATURE_TYPES.FEATURE_TYPE_DEPRECATION_ID[0]]: {
    [INTENT_STAGES.INTENT_IMPLEMENT[0]]: DEPRECATION_IMPLEMENT,
    [INTENT_STAGES.INTENT_EXPERIMENT[0]]: ANY_DEVTRIAL,
    [INTENT_STAGES.INTENT_EXTEND_TRIAL[0]]: DEPRECATION_DEPRECATIONTRIAL,
    [INTENT_STAGES.INTENT_SHIP[0]]: DEPRECATION_PREPARETOSHIP,
    [INTENT_STAGES.INTENT_REMOVED[0]]: DEPRECATION_REMOVED,
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
  [INTENT_STAGES.INTENT_SHIPPED[0]]:
    [IMPLEMENTATION_STATUS.ENABLED_BY_DEFAULT[0], IMPLSTATUS_ALLMILESTONES],
  [INTENT_STAGES.INTENT_REMOVED[0]]:
    [IMPLEMENTATION_STATUS.REMOVED[0], IMPLSTATUS_ALLMILESTONES],
};
