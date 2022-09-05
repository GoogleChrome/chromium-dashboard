import {STANDARD_MATURITY_CHOICES} from './form-field-enums';


const COMMA_SEPARATED_FIELDS = ['owner', 'editors', 'spec_mentors',
  'search_tags', 'devrel', 'i2e_lgtms', 'i2s_lgtms'];

const LINE_SEPARATED_FIELDS = ['explainer_links', 'doc_links', 'sample_links'];

export function formatFeatureForEdit(feature) {
  const formattedFeature = {
    ...feature,
    category: feature.category_int,
    feature_type: feature.feature_type_int,
    intent_stage: feature.intent_stage_int,
    standard_maturity: feature.standard_maturity || STANDARD_MATURITY_CHOICES.UNKNOWN_STD,
    blink_components: feature.blink_components[0],
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
