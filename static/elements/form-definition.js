import {STANDARD_MATURITY_CHOICES} from './form-field-enums';


const COMMA_SEPARATED_FIELDS = ['owner', 'editors', 'spec_mentors',
  'search_tags', 'devrel', 'i2e_lgtms', 'i2s_lgtms'];

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
    standard_maturity: feature.standards.maturity.val || STANDARD_MATURITY_CHOICES.UNKNOWN_STD,

    // from feature.resources
    sample_links: feature.resources.samples,
    doc_links: feature.resources.docs,

    search_tags: feature.tag,

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
    if (feature[field]) formattedFeature[field] = feature[field].join(', ');
  });

  LINE_SEPARATED_FIELDS.map((field) => {
    if (feature[field]) formattedFeature[field] = feature[field].join('\r\n');
  });

  return formattedFeature;
}

// The following arrays define the list of fields for each guide form.

export const METADATA_FORM_FIELDS = [
  'name', 'summary', 'unlisted', 'owner',
  'editors', 'category',
  'feature_type', 'intent_stage',
  'search_tags',
  // Implemention
  'impl_status_chrome',
  'blink_components',
  'bug_url', 'launch_bug_url',
];

export const VERIFY_ACCURACY_FORM_FIELDS = [
  'summary', 'owner', 'editors', 'impl_status_chrome', 'intent_stage',
  'dt_milestone_android_start', 'dt_milestone_desktop_start',
  'dt_milestone_ios_start', 'ot_milestone_android_start',
  'ot_milestone_android_end', 'ot_milestone_desktop_start',
  'ot_milestone_desktop_end', 'ot_milestone_webview_start',
  'ot_milestone_webview_end', 'shipped_android_milestone',
  'shipped_ios_milestone', 'shipped_milestone', 'shipped_webview_milestone',
  'accurate_as_of',
];
