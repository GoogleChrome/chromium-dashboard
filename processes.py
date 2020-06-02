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
    'name, description, progress_items, incoming_stage, outgoing_stage')


def process_to_dict(process):
  """Return nested dicts for the nested namedtuples of a process."""
  process_dict = {
      'name': process.name,
      'description': process.description,
      'applicability': process.applicability,
      'stages': [stage._asdict() for stage in process.stages],
  }
  return process_dict


BLINK_PROCESS_STAGES = [
  ProcessStage(
      'Start incubation',
      'Create an initial WebStatus feature entry and kick off standards '
      'incubation (WICG) to share ideas.',
      ['WICG discourse post',
       'Spec repo',
      ],
      models.INTENT_NONE, models.INTENT_IMPLEMENT),

  ProcessStage(
      'Start prototyping',
      'Share an explainer doc and API. '
      'Start prototyping code in a public repo.',
      ['Explainer',
       'API design',
       'Code in repo',
       'Security review',
       'Privacy review',
       'Intent to Prototype email',
       'Spec reviewer',
      ],
      models.INTENT_IMPLEMENT, models.INTENT_EXPERIMENT),

  ProcessStage(
      'Dev trials and iterate on design',
      'Publicize test-readiness.  Share sample code. '
      'Request feedback from browser vendors.',
      ['DevRel publicity request',
       'Samples',
       'Request signals',
       'External reviews',
       'Ready for Trial email',
      ],
      models.INTENT_EXPERIMENT, models.INTENT_IMPLEMENT_SHIP),

  ProcessStage(
      'Evaluate readiness to ship',
      'Work through a TAG review and gather vendor signals.',
      ['TAG review request',
       'Vendor signals',
      ],
      models.INTENT_IMPLEMENT_SHIP, models.INTENT_SHIP),

  ProcessStage(
      '(Optional) Origin Trial',
      'Set up and run an origin trial. '
      'Act on feedback from partners and web developers.',
      ['OT request',
       'OT available',
       'OT results',
      ],
      models.INTENT_EXTEND_TRIAL, models.INTENT_EXTEND_TRIAL),

  ProcessStage(
      'Prepare to ship',
      'Lock in shipping milestone. Finalize docs and announcements. '
      'Further standardization.',
      ['Intent to Ship email',
       'Request to migrate incubation',
       'TAG issues addressed',
       'Three LGTMs',
       'Updated vendor signals',
      ],
      models.INTENT_SHIP, models.INTENT_REMOVE),
  ]


BLINK_LAUNCH_PROCESS = Process(
    'New feature incubation',
    'Description of blink launch process',
    'When to use it',
    BLINK_PROCESS_STAGES)


BLINK_FAST_TRACK_STAGES = [
  ProcessStage(
      'Identify feature',
      'Create an initial WebStatus feature entry to implement part '
      'of an existing specification or combinaton of specifications.',
      ['Spec links',
      ],
      models.INTENT_NONE, models.INTENT_IMPLEMENT_SHIP),

  ProcessStage(
      'Implement',
      'Check code into Chromium under a flag.',
      ['Code in Chromium',
      ],
      models.INTENT_IMPLEMENT_SHIP, models.INTENT_SHIP),

  ProcessStage(
      'Dev Trial (Optional) Origin Trial',
      'Publicize test-readiness.  Set up and run an origin trial. '
      'Act on feedback from partners and web developers.',
      ['Documentation',
       'Estiamted target milestone',
       'OT request',
       'OT available',
       'OT results',
      ],
      models.INTENT_EXTEND_TRIAL, models.INTENT_EXTEND_TRIAL),

  ProcessStage(
      'Prepare to ship',
      'Lock in shipping milestone. Finalize docs and announcements. '
      'Further standardization.',
      ['Intent to Ship email',
       'Three LGTMs',
       'Finalized target milestone',
      ],
      models.INTENT_SHIP, models.INTENT_REMOVE),
  ]


BLINK_FAST_TRACK_PROCESS = Process(
    'Existing feature implementation',
    'Description of blink fast track process',
    'When to use it',
    BLINK_FAST_TRACK_STAGES)


PSA_ONLY_STAGES = [
  ProcessStage(
      'Create entry',
      'Create a WebStatus feature entry for an existing feature '
      'so that it can be referenced in a PSA email.',
      ['Feature entry',
       'Draft PSA',
       'LGTM',
       'Final PSA',
      ],
      models.INTENT_NONE, models.INTENT_REMOVE),
  ]

PSA_ONLY_PROCESS = Process(
    'Web developer facing change to existing code',
    'Description of PSA process',
    'When to use it',
    PSA_ONLY_STAGES)  # TODO(jrobbins): revisit these stages.


ALL_PROCESSES = {
    models.PROCESS_BLINK_LAUNCH_ID: BLINK_LAUNCH_PROCESS,
    models.PROCESS_FAST_TRACK_ID: BLINK_FAST_TRACK_PROCESS,
    models.PROCESS_PSA_ONLY_ID: PSA_ONLY_PROCESS,
    }
