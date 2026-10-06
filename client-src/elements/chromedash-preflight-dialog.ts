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
import {SlInput, SlSelect} from '@shoelace-style/shoelace';
import './chromedash-callout.js';
import {
  GATE_TEAM_ORDER,
  GATE_FINISHED_REVIEW_STATES,
  PROGRESS_VOTE_STATE,
  PROGRESS_VOTE_STATE_NAMES,
} from './form-field-enums.js';
import {makeDisplaySpec} from './form-field-specs.js';
import {FLAT_METADATA_FIELDS} from './form-definition.js';
import {findFirstFeatureStage, userCanEdit} from './utils.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {customElement, state} from 'lit/decorators.js';
import {Feature, StageDict, User} from '../js-src/cs-client.js';
import {GateDict, gateStateDisplayInfo} from './chromedash-gate-chip.js';
import {
  Action,
  Process,
  ProcessStage,
  ProgressItem,
} from './chromedash-gate-column.js';
import {renderValue} from './chromedash-feature-detail.js';

export interface ProgressVoteValue {
  state: number;
  feedback?: string;
  set_on: string;
  set_by: string;
}

export type ProgressDict = Record<string, ProgressVoteValue> | ProgressItem;

let preflightDialogEl;

export async function openPreflightDialog(
  user: User,
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
      user,
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

export function isPrereqReady(
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
    itemName => !isPrereqReady(itemName, progress)
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
  private _user?: User;
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
  private _expandedItems = new Set<string>();
  @state()
  private _resolve: (value?: boolean) => void = () => {
    console.log('Missing resolve action');
  };
  @state()
  private _dirty = false;
  @state()
  private _saving = false;
  private _touched = new Set<string>();

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

        .data-table tr.feature-value td,
        .data-table tr.feature-values td,
        .data-table tr.feedback td,
        .data-table tr.criteria td {
          border-top: none;
          animation: revealRow 200ms ease-out;
        }

        @keyframes revealRow {
          from {
            opacity: 0;
            transform: translateY(-4px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .data-table td {
          vertical-align: middle;
          padding: 0 var(content-padding);
        }

        .data-table td:first-child {
          width: 1em;
        }

        .data-table td:first-child sl-icon {
          cursor: pointer;
          transition: transform 200ms ease-in-out;
        }

        .data-table td:first-child sl-icon.expanded {
          transform: rotate(90deg);
        }

        .data-table td:nth-child(2) {
          width: 14em;
        }

        .data-table td:nth-child(3) {
          width: 40em;
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

        .status.na,
        .status.not_applicable,
        .status.na_self-certified,
        .status.na_self-certified_then_verified {
          background: var(--gate-not-applicable-background);
          color: var(--gate-not-applicable-color);
        }

        .status.preparing,
        .status.not_started {
          background: var(--gate-preparing-background);
          color: var(--gate-preparing-color);
        }

        .status.pending,
        .status.ready_for_review {
          background: var(--gate-pending-background);
          color: var(--gate-pending-color);
        }

        .status.needs_work {
          background: var(--gate-needs-work-background);
          color: var(--gate-needs-work-color);
        }

        .status.approved,
        .status.verified {
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
    user: User,
    feature: Feature,
    progress: ProgressDict,
    process: Process,
    action: Action,
    stage: StageDict,
    feStage: StageDict,
    featureGates: GateDict[],
    resolve: (value?: boolean) => void
  ) {
    this._user = user;
    this._feature = feature;
    this._progress = progress;
    this._process = process;
    this._action = action;
    this._stage = stage;
    this._feStage = feStage;
    this._featureGates = featureGates;
    this._expandedItems = new Set(
      Object.entries(progress || {})
        .filter(([_, vote]) => Boolean((vote as ProgressVoteValue)?.feedback))
        .map(([itemName]) => itemName)
    );
    this._resolve = resolve;
    this._dirty = false;
    this._touched = new Set();
    this.renderRoot.querySelector('sl-dialog')?.show();
  }

  _fireEvent(eventName, detail) {
    const event = new CustomEvent(eventName, {
      bubbles: true,
      composed: true,
      detail,
    });
    this.dispatchEvent(event);
  }

  canVote() {
    if (this._user?.can_edit_all) {
      return true;
    }
    if (this._user?.can_review_release_notes) {
      return true;
    }
    if ((this._user?.approvable_gate_types || []).length > 0) {
      return true;
    }
    return false;
  }

  canEdit(): boolean {
    return userCanEdit(this._user, this._feature?.id);
  }

  toggleExpanded(itemName: string) {
    const next = new Set(this._expandedItems);
    if (next.has(itemName)) {
      next.delete(itemName);
    } else {
      next.add(itemName);
    }
    this._expandedItems = next;
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

    if (!this.canEdit()) {
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

  renderStatusChip(vote) {
    let statusClass = 'not_started';
    let statusText = 'Not started';
    if (vote) {
      switch (vote.state) {
        case PROGRESS_VOTE_STATE.READY_FOR_REVIEW:
          statusClass = 'ready_for_review';
          statusText = PROGRESS_VOTE_STATE_NAMES.READY_FOR_REVIEW;
          break;
        case PROGRESS_VOTE_STATE.VERIFIED:
          statusClass = 'verified';
          statusText = PROGRESS_VOTE_STATE_NAMES.VERIFIED;
          break;
        case PROGRESS_VOTE_STATE.NA:
          statusClass = 'na';
          statusText = PROGRESS_VOTE_STATE_NAMES.NA;
          break;
        case PROGRESS_VOTE_STATE.NEEDS_WORK:
          statusClass = 'needs_work';
          statusText = PROGRESS_VOTE_STATE_NAMES.NEEDS_WORK;
          break;
      }
    }
    return html` <span class="status ${statusClass}">${statusText}</span> `;
  }

  handleStatusMenuChange(e) {
    this._touched.add(e.target.dataset.pi);
    this._dirty = true;
    if (e.target?.value == PROGRESS_VOTE_STATE.NEEDS_WORK) {
      const itemName: string = e.target?.dataset['pi'] || '';
      const isExpanded = this._expandedItems.has(itemName);
      if (!isExpanded) {
        this.toggleExpanded(itemName);
      }
    }
  }

  handleFeedbackChange(e) {
    this._touched.add(e.target.dataset.pi);
    this._dirty = true;
  }

  handleSave() {
    this._saving = true;
    const promises: Promise<any>[] = [];
    for (const prereq of this._touched) {
      const stateEl = this.renderRoot.querySelector<SlSelect>(
        `.state-widget[data-pi="${prereq}"]`
      );
      const feedbackEl = this.renderRoot.querySelector<SlInput>(
        `.feedback-widget[data-pi="${prereq}"]`
      );
      if (stateEl) {
        const voteState = parseInt(stateEl.value as string);
        const feedback = feedbackEl ? feedbackEl.value.trim() : '';
        promises.push(
          window.csClient.postFeatureProgressVote(
            this._feature.id,
            prereq,
            voteState,
            feedback
          )
        );
      }
    }
    Promise.all(promises).then(() => {
      this._saving = false;
      this.handleCancel();
      this._fireEvent('refetch-needed', {});
    });
  }

  renderStatusMenu(item, vote) {
    const state = vote?.state || PROGRESS_VOTE_STATE.NOT_STARTED;
    return html`
      <sl-select
        value=${state}
        class="state-widget"
        size="small"
        data-pi=${item.name}
        ?disabled=${this._saving}
        @sl-change="${this.handleStatusMenuChange}"
      >
        <sl-option value=${PROGRESS_VOTE_STATE.NOT_STARTED}
          >Not Started</sl-option
        >
        <sl-option value=${PROGRESS_VOTE_STATE.READY_FOR_REVIEW}
          >Ready for review</sl-option
        >
        <sl-option value=${PROGRESS_VOTE_STATE.NEEDS_WORK}
          >Needs work</sl-option
        >
        <sl-option value=${PROGRESS_VOTE_STATE.VERIFIED}>Verified</sl-option>
        <sl-option value=${PROGRESS_VOTE_STATE.NA}>N/A</sl-option>
      </sl-select>
    `;
  }

  renderProgressItem(
    stage: ProcessStage,
    feStage: StageDict | null,
    item: ProgressItem
  ) {
    const isExpanded = this._expandedItems.has(item.name);
    const vote = this._progress?.[item.name] as ProgressVoteValue | undefined;
    const showValueRow =
      isExpanded ||
      (this.canVote() && vote?.state === PROGRESS_VOTE_STATE.READY_FOR_REVIEW);
    const statusRow = html`
      <tr>
        <td>
          <sl-icon
            name="caret-right-fill"
            class="${isExpanded ? 'expanded' : ''}"
            @click=${() => this.toggleExpanded(item.name)}
          ></sl-icon>
        </td>
        <td>
          ${this.canVote() ? this.renderStatusMenu(item, vote) : this.renderStatusChip(vote)}
        </td>
        <td>${item.description || item.name}</td>
        <td>
          ${showValueRow ? nothing : this.renderEditLink(stage, feStage, item)}
        </td>
      </tr>
    `;
    let valueRow = html`${nothing}`;
    if (item.field && showValueRow) {
      const fieldDisplayName = makeDisplaySpec(item.field)[1];
      valueRow = html`
        <tr class="feature-values">
          <td></td>
          <td>${fieldDisplayName}:</td>
          <td>${renderValue(feStage, this._feature, item.field)}</td>
          <td>${this.renderEditLink(stage, feStage, item)}</td>
        </tr>
      `;
    }

    const feedbackWidget = html` <sl-input
      class="feedback-widget"
      size="small"
      data-pi=${item.name}
      @sl-change="${this.handleFeedbackChange}"
      value=${vote?.feedback || ''}
    ></sl-input>`;

    const feedbackRow =
      isExpanded && (vote?.feedback || this.canVote())
        ? html`
            <tr class="feedback">
              <td></td>
              <td>Feedback:</td>
              <td>${this.canVote() ? feedbackWidget : vote?.feedback}</td>
              <td></td>
            </tr>
          `
        : nothing;
    const criteriaRow =
      isExpanded && item.criteria
        ? html`
            <tr class="criteria">
              <td></td>
              <td>Criteria:</td>
              <td>${item.criteria}</td>
              <td></td>
            </tr>
          `
        : nothing;
    return html` ${statusRow} ${valueRow} ${feedbackRow} ${criteriaRow} `;
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
        ${prereqItems.map(item =>
          this.renderProgressItem(stage, feStage, item)
        )}
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
              <td></td>
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
    const saveText = this._saving ? 'Saving...' : 'Save';

    const saveButton = html`
      <sl-button
        size="small"
        @click=${this.handleSave}
        variant="primary"
        ?disabled=${this._saving || !this._dirty}
        >${saveText}
      </sl-button>
    `;
    return html`
      Please address any relevant "Not started" or "Needs work" items before
      requesting review. ${stageTables} ${this.renderGatesTable(otherGates)}

      <sl-button size="small" @click=${this.handleProceed}>Proceed</sl-button>
      <sl-button size="small" variant="warning" @click=${this.handleCancel}
        >Cancel</sl-button
      >
      ${this.canVote() ? saveButton : nothing}
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
