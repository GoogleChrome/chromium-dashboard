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

import {LitElement, css, html, nothing} from 'lit';
import './chromedash-callout.js';
import {
  GATE_TEAM_ORDER,
  GATE_FINISHED_REVIEW_STATES,
  PROGRESS_VOTE_STATE,
} from './form-field-enums.js';
import {FLAT_METADATA_FIELDS} from './form-definition.js';
import {findFirstFeatureStage} from './utils.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {customElement, state} from 'lit/decorators.js';
import {Feature, StageDict} from '../js-src/cs-client.js';
import {GateDict, gateStateDisplayInfo} from './chromedash-gate-chip.js';
import {
  Action,
  Process,
  ProcessStage,
  ProgressItem,
} from './chromedash-gate-column.js';

export interface ProgressVoteValue {
  state: number;
  feedback?: string;
  set_on: string;
  set_by: string;
}

export type ProgressDict = Record<string, ProgressVoteValue> | ProgressItem;

let preflightDialogEl;

export async function openPreflightDialog(
  feature: Feature,
  progress: ProgressDict,
  process: Process,
  action: Action,
  stage: StageDict,
  feStage: StageDict,
  featureGates: GateDict[]
) {
  if (!preflightDialogEl) {
    preflightDialogEl = document.createElement('chromedash-preflight-dialog');
    document.body.appendChild(preflightDialogEl);
    await preflightDialogEl.updateComplete;
  }
  return new Promise(resolve => {
    preflightDialogEl.openWithContext(
      feature,
      progress,
      process,
      action,
      stage,
      feStage,
      featureGates,
      resolve
    );
  });
}

export function isPrereqDone(
  itemName: string,
  progress: ProgressDict
): boolean {
  const vote = progress?.[itemName] as ProgressVoteValue | undefined;
  return (
    vote != null &&
    (vote.state === PROGRESS_VOTE_STATE.VERIFIED ||
      vote.state === PROGRESS_VOTE_STATE.NA)
  );
}

export function somePendingPrereqs(action: Action, progress: ProgressDict) {
  return action.prerequisites.some(
    itemName => !isPrereqDone(itemName, progress)
  );
}

export function somePendingGates(featureGates: GateDict[], feStage: StageDict) {
  return findPendingGates(featureGates, feStage).length > 0;
}

export function findOtherGates(featureGates: GateDict[], feStage: StageDict) {
  const gatesForStage = featureGates.filter(g => g.stage_id == feStage.id);
  const otherGates = gatesForStage.filter(
    g => g.team_name != 'API Owners' && g.team_name != 'Data Quality'
  );
  return otherGates;
}

export function findPendingGates(featureGates: GateDict[], feStage: StageDict) {
  const otherGates = findOtherGates(featureGates, feStage);
  const pendingGates = otherGates.filter(
    g => !GATE_FINISHED_REVIEW_STATES.includes(g.state)
  );
  pendingGates.sort(
    (g1, g2) =>
      GATE_TEAM_ORDER.indexOf(g1.team_name) -
      GATE_TEAM_ORDER.indexOf(g2.team_name)
  );
  return pendingGates;
}

@customElement('chromedash-preflight-dialog')
export class ChromedashPreflightDialog extends LitElement {
  @state()
  private _feature!: Feature;
  @state()
  private _featureGates!: GateDict[];
  @state()
  private _progress!: ProgressDict;
  @state()
  private _process!: Process;
  @state()
  private _action!: Action;
  @state()
  private _stage!: StageDict;
  @state()
  private _feStage!: StageDict;
  @state()
  private _resolve: (value?: boolean) => void = () => {
    console.log('Missing resolve action');
  };

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        h3 {
          margin: var(--content-padding) 0 var(--content-padding-quarter) 0;
          font-size: 16px;
          font-weight: 500;
        }

        .data-table {
          margin-bottom: var(--content-padding-half);
        }

        .data-table tr:first-child td {
          border-top: none;
        }

        .data-table td {
          vertical-align: middle;
          padding: 0 var(content-padding);
        }

        .data-table td:first-child {
          width: 10em;
        }

        .data-table td:last-child {
          width: 4em;
          text-align: right;
        }

        .status {
          display: inline-block;
          padding: 2px 8px;
          border-radius: var(--pill-border-radius);
          font-size: 0.9em;
        }

        .status.not_applicable,
        .status.na_self-certified,
        .status.na_self-certified_then_verified {
          background: var(--gate-not-applicable-background);
          color: var(--gate-not-applicable-color);
        }

        .status.preparing {
          background: var(--gate-preparing-background);
          color: var(--gate-preparing-color);
        }

        .status.pending {
          background: var(--gate-pending-background);
          color: var(--gate-pending-color);
        }

        .status.needs_work {
          background: var(--gate-needs-work-background);
          color: var(--gate-needs-work-color);
        }

        .status.approved {
          background: var(--gate-approved-background);
          color: var(--gate-approved-color);
        }

        .status.denied {
          background: var(--gate-denied-background);
          color: var(--gate-denied-color);
        }

        .status.internal_review {
          background: var(--gate-pending-background);
          color: var(--gate-pending-color);
        }

        .status.na_requested {
          background: var(--gate-pending-background);
          color: var(--gate-pending-color);
        }

        sl-button {
          float: right;
          margin: var(--content-padding-half);
        }
      `,
    ];
  }

  openWithContext(
    feature: Feature,
    progress: ProgressDict,
    process: Process,
    action: Action,
    stage: StageDict,
    feStage: StageDict,
    featureGates: GateDict[],
    resolve: (value?: boolean) => void
  ) {
    this._feature = feature;
    this._progress = progress;
    this._process = process;
    this._action = action;
    this._stage = stage;
    this._feStage = feStage;
    this._featureGates = featureGates;
    this._resolve = resolve;
    this.renderRoot.querySelector('sl-dialog')?.show();
  }

  hide() {
    this.renderRoot.querySelector('sl-dialog')?.hide();
  }

  handleCancel() {
    this.hide();
    this._resolve(false);
  }

  handleProceed() {
    // The button opens a new tab due to the href and target attrs.
    // Also, close this dialog, so it is gone when the user returns.
    this.hide();
    this._resolve(true);
  }

  renderEditLink(
    stage: ProcessStage | null,
    feStage: StageDict | null,
    pi: ProgressItem
  ) {
    // This function only renders links for progress items that have a field.
    if (!pi.field) {
      return nothing;
    }

    const isMetadataField = FLAT_METADATA_FIELDS.sections.some(
      section => pi.field !== undefined && section.fields.includes(pi.field)
    );
    const pathSegment =
      !isMetadataField && stage && feStage
        ? `${stage.outgoing_stage}/${feStage.id}`
        : 'metadata';

    return html`
      <a
        class="edit-progress-item"
        href="/guide/stage/${this._feature.id}/${pathSegment}#id_${pi.field}"
        @click=${this.hide}
      >
        Edit
      </a>
    `;
  }

  renderStageTable(stage: ProcessStage, prereqItems: ProgressItem[]) {
    if (prereqItems.length === 0) {
      return nothing;
    }
    const feStage =
      stage.outgoing_stage !== undefined
        ? findFirstFeatureStage(
            stage.outgoing_stage,
            this._stage,
            this._feature
          )
        : null;

    return html`
      <h3>${stage.name}</h3>
      <table class="data-table">
        ${prereqItems.map(item => {
          const isVerified = this._progress.hasOwnProperty(item.name);
          return html`
            <tr>
              <td>
                <span class="status ${isVerified ? 'approved' : 'preparing'}">
                  ${isVerified ? 'Verified' : 'Not started'}
                </span>
              </td>
              <td>${item.description || item.name}</td>
              <td>${this.renderEditLink(stage, feStage, item)}</td>
            </tr>
          `;
        })}
      </table>
    `;
  }

  renderGateState(state: number) {
    let {stateName, className, statusIconName, abbrev} =
      gateStateDisplayInfo(state);

    if (stateName === 'Preparing') {
      stateName = 'Not started';
      abbrev = 'Not started';
    }

    return html`
      <span class="status ${className}" title="${stateName}">${abbrev}</span>
    `;
  }

  renderGatesTable(otherGates: GateDict[]) {
    if (otherGates.length === 0) {
      return nothing;
    }

    return html`
      <h3>Other gates</h3>
      <table class="data-table">
        ${otherGates.map(
          g => html`
            <tr>
              <td>${this.renderGateState(g.state)}</td>
              <td>${g.team_name}</td>
              <td>
                <a
                  href="/feature/${this._feature.id}?gate=${g.id}"
                  @click=${this.hide}
                  >View</a
                >
              </td>
            </tr>
          `
        )}
      </table>
    `;
  }

  renderDialogContent() {
    if (this._feature == null) {
      return nothing;
    }

    const prereqNames = new Set(this._action.prerequisites || []);
    const seenPrereqs = new Set<string>();
    const stageTables = (this._process?.stages || []).map(s => {
      const stagePrereqs = (s.progress_items || []).filter(pi => {
        // Note that metadata-related PIs are associated with the
        // first stage in the process.
        if (prereqNames.has(pi.name) && !seenPrereqs.has(pi.name)) {
          seenPrereqs.add(pi.name);
          return true;
        }
        return false;
      });
      return this.renderStageTable(s, stagePrereqs);
    });

    const otherGates = findOtherGates(this._featureGates, this._feStage);

    return html`
      Please address any relevant "Not started" or "Needs work" items before
      requesting review. ${stageTables} ${this.renderGatesTable(otherGates)}

      <sl-button size="small" @click=${this.handleProceed}
        >Proceed anyway
      </sl-button>
      <sl-button size="small" variant="warning" @click=${this.handleCancel}
        >Don't draft email yet</sl-button
      >
    `;
  }

  render() {
    return html`
      <sl-dialog
        class="missing-prereqs"
        label="Checklist: ${this._action?.name}"
        style="--width:fit-content"
      >
        ${this.renderDialogContent()}
      </sl-dialog>
    `;
  }
}
