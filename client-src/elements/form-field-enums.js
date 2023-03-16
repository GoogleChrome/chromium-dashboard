// The following objects define the list of options for select fields.
// Since the order of appearance of object properties is preserved,
// we can use this same order as the order of the select options.
// The value of each property, [intValue, stringLabel], is used
// for the option value and label.

export const FEATURE_CATEGORIES = {
  WEBCOMPONENTS: [1, 'Web Components'],
  MISC: [2, 'Miscellaneous'],
  SECURITY: [3, 'Security'],
  MULTIMEDIA: [4, 'Multimedia'],
  DOM: [5, 'DOM'],
  FILE: [6, 'File APIs'],
  OFFLINE: [7, 'Offline / Storage'],
  DEVICE: [8, 'Device'],
  COMMUNICATION: [9, 'Realtime / Communication'],
  JAVASCRIPT: [10, 'JavaScript'],
  NETWORKING: [11, 'Network / Connectivity'],
  INPUT: [12, 'User input'],
  PERFORMANCE: [13, 'Performance'],
  GRAPHICS: [14, 'Graphics'],
  CSS: [15, 'CSS'],
  HOUDINI: [16, 'Houdini'],
  SERVICEWORKER: [17, 'Service Worker'],
  WEBRTC: [18, 'WebRTC'],
  LAYERED: [19, 'Layered APIs'],
  WEBASSEMBLY: [20, 'WebAssembly'],
  CAPABILITIES: [21, 'Capabilities (Fugu)'],
};

export const ENTERPRISE_FEATURE_CATEGORIES = {
  SECURITYANDPRIVACY: [1, 'Security / Privacy'],
  USERPRODUCTIVITYANDAPPS: [2, 'User Productivity / Apps'],
  MANAGEMENT: [3, 'Management'],
};

export const ENTERPRISE_FEATURE_CATEGORIES_DISPLAYNAME = {
  1: 'Security/Privacy', // SECURITYANDPRIVACY
  2: 'User Productivity/Apps', // USERPRODUCTIVITYANDAPPS
  3: 'Management', // MANAGEMENT
};

export const PLATFORM_CATEGORIES = {
  PLATFORM_ANDROID: [1, 'Android'],
  PLATFORM_IOS: [2, 'iOS'],
  PLATFORM_CHROMEOS: [3, 'Chrome OS'],
  PLATFORM_LACROS: [4, 'LaCrOS'],
  PLATFORM_LINUX: [5, 'Linux'],
  PLATFORM_MAC: [6, 'Mac'],
  PLATFORM_WINDOWS: [7, 'Windows'],
  PLATFORM_FUCHSIA: [8, 'Fuchsia'],
};

export const PLATFORMS_DISPLAYNAME = {
  1: 'Android', // PLATFORM_ANDROID
  2: 'iOS', // PLATFORM_IOS
  3: 'Chrome OS', // PLATFORM_CHROMEOS
  4: 'LaCrOS', // PLATFORM_LACROS
  5: 'Linux', // PLATFORM_LINUX
  6: 'Mac', // PLATFORM_MAC
  7: 'Windows', // PLATFORM_WINDOWS
  8: 'Fuchsia', // PLATFORM_FUCHSIA
};

// FEATURE_TYPES object is organized as [intValue, stringLabel, description],
// the descriptions are used only for the descriptions of feature_type_radio_group
export const FEATURE_TYPES_WITHOUT_ENTERPRISE = {
  FEATURE_TYPE_INCUBATE_ID: [0, 'New feature incubation',
    'When building new features, we follow a process that emphasizes engagement ' +
    'with the WICG and other stakeholders early.'],
  FEATURE_TYPE_EXISTING_ID: [1, 'Existing feature implementation',
    'If there is already an agreed specification, work may quickly start on ' +
    'implementation and origin trials.'],
  FEATURE_TYPE_CODE_CHANGE_ID: [2, 'Web developer-facing change to existing code',
    'Sometimes a change to a shipped feature requires an additional feature entry. ' +
    'This type of feature entry can be referenced from a PSA immediately.'],
  FEATURE_TYPE_DEPRECATION_ID: [3, 'Feature deprecation',
    'Deprecate and remove an old feature.'],
};
export const FEATURE_TYPES = {
  ...FEATURE_TYPES_WITHOUT_ENTERPRISE,
  FEATURE_TYPE_ENTERPRISE_ID: [4, 'New Feature or removal affecting enterprises',
    'For features or changes that need to be communicated to enterprises or schools.'],
};

export const INTENT_STAGES = {
  INTENT_NONE: [0, 'None'],
  INTENT_INCUBATE: [7, 'Start incubating'], // Start incubating
  INTENT_IMPLEMENT: [1, 'Start prototyping'], // Start prototyping
  INTENT_EXPERIMENT: [2, 'Dev trials'], // Dev trials
  INTENT_IMPLEMENT_SHIP: [4, 'Evaluate readiness to ship'], // Eval readiness to ship
  INTENT_EXTEND_TRIAL: [3, 'Origin Trial'], // Origin trials
  INTENT_SHIP: [5, 'Prepare to ship'], // Prepare to ship
  INTENT_REMOVED: [6, 'Removed'],
  INTENT_SHIPPED: [8, 'Shipped'],
  INTENT_PARKED: [9, 'Parked'],
  INTENT_ROLLOUT: [10, 'Rollout'],
};

// Every mutable field that exists on the Stage entity and every key
// in MilestoneSet.MILESTONE_FIELD_MAPPING should be listed here.
export const STAGE_SPECIFIC_FIELDS = new Set([
  // Milestone fields.
  'shipped_milestone',
  'shipped_android_milestone',
  'shipped_ios_milestone',
  'shipped_webview_milestone',
  'ot_milestone_desktop_start',
  'ot_milestone_desktop_end',
  'ot_milestone_android_start',
  'ot_milestone_android_end',
  'ot_milestone_ios_start',
  'ot_milestone_ios_end',
  'ot_milestone_webview_start',
  'ot_milestone_webview_end',
  'dt_milestone_desktop_start',
  'dt_milestone_android_start',
  'dt_milestone_ios_start',
  'dt_milestone_webview_start',
  'extension_desktop_last',
  'extension_android_last',
  'extension_webview_last',

  // Intent fields.
  'intent_to_implement_url',
  'intent_to_ship_url',
  'intent_to_experiment_url',
  'intent_to_extend_experiment_url',

  // Misc fields.
  'origin_trial_feedback_url',
  'finch_url',
  'experiment_goals',
  'experiment_risks',
  'experiment_extension_reason',
  'rollout_milestone',
  'rollout_platforms',
  'rollout_details',
  'enterprise_policies',
  'ready_for_trial_url',
]);

export const DEPRECATED_FIELDS = new Set([
  'experiment_timeline',
  'i2e_lgtms',
  'i2s_lgtms',
  'r4dt_lgtms',
  'standardization',
]);


export const GATE_TYPES = {
  API_PROTOTYPE: 1,
  API_ORIGIN_TRIAL: 2,
  API_EXTEND_ORIGIN_TRIAL: 3,
  API_SHIP: 4,
  PRIVACY_ORIGIN_TRIAL: 32,
  PRIVACY_SHIP: 34,
  SECURITY_ORIGIN_TRIAL: 42,
  SECURITY_SHIP: 44,

  ENTERPRISE_SHIP: 54,
  DEBUGGABILITY_ORIGIN_TRIAL: 62,
  DEBUGGABILITY_SHIP: 64,
  TESTING_SHIP: 74,
};

export const GATE_TEAM_ORDER = [
  'Privacy', 'Security', 'Enterprise', 'Debuggability',
  'Testing', 'API Owners'];


export const OT_MILESTONE_END_FIELDS = {
  'ot_milestone_desktop_end': 'desktop_last',
  'ot_milestone_android_end': 'android_last',
  'ot_milestone_webview_end': 'webview_last',
};

export const IMPLEMENTATION_STATUS = {
  NO_ACTIVE_DEV: [1, 'No active development'],
  PROPOSED: [2, 'Proposed'],
  IN_DEVELOPMENT: [3, 'In development'],
  BEHIND_A_FLAG: [4, 'In developer trial (Behind a flag)'],
  ENABLED_BY_DEFAULT: [5, 'Enabled by default'],
  DEPRECATED: [6, 'Deprecated'],
  REMOVED: [7, 'Removed'],
  ORIGIN_TRIAL: [8, 'Origin trial'],
  INTERVENTION: [9, 'Browser Intervention'],
  ON_HOLD: [10, 'On hold'],
  NO_LONGER_PURSUING: [1000, 'No longer pursuing'],
};

export const STANDARD_MATURITY_CHOICES = {
  // No text for UNSET_STD==0. One of the values below will be set on first edit.
  UNKNOWN_STD: [1, 'Unknown standards status - check spec link for status'],
  PROPOSAL_STD: [2, 'Proposal in a personal repository, no adoption from community'],
  INCUBATION_STD: [3, 'Specification being incubated in a Community Group'],
  WORKINGDRAFT_STD: [4, 'Specification currently under development in a Working Group'],
  STANDARD_STD: [5, 'Final published standard: Recommendation, Living Standard, ' +
      'Candidate Recommendation, or similar final form'],
};

// Status for security and privacy reviews.
export const REVIEW_STATUS_CHOICES = {
  REVIEW_PENDING: [1, 'Pending'],
  REVIEW_ISSUES_OPEN: [2, 'Issues open'],
  REVIEW_ISSUES_ADDRESSED: [3, 'Issues addressed'],
  REVIEW_NA: [4, 'Not applicable'],
};

// Signals from other implementations in an intent-to-ship
// SHIPPED = 1
// IN_DEV = 2
// PUBLIC_SUPPORT = 3
// MIXED_SIGNALS = 4 # Deprecated
// NO_PUBLIC_SIGNALS = 5
// PUBLIC_SKEPTICISM = 6 # Deprecated
// OPPOSED = 7
// NEUTRAL = 8
// SIGNALS_NA = 9
// GECKO_UNDER_CONSIDERATION = 10
// GECKO_IMPORTANT = 11
// GECKO_WORTH_PROTOTYPING = 12
// GECKO_NONHARMFUL = 13
// GECKO_DEFER = 14
// GECKO_HARMFUL = 15

export const VENDOR_VIEWS_COMMON = {
  SHIPPED: [1, 'Shipped/Shipping'],
  IN_DEV: [2, 'In development'],
  PUBLIC_SUPPORT: [3, 'Positive'],
  NO_PUBLIC_SIGNALS: [5, 'No signal'],
  OPPOSED: [7, 'Negative'],
  NEUTRAL: [8, 'Neutral'],
  SIGNALS_NA: [9, 'N/A'],
};

export const VENDOR_VIEWS_GECKO = {
  ...VENDOR_VIEWS_COMMON,
  GECKO_UNDER_CONSIDERATION: [10, 'Under consideration'],
  GECKO_IMPORTANT: [11, 'Important'],
  GECKO_WORTH_PROTOTYPING: [12, 'Worth prototyping'],
  GECKO_NONHARMFUL: [13, 'Non-harmful'],
  GECKO_DEFER: [14, 'Defer'],
  GECKO_HARMFUL: [15, 'Harmful'],
};

export const WEB_DEV_VIEWS = {
  DEV_STRONG_POSITIVE: [1, 'Strongly positive'],
  DEV_POSITIVE: [2, 'Positive'],
  DEV_MIXED_SIGNALS: [3, 'Mixed signals'],
  DEV_NO_SIGNALS: [4, 'No signals'],
  DEV_NEGATIVE: [5, 'Negative'],
  DEV_STRONG_NEGATIVE: [6, 'Strongly negative'],
};
