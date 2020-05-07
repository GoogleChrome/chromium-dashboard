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


ProcessStage = collections.namedtuple(
    'ProcessStage',
    'name, description, progress_items, incoming_stage, outgoing_stage')


BLINK_PROCESS = [
  ProcessStage(
      'Start incubation',
      'Create an initial WebStatus feature entry and kick off standards '
      'incubation (WICG) to share ideas',
      ['Feature name, description, owners, and other details',
       'WICG discourse post',
       'Create repo',
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
       'Intent to Prototype mail',
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
       'Ready for Trial mail',
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
      ['Intent to Ship mail',
       'Request to migrate incubation',
       'TAG issues addressed',
       '3 LGTMs',
       'Updated vendor signals',
      ],
      models.INTENT_SHIP, models.INTENT_REMOVE),
  ]
