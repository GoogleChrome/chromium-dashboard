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

import collections

from internals import approval_defs
from internals import models


Process = collections.namedtuple(
    'Process',
    'name, description, applicability, stages')
# Note: A new feature always starts with intent_stage == INTENT_NONE
# regardless of process.  intent_stage is set to the first stage of
# a specific process when the user clicks a "Start" button and submits
# a form that sets intent_stage.


ProcessStage = collections.namedtuple(
    'ProcessStage',
    'name, description, progress_items, actions, approvals, '
    'incoming_stage, outgoing_stage')

ProgressItem = collections.namedtuple(
    'ProgressItem',
    'name, field')

Action = collections.namedtuple(
    'Action',
    'name, url, prerequisites')


def process_to_dict(process):
  """Return nested dicts for the nested namedtuples of a process."""
  # These lines are sort of like a deep version of _asdict().
  stages = [stage._asdict() for stage in process.stages]
  for stage in stages:
    stage['progress_items'] = [pi._asdict() for pi in stage['progress_items']]
    stage['actions'] = [act._asdict() for act in stage['actions']]
    stage['approvals'] = [appr._asdict() for appr in stage['approvals']]

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
PI_DRAFT_API_SPEC = ProgressItem('Draft API spec', None)
PI_I2P_EMAIL = ProgressItem(
    'Intent to Prototype email', 'intent_to_implement_url')

PI_SAMPLES = ProgressItem('Samples', 'sample_links')
PI_DRAFT_API_OVERVIEW = ProgressItem('Draft API overview (may be on MDN)', None)
PI_REQUEST_SIGNALS = ProgressItem('Request signals', 'safari_views')
PI_SEC_REVIEW = ProgressItem('Security review issues addressed', None)
PI_PRI_REVIEW = ProgressItem('Privacy review issues addressed', None)
# TODO(jrobbins): needs detector.
PI_EXTERNAL_REVIEWS = ProgressItem('External reviews', None)
PI_R4DT_EMAIL = ProgressItem('Ready for Trial email', 'ready_for_trial_url')

PI_TAG_REQUESTED = ProgressItem('TAG review requested', 'tag_review')
PI_VENDOR_SIGNALS = ProgressItem('Vendor signals', 'safari_views')
PI_WEB_DEV_SIGNALS = ProgressItem('Web developer signals', 'web_dev_views')
PI_DOC_LINKS = ProgressItem('Doc links', 'doc_links')
# TODO(jrobbins): needs detector.
PI_DOC_SIGNOFF = ProgressItem('Documentation signoff', None)
PI_EST_TARGET_MILESTONE = ProgressItem(
    'Estimated target milestone', 'shipped_milestone')

# TODO(jrobbins): needs detector.
PI_OT_REQUEST = ProgressItem('OT request', None)
# TODO(jrobbins): needs detector.
PI_OT_AVAILABLE = ProgressItem('OT available', None)
# TODO(jrobbins): needs detector.
PI_OT_RESULTS = ProgressItem('OT results', None)
PI_I2E_EMAIL = ProgressItem(
    'Intent to Experiment email', 'intent_to_experiment_url')
PI_I2E_LGTMS = ProgressItem('One LGTM on Intent to Experiment', 'i2e_lgtms')

PI_MIGRATE_INCUBATION = ProgressItem('Request to migrate incubation', None)
PI_TAG_ADDRESSED = ProgressItem(
    'TAG review issues addressed', 'tag_review_status')
PI_UPDATE_VENDOR_SIGNALS = ProgressItem(
    'Updated vendor signals', 'safari_views')
PI_UPDATE_TARGET_MILESTONE = ProgressItem(
    'Updated target milestone', 'shipped_milestone')
PI_I2S_EMAIL = ProgressItem('Intent to Ship email', 'intent_to_ship_url')
PI_I2S_LGTMS = ProgressItem('Three LGTMs on Intent to Ship', 'i2s_lgtms')

# TODO(jrobbins): needs detector.
PI_FINAL_VENDOR_SIGNALS = ProgressItem('Finalized vendor signals', 'safari_views')
# TODO(jrobbins): needs detector.
PI_FINAL_TARGET_MILESTONE = ProgressItem(
    'Finalized target milestone', 'shipped_milestone')

PI_CODE = ProgressItem('Code in Chromium', None)

PI_PSA_EMAIL = ProgressItem('Web facing PSA email', None)

# TODO(jrobbins): needs detector.
PI_DT_REQUEST = ProgressItem('DT request', None)
# TODO(jrobbins): needs detector.
PI_DT_AVAILABLE = ProgressItem('DT available', None)
# TODO(jrobbins): needs detector.
PI_REMOVAL_OF_DT = ProgressItem('Removal of DT', None)
PI_DT_EMAIL = ProgressItem(
    'Request for Deprecation Trial email', 'intent_to_experiment_url')
PI_DT_LGTMS = ProgressItem(
    'One LGTM on Request for Deprecation Trial', 'i2e_lgtms')

# TODO(jrobbins): needs detector.
PI_EXISTING_FEATURE = ProgressItem('Link to existing feature', None)

PI_CODE_REMOVED = ProgressItem('Code removed', None)


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
      models.INTENT_NONE, models.INTENT_INCUBATE),

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
              [PI_SPEC_LINK])],
      [approval_defs.PrototypeApproval],
      models.INTENT_INCUBATE, models.INTENT_IMPLEMENT),

  ProcessStage(
      'Dev trials and iterate on design',
      'Publicize availablity for developers to try. '
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
      [Action('Draft Ready for Trial email', INTENT_EMAIL_URL, [])],
      [],
      models.INTENT_IMPLEMENT, models.INTENT_EXPERIMENT),

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
      models.INTENT_EXPERIMENT, models.INTENT_IMPLEMENT_SHIP),

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
      [Action('Draft Intent to Experiment email', INTENT_EMAIL_URL, [])],
      [approval_defs.ExperimentApproval],
      models.INTENT_IMPLEMENT_SHIP, models.INTENT_EXTEND_TRIAL),

  ProcessStage(
      'Prepare to ship',
      'Lock in shipping milestone. Finalize docs and announcements. '
      'Further standardization.',
      [PI_MIGRATE_INCUBATION,
       PI_TAG_ADDRESSED,
       PI_UPDATE_VENDOR_SIGNALS,
       PI_UPDATE_TARGET_MILESTONE,
       PI_I2S_EMAIL,
       PI_I2S_LGTMS,
      ],
      [Action('Draft Intent to Ship email', INTENT_EMAIL_URL, [])],
      [approval_defs.ShipApproval],
      models.INTENT_IMPLEMENT_SHIP, models.INTENT_SHIP),

  ProcessStage(
      'Ship',
      'Update milestones and other information when the feature '
      'actually ships.',
      [PI_FINAL_VENDOR_SIGNALS,
       PI_FINAL_TARGET_MILESTONE,
      ],
      [],
      [],
      models.INTENT_SHIP, models.INTENT_SHIPPED),
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
       PI_CODE,
       ],
      [Action('Draft Intent to Prototype email', INTENT_EMAIL_URL, [])],
      [approval_defs.PrototypeApproval],
      models.INTENT_NONE, models.INTENT_IMPLEMENT),

  ProcessStage(
      'Dev trials and iterate on implementation',
      'Publicize availablity for developers to try. '
      'Provide sample code. '
      'Act on feedback from partners and web developers.',
      [PI_SAMPLES,
       PI_DRAFT_API_OVERVIEW,
       PI_R4DT_EMAIL,
       PI_VENDOR_SIGNALS,
       PI_EST_TARGET_MILESTONE,
      ],
      [Action('Draft Ready for Trial email', INTENT_EMAIL_URL, [])],
      [],
      models.INTENT_IMPLEMENT, models.INTENT_EXPERIMENT),

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
      [Action('Draft Intent to Experiment email', INTENT_EMAIL_URL, [])],
      [approval_defs.ExperimentApproval],
      models.INTENT_EXPERIMENT, models.INTENT_EXTEND_TRIAL),

  ProcessStage(
      'Prepare to ship',
      'Lock in shipping milestone. Finalize docs and announcements. '
      'Further standardization.',
      [PI_DOC_SIGNOFF,
       PI_UPDATE_TARGET_MILESTONE,
       PI_I2S_EMAIL,
       PI_I2S_LGTMS,
      ],
      [Action('Draft Intent to Ship email', INTENT_EMAIL_URL, [])],
      [approval_defs.ShipApproval],
      models.INTENT_EXPERIMENT, models.INTENT_SHIP),

  ProcessStage(
      'Ship',
      'Update milestones and other information when the feature '
      'actually ships.',
      [PI_FINAL_VENDOR_SIGNALS,
       PI_FINAL_TARGET_MILESTONE,
      ],
      [],
      [],
      models.INTENT_SHIP, models.INTENT_SHIPPED),
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
       PI_CODE,
      ],
      [],
      [],
      models.INTENT_NONE, models.INTENT_IMPLEMENT),

  ProcessStage(
      'Dev trials and iterate on implementation',
      '(Optional) Publicize availablity for developers to try. '
      'Act on feedback from partners and web developers.',
      [PI_R4DT_EMAIL,
       PI_VENDOR_SIGNALS,
       PI_EST_TARGET_MILESTONE,
      ],
      [Action('Draft Ready for Trial email', INTENT_EMAIL_URL, [])],
      [],
      models.INTENT_IMPLEMENT, models.INTENT_EXPERIMENT),

  ProcessStage(
      'Prepare to ship',
      'Lock in shipping milestone.',
      [PI_PSA_EMAIL,
       PI_UPDATE_TARGET_MILESTONE,
       PI_I2S_EMAIL,
      ],
      [Action('Draft Intent to Ship email', INTENT_EMAIL_URL, [])],
      [approval_defs.ShipApproval],
      models.INTENT_EXPERIMENT, models.INTENT_SHIP),

  ProcessStage(
      'Ship',
      'Update milestones and other information when the feature '
      'actually ships.',
      [PI_FINAL_VENDOR_SIGNALS,
       PI_FINAL_TARGET_MILESTONE,
      ],
      [],
      [],
      models.INTENT_SHIP, models.INTENT_SHIPPED),
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
       PI_CODE,
      ],
      [Action('Draft Intent to Deprecate and Remove email', INTENT_EMAIL_URL,
              [])],
      [approval_defs.PrototypeApproval],
      models.INTENT_NONE, models.INTENT_IMPLEMENT),

  # TODO(cwilso): Work out additional steps for flag defaulting to disabled.
  ProcessStage(
      'Dev trial of deprecation',
      'Publicize deprecation and address risks. ',
      [PI_R4DT_EMAIL,
       PI_VENDOR_SIGNALS,
       PI_EST_TARGET_MILESTONE,
      ],
      [Action('Draft Ready for Trial email', INTENT_EMAIL_URL, [])],
      [],
      models.INTENT_IMPLEMENT, models.INTENT_EXPERIMENT),

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
              [])],
      # TODO(jrobbins): Intent to extend deprecation.
      [approval_defs.ExperimentApproval],
      models.INTENT_EXPERIMENT, models.INTENT_EXTEND_TRIAL),

  ProcessStage(
      'Prepare to ship',
      'Lock in shipping milestone. '
      'Finalize docs and announcements before disabling feature by default.',
      [PI_UPDATE_TARGET_MILESTONE,
       PI_I2S_EMAIL,
       PI_I2S_LGTMS,
      ],
      [Action('Draft Intent to Ship email', INTENT_EMAIL_URL, [])],
      [approval_defs.ShipApproval],
      models.INTENT_EXPERIMENT, models.INTENT_SHIP),

  ProcessStage(
      'Remove code',
      'Once the feature is no longer available, remove the code.',
      [PI_CODE_REMOVED,
      ],
      [Action('Generate an Intent to Extend Deprecation Trial',
              INTENT_EMAIL_URL, []),
       ],
      [],
      models.INTENT_SHIP, models.INTENT_REMOVED),
  ]


DEPRECATION_PROCESS = Process(
    'Feature deprecation',
    'Description of deprecation process',  # Not used yet.
    'When to use it',  # Not used yet.
    DEPRECATION_STAGES)


ALL_PROCESSES = {
    models.FEATURE_TYPE_INCUBATE_ID: BLINK_LAUNCH_PROCESS,
    models.FEATURE_TYPE_EXISTING_ID: BLINK_FAST_TRACK_PROCESS,
    models.FEATURE_TYPE_CODE_CHANGE_ID: PSA_ONLY_PROCESS,
    models.FEATURE_TYPE_DEPRECATION_ID: DEPRECATION_PROCESS,
    }


INTENT_EMAIL_SECTIONS = {
    models.INTENT_NONE: [],
    models.INTENT_INCUBATE: [],
    models.INTENT_IMPLEMENT: ['motivation'],
    models.INTENT_EXPERIMENT: ['i2p_thread', 'experiment'],
    models.INTENT_IMPLEMENT_SHIP: [
        'need_api_owners_lgtms', 'motivation', 'tracking_bug', 'sample_links'],
    models.INTENT_EXTEND_TRIAL: [
        'i2p_thread', 'experiment', 'extension_reason'],
    models.INTENT_SHIP: [
        'need_api_owners_lgtms', 'i2p_thread', 'tracking_bug', 'sample_links'],
    models.INTENT_REMOVED: [],
    models.INTENT_SHIPPED: [],
    models.INTENT_PARKED: [],
    }


def initial_tag_review_status(feature_type):
  """Incubating a new feature requires a TAG review, other types do not."""
  if feature_type == models.FEATURE_TYPE_INCUBATE_ID:
    return models.REVIEW_PENDING
  return models.REVIEW_NA


def review_is_done(status):
  return status in (models.REVIEW_ISSUES_ADDRESSED, models.REVIEW_NA)


# These functions return a true value when the checkmark should be shown.
# If they return a string, and it starts with "http:" or "https:", it will
# be used as a link URL.
PROGRESS_DETECTORS = {
    'Initial public proposal':
    lambda f: f.initial_public_proposal_url,

    'Explainer':
    lambda f: f.explainer_links and f.explainer_links[0],

    'Security review issues addressed':
    lambda f: review_is_done(f.security_review_status),

    'Privacy review issues addressed':
    lambda f: review_is_done(f.privacy_review_status),

    'Intent to Prototype email':
    lambda f: f.intent_to_implement_url,

    'Intent to Ship email':
    lambda f: f.intent_to_ship_url,

    'Ready for Trial email':
    lambda f: f.ready_for_trial_url,

    'Intent to Experiment email':
    lambda f: f.intent_to_experiment_url,

    'One LGTM on Intent to Experiment':
    lambda f: f.i2e_lgtms,

    'One LGTM on Request for Deprecation Trial':
    lambda f: f.i2e_lgtms,

    'Three LGTMs on Intent to Ship':
    lambda f: f.i2s_lgtms and len(f.i2s_lgtms) >= 3,

    'Samples':
    lambda f: f.sample_links and f.sample_links[0],

    'Doc links':
    lambda f: f.doc_links and f.doc_links[0],

    'Spec link':
    lambda f: f.spec_link,

    'Draft API spec':
    lambda f: f.spec_link,

    'API spec':
    lambda f: f.api_spec,

    'Spec mentor':
    lambda f: f.spec_mentors,

    'TAG review requested':
    lambda f: f.tag_review,

    'TAG review issues addressed':
    lambda f: review_is_done(f.tag_review_status),

    'Web developer signals':
    lambda f: bool(f.web_dev_views and
                   f.web_dev_views != models.DEV_NO_SIGNALS),

    'Vendor signals':
    lambda f: bool(
        f.ff_views != models.NO_PUBLIC_SIGNALS or
        f.safari_views != models.NO_PUBLIC_SIGNALS or
        f.ie_views != models.NO_PUBLIC_SIGNALS),  # Deprecated

    'Estimated target milestone':
    lambda f: bool(f.shipped_milestone),

    'Code in Chromium':
    lambda f: f.impl_status_chrome in (
        models.IN_DEVELOPMENT, models.BEHIND_A_FLAG, models.ENABLED_BY_DEFAULT,
        models.ORIGIN_TRIAL, models.INTERVENTION),

    'Motivation':
    lambda f: bool(f.motivation),

    'Code removed':
    lambda f: f.impl_status_chrome == models.REMOVED,
}
