// Constants that are used by the search help dialog.
// And will be used by autocomplete in the future.

import {type HTMLTemplateResult} from 'lit';
import {
  FEATURE_CATEGORIES,
  FEATURE_TYPES,
  IMPLEMENTATION_STATUS,
  INTENT_STAGES,
  REVIEW_STATUS_CHOICES,
  ROLLOUT_IMPACT,
  VENDOR_VIEWS_COMMON,
  VENDOR_VIEWS_GECKO,
  WEB_DEV_VIEWS,
} from './form-field-enums';

export const TEXT_KIND = 'text';
export const NUM_KIND = 'number';
export const MILESTONE_KIND = 'milestone';
export const DATE_KIND = 'YYYY-MM-DD';
export const EMAIL_KIND = 'user@example.com';
export const ENUM_KIND = 'enum';

export interface QueryField {
  name: string;
  kind: string;
  doc: string;
  choices?:
    | Record<string, [number, string]>
    | Record<string, [number, string, string | HTMLTemplateResult]>;
}
export const QUERIABLE_FIELDS: QueryField[] = [
  {
    name: 'created.when',
    kind: DATE_KIND,
    doc: 'Date that the feature entry was created',
  },
  {
    name: 'updated.when',
    kind: DATE_KIND,
    doc: 'Date that the feature was most recently edited',
  },
  {name: 'name', kind: TEXT_KIND, doc: 'The name of the feature'},
  // 'summary': Feature.summary,
  // 'unlisted': Feature.unlisted,
  //  'motivation': Feature.motivation,
  //  'star_count': Feature.star_count,
  {
    name: 'tags',
    kind: TEXT_KIND,
    doc: 'Search tags for finding feature entries',
  },
  {name: 'owner', kind: EMAIL_KIND, doc: 'One of the feature owners'},
  //  'intent_to_implement_url': Feature.intent_to_implement_url,
  //  'intent_to_ship_url': Feature.intent_to_ship_url,
  //  'ready_for_trial_url': Feature.ready_for_trial_url,
  //  'intent_to_experiment_url': Feature.intent_to_experiment_url,
  //  'intent_to_extend_experiment_url': Feature.intent_to_extend_experiment_url,
  //  'i2e_lgtms': Feature.i2e_lgtms,
  //  'i2s_lgtms': Feature.i2s_lgtms,
  //  'browsers.chrome.bug': Feature.bug_url,
  //  'launch_bug_url': Feature.launch_bug_url,
  //  'initial_public_proposal_url': Feature.initial_public_proposal_url,
  //  'browsers.chrome.blink_components': Feature.blink_components,
  {
    name: 'browsers.chrome.devrel',
    kind: EMAIL_KIND,
    doc: 'Developer relations contact',
  },

  //  'browsers.chrome.status': Feature.impl_status_chrome,
  {
    name: 'browsers.chrome.desktop',
    kind: MILESTONE_KIND,
    doc: 'Desktop shipping milestone',
  },
  {
    name: 'browsers.chrome.android',
    kind: MILESTONE_KIND,
    doc: 'Android shipping milestone',
  },
  {
    name: 'browsers.chrome.ios',
    kind: MILESTONE_KIND,
    doc: 'iOS shipping milestone',
  },
  {
    name: 'browsers.chrome.webview',
    kind: MILESTONE_KIND,
    doc: 'Webview shipping milestone',
  },
  // 'requires_embedder_support': Feature.requires_embedder_support,

  {
    name: 'browsers.chrome.flag_name',
    kind: TEXT_KIND,
    doc: 'Flag name that allows developers to enable the feature',
  },
  {name: 'browsers.chrome.finch_name', kind: TEXT_KIND, doc: 'Finch name'},
  // 'browsers.chrome.non_finch_justification': Feature.non_finch_justification,
  // 'all_platforms': Feature.all_platforms,
  // 'all_platforms_descr': Feature.all_platforms_descr,
  // 'wpt': Feature.wpt,
  {
    name: 'browsers.chrome.devtrial.desktop.start',
    kind: MILESTONE_KIND,
    doc: 'Desktop DevTrial start',
  },
  {
    name: 'browsers.chrome.devtrial.android.start',
    kind: MILESTONE_KIND,
    doc: 'Android DevTrial start',
  },
  {
    name: 'browsers.chrome.devtrial.ios.start',
    kind: MILESTONE_KIND,
    doc: 'iOS DevTrial start',
  },
  {
    name: 'browsers.chrome.devtrial.webview.start',
    kind: MILESTONE_KIND,
    doc: 'WebView DevTrial start',
  },

  // 'standards.maturity': Feature.standard_maturity,
  // 'standards.spec': Feature.spec_link,
  // 'api_spec': Feature.api_spec,
  // 'spec_mentors': Feature.spec_mentors,
  // 'security_review_status': Feature.security_review_status,
  // 'privacy_review_status': Feature.privacy_review_status,
  // 'tag_review.url': Feature.tag_review,
  // 'explainer': Feature.explainer_links,

  // 'resources.docs': Feature.doc_links,
  // 'non_oss_deps': Feature.non_oss_deps,

  {
    name: 'browsers.chrome.ot.desktop.start',
    kind: MILESTONE_KIND,
    doc: 'Desktop Origin Trial start',
  },
  {
    name: 'browsers.chrome.ot.desktop.end',
    kind: MILESTONE_KIND,
    doc: 'Desktop Origin Trial end',
  },
  {
    name: 'browsers.chrome.ot.android.start',
    kind: MILESTONE_KIND,
    doc: 'Android Origin Trial start',
  },
  {
    name: 'browsers.chrome.ot.android.end',
    kind: MILESTONE_KIND,
    doc: 'Android Origin Trial end',
  },
  {
    name: 'browsers.chrome.ot.webview.start',
    kind: MILESTONE_KIND,
    doc: 'WebView Origin Trial start',
  },
  {
    name: 'browsers.chrome.ot.webview.end',
    kind: MILESTONE_KIND,
    doc: 'WebView Origin Trial end',
  },
  {
    name: 'rollout_milestone',
    kind: MILESTONE_KIND,
    doc: 'Stable rollout milestone',
  },
  {
    name: 'any_start_milestone',
    kind: MILESTONE_KIND,
    doc:
      'A milestone in which the feature is scheduled to ship or start an ' +
      'origin trial or dev trial, on any platform',
  },
  // 'browsers.chrome.ot.feedback_url': Feature.origin_trial_feedback_url,
  // 'finch_url': Feature.finch_url,

  // TODO(kyleju): Use ALL_FIELDS from form-field-specs.js.
  // Available ENUM fields.
  {
    name: 'category',
    kind: ENUM_KIND,
    doc: 'Feature category',
    choices: FEATURE_CATEGORIES,
  },
  {
    name: 'feature_type',
    kind: ENUM_KIND,
    doc: 'Feature type',
    choices: FEATURE_TYPES,
  },
  {
    name: 'impl_status_chrome',
    kind: ENUM_KIND,
    doc: 'Implementation status',
    choices: IMPLEMENTATION_STATUS,
  },
  {
    name: 'intent_stage',
    kind: ENUM_KIND,
    doc: 'Spec process stage',
    choices: INTENT_STAGES,
  },
  {
    name: 'rollout_impact',
    kind: ENUM_KIND,
    doc: 'Impact',
    choices: ROLLOUT_IMPACT,
  },
  // TODO: rollout_platforms is not yet supported.
  // {name: 'rollout_platforms', kind: ENUM_KIND,
  // doc: 'Rollout platforms',
  //  choices: PLATFORM_CATEGORIES,
  //  },
  // TODO: The enum valus are super long.
  // {name: 'standard_maturity', kind: ENUM_KIND,
  //  doc: 'Standard maturity',
  // choices: STANDARD_MATURITY_CHOICES,
  // },
  {
    name: 'security_review_status',
    kind: ENUM_KIND,
    doc: 'Security review status',
    choices: REVIEW_STATUS_CHOICES,
  },
  {
    name: 'privacy_review_status',
    kind: ENUM_KIND,
    doc: 'Privacy review status',
    choices: REVIEW_STATUS_CHOICES,
  },
  {
    name: 'tag_review_status',
    kind: ENUM_KIND,
    doc: 'TAG Specification Review Status',
    choices: REVIEW_STATUS_CHOICES,
  },
  {
    name: 'browsers.safari.view',
    kind: ENUM_KIND,
    doc: 'Safari views',
    choices: VENDOR_VIEWS_COMMON,
  },
  {
    name: 'browsers.ff.view',
    kind: ENUM_KIND,
    doc: 'Firefox views',
    choices: VENDOR_VIEWS_GECKO,
  },
  {
    name: 'browsers.webdev.view',
    kind: ENUM_KIND,
    doc: 'Web / Framework developer views',
    choices: WEB_DEV_VIEWS,
  },
  {
    name: 'accurate_as_of',
    kind: DATE_KIND,
    doc: "When the feature's fields were last verified",
  },
];
