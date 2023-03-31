# -*- coding: utf-8 -*-
# Copyright 2020 Google Inc.
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

from dataclasses import asdict, dataclass

from internals import approval_defs
from internals import core_enums
from internals import core_models
from internals import stage_helpers


@dataclass
class Action:
  name: str
  url: str
  prerequisites: list[str]

@dataclass
class ProgressItem:
  name: str
  field: str | None = None

# Note: A new feature always starts with intent_stage == INTENT_NONE
# regardless of process.  intent_stage is set to the first stage of
# a specific process when the user clicks a "Start" button and submits
# a form that sets intent_stage.
@dataclass
class ProcessStage:
  name: str
  description: str
  progress_items: list[ProgressItem]
  actions: list[Action]
  approvals: list[approval_defs.ApprovalFieldDef]
  incoming_stage: int
  outgoing_stage: int
  stage_type: int | None

@dataclass
class Process:
  name: str
  description: str
  applicability: str
  stages: list[ProcessStage]


def process_to_dict(process):
  """Return nested dicts for the nested dataclasses of a process."""
  # asdict() will recursively convert any dataclass props to dicts.
  stages = [asdict(stage) for stage in process.stages]
  process_dict = {
      'name': process.name,
      'description': process.description,
      'applicability': process.applicability,
      'stages': stages,
  }
  return process_dict


# This page generates a preview of an email that can be sent
# to a mailing list to announce an intent.
# {feature_id} and {outgoing_stage} are filled in by JS code.
# The param "intent" adds clauses the template to include details
# needed for an intent email.  The param "launch" causes those
# details to be omitted and a link to create a launch bug shown instead.
INTENT_EMAIL_URL = ('/admin/features/launch/{feature_id}'
                    '/{outgoing_stage}'
                    '?intent=1')
LAUNCH_BUG_TEMPLATE_URL = '/admin/features/launch/{feature_id}?launch=1'
# TODO(jrobbins): Creation of the launch bug has been a TODO for 5 years.


PI_INITIAL_PUBLIC_PROPOSAL = ProgressItem(
    'Initial public proposal', 'initial_public_proposal_url')
PI_MOTIVATION = ProgressItem('Motivation', 'motivation')
PI_EXPLAINER = ProgressItem('Explainer', 'explainer_links')

PI_SPEC_LINK = ProgressItem('Spec link', 'spec_link')
PI_SPEC_MENTOR = ProgressItem('Spec mentor', 'spec_mentors')
PI_DRAFT_API_SPEC = ProgressItem('Draft API spec')
PI_I2P_EMAIL = ProgressItem(
    'Intent to Prototype email', 'intent_to_implement_url')

PI_SAMPLES = ProgressItem('Samples', 'sample_links')
PI_DRAFT_API_OVERVIEW = ProgressItem('Draft API overview (may be on MDN)')
PI_REQUEST_SIGNALS = ProgressItem('Request signals', 'safari_views')
PI_SEC_REVIEW = ProgressItem('Security review issues addressed')
PI_PRI_REVIEW = ProgressItem('Privacy review issues addressed')
# TODO(jrobbins): needs detector.
PI_EXTERNAL_REVIEWS = ProgressItem('External reviews')
PI_R4DT_EMAIL = ProgressItem('Ready for Trial email', 'announcement_url')

PI_TAG_REQUESTED = ProgressItem('TAG review requested', 'tag_review')
PI_VENDOR_SIGNALS = ProgressItem('Vendor signals', 'safari_views')
PI_WEB_DEV_SIGNALS = ProgressItem('Web developer signals', 'web_dev_views')
PI_DOC_LINKS = ProgressItem('Doc links', 'doc_links')
# TODO(jrobbins): needs detector.
PI_DOC_SIGNOFF = ProgressItem('Documentation signoff')
PI_EST_TARGET_MILESTONE = ProgressItem(
    'Estimated target milestone', 'shipped_milestone')

# TODO(jrobbins): needs detector.
PI_OT_REQUEST = ProgressItem('OT request')
# TODO(jrobbins): needs detector.
PI_OT_AVAILABLE = ProgressItem('OT available')
# TODO(jrobbins): needs detector.
PI_OT_RESULTS = ProgressItem('OT results')
PI_I2E_EMAIL = ProgressItem(
    'Intent to Experiment email', 'intent_to_experiment_url')
PI_I2E_LGTMS = ProgressItem('One LGTM on Intent to Experiment')

PI_MIGRATE_INCUBATION = ProgressItem('Request to migrate incubation')
PI_TAG_ADDRESSED = ProgressItem(
    'TAG review issues addressed', 'tag_review_status')
PI_UPDATED_VENDOR_SIGNALS = ProgressItem(
    'Updated vendor signals', 'safari_views')
PI_UPDATED_TARGET_MILESTONE = ProgressItem(
    'Updated target milestone', 'shipped_milestone')
PI_I2S_EMAIL = ProgressItem('Intent to Ship email', 'intent_to_ship_url')
PI_I2S_LGTMS = ProgressItem('Three LGTMs on Intent to Ship')

# TODO(jrobbins): needs detector.
PI_FINAL_VENDOR_SIGNALS = ProgressItem('Final vendor signals', 'safari_views')
# TODO(jrobbins): needs detector.
PI_FINAL_TARGET_MILESTONE = ProgressItem(
    'Final target milestone', 'shipped_milestone')

PI_CODE_IN_CHROMIUM = ProgressItem('Code in Chromium')

PI_PSA_EMAIL = ProgressItem('Web facing PSA email')

# TODO(jrobbins): needs detector.
PI_DT_REQUEST = ProgressItem('DT request')
# TODO(jrobbins): needs detector.
PI_DT_AVAILABLE = ProgressItem('DT available')
# TODO(jrobbins): needs detector.
PI_REMOVAL_OF_DT = ProgressItem('Removal of DT')
PI_DT_EMAIL = ProgressItem(
    'Request for Deprecation Trial email', 'intent_to_experiment_url')
PI_DT_LGTMS = ProgressItem(
    'One LGTM on Request for Deprecation Trial')

# TODO(jrobbins): needs detector.
PI_EXISTING_FEATURE = ProgressItem('Link to existing feature')

PI_CODE_REMOVED = ProgressItem('Code removed')

PI_ROLLOUT_IMPACT = ProgressItem('Rollout impact', 'rollout_impact')
PI_ROLLOUT_MILESTONE = ProgressItem('Rollout milestone', 'rollout_milestone')
PI_ROLLOUT_PLATFORMS = ProgressItem('Rollout platforms', 'rollout_platforms')
PI_ROLLOUT_DETAILS = ProgressItem('Rollout details', 'rollout_details')
PI_ENTERPRISE_POLICIES = ProgressItem('Enterprise policies', 'enterprise_policies')


# This is a stage that can be inserted in the stages of any non-enterprise
# features that are marked as breaking changes.
FEATURE_ROLLOUT_STAGE = ProcessStage(
      'Start feature rollout',
      'Lock in shipping milestone. '
      'Create feature flag for the feature. '
      'Create policies to enable/disable and control the feature. '
      'Finalize docs and announcements and start rolling out the feature.',
      [PI_ROLLOUT_IMPACT,
       PI_ROLLOUT_MILESTONE,
       PI_ROLLOUT_PLATFORMS,
       PI_ROLLOUT_DETAILS,
       PI_ENTERPRISE_POLICIES,
      ],
      [],
      [],
      core_enums.INTENT_SHIP, core_enums.INTENT_ROLLOUT,
      stage_type=core_enums.STAGE_ENT_ROLLOUT)


BLINK_PROCESS_STAGES = [
  ProcessStage(
      'Start incubating',
      'Create an initial WebStatus feature entry and kick off standards '
      'incubation (WICG) to share ideas.',
      [PI_INITIAL_PUBLIC_PROPOSAL,
       PI_MOTIVATION,
       PI_EXPLAINER,
      ],
      [],
      [],
      core_enums.INTENT_NONE, core_enums.INTENT_INCUBATE,
      stage_type=core_enums.STAGE_BLINK_INCUBATE),

  ProcessStage(
      'Start prototyping',
      'Share an explainer doc and API. '
      'Start prototyping code in a public repo.',
      [PI_SPEC_LINK,
       PI_SPEC_MENTOR,
       PI_DRAFT_API_SPEC,
       PI_I2P_EMAIL,
      ],
      [Action('Draft Intent to Prototype email', INTENT_EMAIL_URL,
              [PI_INITIAL_PUBLIC_PROPOSAL.name, PI_MOTIVATION.name,
               PI_EXPLAINER.name])],
      [approval_defs.PrototypeApproval],
      core_enums.INTENT_INCUBATE, core_enums.INTENT_IMPLEMENT,
      stage_type=core_enums.STAGE_BLINK_PROTOTYPE),

  ProcessStage(
      'Dev trials and iterate on design',
      'Publicize availability for developers to try. '
      'Provide sample code. '
      'Request feedback from browser vendors.',
      [PI_SAMPLES,
       PI_DRAFT_API_OVERVIEW,
       PI_REQUEST_SIGNALS,
       PI_SEC_REVIEW,
       PI_PRI_REVIEW,
       PI_EXTERNAL_REVIEWS,
       PI_R4DT_EMAIL,
      ],
      [Action('Draft Ready for Trial email', INTENT_EMAIL_URL,
              [PI_INITIAL_PUBLIC_PROPOSAL.name, PI_MOTIVATION.name,
               PI_EXPLAINER.name, PI_SPEC_LINK.name])],
      [],
      core_enums.INTENT_IMPLEMENT, core_enums.INTENT_EXPERIMENT,
      stage_type=core_enums.STAGE_BLINK_DEV_TRIAL),

  ProcessStage(
      'Evaluate readiness to ship',
      'Work through a TAG review and gather vendor signals.',
      [PI_TAG_REQUESTED,
       PI_VENDOR_SIGNALS,
       PI_WEB_DEV_SIGNALS,
       PI_DOC_LINKS,
       PI_DOC_SIGNOFF,
       PI_EST_TARGET_MILESTONE,
      ],
      [],
      [],
      core_enums.INTENT_EXPERIMENT, core_enums.INTENT_IMPLEMENT_SHIP,
      stage_type=core_enums.STAGE_BLINK_EVAL_READINESS),

  ProcessStage(
      'Origin Trial',
      '(Optional) Set up and run an origin trial. '
      'Act on feedback from partners and web developers.',
      [PI_OT_REQUEST,
       PI_OT_AVAILABLE,
       PI_OT_RESULTS,
       PI_I2E_EMAIL,
       PI_I2E_LGTMS,
      ],
      [Action('Draft Intent to Experiment email', INTENT_EMAIL_URL,
              [PI_INITIAL_PUBLIC_PROPOSAL.name, PI_MOTIVATION.name,
               PI_EXPLAINER.name, PI_SPEC_LINK.name,
               PI_EST_TARGET_MILESTONE.name])],
      [approval_defs.ExperimentApproval],
      core_enums.INTENT_IMPLEMENT_SHIP, core_enums.INTENT_EXTEND_TRIAL,
      stage_type=core_enums.STAGE_BLINK_ORIGIN_TRIAL),

  ProcessStage(
      'Prepare to ship',
      'Lock in shipping milestone. Finalize docs and announcements. '
      'Further standardization.',
      [PI_MIGRATE_INCUBATION,
       PI_TAG_ADDRESSED,
       PI_UPDATED_VENDOR_SIGNALS,
       PI_UPDATED_TARGET_MILESTONE,
       PI_I2S_EMAIL,
       PI_I2S_LGTMS,
      ],
      [Action('Draft Intent to Ship email', INTENT_EMAIL_URL,
              [PI_INITIAL_PUBLIC_PROPOSAL.name, PI_MOTIVATION.name,
               PI_EXPLAINER.name, PI_SPEC_LINK.name,
               PI_TAG_ADDRESSED.name, PI_UPDATED_VENDOR_SIGNALS.name,
               PI_UPDATED_TARGET_MILESTONE.name])],
      [approval_defs.ShipApproval],
      core_enums.INTENT_IMPLEMENT_SHIP, core_enums.INTENT_SHIP,
      stage_type=core_enums.STAGE_BLINK_SHIPPING),

  ProcessStage(
      'Ship',
      'Update milestones and other information when the feature '
      'actually ships.',
      [PI_FINAL_VENDOR_SIGNALS,
       PI_FINAL_TARGET_MILESTONE,
      ],
      [],
      [],
      core_enums.INTENT_SHIP, core_enums.INTENT_SHIPPED,
      stage_type=None),
    FEATURE_ROLLOUT_STAGE,
  ]


BLINK_LAUNCH_PROCESS = Process(
    'New feature incubation',
    'Description of blink launch process',  # Not used yet.
    'When to use it',  # Not used yet.
    BLINK_PROCESS_STAGES)


BLINK_FAST_TRACK_STAGES = [
  ProcessStage(
      'Start prototyping',
      'Write up use cases and scenarios, start coding as a '
      'runtime enabled feature.',
      [PI_SPEC_LINK,
       PI_CODE_IN_CHROMIUM,
       ],
      [Action('Draft Intent to Prototype email', INTENT_EMAIL_URL,
              [PI_SPEC_LINK.name])],
      [approval_defs.PrototypeApproval],
      core_enums.INTENT_NONE, core_enums.INTENT_IMPLEMENT,
      stage_type=core_enums.STAGE_FAST_PROTOTYPE),

  ProcessStage(
      'Dev trials and iterate on implementation',
      'Publicize availability for developers to try. '
      'Provide sample code. '
      'Act on feedback from partners and web developers.',
      [PI_SAMPLES,
       PI_DRAFT_API_OVERVIEW,
       PI_R4DT_EMAIL,
       PI_VENDOR_SIGNALS,
       PI_EST_TARGET_MILESTONE,
      ],
      [Action('Draft Ready for Trial email', INTENT_EMAIL_URL,
              [PI_SPEC_LINK.name, PI_EST_TARGET_MILESTONE.name])],
      [],
      core_enums.INTENT_IMPLEMENT, core_enums.INTENT_EXPERIMENT,
      stage_type=core_enums.STAGE_FAST_DEV_TRIAL),

  ProcessStage(
      'Origin Trial',
      '(Optional) Set up and run an origin trial. '
      'Act on feedback from partners and web developers.',
      [PI_OT_REQUEST,
       PI_OT_AVAILABLE,
       PI_OT_RESULTS,
       PI_I2E_EMAIL,
       PI_I2E_LGTMS,
      ],
      [Action('Draft Intent to Experiment email', INTENT_EMAIL_URL,
              [PI_SPEC_LINK.name, PI_EST_TARGET_MILESTONE.name])],
      [approval_defs.ExperimentApproval],
      core_enums.INTENT_EXPERIMENT, core_enums.INTENT_EXTEND_TRIAL,
      stage_type=core_enums.STAGE_FAST_ORIGIN_TRIAL),

  ProcessStage(
      'Prepare to ship',
      'Lock in shipping milestone. Finalize docs and announcements. '
      'Further standardization.',
      [PI_DOC_SIGNOFF,
       PI_UPDATED_TARGET_MILESTONE,
       PI_I2S_EMAIL,
       PI_I2S_LGTMS,
      ],
      [Action('Draft Intent to Ship email', INTENT_EMAIL_URL,
              [PI_SPEC_LINK.name, PI_UPDATED_TARGET_MILESTONE.name])],
      [approval_defs.ShipApproval],
      core_enums.INTENT_EXPERIMENT, core_enums.INTENT_SHIP,
      stage_type=core_enums.STAGE_FAST_SHIPPING),

  ProcessStage(
      'Ship',
      'Update milestones and other information when the feature '
      'actually ships.',
      [PI_FINAL_VENDOR_SIGNALS,
       PI_FINAL_TARGET_MILESTONE,
      ],
      [],
      [],
      core_enums.INTENT_SHIP, core_enums.INTENT_SHIPPED,
      stage_type=None),
    FEATURE_ROLLOUT_STAGE,
  ]


BLINK_FAST_TRACK_PROCESS = Process(
    'Existing feature implementation',
    'Description of blink fast track process',  # Not used yet.
    'When to use it',  # Not used yet.
    BLINK_FAST_TRACK_STAGES)


PSA_ONLY_STAGES = [
  ProcessStage(
      'Implement',
      'Check code into Chromium under a flag.',
      [PI_SPEC_LINK,
       PI_CODE_IN_CHROMIUM,
      ],
      [],
      [],
      core_enums.INTENT_NONE, core_enums.INTENT_IMPLEMENT,
      stage_type=core_enums.STAGE_PSA_IMPLEMENT),

  ProcessStage(
      'Dev trials and iterate on implementation',
      '(Optional) Publicize availability for developers to try. '
      'Act on feedback from partners and web developers.',
      [PI_R4DT_EMAIL,
       PI_VENDOR_SIGNALS,
       PI_EST_TARGET_MILESTONE,
      ],
      [Action('Draft Ready for Trial email', INTENT_EMAIL_URL,
              [PI_SPEC_LINK.name, PI_EST_TARGET_MILESTONE.name])],
      [],
      core_enums.INTENT_IMPLEMENT, core_enums.INTENT_EXPERIMENT,
      stage_type=core_enums.STAGE_PSA_DEV_TRIAL),

  ProcessStage(
      'Prepare to ship',
      'Lock in shipping milestone.',
      [PI_PSA_EMAIL,
       PI_UPDATED_TARGET_MILESTONE,
       PI_I2S_EMAIL,
      ],
      [Action('Draft Intent to Ship email', INTENT_EMAIL_URL,
              [PI_SPEC_LINK.name, PI_UPDATED_TARGET_MILESTONE.name])],
      [approval_defs.ShipApproval],
      core_enums.INTENT_EXPERIMENT, core_enums.INTENT_SHIP,
      stage_type=core_enums.STAGE_PSA_SHIPPING),

  ProcessStage(
      'Ship',
      'Update milestones and other information when the feature '
      'actually ships.',
      [PI_FINAL_VENDOR_SIGNALS,
       PI_FINAL_TARGET_MILESTONE,
      ],
      [],
      [],
      core_enums.INTENT_SHIP, core_enums.INTENT_SHIPPED,
      stage_type=None),
    FEATURE_ROLLOUT_STAGE,
  ]


PSA_ONLY_PROCESS = Process(
    'Web developer facing change to existing code',
    'Description of PSA process',   # Not used yet.
    'When to use it',  # Not used yet.
    PSA_ONLY_STAGES)


DEPRECATION_STAGES = [
  ProcessStage(
      'Write up motivation',
      'Create an initial WebStatus feature entry to deprecate '
      'an existing feature, including motivation and impact. '
      'Then, move existing Chromium code under a flag.',
      [PI_EXISTING_FEATURE,
       PI_MOTIVATION,
      ],
      [Action('Draft Intent to Deprecate and Remove email', INTENT_EMAIL_URL,
              [PI_MOTIVATION.name])],
      [approval_defs.PrototypeApproval],
      core_enums.INTENT_NONE, core_enums.INTENT_IMPLEMENT,
      stage_type=core_enums.STAGE_DEP_PLAN),

  # TODO(cwilso): Work out additional steps for flag defaulting to disabled.
  ProcessStage(
      'Dev trial of deprecation',
      'Publicize deprecation and address risks. ',
      [PI_R4DT_EMAIL,
       PI_VENDOR_SIGNALS,
       PI_EST_TARGET_MILESTONE,
      ],
      [Action('Draft Ready for Trial email', INTENT_EMAIL_URL,
              [PI_MOTIVATION.name, PI_VENDOR_SIGNALS.name,
               PI_EST_TARGET_MILESTONE.name])],
      [],
      core_enums.INTENT_IMPLEMENT, core_enums.INTENT_EXPERIMENT,
      stage_type=core_enums.STAGE_DEP_DEV_TRIAL),

  ProcessStage(
      'Prepare for Deprecation Trial',
      '(Optional) Set up and run a deprecation trial. ',
      [PI_DT_REQUEST,
       PI_DT_AVAILABLE,
       PI_REMOVAL_OF_DT,
       PI_DT_EMAIL,
       PI_DT_LGTMS,
      ],
      [Action('Draft Request for Deprecation Trial email', INTENT_EMAIL_URL,
              [PI_MOTIVATION.name, PI_VENDOR_SIGNALS.name,
               PI_EST_TARGET_MILESTONE.name])],
      # TODO(jrobbins): Intent to extend deprecation.
      [approval_defs.ExperimentApproval],
      core_enums.INTENT_EXPERIMENT, core_enums.INTENT_EXTEND_TRIAL,
      stage_type=core_enums.STAGE_DEP_DEPRECATION_TRIAL),

  ProcessStage(
      'Prepare to ship',
      'Lock in shipping milestone. '
      'Finalize docs and announcements before disabling feature by default.',
      [PI_UPDATED_TARGET_MILESTONE,
       PI_I2S_EMAIL,
       PI_I2S_LGTMS,
      ],
      [Action('Draft Intent to Ship email', INTENT_EMAIL_URL,
              [PI_MOTIVATION.name, PI_VENDOR_SIGNALS.name,
               PI_UPDATED_TARGET_MILESTONE.name])],
      [approval_defs.ShipApproval],
      core_enums.INTENT_EXPERIMENT, core_enums.INTENT_SHIP,
      stage_type=core_enums.STAGE_DEP_SHIPPING),

  ProcessStage(
      'Remove code',
      'Once the feature is no longer available, remove the code.',
      [PI_CODE_REMOVED,
      ],
      [Action('Generate an Intent to Extend Deprecation Trial',
              INTENT_EMAIL_URL,
              [PI_MOTIVATION.name, PI_VENDOR_SIGNALS.name,
               PI_UPDATED_TARGET_MILESTONE.name]),
       ],
      [],
      core_enums.INTENT_SHIP, core_enums.INTENT_REMOVED,
      stage_type=core_enums.STAGE_DEP_REMOVE_CODE),
    FEATURE_ROLLOUT_STAGE,
  ]

# Thise are the stages for a feature that has the enterprise feature type.
ENTERPRISE_STAGES = [
  ProcessStage(
      'Start feature rollout',
      'Lock in shipping milestone. '
      'Create feature flag for the feature. '
      'Create policies to enable/disable and control the feature. '
      'Finalize docs and announcements and start rolling out the feature.',
      [PI_ROLLOUT_IMPACT,
       PI_ROLLOUT_MILESTONE,
       PI_ROLLOUT_PLATFORMS,
       PI_ROLLOUT_DETAILS,
       PI_ENTERPRISE_POLICIES,
      ],
      [],
      [],
      core_enums.INTENT_NONE, core_enums.INTENT_ROLLOUT,
      stage_type=core_enums.STAGE_ENT_ROLLOUT),
]


DEPRECATION_PROCESS = Process(
    'Feature deprecation',
    'Description of deprecation process',  # Not used yet.
    'When to use it',  # Not used yet.
    DEPRECATION_STAGES)


ENTERPRISE_PROCESS = Process(
    'New Feature or removal affecting enterprises',
    'Description of enterprise process',  # Not used yet.
    'When to use it',  # Not used yet.
    ENTERPRISE_STAGES)


ALL_PROCESSES = {
    core_enums.FEATURE_TYPE_INCUBATE_ID: BLINK_LAUNCH_PROCESS,
    core_enums.FEATURE_TYPE_EXISTING_ID: BLINK_FAST_TRACK_PROCESS,
    core_enums.FEATURE_TYPE_CODE_CHANGE_ID: PSA_ONLY_PROCESS,
    core_enums.FEATURE_TYPE_DEPRECATION_ID: DEPRECATION_PROCESS,
    core_enums.FEATURE_TYPE_ENTERPRISE_ID: ENTERPRISE_PROCESS,
    }


INTENT_EMAIL_SECTIONS = {
    core_enums.INTENT_NONE: [],
    core_enums.INTENT_INCUBATE: [],
    core_enums.INTENT_IMPLEMENT: ['motivation'],
    core_enums.INTENT_EXPERIMENT: ['i2p_thread', 'experiment'],
    core_enums.INTENT_IMPLEMENT_SHIP: [
        'need_api_owners_lgtms', 'motivation', 'tracking_bug', 'sample_links'],
    core_enums.INTENT_EXTEND_TRIAL: [
        'i2p_thread', 'experiment', 'extension_reason'],
    core_enums.INTENT_SHIP: [
        'need_api_owners_lgtms', 'i2p_thread', 'tracking_bug', 'sample_links',
        'anticipated_spec_changes', 'ship'],
    core_enums.INTENT_REMOVED: [],
    core_enums.INTENT_SHIPPED: [],
    core_enums.INTENT_PARKED: [],
    }


def initial_tag_review_status(feature_type):
  """Incubating a new feature requires a TAG review, other types do not."""
  if feature_type == core_enums.FEATURE_TYPE_INCUBATE_ID:
    return core_enums.REVIEW_PENDING
  return core_enums.REVIEW_NA


def review_is_done(status):
  return status in (core_enums.REVIEW_ISSUES_ADDRESSED, core_enums.REVIEW_NA)


# These functions return a true value when the checkmark should be shown.
# If they return a string, and it starts with "http:" or "https:", it will
# be used as a link URL.
PROGRESS_DETECTORS = {
    'Initial public proposal':
    lambda f, _: f.initial_public_proposal_url,

    'Explainer':
    lambda f, _: f.explainer_links and f.explainer_links[0],

    'Security review issues addressed':
    lambda f, _: review_is_done(f.security_review_status),

    'Privacy review issues addressed':
    lambda f, _: review_is_done(f.privacy_review_status),

    'Intent to Prototype email':
    lambda f, stages: (
        core_enums.STAGE_TYPES_PROTOTYPE[f.feature_type] and
        stages[core_enums.STAGE_TYPES_PROTOTYPE[f.feature_type]][0].intent_thread_url),

    'Intent to Ship email':
    lambda f, stages: (core_enums.STAGE_TYPES_SHIPPING[f.feature_type] and
        stages[core_enums.STAGE_TYPES_SHIPPING[f.feature_type]][0].intent_thread_url),

    'Ready for Trial email':
    lambda f, stages: (core_enums.STAGE_TYPES_DEV_TRIAL[f.feature_type] and
        stages[core_enums.STAGE_TYPES_DEV_TRIAL[f.feature_type]][0].announcement_url),

    'Intent to Experiment email':
    lambda f, stages: (core_enums.STAGE_TYPES_ORIGIN_TRIAL[f.feature_type] and
        stages[core_enums.STAGE_TYPES_ORIGIN_TRIAL[f.feature_type]][0].intent_thread_url),

    'Samples':
    lambda f, _: f.sample_links and f.sample_links[0],

    'Doc links':
    lambda f, _: f.doc_links and f.doc_links[0],

    'Spec link':
    lambda f, _: f.spec_link,

    'Draft API spec':
    lambda f, _: f.spec_link,

    'API spec':
    lambda f, _: f.api_spec,

    'Spec mentor':
    lambda f, _: f.spec_mentor_emails,

    'TAG review requested':
    lambda f, _: f.tag_review,

    'TAG review issues addressed':
    lambda f, _: review_is_done(f.tag_review_status),

    'Web developer signals':
    lambda f, _: bool(f.web_dev_views and
        f.web_dev_views != core_enums.DEV_NO_SIGNALS),

    'Vendor signals':
    lambda f, _: bool(
        f.ff_views != core_enums.NO_PUBLIC_SIGNALS or
        f.safari_views != core_enums.NO_PUBLIC_SIGNALS),

    'Updated vendor signals':
    lambda f, _: bool(
        f.ff_views != core_enums.NO_PUBLIC_SIGNALS or
        f.safari_views != core_enums.NO_PUBLIC_SIGNALS),

    'Final vendor signals':
    lambda f, _: bool(
        f.ff_views != core_enums.NO_PUBLIC_SIGNALS or
        f.safari_views != core_enums.NO_PUBLIC_SIGNALS),

    'Estimated target milestone':
    lambda f, stages: bool(core_enums.STAGE_TYPES_SHIPPING[f.feature_type] and
        stages[core_enums.STAGE_TYPES_SHIPPING[f.feature_type]][0].milestones and
        stages[core_enums.STAGE_TYPES_SHIPPING[f.feature_type]][0].milestones.desktop_first),

    'Updated target milestone':
    lambda f, stages: bool(core_enums.STAGE_TYPES_SHIPPING[f.feature_type] and
        stages[core_enums.STAGE_TYPES_SHIPPING[f.feature_type]][0].milestones and
        stages[core_enums.STAGE_TYPES_SHIPPING[f.feature_type]][0].milestones.desktop_first),

    'Final target milestone':
    lambda f, stages: bool(core_enums.STAGE_TYPES_SHIPPING[f.feature_type] and
        stages[core_enums.STAGE_TYPES_SHIPPING[f.feature_type]][0].milestones and
        stages[core_enums.STAGE_TYPES_SHIPPING[f.feature_type]][0].milestones.desktop_first),

    'Code in Chromium':
    lambda f, _: f.impl_status_chrome in (
        core_enums.IN_DEVELOPMENT, core_enums.BEHIND_A_FLAG,
        core_enums.ENABLED_BY_DEFAULT,
        core_enums.ORIGIN_TRIAL, core_enums.INTERVENTION),

    'Motivation':
    lambda f, _: bool(f.motivation),

    'Code removed':
    lambda f, _: f.impl_status_chrome == core_enums.REMOVED,

    'Rollout impact':
    lambda f, stages: stages[core_enums.STAGE_TYPES_ROLLOUT[f.feature_type]] and
        stages[core_enums.STAGE_TYPES_ROLLOUT[f.feature_type]][0].rollout_impact,

    'Rollout milestone':
    lambda f, stages: stages[core_enums.STAGE_TYPES_ROLLOUT[f.feature_type]] and
        stages[core_enums.STAGE_TYPES_ROLLOUT[f.feature_type]][0].rollout_milestone,

    'Rollout platforms':
    lambda f, stages: stages[core_enums.STAGE_TYPES_ROLLOUT[f.feature_type]] and
        stages[core_enums.STAGE_TYPES_ROLLOUT[f.feature_type]][0].rollout_platforms,

    'Rollout details':
    lambda f, stages: stages[core_enums.STAGE_TYPES_ROLLOUT[f.feature_type]] and
        stages[core_enums.STAGE_TYPES_ROLLOUT[f.feature_type]][0].rollout_details,

    'Enterprise policies':
    lambda f, stages: stages[core_enums.STAGE_TYPES_ROLLOUT[f.feature_type]] and
        stages[core_enums.STAGE_TYPES_ROLLOUT[f.feature_type]][0].enterprise_policies,
}
