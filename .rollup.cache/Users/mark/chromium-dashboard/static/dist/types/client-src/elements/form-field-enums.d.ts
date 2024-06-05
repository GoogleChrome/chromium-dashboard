export namespace FEATURE_CATEGORIES {
    let WEBCOMPONENTS: (string | number)[];
    let MISC: (string | number)[];
    let SECURITY: (string | number)[];
    let MULTIMEDIA: (string | number)[];
    let DOM: (string | number)[];
    let FILE: (string | number)[];
    let OFFLINE: (string | number)[];
    let DEVICE: (string | number)[];
    let COMMUNICATION: (string | number)[];
    let JAVASCRIPT: (string | number)[];
    let NETWORKING: (string | number)[];
    let INPUT: (string | number)[];
    let PERFORMANCE: (string | number)[];
    let GRAPHICS: (string | number)[];
    let CSS: (string | number)[];
    let HOUDINI: (string | number)[];
    let SERVICEWORKER: (string | number)[];
    let WEBRTC: (string | number)[];
    let LAYERED: (string | number)[];
    let WEBASSEMBLY: (string | number)[];
    let CAPABILITIES: (string | number)[];
    let IWA: (string | number)[];
}
export namespace ENTERPRISE_FEATURE_CATEGORIES {
    let SECURITYANDPRIVACY: (string | number)[];
    let USERPRODUCTIVITYANDAPPS: (string | number)[];
    let MANAGEMENT: (string | number)[];
}
export const ENTERPRISE_FEATURE_CATEGORIES_DISPLAYNAME: {
    1: string;
    2: string;
    3: string;
};
export namespace PLATFORM_CATEGORIES {
    let PLATFORM_ANDROID: (string | number)[];
    let PLATFORM_IOS: (string | number)[];
    let PLATFORM_CHROMEOS: (string | number)[];
    let PLATFORM_LACROS: (string | number)[];
    let PLATFORM_LINUX: (string | number)[];
    let PLATFORM_MAC: (string | number)[];
    let PLATFORM_WINDOWS: (string | number)[];
    let PLATFORM_FUCHSIA: (string | number)[];
}
export const PLATFORMS_DISPLAYNAME: {
    1: string;
    2: string;
    3: string;
    4: string;
    5: string;
    6: string;
    7: string;
    8: string;
};
export const ENTERPRISE_IMPACT_DISPLAYNAME: {
    1: string;
    2: string;
    3: string;
    4: string;
};
export namespace ENTERPRISE_IMPACT {
    let IMPACT_NONE: (string | number)[];
    let IMPACT_LOW: (string | number)[];
    let IMPACT_MEDIUM: (string | number)[];
    let IMPACT_HIGH: (string | number)[];
}
export namespace ROLLOUT_IMPACT {
    let IMPACT_LOW_1: (string | number)[];
    export { IMPACT_LOW_1 as IMPACT_LOW };
    let IMPACT_MEDIUM_1: (string | number)[];
    export { IMPACT_MEDIUM_1 as IMPACT_MEDIUM };
    let IMPACT_HIGH_1: (string | number)[];
    export { IMPACT_HIGH_1 as IMPACT_HIGH };
}
export const ROLLOUT_IMPACT_DISPLAYNAME: {
    1: string;
    2: string;
    3: string;
};
export namespace FEATURE_TYPES_WITHOUT_ENTERPRISE {
    let FEATURE_TYPE_INCUBATE_ID: (string | number)[];
    let FEATURE_TYPE_EXISTING_ID: (string | number)[];
    let FEATURE_TYPE_CODE_CHANGE_ID: (string | number)[];
    let FEATURE_TYPE_DEPRECATION_ID: (string | number)[];
}
export namespace FEATURE_TYPES {
    let FEATURE_TYPE_ENTERPRISE_ID: (string | number)[];
}
export const STAGE_BLINK_INCUBATE: 110;
export const STAGE_BLINK_PROTOTYPE: 120;
export const STAGE_BLINK_DEV_TRIAL: 130;
export const STAGE_BLINK_EVAL_READINESS: 140;
export const STAGE_BLINK_ORIGIN_TRIAL: 150;
export const STAGE_BLINK_EXTEND_ORIGIN_TRIAL: 151;
export const STAGE_BLINK_SHIPPING: 160;
export const STAGE_FAST_PROTOTYPE: 220;
export const STAGE_FAST_DEV_TRIAL: 230;
export const STAGE_FAST_ORIGIN_TRIAL: 250;
export const STAGE_FAST_EXTEND_ORIGIN_TRIAL: 251;
export const STAGE_FAST_SHIPPING: 260;
export const STAGE_PSA_IMPLEMENT_FIELDS: 320;
export const STAGE_PSA_DEV_TRIAL: 330;
export const STAGE_PSA_SHIPPING: 360;
export const STAGE_DEP_PLAN: 410;
export const STAGE_DEP_DEV_TRIAL: 430;
export const STAGE_DEP_DEPRECATION_TRIAL: 450;
export const STAGE_DEP_EXTEND_DEPRECATION_TRIAL: 451;
export const STAGE_DEP_SHIPPING: 460;
export const STAGE_ENT_ROLLOUT: 1061;
export const STAGE_ENT_SHIPPED: 1070;
export const STAGE_TYPES_DEV_TRIAL: Set<number>;
export const STAGE_TYPES_ORIGIN_TRIAL: Set<number>;
export const STAGE_TYPES_SHIPPING: Set<number>;
export const OT_EXTENSION_STAGE_MAPPING: {
    150: number;
    250: number;
    450: number;
};
export const OT_EXTENSION_STAGE_TYPES: Set<number>;
export const STAGE_SHORT_NAMES: {
    110: string;
    120: string;
    130: string;
    140: string;
    150: string;
    151: string;
    160: string;
    220: string;
    230: string;
    250: string;
    251: string;
    260: string;
    320: string;
    330: string;
    360: string;
    410: string;
    430: string;
    450: string;
    451: string;
    460: string;
    1061: string;
    1070: string;
};
export namespace INTENT_STAGES {
    let INTENT_NONE: (string | number)[];
    let INTENT_INCUBATE: (string | number)[];
    let INTENT_IMPLEMENT: (string | number)[];
    let INTENT_EXPERIMENT: (string | number)[];
    let INTENT_IMPLEMENT_SHIP: (string | number)[];
    let INTENT_ORIGIN_TRIAL: (string | number)[];
    let INTENT_EXTEND_ORIGIN_TRIAL: (string | number)[];
    let INTENT_SHIP: (string | number)[];
    let INTENT_REMOVED: (string | number)[];
    let INTENT_SHIPPED: (string | number)[];
    let INTENT_PARKED: (string | number)[];
    let INTENT_ROLLOUT: (string | number)[];
}
export const DT_MILESTONE_FIELDS: Set<string>;
export const OT_MILESTONE_START_FIELDS: Set<string>;
export const SHIPPED_MILESTONE_FIELDS: Set<string>;
export const STAGE_SPECIFIC_FIELDS: Set<string>;
export namespace STAGE_FIELD_NAME_MAPPING {
    let shipped_milestone: string;
    let shipped_android_milestone: string;
    let shipped_ios_milestone: string;
    let shipped_webview_milestone: string;
    let ot_milestone_desktop_start: string;
    let ot_milestone_desktop_end: string;
    let ot_milestone_android_start: string;
    let ot_milestone_android_end: string;
    let ot_milestone_webview_start: string;
    let ot_milestone_webview_end: string;
    let ot_creation__milestone_desktop_first: string;
    let ot_creation__milestone_desktop_last: string;
    let ot_extension__milestone_desktop_last: string;
    let dt_milestone_desktop_start: string;
    let dt_milestone_android_start: string;
    let dt_milestone_ios_start: string;
    let dt_milestone_webview_start: string;
    let extension_desktop_last: string;
    let extension_android_last: string;
    let extension_webview_last: string;
    let intent_to_implement_url: string;
    let intent_to_ship_url: string;
    let intent_to_experiment_url: string;
    let intent_to_extend_experiment_url: string;
    let ot_creation__intent_to_experiment_url: string;
    let ot_extension__intent_to_extend_experiment_url: string;
    let r4dt_url: string;
}
export const DEPRECATED_FIELDS: Set<string>;
export namespace GATE_TYPES {
    let API_PROTOTYPE: number;
    let API_ORIGIN_TRIAL: number;
    let API_EXTEND_ORIGIN_TRIAL: number;
    let API_SHIP: number;
    let API_PLAN: number;
    let PRIVACY_ORIGIN_TRIAL: number;
    let PRIVACY_SHIP: number;
    let SECURITY_ORIGIN_TRIAL: number;
    let SECURITY_SHIP: number;
    let ENTERPRISE_SHIP: number;
    let ENTERPRISE_PLAN: number;
    let DEBUGGABILITY_ORIGIN_TRIAL: number;
    let DEBUGGABILITY_SHIP: number;
    let DEBUGGABILITY_PLAN: number;
    let TESTING_SHIP: number;
    let TESTING_PLAN: number;
}
export const GATE_PREPARING: 0;
export const GATE_REVIEW_REQUESTED: 2;
export const GATE_NA_REQUESTED: 9;
export namespace VOTE_OPTIONS {
    let NO_RESPONSE: (string | number)[];
    let NA: (string | number)[];
    let REVIEW_STARTED: (string | number)[];
    let NEEDS_WORK: (string | number)[];
    let INTERNAL_REVIEW: (string | number)[];
    let APPROVED: (string | number)[];
    let DENIED: (string | number)[];
}
export const GATE_ACTIVE_REVIEW_STATES: (string | number)[];
export const GATE_FINISHED_REVIEW_STATES: (string | number)[];
export const GATE_TEAM_ORDER: string[];
export namespace OT_MILESTONE_END_FIELDS {
    let ot_milestone_desktop_end_1: string;
    export { ot_milestone_desktop_end_1 as ot_milestone_desktop_end };
    let ot_milestone_android_end_1: string;
    export { ot_milestone_android_end_1 as ot_milestone_android_end };
    let ot_milestone_webview_end_1: string;
    export { ot_milestone_webview_end_1 as ot_milestone_webview_end };
}
export namespace IMPLEMENTATION_STATUS {
    let NO_ACTIVE_DEV: (string | number)[];
    let PROPOSED: (string | number)[];
    let IN_DEVELOPMENT: (string | number)[];
    let BEHIND_A_FLAG: (string | number)[];
    let ENABLED_BY_DEFAULT: (string | number)[];
    let DEPRECATED: (string | number)[];
    let REMOVED: (string | number)[];
    let ORIGIN_TRIAL: (string | number)[];
    let INTERVENTION: (string | number)[];
    let ON_HOLD: (string | number)[];
    let NO_LONGER_PURSUING: (string | number)[];
}
export namespace STANDARD_MATURITY_CHOICES {
    let UNKNOWN_STD: (string | number)[];
    let PROPOSAL_STD: (string | number)[];
    let INCUBATION_STD: (string | number)[];
    let WORKINGDRAFT_STD: (string | number)[];
    let STANDARD_STD: (string | number)[];
}
export namespace REVIEW_STATUS_CHOICES {
    let REVIEW_PENDING: (string | number)[];
    let REVIEW_ISSUES_OPEN: (string | number)[];
    let REVIEW_ISSUES_ADDRESSED: (string | number)[];
    let REVIEW_NA: (string | number)[];
}
export namespace VENDOR_VIEWS_COMMON {
    let SHIPPED: (string | number)[];
    let IN_DEV: (string | number)[];
    let PUBLIC_SUPPORT: (string | number)[];
    let NO_PUBLIC_SIGNALS: (string | number)[];
    let OPPOSED: (string | number)[];
    let NEUTRAL: (string | number)[];
    let SIGNALS_NA: (string | number)[];
}
export namespace VENDOR_VIEWS_GECKO {
    let NO_PUBLIC_SIGNALS_1: (string | number)[];
    export { NO_PUBLIC_SIGNALS_1 as NO_PUBLIC_SIGNALS };
    let SIGNALS_NA_1: (string | number)[];
    export { SIGNALS_NA_1 as SIGNALS_NA };
    export let GECKO_UNDER_CONSIDERATION: (string | number)[];
    export let GECKO_DEFER: (string | number)[];
    let PUBLIC_SUPPORT_1: (string | number)[];
    export { PUBLIC_SUPPORT_1 as PUBLIC_SUPPORT };
    let OPPOSED_1: (string | number)[];
    export { OPPOSED_1 as OPPOSED };
    let NEUTRAL_1: (string | number)[];
    export { NEUTRAL_1 as NEUTRAL };
    let SHIPPED_1: (string | number)[];
    export { SHIPPED_1 as SHIPPED };
}
export namespace WEB_DEV_VIEWS {
    let DEV_STRONG_POSITIVE: (string | number)[];
    let DEV_POSITIVE: (string | number)[];
    let DEV_MIXED_SIGNALS: (string | number)[];
    let DEV_NO_SIGNALS: (string | number)[];
    let DEV_NEGATIVE: (string | number)[];
    let DEV_STRONG_NEGATIVE: (string | number)[];
}
