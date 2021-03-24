from __future__ import division
from __future__ import print_function

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

import models


Process = collections.namedtuple(
    'Process',
    'name, description, applicability, stages')
# Note: A new feature always starts with intent_stage == INTENT_NONE
# regardless of process.  intent_stage is set to the first stage of
# a specific process when the user clicks a "Start" button and submits
# a form that sets intent_stage.


ProcessStage = collections.namedtuple(
    'ProcessStage',
    'name, description, progress_items, actions, '
    'incoming_stage, outgoing_stage')


def process_to_dict(process):
  """Return nested dicts for the nested namedtuples of a process."""
  process_dict = {
      'name': process.name,
      'description': process.description,
      'applicability': process.applicability,
      'stages': [stage._asdict() for stage in process.stages],
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


BLINK_PROCESS_STAGES = [
  ProcessStage(
      'Start incubating',
      'Create an initial WebStatus feature entry and kick off standards '
      'incubation (WICG) to share ideas.',
      ['Initial public proposal',
       'Motivation',
       'Explainer',
      ],
      [],
      models.INTENT_NONE, models.INTENT_INCUBATE),

  ProcessStage(
      'Start prototyping',
      'Share an explainer doc and API. '
      'Start prototyping code in a public repo.',
      ['Spec link',
       'Spec mentor',
       'Draft API spec',
       'Intent to Prototype email',
      ],
      [('Draft Intent to Prototype email', INTENT_EMAIL_URL)],
      models.INTENT_INCUBATE, models.INTENT_IMPLEMENT),

  ProcessStage(
      'Dev trials and iterate on design',
      'Publicize availablity for developers to try. '
      'Provide sample code. '
      'Request feedback from browser vendors.',
      ['Samples',
       'Draft API overview',
       'Request signals',
       'Security review issues addressed',
       'Privacy review issues addressed',
       'External reviews',  # TODO(jrobbins): needs detector.
       'Ready for Trial email',
      ],
      [('Draft Ready for Trial email', INTENT_EMAIL_URL)],
      models.INTENT_IMPLEMENT, models.INTENT_EXPERIMENT),

  ProcessStage(
      'Evaluate readiness to ship',
      'Work through a TAG review and gather vendor signals.',
      ['TAG review requested',
       'Vendor signals',
       'Web developer signals',
       'Doc links',
       'Documentation signoff',  # TODO(jrobbins): needs detector.
       'Estimated target milestone',
      ],
      [],
      models.INTENT_EXPERIMENT, models.INTENT_IMPLEMENT_SHIP),

  ProcessStage(
      'Origin Trial',
      '(Optional) Set up and run an origin trial. '
      'Act on feedback from partners and web developers.',
      ['OT request',  # TODO(jrobbins): needs detector.
       'OT available',  # TODO(jrobbins): needs detector.
       'OT results',  # TODO(jrobbins): needs detector.
       'Intent to Experiment email',
       'One LGTM on Intent to Experiment',
      ],
      [('Draft Intent to Experiment email', INTENT_EMAIL_URL)],
      models.INTENT_IMPLEMENT_SHIP, models.INTENT_EXTEND_TRIAL),

  ProcessStage(
      'Prepare to ship',
      'Lock in shipping milestone. Finalize docs and announcements. '
      'Further standardization.',
      ['Request to migrate incubation',
       'TAG review issues addressed',
       'Updated vendor signals',
       'Updated target milestone',
       'Intent to Ship email',
       'Three LGTMs on Intent to Ship',
      ],
      [('Draft Intent to Ship email', INTENT_EMAIL_URL)],
      models.INTENT_IMPLEMENT_SHIP, models.INTENT_SHIP),

  ProcessStage(
      'Ship',
      'Update milestones and other information when the feature '
      'actually ships.',
      ['Finalized vendor signals',  # TODO(jrobbins): needs detector.
       'Finalized target milestone',  # TODO(jrobbins): needs detector.
      ],
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
      'Identify feature',
      'Create an initial WebStatus feature entry to implement part '
      'of an existing specification or combinaton of specifications.',
      ['Spec link',
       'API spec',
      ],
      [],
      models.INTENT_NONE, models.INTENT_INCUBATE),

  ProcessStage(
      'Implement',
      'Check code into Chromium under a flag.',
      ['Code in Chromium',
      ],
      [],
      models.INTENT_INCUBATE, models.INTENT_IMPLEMENT),

  ProcessStage(
      'Dev trials and iterate on implementation',
      'Publicize availablity for developers to try. '
      'Provide sample code. '
      'Act on feedback from partners and web developers.',
      ['Samples',
       'Draft API overview (may be on MDN)',
       'Ready for Trial email',
       'Vendor signals',
       'Estimated target milestone',
      ],
      [('Draft Ready for Trial email', INTENT_EMAIL_URL)],
      models.INTENT_IMPLEMENT, models.INTENT_EXPERIMENT),

  ProcessStage(
      'Origin Trial',
      '(Optional) Set up and run an origin trial. '
      'Act on feedback from partners and web developers.',
      ['OT request',  # TODO(jrobbins): needs detector.
       'OT available',  # TODO(jrobbins): needs detector.
       'OT results',  # TODO(jrobbins): needs detector.
       'Intent to Experiment email',
       'One LGTM on Intent to Experiment',
      ],
      [('Draft Intent to Experiment email', INTENT_EMAIL_URL)],
      models.INTENT_EXPERIMENT, models.INTENT_EXTEND_TRIAL),

  ProcessStage(
      'Prepare to ship',
      'Lock in shipping milestone. Finalize docs and announcements. '
      'Further standardization.',
      ['Documentation signoff',  # TODO(jrobbins): needs detector.
       'Updated target milestone',  # TODO(jrobbins): needs detector.
       'Intent to Ship email',
       'Three LGTMs on Intent to Ship',
      ],
      [('Draft Intent to Ship email', INTENT_EMAIL_URL)],
      models.INTENT_EXPERIMENT, models.INTENT_SHIP),

  ProcessStage(
      'Ship',
      'Update milestones and other information when the feature '
      'actually ships.',
      ['Finalized vendor signals',  # TODO(jrobbins): needs detector.
       'Finalized target milestone',  # TODO(jrobbins): needs detector.
      ],
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
      'Identify feature',
      'Create an initial WebStatus feature entry for a web developer '
      'facing change to existing code.',
      ['Spec links',
      ],
      [],
      models.INTENT_NONE, models.INTENT_INCUBATE),

  ProcessStage(
      'Implement',
      'Check code into Chromium under a flag.',
      ['Code in Chromium',
      ],
      [],
      models.INTENT_INCUBATE, models.INTENT_IMPLEMENT),

  ProcessStage(
      'Dev trials and iterate on implementation',
      'Publicize availablity for developers to try. '
      'Act on feedback from partners and web developers.',
      ['Ready for Trial email',
       'Vendor signals',
       'Estimated target milestone',
      ],
      [('Draft Ready for Trial email', INTENT_EMAIL_URL)],
      models.INTENT_IMPLEMENT, models.INTENT_EXPERIMENT),

  ProcessStage(
      'Prepare to ship',
      'Lock in shipping milestone.',
      ['Web facing PSA email',
       'Updated target milestone',
       'Intent to Ship email',
      ],
      [('Draft Intent to Ship email', INTENT_EMAIL_URL)],
      models.INTENT_EXPERIMENT, models.INTENT_SHIP),

  ProcessStage(
      'Ship',
      'Update milestones and other information when the feature '
      'actually ships.',
      ['Finalized vendor signals',  # TODO(jrobbins): needs detector.
       'Finalized target milestone',  # TODO(jrobbins): needs detector.
      ],
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
      ['Link to existing feature',  # TODO(jrobbins): needs detector.
       'Motivation',
       'Code in Chromium',
      ],
      [('Draft Intent to Deprecate and Remove email', INTENT_EMAIL_URL)],
      models.INTENT_NONE, models.INTENT_INCUBATE),

  # TODO(cwilso): Work out additional steps for flag defaulting to disabled.
  ProcessStage(
      'Dev trial of deprecation',
      'Publicize deprecation and address risks. ',
      ['Ready for Trial email',
       'Vendor signals',
       'Estimated target milestone',
      ],
      [('Draft Ready for Trial email', INTENT_EMAIL_URL)],
      models.INTENT_INCUBATE, models.INTENT_EXPERIMENT),

  ProcessStage(
      'Prepare for Deprecation Trial',
      '(Optional) Set up and run a deprecation trial. ',
      ['DT request',  # TODO(jrobbins): needs detector.
       'DT available',  # TODO(jrobbins): needs detector.
       'Removal of DT',  # TODO(jrobbins): needs detector.
       'Request for Deprecation Trial email',
       'One LGTM on Request for Deprecation Trial',
      ],
      [('Draft Request for Deprecation Trial email', INTENT_EMAIL_URL)],
      # TODO(jrobbins): Intent to extend deprecation.
      models.INTENT_EXPERIMENT, models.INTENT_EXTEND_TRIAL),

  ProcessStage(
      'Prepare to ship',
      'Lock in shipping milestone. '
      'Finalize docs and announcements before disabling feature by default.',
      ['Updated target milestone',  # TODO(jrobbins): needs detector.
       'Intent to Ship email',
       'Three LGTMs on Intent to Ship',
      ],
      [('Draft Intent to Ship email', INTENT_EMAIL_URL)],
      models.INTENT_EXPERIMENT, models.INTENT_SHIP),

  ProcessStage(
      'Remove code',
      'Once the feature is no longer available, remove the code.',
      ['Code removed',
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
        f.ie_views != models.NO_PUBLIC_SIGNALS),

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
