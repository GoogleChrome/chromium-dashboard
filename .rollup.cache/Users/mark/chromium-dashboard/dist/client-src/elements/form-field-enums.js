// The following objects define the list of options for select fields.
// Since the order of appearance of object properties is preserved,
// we can use this same order as the order of the select options.
// The value of each property, [intValue, stringLabel], is used
// for the option value and label.
var _a, _b;
import { __assign } from "tslib";
export var FEATURE_CATEGORIES = {
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
    IWA: [22, 'Isolated Web Apps-specific API'],
};
export var ENTERPRISE_FEATURE_CATEGORIES = {
    SECURITYANDPRIVACY: [1, 'Security / Privacy'],
    USERPRODUCTIVITYANDAPPS: [2, 'User Productivity / Apps'],
    MANAGEMENT: [3, 'Management'],
};
export var ENTERPRISE_FEATURE_CATEGORIES_DISPLAYNAME = {
    1: 'Security/Privacy', // SECURITYANDPRIVACY
    2: 'User Productivity/Apps', // USERPRODUCTIVITYANDAPPS
    3: 'Management', // MANAGEMENT
};
export var PLATFORM_CATEGORIES = {
    PLATFORM_ANDROID: [1, 'Android'],
    PLATFORM_IOS: [2, 'iOS'],
    PLATFORM_CHROMEOS: [3, 'ChromeOS'],
    PLATFORM_LACROS: [4, 'LaCrOS'],
    PLATFORM_LINUX: [5, 'Linux'],
    PLATFORM_MAC: [6, 'Mac'],
    PLATFORM_WINDOWS: [7, 'Windows'],
    PLATFORM_FUCHSIA: [8, 'Fuchsia'],
};
export var PLATFORMS_DISPLAYNAME = {
    1: 'Android', // PLATFORM_ANDROID
    2: 'iOS', // PLATFORM_IOS
    3: 'ChromeOS', // PLATFORM_CHROMEOS
    4: 'LaCrOS', // PLATFORM_LACROS
    5: 'Linux', // PLATFORM_LINUX
    6: 'Mac', // PLATFORM_MAC
    7: 'Windows', // PLATFORM_WINDOWS
    8: 'Fuchsia', // PLATFORM_FUCHSIA
};
export var ENTERPRISE_IMPACT_DISPLAYNAME = {
    1: 'None', // IMPACT_NONE
    2: 'Low', // IMPACT_LOW
    3: 'Medium', // IMPACT_MEDIUM
    4: 'High', // IMPACT_HIGH
};
export var ENTERPRISE_IMPACT = {
    IMPACT_NONE: [1, 'None'],
    IMPACT_LOW: [2, 'Low'],
    IMPACT_MEDIUM: [3, 'Medium'],
    IMPACT_HIGH: [4, 'High'],
};
export var ROLLOUT_IMPACT = {
    IMPACT_LOW: [1, 'Low'],
    IMPACT_MEDIUM: [2, 'Medium'],
    IMPACT_HIGH: [3, 'High'],
};
export var ROLLOUT_IMPACT_DISPLAYNAME = {
    1: 'Low', // IMPACT_LOW
    2: 'Medium', // IMPACT_MEDIUM
    3: 'High', // IMPACT_HIGH
};
// FEATURE_TYPES object is organized as [intValue, stringLabel, description],
// the descriptions are used only for the descriptions of feature_type_radio_group
export var FEATURE_TYPES_WITHOUT_ENTERPRISE = {
    FEATURE_TYPE_INCUBATE_ID: [
        0,
        'New feature incubation',
        'When building new features, we follow a process that emphasizes engagement ' +
            'with the WICG and other stakeholders early.',
    ],
    FEATURE_TYPE_EXISTING_ID: [
        1,
        'Existing feature implementation',
        'If there is already an agreed specification, work may quickly start on ' +
            'implementation and origin trials.',
    ],
    FEATURE_TYPE_CODE_CHANGE_ID: [
        2,
        'Web developer-facing change to existing code',
        'Not common.  Track a code change that does not change any API and has ' +
            'very low interoperability risk, but might be noticed by web developers.' +
            'This type of feature entry can be referenced from a PSA immediately.',
    ],
    FEATURE_TYPE_DEPRECATION_ID: [
        3,
        'Feature deprecation',
        'Deprecate and remove an old feature.',
    ],
};
export var FEATURE_TYPES = __assign(__assign({}, FEATURE_TYPES_WITHOUT_ENTERPRISE), { FEATURE_TYPE_ENTERPRISE_ID: [
        4,
        'New Feature or removal affecting enterprises',
        'For features or changes that need to be communicated to enterprises or schools.',
    ] });
// ***********************************************************************
// Stage type values for each process. Even though some of the stages
// in these processes are similar to each other, they have distinct enum
// values so that they can have different gates.
// *********************************************************************
// For incubating new standard features: the "blink" process.
export var STAGE_BLINK_INCUBATE = 110;
export var STAGE_BLINK_PROTOTYPE = 120;
export var STAGE_BLINK_DEV_TRIAL = 130;
export var STAGE_BLINK_EVAL_READINESS = 140;
export var STAGE_BLINK_ORIGIN_TRIAL = 150;
export var STAGE_BLINK_EXTEND_ORIGIN_TRIAL = 151;
export var STAGE_BLINK_SHIPPING = 160;
// Note: We might define post-ship support stage(s) later.
// For implementing existing standards: the "fast track" process.
export var STAGE_FAST_PROTOTYPE = 220;
export var STAGE_FAST_DEV_TRIAL = 230;
export var STAGE_FAST_ORIGIN_TRIAL = 250;
export var STAGE_FAST_EXTEND_ORIGIN_TRIAL = 251;
export var STAGE_FAST_SHIPPING = 260;
// For developer-facing code changes not impacting a standard: the "PSA" process.
export var STAGE_PSA_IMPLEMENT_FIELDS = 320;
export var STAGE_PSA_DEV_TRIAL = 330;
export var STAGE_PSA_SHIPPING = 360;
// For deprecating a feature: the "DEP" process.
export var STAGE_DEP_PLAN = 410;
export var STAGE_DEP_DEV_TRIAL = 430;
export var STAGE_DEP_DEPRECATION_TRIAL = 450;
export var STAGE_DEP_EXTEND_DEPRECATION_TRIAL = 451;
export var STAGE_DEP_SHIPPING = 460;
// const STAGE_DEP_REMOVE_CODE = 470;
// Note STAGE_* enum values 500-999 are reseverd for future WP processes.
// Define enterprise feature processes.
// Note: This stage can be added to any feature that is following any process.
export var STAGE_ENT_ROLLOUT = 1061;
export var STAGE_ENT_SHIPPED = 1070;
export var STAGE_TYPES_DEV_TRIAL = new Set([
    STAGE_BLINK_DEV_TRIAL,
    STAGE_FAST_DEV_TRIAL,
    STAGE_PSA_DEV_TRIAL,
    STAGE_DEP_DEV_TRIAL,
]);
export var STAGE_TYPES_ORIGIN_TRIAL = new Set([
    STAGE_BLINK_ORIGIN_TRIAL,
    STAGE_FAST_ORIGIN_TRIAL,
    STAGE_DEP_DEPRECATION_TRIAL,
]);
export var STAGE_TYPES_SHIPPING = new Set([
    STAGE_BLINK_SHIPPING,
    STAGE_FAST_SHIPPING,
    STAGE_PSA_SHIPPING,
    STAGE_DEP_SHIPPING,
]);
// key: Origin trial stage types,
// value: extension stage type associated with the origin trial type.
export var OT_EXTENSION_STAGE_MAPPING = (_a = {},
    _a[STAGE_BLINK_ORIGIN_TRIAL] = STAGE_BLINK_EXTEND_ORIGIN_TRIAL,
    _a[STAGE_FAST_ORIGIN_TRIAL] = STAGE_FAST_EXTEND_ORIGIN_TRIAL,
    _a[STAGE_DEP_DEPRECATION_TRIAL] = STAGE_DEP_EXTEND_DEPRECATION_TRIAL,
    _a);
export var OT_EXTENSION_STAGE_TYPES = new Set([
    STAGE_BLINK_EXTEND_ORIGIN_TRIAL,
    STAGE_FAST_EXTEND_ORIGIN_TRIAL,
    STAGE_DEP_EXTEND_DEPRECATION_TRIAL,
]);
export var STAGE_SHORT_NAMES = (_b = {},
    _b[STAGE_BLINK_INCUBATE] = 'Incubate',
    _b[STAGE_BLINK_PROTOTYPE] = 'Prototype',
    _b[STAGE_BLINK_DEV_TRIAL] = 'DevTrial',
    _b[STAGE_BLINK_EVAL_READINESS] = 'Eval readiness',
    _b[STAGE_BLINK_ORIGIN_TRIAL] = 'OT',
    _b[STAGE_BLINK_EXTEND_ORIGIN_TRIAL] = 'Extend OT',
    _b[STAGE_BLINK_SHIPPING] = 'Ship',
    _b[STAGE_FAST_PROTOTYPE] = 'Prototype',
    _b[STAGE_FAST_DEV_TRIAL] = 'DevTrial',
    _b[STAGE_FAST_ORIGIN_TRIAL] = 'OT',
    _b[STAGE_FAST_EXTEND_ORIGIN_TRIAL] = 'Extend OT',
    _b[STAGE_FAST_SHIPPING] = 'Ship',
    _b[STAGE_PSA_IMPLEMENT_FIELDS] = 'Implement',
    _b[STAGE_PSA_DEV_TRIAL] = 'DevTrial',
    _b[STAGE_PSA_SHIPPING] = 'Ship',
    _b[STAGE_DEP_PLAN] = 'Plan',
    _b[STAGE_DEP_DEV_TRIAL] = 'DevTrial',
    _b[STAGE_DEP_DEPRECATION_TRIAL] = 'Dep Trial',
    _b[STAGE_DEP_EXTEND_DEPRECATION_TRIAL] = 'Extend Dep Trial',
    _b[STAGE_DEP_SHIPPING] = 'Ship',
    _b[STAGE_ENT_ROLLOUT] = 'Rollout',
    _b[STAGE_ENT_SHIPPED] = 'Ship',
    _b);
export var INTENT_STAGES = {
    INTENT_NONE: [0, 'None'],
    INTENT_INCUBATE: [7, 'Start incubating'], // Start incubating
    INTENT_IMPLEMENT: [1, 'Start prototyping'], // Start prototyping
    INTENT_EXPERIMENT: [2, 'Dev trials'], // Dev trials
    INTENT_IMPLEMENT_SHIP: [4, 'Evaluate readiness to ship'], // Eval readiness to ship
    INTENT_ORIGIN_TRIAL: [3, 'Origin Trial'], // Origin trials
    INTENT_EXTEND_ORIGIN_TRIAL: [11, 'Extend Trial'],
    INTENT_SHIP: [5, 'Prepare to ship'], // Prepare to ship
    INTENT_REMOVED: [6, 'Removed'],
    INTENT_SHIPPED: [8, 'Shipped'],
    INTENT_PARKED: [9, 'Parked'],
    INTENT_ROLLOUT: [10, 'Rollout'],
};
export var DT_MILESTONE_FIELDS = new Set([
    'dt_milestone_desktop_start',
    'dt_milestone_android_start',
    'dt_milestone_ios_start',
    'dt_milestone_webview_start',
]);
export var OT_MILESTONE_START_FIELDS = new Set([
    'ot_milestone_desktop_start',
    'ot_milestone_android_start',
    'ot_milestone_webview_start',
    // 'ot_milestone_ios_start',
]);
export var SHIPPED_MILESTONE_FIELDS = new Set([
    'shipped_milestone',
    'shipped_android_milestone',
    'shipped_ios_milestone',
    'shipped_webview_milestone',
]);
// Every mutable field that exists on the Stage entity and every key
// in MilestoneSet.MILESTONE_FIELD_MAPPING should be listed here.
export var STAGE_SPECIFIC_FIELDS = new Set([
    // Milestone fields.
    'shipped_milestone',
    'shipped_android_milestone',
    'shipped_ios_milestone',
    'shipped_webview_milestone',
    'ot_milestone_desktop_start',
    'ot_milestone_desktop_end',
    'ot_milestone_android_start',
    'ot_milestone_android_end',
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
    'intent_thread_url',
    'ot_creation__intent_to_experiment_url',
    'ot_extension__intent_to_extend_experiment_url',
    'r4dt_url',
    // Misc fields.
    'display_name',
    'ot_display_name',
    'ot_owner_email',
    'origin_trial_feedback_url',
    'ot_chromium_trial_name',
    'ot_description',
    'ot_emails',
    'ot_feedback_submission_url',
    'ot_request_note',
    'ot_webfeature_use_counter',
    'ot_documentation_url',
    'ot_is_deprecation_trial',
    'ot_has_third_party_support',
    'ot_is_critical_trial',
    'ot_creation__milestone_desktop_first',
    'ot_creation__milestone_desktop_last',
    'ot_extension__milestone_desktop_last',
    'ot_require_approvals',
    'ot_approval_buganizer_component',
    'ot_approval_group_email',
    'ot_approval_criteria_url',
    'finch_url',
    'experiment_goals',
    'experiment_risks',
    'experiment_extension_reason',
    'rollout_impact',
    'rollout_milestone',
    'rollout_platforms',
    'rollout_details',
    'enterprise_policies',
    'announcement_url',
]);
// Mapping of specific field names to their more generic stage names.
export var STAGE_FIELD_NAME_MAPPING = {
    // Milestone fields.
    shipped_milestone: 'desktop_first',
    shipped_android_milestone: 'android_first',
    shipped_ios_milestone: 'ios_first',
    shipped_webview_milestone: 'webview_first',
    ot_milestone_desktop_start: 'desktop_first',
    ot_milestone_desktop_end: 'desktop_last',
    ot_milestone_android_start: 'android_first',
    ot_milestone_android_end: 'android_last',
    ot_milestone_webview_start: 'webview_first',
    ot_milestone_webview_end: 'webview_last',
    ot_creation__milestone_desktop_first: 'desktop_first',
    ot_creation__milestone_desktop_last: 'desktop_last',
    ot_extension__milestone_desktop_last: 'desktop_last',
    dt_milestone_desktop_start: 'desktop_first',
    dt_milestone_android_start: 'android_first',
    dt_milestone_ios_start: 'ios_first',
    dt_milestone_webview_start: 'webview_first',
    extension_desktop_last: 'desktop_last',
    extension_android_last: 'android_last',
    extension_webview_last: 'webview_last',
    // Intent fields.
    intent_to_implement_url: 'intent_thread_url',
    intent_to_ship_url: 'intent_thread_url',
    intent_to_experiment_url: 'intent_thread_url',
    intent_to_extend_experiment_url: 'intent_thread_url',
    ot_creation__intent_to_experiment_url: 'intent_thread_url',
    ot_extension__intent_to_extend_experiment_url: 'intent_thread_url',
    r4dt_url: 'intent_thread_url',
};
export var DEPRECATED_FIELDS = new Set([
    'experiment_timeline',
    'i2e_lgtms',
    'i2s_lgtms',
    'r4dt_lgtms',
    'standardization',
]);
export var GATE_TYPES = {
    API_PROTOTYPE: 1,
    API_ORIGIN_TRIAL: 2,
    API_EXTEND_ORIGIN_TRIAL: 3,
    API_SHIP: 4,
    API_PLAN: 5,
    PRIVACY_ORIGIN_TRIAL: 32,
    PRIVACY_SHIP: 34,
    // Not needed: PRIVACY_PLAN: 35,
    SECURITY_ORIGIN_TRIAL: 42,
    SECURITY_SHIP: 44,
    // Not needed: SECURITY_PLAN: 45,
    ENTERPRISE_SHIP: 54,
    ENTERPRISE_PLAN: 55,
    DEBUGGABILITY_ORIGIN_TRIAL: 62,
    DEBUGGABILITY_SHIP: 64,
    DEBUGGABILITY_PLAN: 65,
    TESTING_SHIP: 74,
    TESTING_PLAN: 75,
};
export var GATE_PREPARING = 0;
export var GATE_REVIEW_REQUESTED = 2;
export var GATE_NA_REQUESTED = 9;
export var VOTE_OPTIONS = {
    NO_RESPONSE: [7, 'No response'],
    NA: [1, 'N/a or Ack'],
    REVIEW_STARTED: [3, 'Review started'],
    NEEDS_WORK: [4, 'Needs work'],
    INTERNAL_REVIEW: [8, 'Internal review'],
    APPROVED: [5, 'Approved'],
    DENIED: [6, 'Denied'],
};
export var GATE_ACTIVE_REVIEW_STATES = [
    GATE_REVIEW_REQUESTED,
    VOTE_OPTIONS.REVIEW_STARTED[0],
    VOTE_OPTIONS.NEEDS_WORK[0],
    VOTE_OPTIONS.INTERNAL_REVIEW[0],
    GATE_NA_REQUESTED,
];
export var GATE_FINISHED_REVIEW_STATES = [
    VOTE_OPTIONS.NA[0],
    VOTE_OPTIONS.APPROVED[0],
    VOTE_OPTIONS.DENIED[0],
];
export var GATE_TEAM_ORDER = [
    'Privacy',
    'Security',
    'Enterprise',
    'Debuggability',
    'Testing',
    'API Owners',
];
export var OT_MILESTONE_END_FIELDS = {
    ot_milestone_desktop_end: 'desktop_last',
    ot_milestone_android_end: 'android_last',
    ot_milestone_webview_end: 'webview_last',
};
export var IMPLEMENTATION_STATUS = {
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
export var STANDARD_MATURITY_CHOICES = {
    // No text for UNSET_STD==0. One of the values below will be set on first edit.
    UNKNOWN_STD: [1, 'Unknown standards status - check spec link for status'],
    PROPOSAL_STD: [
        2,
        'Proposal in a personal repository, no adoption from community',
    ],
    INCUBATION_STD: [3, 'Specification being incubated in a Community Group'],
    WORKINGDRAFT_STD: [
        4,
        'Specification currently under development in a Working Group',
    ],
    STANDARD_STD: [
        5,
        'Final published standard: Recommendation, Living Standard, ' +
            'Candidate Recommendation, or similar final form',
    ],
};
// Status for security and privacy reviews.
export var REVIEW_STATUS_CHOICES = {
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
// GECKO_IMPORTANT = 11 # Deprecated; use PUBLIC_SUPPORT
// GECKO_WORTH_PROTOTYPING = 12 # Deprecated; use PUBLIC_SUPPORT
// GECKO_NONHARMFUL = 13 # Deprecated; use NEUTRAL
// GECKO_DEFER = 14
// GECKO_HARMFUL = 15 # Deprecated; use OPPOSED
export var VENDOR_VIEWS_COMMON = {
    SHIPPED: [1, 'Shipped/Shipping'],
    IN_DEV: [2, 'In development'],
    PUBLIC_SUPPORT: [3, 'Positive'],
    NO_PUBLIC_SIGNALS: [5, 'No signal'],
    OPPOSED: [7, 'Negative'],
    NEUTRAL: [8, 'Neutral'],
    SIGNALS_NA: [9, 'N/A'],
};
export var VENDOR_VIEWS_GECKO = {
    NO_PUBLIC_SIGNALS: [5, 'No signal'],
    SIGNALS_NA: [9, 'N/A'],
    GECKO_UNDER_CONSIDERATION: [10, 'Under consideration'],
    GECKO_DEFER: [14, 'Defer'],
    PUBLIC_SUPPORT: [3, 'Positive'],
    OPPOSED: [7, 'Negative'],
    NEUTRAL: [8, 'Neutral'],
    SHIPPED: [1, 'Shipped/Shipping'],
};
export var WEB_DEV_VIEWS = {
    DEV_STRONG_POSITIVE: [1, 'Strongly positive'],
    DEV_POSITIVE: [2, 'Positive'],
    DEV_MIXED_SIGNALS: [3, 'Mixed signals'],
    DEV_NO_SIGNALS: [4, 'No signals'],
    DEV_NEGATIVE: [5, 'Negative'],
    DEV_STRONG_NEGATIVE: [6, 'Strongly negative'],
};
//# sourceMappingURL=form-field-enums.js.map