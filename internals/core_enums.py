# Copyright 2022 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License")
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import collections
from typing import Optional


WEBCOMPONENTS = 1
MISC = 2
SECURITY = 3
MULTIMEDIA = 4
DOM = 5
FILE = 6
OFFLINE = 7
DEVICE = 8
COMMUNICATION = 9
JAVASCRIPT = 10
NETWORKING = 11
INPUT = 12
PERFORMANCE = 13
GRAPHICS = 14
CSS = 15
HOUDINI = 16
SERVICEWORKER = 17
WEBRTC = 18
LAYERED = 19
WEBASSEMBLY = 20
CAPABILITIES = 21

FEATURE_CATEGORIES = {
  CSS: 'CSS',
  WEBCOMPONENTS: 'Web Components',
  MISC: 'Miscellaneous',
  SECURITY: 'Security',
  MULTIMEDIA: 'Multimedia',
  DOM: 'DOM',
  FILE: 'File APIs',
  OFFLINE: 'Offline / Storage',
  DEVICE: 'Device',
  COMMUNICATION: 'Realtime / Communication',
  JAVASCRIPT: 'JavaScript',
  NETWORKING: 'Network / Connectivity',
  INPUT: 'User input',
  PERFORMANCE: 'Performance',
  GRAPHICS: 'Graphics',
  HOUDINI: 'Houdini',
  SERVICEWORKER: 'Service Worker',
  WEBRTC: 'Web RTC',
  LAYERED: 'Layered APIs',
  WEBASSEMBLY: 'WebAssembly',
  CAPABILITIES: 'Capabilities (Fugu)'
  }

FEATURE_TYPE_INCUBATE_ID = 0
FEATURE_TYPE_EXISTING_ID = 1
FEATURE_TYPE_CODE_CHANGE_ID = 2
FEATURE_TYPE_DEPRECATION_ID = 3

FEATURE_TYPES = {
    FEATURE_TYPE_INCUBATE_ID: 'New feature incubation',
    FEATURE_TYPE_EXISTING_ID: 'Existing feature implementation',
    FEATURE_TYPE_CODE_CHANGE_ID: 'Web developer facing change to existing code',
    FEATURE_TYPE_DEPRECATION_ID: 'Feature deprecation',
}


# Intent stages and mapping from stage to stage name.
INTENT_NONE = 0
INTENT_INCUBATE = 7  # Start incubating
INTENT_IMPLEMENT = 1  # Start prototyping
INTENT_EXPERIMENT = 2  # Dev trials
INTENT_IMPLEMENT_SHIP = 4  # Eval readiness to ship
INTENT_EXTEND_TRIAL = 3  # Origin trials
INTENT_SHIP = 5  # Prepare to ship
INTENT_REMOVED = 6
INTENT_SHIPPED = 8
INTENT_PARKED = 9

INTENT_STAGES = collections.OrderedDict([
  (INTENT_NONE, 'None'),
  (INTENT_INCUBATE, 'Start incubating'),
  (INTENT_IMPLEMENT, 'Start prototyping'),
  (INTENT_EXPERIMENT, 'Dev trials'),
  (INTENT_IMPLEMENT_SHIP, 'Evaluate readiness to ship'),
  (INTENT_EXTEND_TRIAL, 'Origin Trial'),
  (INTENT_SHIP, 'Prepare to ship'),
  (INTENT_REMOVED, 'Removed'),
  (INTENT_SHIPPED, 'Shipped'),
  (INTENT_PARKED, 'Parked'),
])


# Stage_type values for each process.  Even though some of the stages
# in these processes are similar to each other, they have distinct enum
# values so that they can have different gates.

# For incubating new standard features: the "blink" process.
STAGE_BLINK_INCUBATE = 110
STAGE_BLINK_PROTOTYPE = 120
STAGE_BLINK_DEV_TRIAL = 130
STAGE_BLINK_EVAL_READINESS = 140
STAGE_BLINK_ORIGIN_TRIAL = 150
STAGE_BLINK_EXTEND_ORIGIN_TRIAL = 151
STAGE_BLINK_SHIPPING = 160
# Note: We might define post-ship support stage(s) later.

# For implementing existing standards: the "fast track" process.
STAGE_FAST_PROTOTYPE = 220
STAGE_FAST_DEV_TRIAL = 230
STAGE_FAST_ORIGIN_TRIAL = 250
STAGE_FAST_EXTEND_ORIGIN_TRIAL = 251
STAGE_FAST_SHIPPING = 260

# For developer-facing code changes not impacting a standard: the "PSA" process.
STAGE_PSA_IMPLEMENT = 320
STAGE_PSA_DEV_TRIAL = 330
STAGE_PSA_SHIPPING = 360

# For deprecating a feature: the "DEP" process.
STAGE_DEP_PLAN = 410
STAGE_DEP_DEV_TRIAL = 430
STAGE_DEP_DEPRECATION_TRIAL = 450
STAGE_DEP_EXTEND_DEPRECATION_TRIAL = 451
STAGE_DEP_SHIPPING = 460
STAGE_DEP_REMOVE_CODE = 470
# TODO(jrobbins): reverse origin trial stage?

# Note STAGE_* enum values 500-9999 are reseverd for future WP processes.

# Define enterprise feature processes.
# Note: This stage can ge added to any feature that is following any process.
STAGE_ENT_ROLLOUT = 1061

# Gate types
GATE_PROTOTYPE = 1
GATE_ORIGIN_TRIAL = 2
GATE_EXTEND_ORIGIN_TRIAL = 3
GATE_SHIP = 4

# List of (stage type, gate type) for each feature type.
STAGES_AND_GATES_BY_FEATURE_TYPE = {
    FEATURE_TYPE_INCUBATE_ID: [
        (STAGE_BLINK_INCUBATE, None),
        (STAGE_BLINK_PROTOTYPE, GATE_PROTOTYPE),
        (STAGE_BLINK_DEV_TRIAL, None),
        (STAGE_BLINK_EVAL_READINESS, None),
        (STAGE_BLINK_ORIGIN_TRIAL, GATE_ORIGIN_TRIAL),
        (STAGE_BLINK_EXTEND_ORIGIN_TRIAL, GATE_EXTEND_ORIGIN_TRIAL),
        (STAGE_BLINK_SHIPPING, GATE_SHIP)],
    FEATURE_TYPE_EXISTING_ID: [
        (STAGE_FAST_PROTOTYPE, GATE_PROTOTYPE),
        (STAGE_FAST_DEV_TRIAL, None),
        (STAGE_FAST_ORIGIN_TRIAL, GATE_ORIGIN_TRIAL),
        (STAGE_FAST_EXTEND_ORIGIN_TRIAL, GATE_EXTEND_ORIGIN_TRIAL),
        (STAGE_FAST_SHIPPING, GATE_SHIP)],
    FEATURE_TYPE_CODE_CHANGE_ID: [
        (STAGE_PSA_IMPLEMENT, None),
        (STAGE_PSA_DEV_TRIAL, None),
        (STAGE_PSA_SHIPPING, GATE_SHIP)],
    FEATURE_TYPE_DEPRECATION_ID: [
        (STAGE_DEP_PLAN, None),
        (STAGE_DEP_DEV_TRIAL, None),
        (STAGE_DEP_DEPRECATION_TRIAL, GATE_ORIGIN_TRIAL),
        (STAGE_DEP_EXTEND_DEPRECATION_TRIAL, GATE_EXTEND_ORIGIN_TRIAL),
        (STAGE_DEP_SHIPPING, GATE_SHIP),
        (STAGE_DEP_REMOVE_CODE, None)]
  }

# Prototype stage types for every feature type.
STAGE_TYPES_PROTOTYPE: dict[int, Optional[int]] = {
    FEATURE_TYPE_INCUBATE_ID: STAGE_BLINK_PROTOTYPE,
    FEATURE_TYPE_EXISTING_ID: STAGE_FAST_PROTOTYPE,
    FEATURE_TYPE_CODE_CHANGE_ID: None,
    FEATURE_TYPE_DEPRECATION_ID: None
  }
# Dev trial stage types for every feature type.
STAGE_TYPES_DEV_TRIAL: dict[int, Optional[int]] = {
    FEATURE_TYPE_INCUBATE_ID: STAGE_BLINK_DEV_TRIAL,
    FEATURE_TYPE_EXISTING_ID: STAGE_FAST_DEV_TRIAL,
    FEATURE_TYPE_CODE_CHANGE_ID: STAGE_PSA_DEV_TRIAL,
    FEATURE_TYPE_DEPRECATION_ID: STAGE_DEP_DEV_TRIAL
  }
# Origin trial stage types for every feature type.
STAGE_TYPES_ORIGIN_TRIAL: dict[int, Optional[int]] = {
    FEATURE_TYPE_INCUBATE_ID: STAGE_BLINK_ORIGIN_TRIAL,
    FEATURE_TYPE_EXISTING_ID: STAGE_FAST_ORIGIN_TRIAL,
    FEATURE_TYPE_CODE_CHANGE_ID: None,
    FEATURE_TYPE_DEPRECATION_ID: STAGE_DEP_DEPRECATION_TRIAL
  }
# Origin trial extension stage types for every feature type.
STAGE_TYPES_EXTEND_ORIGIN_TRIAL: dict[int, Optional[int]] = {
    FEATURE_TYPE_INCUBATE_ID: STAGE_BLINK_EXTEND_ORIGIN_TRIAL,
    FEATURE_TYPE_EXISTING_ID: STAGE_FAST_EXTEND_ORIGIN_TRIAL,
    FEATURE_TYPE_CODE_CHANGE_ID: None,
    FEATURE_TYPE_DEPRECATION_ID: STAGE_DEP_EXTEND_DEPRECATION_TRIAL
  }
# Shipping stage types for every feature type.
STAGE_TYPES_SHIPPING: dict[int, Optional[int]] = {
    FEATURE_TYPE_INCUBATE_ID: STAGE_BLINK_SHIPPING,
    FEATURE_TYPE_EXISTING_ID: STAGE_FAST_SHIPPING,
    FEATURE_TYPE_CODE_CHANGE_ID: STAGE_PSA_SHIPPING,
    FEATURE_TYPE_DEPRECATION_ID: STAGE_DEP_SHIPPING
  }

# Mapping of original field names to the new stage types the fields live on.
STAGE_TYPES_BY_FIELD_MAPPING: dict[str, dict[int, Optional[int]]] = {
    'finch_url': STAGE_TYPES_SHIPPING,
    'experiment_goals': STAGE_TYPES_ORIGIN_TRIAL,
    'experiment_risks': STAGE_TYPES_ORIGIN_TRIAL,
    'experiment_extension_reason': STAGE_TYPES_EXTEND_ORIGIN_TRIAL,
    'origin_trial_feedback_url': STAGE_TYPES_ORIGIN_TRIAL,
    'intent_to_implement_url': STAGE_TYPES_PROTOTYPE,
    'announcement_url': STAGE_TYPES_DEV_TRIAL,
    'intent_to_ship_url': STAGE_TYPES_SHIPPING,
    'intent_to_experiment_url': STAGE_TYPES_ORIGIN_TRIAL,
    'intent_to_extend_experiment_url': STAGE_TYPES_EXTEND_ORIGIN_TRIAL,
    'shipped_milestone': STAGE_TYPES_SHIPPING,
    'shipped_android_milestone': STAGE_TYPES_SHIPPING,
    'shipped_ios_milestone': STAGE_TYPES_SHIPPING,
    'shipped_webview_milestone': STAGE_TYPES_SHIPPING,
    'ot_milestone_desktop_start': STAGE_TYPES_ORIGIN_TRIAL,
    'ot_milestone_desktop_end': STAGE_TYPES_ORIGIN_TRIAL,
    'ot_milestone_android_start': STAGE_TYPES_ORIGIN_TRIAL,
    'ot_milestone_android_end': STAGE_TYPES_ORIGIN_TRIAL,
    'ot_milestone_ios_start': STAGE_TYPES_ORIGIN_TRIAL,
    'ot_milestone_ios_end': STAGE_TYPES_ORIGIN_TRIAL,
    'ot_milestone_webview_start': STAGE_TYPES_ORIGIN_TRIAL,
    'ot_milestone_webview_end': STAGE_TYPES_ORIGIN_TRIAL,
    'dt_milestone_desktop_start': STAGE_TYPES_DEV_TRIAL,
    'dt_milestone_android_start': STAGE_TYPES_DEV_TRIAL,
    'dt_milestone_ios_start': STAGE_TYPES_DEV_TRIAL,
    'dt_milestone_webview_start': STAGE_TYPES_DEV_TRIAL
  }

# Mapping of which stage types are associated with each gate type.
STAGE_TYPES_BY_GATE_TYPE_MAPPING: dict[int, dict[int, Optional[int]]] = {
  GATE_PROTOTYPE: STAGE_TYPES_PROTOTYPE,
  GATE_ORIGIN_TRIAL: STAGE_TYPES_ORIGIN_TRIAL,
  GATE_EXTEND_ORIGIN_TRIAL: STAGE_TYPES_EXTEND_ORIGIN_TRIAL,
  GATE_SHIP: STAGE_TYPES_SHIPPING
}

NO_ACTIVE_DEV = 1
PROPOSED = 2
IN_DEVELOPMENT = 3
BEHIND_A_FLAG = 4
ENABLED_BY_DEFAULT = 5
DEPRECATED = 6
REMOVED = 7
ORIGIN_TRIAL = 8
INTERVENTION = 9
ON_HOLD = 10
NO_LONGER_PURSUING = 1000 # ensure it is at the bottom of the list

RELEASE_IMPL_STATES = {
    BEHIND_A_FLAG, ENABLED_BY_DEFAULT,
    DEPRECATED, REMOVED, ORIGIN_TRIAL, INTERVENTION,
}

# Ordered dictionary, make sure the order of this dictionary matches that of
# the sorted list above!
IMPLEMENTATION_STATUS = collections.OrderedDict()
IMPLEMENTATION_STATUS[NO_ACTIVE_DEV] = 'No active development'
IMPLEMENTATION_STATUS[PROPOSED] = 'Proposed'
IMPLEMENTATION_STATUS[IN_DEVELOPMENT] = 'In development'
IMPLEMENTATION_STATUS[BEHIND_A_FLAG] = 'In developer trial (Behind a flag)'
IMPLEMENTATION_STATUS[ENABLED_BY_DEFAULT] = 'Enabled by default'
IMPLEMENTATION_STATUS[DEPRECATED] = 'Deprecated'
IMPLEMENTATION_STATUS[REMOVED] = 'Removed'
IMPLEMENTATION_STATUS[ORIGIN_TRIAL] = 'Origin trial'
IMPLEMENTATION_STATUS[INTERVENTION] = 'Browser Intervention'
IMPLEMENTATION_STATUS[ON_HOLD] = 'On hold'
IMPLEMENTATION_STATUS[NO_LONGER_PURSUING] = 'No longer pursuing'

MAJOR_NEW_API = 1
MAJOR_MINOR_NEW_API = 2
SUBSTANTIVE_CHANGES = 3
MINOR_EXISTING_CHANGES = 4
EXTREMELY_SMALL_CHANGE = 5

# Status for security and privacy reviews.
REVIEW_PENDING = 1
REVIEW_ISSUES_OPEN = 2
REVIEW_ISSUES_ADDRESSED = 3
REVIEW_NA = 4

REVIEW_STATUS_CHOICES = {
    REVIEW_PENDING: 'Pending',
    REVIEW_ISSUES_OPEN: 'Issues open',
    REVIEW_ISSUES_ADDRESSED: 'Issues addressed',
    REVIEW_NA: 'Not applicable',
    }


FOOTPRINT_CHOICES = {
  MAJOR_NEW_API: ('A major new independent API (e.g. adding many '
                  'independent concepts with many methods/properties/objects)'),
  MAJOR_MINOR_NEW_API: ('Major changes to an existing API OR a minor new '
                        'independent API (e.g. adding many new '
                        'methods/properties or introducing new concepts to '
                        'augment an existing API)'),
  SUBSTANTIVE_CHANGES: ('Substantive changes to an existing API (e.g. small '
                        'number of new methods/properties)'),
  MINOR_EXISTING_CHANGES: (
      'Minor changes to an existing API (e.g. adding a new keyword/allowed '
      'argument to a property/method)'),
  EXTREMELY_SMALL_CHANGE: ('Extremely small tweaks to an existing API (e.g. '
                           'how existing keywords/arguments are interpreted)'),
  }

MAINSTREAM_NEWS = 1
WARRANTS_ARTICLE = 2
IN_LARGER_ARTICLE = 3
SMALL_NUM_DEVS = 4
SUPER_SMALL = 5

# Signals from other implementations in an intent-to-ship
SHIPPED = 1
IN_DEV = 2
PUBLIC_SUPPORT = 3
MIXED_SIGNALS = 4  # Deprecated
NO_PUBLIC_SIGNALS = 5
PUBLIC_SKEPTICISM = 6  # Deprecated
OPPOSED = 7
NEUTRAL = 8
SIGNALS_NA = 9
GECKO_UNDER_CONSIDERATION = 10
GECKO_IMPORTANT = 11
GECKO_WORTH_PROTOTYPING = 12
GECKO_NONHARMFUL = 13
GECKO_DEFER = 14
GECKO_HARMFUL = 15


VENDOR_VIEWS_COMMON = {
  SHIPPED: 'Shipped/Shipping',
  IN_DEV: 'In development',
  PUBLIC_SUPPORT: 'Positive',
  NO_PUBLIC_SIGNALS: 'No signal',
  OPPOSED: 'Negative',
  NEUTRAL: 'Neutral',
  SIGNALS_NA: 'N/A',
  }

VENDOR_VIEWS_GECKO = VENDOR_VIEWS_COMMON.copy()
VENDOR_VIEWS_GECKO.update({
  GECKO_UNDER_CONSIDERATION: 'Under consideration',
  GECKO_IMPORTANT: 'Important',
  GECKO_WORTH_PROTOTYPING: 'Worth prototyping',
  GECKO_NONHARMFUL: 'Non-harmful',
  GECKO_DEFER: 'Defer',
  GECKO_HARMFUL: 'Harmful',
  })

# These vendors have no "custom" views values yet.
VENDOR_VIEWS_EDGE = VENDOR_VIEWS_COMMON
VENDOR_VIEWS_WEBKIT = VENDOR_VIEWS_COMMON

VENDOR_VIEWS = {}
VENDOR_VIEWS.update(VENDOR_VIEWS_GECKO)
VENDOR_VIEWS.update(VENDOR_VIEWS_EDGE)
VENDOR_VIEWS.update(VENDOR_VIEWS_WEBKIT)

DEFACTO_STD = 1
ESTABLISHED_STD = 2
WORKING_DRAFT = 3
EDITORS_DRAFT = 4
PUBLIC_DISCUSSION = 5
NO_STD_OR_DISCUSSION = 6

STANDARDIZATION = {
  DEFACTO_STD: 'De-facto standard',
  ESTABLISHED_STD: 'Established standard',
  WORKING_DRAFT: 'Working draft or equivalent',
  EDITORS_DRAFT: "Editor's draft",
  PUBLIC_DISCUSSION: 'Public discussion',
  NO_STD_OR_DISCUSSION: 'No public standards discussion',
  }

UNSET_STD = 0
UNKNOWN_STD = 1
PROPOSAL_STD = 2
INCUBATION_STD = 3
WORKINGDRAFT_STD = 4
STANDARD_STD = 5

STANDARD_MATURITY_CHOICES = {
  # No text for UNSET_STD.  One of the values below will be set on first edit.
  UNKNOWN_STD: 'Unknown standards status - check spec link for status',
  PROPOSAL_STD: 'Proposal in a personal repository, no adoption from community',
  INCUBATION_STD: 'Specification being incubated in a Community Group',
  WORKINGDRAFT_STD: ('Specification currently under development in a '
                     'Working Group'),
  STANDARD_STD: ('Final published standard: Recommendation, Living Standard, '
                 'Candidate Recommendation, or similar final form'),
}

STANDARD_MATURITY_SHORT = {
  UNSET_STD: 'Unknown status',
  UNKNOWN_STD: 'Unknown status',
  PROPOSAL_STD: 'Pre-incubation',
  INCUBATION_STD: 'Incubation',
  WORKINGDRAFT_STD: 'Working draft',
  STANDARD_STD: 'Published standard',
}

# For features that don't have a standard_maturity value set, but do have
# the old standardization field, infer a maturity.
STANDARD_MATURITY_BACKFILL = {
    DEFACTO_STD: STANDARD_STD,
    ESTABLISHED_STD: STANDARD_STD,
    WORKING_DRAFT: WORKINGDRAFT_STD,
    EDITORS_DRAFT: INCUBATION_STD,
    PUBLIC_DISCUSSION: INCUBATION_STD,
    NO_STD_OR_DISCUSSION: PROPOSAL_STD,
}

DEV_STRONG_POSITIVE = 1
DEV_POSITIVE = 2
DEV_MIXED_SIGNALS = 3
DEV_NO_SIGNALS = 4
DEV_NEGATIVE = 5
DEV_STRONG_NEGATIVE = 6

WEB_DEV_VIEWS = {
  DEV_STRONG_POSITIVE: 'Strongly positive',
  DEV_POSITIVE: 'Positive',
  DEV_MIXED_SIGNALS: 'Mixed signals',
  DEV_NO_SIGNALS: 'No signals',
  DEV_NEGATIVE: 'Negative',
  DEV_STRONG_NEGATIVE: 'Strongly negative',
  }


PROPERTY_NAMES_TO_ENUM_DICTS = {
    'category': FEATURE_CATEGORIES,
    'intent_stage': INTENT_STAGES,
    'impl_status_chrome': IMPLEMENTATION_STATUS,
    'security_review_status': REVIEW_STATUS_CHOICES,
    'privacy_review_status': REVIEW_STATUS_CHOICES,
    'standard_maturity': STANDARD_MATURITY_CHOICES,
    'standardization': STANDARDIZATION,
    'ff_views': VENDOR_VIEWS,
    'ie_views': VENDOR_VIEWS,
    'safari_views': VENDOR_VIEWS,
    'web_dev_views': WEB_DEV_VIEWS,
  }


def convert_enum_int_to_string(property_name, value):
  """If the property is an enum, return human-readable string, else value."""
  # Check if the value is an int or can be converted to an int.
  try:
    int_val = int(value)
  except Exception:
    return value
  enum_dict = PROPERTY_NAMES_TO_ENUM_DICTS.get(property_name, {})
  converted_value = enum_dict.get(int_val, value)
  return converted_value
