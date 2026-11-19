/**
 * Copyright 2026 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import {LitElement, html} from 'lit';
import {customElement, state} from 'lit/decorators.js';
import {clearURLParams, updateURLParams} from './utils.js';
import * as enums from './form-field-enums.js';
import {Feature, StageDict} from '../js-src/cs-client.js';
import {type GateDict} from './chromedash-gate-chip.js';

let intentDialogEl;

// The different types of intents used to dictate fields in the intent templates.
enum IntentDraftTypeEnum {
  PROTOTYPE = 'prototype',
  DEVELOPER_TESTING = 'developer_testing',
  EXPERIMENT = 'experiment',
  EXTEND_EXPERIMENT = 'extend_experiment',
  SHIP = 'ship',
  PSA = 'psa',
  DEPRECATE = 'deprecate',
}

const INTENT_DRAFT_TYPES_BY_STAGE_TYPE = {
  [enums.STAGE_BLINK_PROTOTYPE]: IntentDraftTypeEnum.PROTOTYPE,
  [enums.STAGE_BLINK_DEV_TRIAL]: IntentDraftTypeEnum.DEVELOPER_TESTING,
  [enums.STAGE_BLINK_ORIGIN_TRIAL]: IntentDraftTypeEnum.EXPERIMENT,
  [enums.STAGE_BLINK_EXTEND_ORIGIN_TRIAL]:
    IntentDraftTypeEnum.EXTEND_EXPERIMENT,
  [enums.STAGE_BLINK_SHIPPING]: IntentDraftTypeEnum.SHIP,
  [enums.STAGE_FAST_PROTOTYPE]: IntentDraftTypeEnum.PROTOTYPE,
  [enums.STAGE_FAST_DEV_TRIAL]: IntentDraftTypeEnum.DEVELOPER_TESTING,
  [enums.STAGE_FAST_ORIGIN_TRIAL]: IntentDraftTypeEnum.EXPERIMENT,
  [enums.STAGE_FAST_EXTEND_ORIGIN_TRIAL]: IntentDraftTypeEnum.EXTEND_EXPERIMENT,
  [enums.STAGE_FAST_SHIPPING]: IntentDraftTypeEnum.SHIP,
  [enums.STAGE_PSA_DEV_TRIAL]: IntentDraftTypeEnum.DEVELOPER_TESTING,
  [enums.STAGE_PSA_SHIPPING]: IntentDraftTypeEnum.PSA,
  [enums.STAGE_DEP_PLAN]: IntentDraftTypeEnum.DEPRECATE,
  [enums.STAGE_DEP_DEV_TRIAL]: IntentDraftTypeEnum.DEVELOPER_TESTING,
  [enums.STAGE_DEP_DEPRECATION_TRIAL]: IntentDraftTypeEnum.EXPERIMENT,
  [enums.STAGE_DEP_EXTEND_DEPRECATION_TRIAL]:
    IntentDraftTypeEnum.EXTEND_EXPERIMENT,
  [enums.STAGE_DEP_SHIPPING]: IntentDraftTypeEnum.SHIP,
};

const SUBJECT_PREFIXES = {
  [IntentDraftTypeEnum.PROTOTYPE]: 'Intent to Prototype',
  [IntentDraftTypeEnum.DEVELOPER_TESTING]: 'Ready for Developer Testing',
  [IntentDraftTypeEnum.EXPERIMENT]: 'Intent to Experiment',
  [IntentDraftTypeEnum.EXTEND_EXPERIMENT]: 'Intent to Extend Experiment',
  [IntentDraftTypeEnum.PSA]: 'Web-Facing Change PSA',
  [IntentDraftTypeEnum.DEPRECATE]: 'Intent to Deprecate and Remove',
  [IntentDraftTypeEnum.SHIP]: 'Intent to Ship',
};

const GATE_TYPES_WITH_INTENTS = [
  enums.GATE_TYPES.API_PROTOTYPE,
  enums.GATE_TYPES.API_ORIGIN_TRIAL,
  enums.GATE_TYPES.API_EXTEND_ORIGIN_TRIAL,
  enums.GATE_TYPES.API_SHIP,
  enums.GATE_TYPES.API_PLAN,
];

export function stageTypeToIntentSubject(stage_type: number): string {
  const intentDraftType = INTENT_DRAFT_TYPES_BY_STAGE_TYPE[stage_type];
  return SUBJECT_PREFIXES[intentDraftType] || 'Unknown intent';
}

export function shouldOfferIntentDialog(gate: {
  gate_type: number;
  state: number;
}): boolean {
  return (
    gate.state !== enums.GATE_PREPARING &&
    GATE_TYPES_WITH_INTENTS.includes(gate.gate_type)
  );
}

export async function openIntentDialog(
  feature: Feature,
  stage: StageDict,
  gate: GateDict
) {
  if (!intentDialogEl || !intentDialogEl.isConnected) {
    intentDialogEl = document.createElement('chromedash-intent-dialog');
    document.body.appendChild(intentDialogEl);
    await intentDialogEl.updateComplete;
  }
  intentDialogEl.openWithContext(feature, stage, gate);
}

@customElement('chromedash-intent-dialog')
export class ChromedashIntentDialog extends LitElement {
  @state()
  feature!: Feature;
  @state()
  stage!: StageDict;
  @state()
  gate!: GateDict;

  openWithContext(feature: Feature, stage: StageDict, gate: GateDict) {
    this.feature = feature;
    this.stage = stage;
    this.gate = gate;
    updateURLParams('dialog', 'intent');
    this.renderRoot.querySelector('sl-dialog')?.show();
  }

  hide() {
    clearURLParams('dialog');
    this.renderRoot.querySelector('sl-dialog')?.hide();
  }

  handleHide(e: Event) {
    if (e.target !== e.currentTarget) {
      return;
    }
    clearURLParams('dialog');
  }

  render() {
    const subject = stageTypeToIntentSubject(this.stage?.stage_type);
    return html`
      <sl-dialog label="${subject}" @sl-hide=${this.handleHide}></sl-dialog>
    `;
  }
}
