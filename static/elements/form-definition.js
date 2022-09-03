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
