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

import {LitElement, TemplateResult, css, html, nothing} from 'lit';
import {customElement, property, state} from 'lit/decorators.js';
import {
  GATE_TEAM_ORDER,
  GATE_APPROVED_REVIEW_STATES,
  VOTE_OPTIONS,
  PROGRESS_VOTE_STATE,
  GATE_PREPARING,
  GATE_REVIEW_REQUESTED,
  GATE_NA_REQUESTED,
} from './form-field-enums.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {Feature, StageDict, User} from '../js-src/cs-client.js';
import {GateDict} from './chromedash-gate-chip.js';
import {FEATURE_TYPES, GATE_TYPES} from './form-field-enums.js';
import {
  Action,
  ProcessStage,
  Process,
  ProgressItem,
} from './chromedash-gate-column.js';
import {findProcessStage, parseRawQuery, showToastMessage} from './utils.js';
import {
  openPreflightDialog,
  ProgressVoteValue,
  findOtherGates,
} from './chromedash-preflight-dialog.js';

@customElement('chromedash-checklist-summary')
export class ChromedashChecklistSummary extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        .bubble {
          padding: var(--content-padding-half);
          border-radius: var(--border-radius);
          background: var(--accordion-background);
          margin-bottom: var(--content-padding-large);
        }
        #strip-chart {
          display: flex;
          padding: 1px;
          border: var(--default-border);
        }
        #strip-chart > div {
          flex: 1;
          height: 20px;
          border-right: 1px solid white;
        }
        #strip-chart .verified {
          background: var(--sl-color-green-500);
        }
        #strip-chart .ready {
          background: var(--sl-color-blue-500);
        }
        #strip-chart .needs-work {
          background: var(--sl-color-orange-500);
        }
        #strip-chart .preparing {
          background: var(--sl-color-neutral-300);
        }
      `,
    ];
  }

  @property({type: Object})
  user!: User;
  @state()
  feature!: Feature;
  @state()
  featureGates!: GateDict[];
  @state()
  stage!: StageDict;
  @state()
  gate!: GateDict;
  @state()
  process!: Process;
  @state()
  progress!: ProgressItem;
  @state()
  loading = true;

  fetchData() {
    Promise.all([window.csClient.getGates(this.feature.id)])
      .then(([gatesRes]) => {
        this.featureGates = gatesRes.gates;
      })
      .catch(() => {
        showToastMessage(
          'Some errors occurred. Please refresh the page or try again later.'
        );
      });
  }

  handleViewChecklist(processStage, action) {
    openPreflightDialog(
      this.feature,
      this.progress,
      this.process,
      action,
      processStage,
      this.stage,
      this.featureGates
    );
  }

  countPrereqs(action, states: number[]) {
    const matching = action.prerequisites.filter(itemName => {
      const vote = this.progress?.[itemName] as ProgressVoteValue | undefined;
      return vote
        ? states.includes(vote.state)
        : states.includes(PROGRESS_VOTE_STATE.NOT_STARTED);
    });
    return matching.length;
  }

  countGates(states: number[]) {
    const otherGates = findOtherGates(this.featureGates, this.stage);
    const matching = otherGates.filter(gate => states.includes(gate.state));
    return matching.length;
  }

  renderStripChart(
    numVerified: number,
    numReady: number,
    numNeedsWork: number,
    numPreparing: number
  ) {
    return html`
      ${Array(numVerified).fill(html`<div class="verified"></div>`)}
      ${Array(numReady).fill(html`<div class="ready"></div>`)}
      ${Array(numNeedsWork).fill(html`<div class="needs-work"></div>`)}
      ${Array(numPreparing).fill(html`<div class="preparing"></div>`)}
    `;
  }

  renderLegend(numVerified, numReady, numNeedsWork, numPreparing) {
    const parts: string[] = [];
    if (numVerified > 0) {
      parts.push(`${numVerified} Verified. `);
    }
    if (numReady > 0) {
      parts.push(`${numReady} Ready for review. `);
    }
    if (numNeedsWork > 0) {
      parts.push(`${numNeedsWork} Needs work. `);
    }
    if (numPreparing > 0) {
      parts.push(`${numPreparing} Not started. `);
    }
    return parts;
  }

  renderChecklistSummary(processStage, action) {
    const numVerified =
      this.countPrereqs(action, [
        PROGRESS_VOTE_STATE.VERIFIED,
        PROGRESS_VOTE_STATE.NA,
      ]) + this.countGates(GATE_APPROVED_REVIEW_STATES);
    const numReady =
      this.countPrereqs(action, [PROGRESS_VOTE_STATE.READY_FOR_REVIEW]) +
      this.countGates([
        GATE_REVIEW_REQUESTED,
        GATE_NA_REQUESTED,
        VOTE_OPTIONS.REVIEW_STARTED[0],
        VOTE_OPTIONS.INTERNAL_REVIEW[0],
      ]);
    const numNeedsWork =
      this.countPrereqs(action, [PROGRESS_VOTE_STATE.NEEDS_WORK]) +
      this.countGates([VOTE_OPTIONS.NEEDS_WORK[0]]);
    const numPreparing =
      this.countPrereqs(action, [PROGRESS_VOTE_STATE.NOT_STARTED]) +
      this.countGates([GATE_PREPARING]);

    return html`
      <div class="bubble">
        <div id="strip-chart">
          ${this.renderStripChart(numVerified, numReady, numNeedsWork, numPreparing)}
        </div>
        <div id="legend">
          ${this.renderLegend(numVerified, numReady, numNeedsWork, numPreparing)}
        </div>
        <sl-button
          size="small"
          @click=${() => this.handleViewChecklist(processStage, action)}
          >View checklist</sl-button
        >
      </div>
    `;
  }

  render(): TemplateResult {
    if (this.loading) {
      return html`${nothing}`;
    }
    if (!this.featureGates || this.featureGates.length === 0) {
      this.fetchData();
      return html`${nothing}`;
    }
    if (
      this.gate?.gate_type !== GATE_TYPES.DQ_PLAN &&
      this.gate?.gate_type !== GATE_TYPES.DQ_SHIP
    ) {
      return html`${nothing}`;
    }

    const processStage = findProcessStage(this.stage, this.process);
    const relevantActions = (processStage?.actions || []).filter(act =>
      act.gate_types.includes(this.gate.gate_type)
    );
    if (relevantActions.length == 0) {
      return html`${nothing}`;
    }

    return html`
      <h2>Checklist summary</h2>
      ${relevantActions.map(act => this.renderChecklistSummary(processStage, act))}
    `;
  }
}
