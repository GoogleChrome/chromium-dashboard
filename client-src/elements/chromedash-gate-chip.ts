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
import {SHARED_STYLES} from '../css/shared-css.js';
import {updateURLParams} from './utils.js';
import {customElement, property} from 'lit/decorators.js';
import {Feature, StageDict} from '../js-src/cs-client.js';

const GATE_STATE_TO_NAME = {
  0: 'Preparing', // PREPARING
  1: 'Not applicable', //  NA
  2: 'Pending', // REVIEW_REQUESTED
  3: 'Pending', // REVIEW_STARTED
  4: 'Needs work', // NEEDS_WORK
  5: 'Approved', // APPROVED
  6: 'Denied', // DENIED
  // TODO(jrobbins): COMPLETE for auto-approved.
  8: 'Internal review', // INTERNAL_REVIEW
  9: 'N/A requested', // NA_REQUESTED
  10: 'N/A (self-certified)', //  NA_SELF
  11: 'N/A (self-certified then verified)', //  NA_VERIFIED
};

const GATE_STATE_TO_ICON = {
  0: 'arrow_circle_right_20px', // PREPARING
  //  NA has no icon.
  2: 'pending_20px', // REVIEW_REQUESTED
  3: 'pending_20px', // REVIEW_STARTED
  4: 'autorenew_20px', // NEEDS_WORK
  5: 'check_circle_filled_20px', // APPROVED
  6: 'block_20px', // DENIED
  // TODO(jrobbins): COMPLETE for auto-approved also check_circle_filled_20px.
  // INTERNAL_REVIEW has no icon.
  // NA_SELF has no icon.
  // NA_VERIFIED has no icon.
};

const GATE_STATE_TO_ABBREV = {
  1: 'N/A', //  NA
  8: 'INT', // INTERNAL_REVIEW
  9: 'N/A?', // NA_REQUESTED
  10: 'N/A (self)', //  NA_SELF
  11: 'N/A (ver)', //  NA_VERIFIED
};

export interface GateDict {
  id: number;
  feature_id: number;
  stage_id: number;
  gate_type: number;
  team_name: string;
  gate_name: string;
  escalation_email?: string;
  state: number;
  requested_on?: string;
  responded_on?: string;
  assignee_emails: string[];
  next_action?: string;
  additional_review: boolean;
  slo_initial_response: number;
  slo_initial_response_took: number;
  slo_initial_response_remaining: number;
  slo_resolve: number;
  slo_resolve_took: number;
  slo_resolve_remaining: number;
  needs_work_started_on: string;
  possible_assignee_emails: string[];
  self_certify_possible: boolean;
  self_certify_eligible: boolean;
  survey_answers: {
    is_language_polyfill: boolean;
    is_api_polyfill: boolean;
    is_same_origin_css: boolean;
    launch_or_contact: string;
  };
}

@customElement('chromedash-gate-chip')
class ChromedashGateChip extends LitElement {
  @property({type: Object})
  feature!: Feature;
  @property({type: Object})
  stage!: StageDict;
  @property({type: Object})
  gate!: GateDict;
  @property({type: Number})
  selectedGateId = 0;

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        cw-icon {
          font-size: 1.2rem;
        }

        cw-button::part(label) {
          padding: 0 4px;
        }

        cw-button::part(suffix) {
          padding-right: 4px;
        }

        cw-button::part(base) {
          border: var(--chip-border);
          padding: 0 0 0 4px;
          align-items: center;
        }

        cw-button.selected::part(base) {
          box-shadow: 0 0 0 2px var(--dark-spot-color);
        }

        cw-button:hover .teamname {
          text-decoration: underline;
        }

        cw-button.not_applicable::part(base),
        cw-button.na_self-certified::part(base) {
          background: var(--gate-not-applicable-background);
          color: var(--gate-not-applicable-color);
        }
        cw-button.na_self-certified_then_verified::part(base) {
          background: var(--gate-not-applicable-background);
          color: var(--gate-not-applicable-color);
        }
        cw-button.not_applicable::part(prefix),
        cw-button.na_self-certified::part(prefix) {
          align-items: baseline;
        }

        cw-button.preparing::part(base) {
          background: var(--gate-preparing-background);
          color: var(--gate-preparing-color);
        }
        .preparing cw-icon {
          color: var(--gate-preparing-icon-color);
        }

        cw-button.pending::part(base) {
          background: var(--gate-pending-background);
          color: var(--gate-pending-color);
        }
        .pending cw-icon {
          color: var(--gate-pending-icon-color);
        }

        cw-button.needs_work::part(base) {
          background: var(--gate-needs-work-background);
          color: var(--gate-needs-work-color);
        }
        .needs_work cw-icon {
          color: var(--gate-needs-work-icon-color);
        }

        cw-button.approved::part(base) {
          background: var(--gate-approved-background);
          color: var(--gate-approved-color);
        }
        .approved cw-icon {
          color: var(--gate-approved-icon-color);
        }

        cw-button.denied::part(base) {
          background: var(--gate-denied-background);
          color: var(--gate-denied-color);
        }
        .denied cw-icon {
          color: var(--gate-denied-icon-color);
        }

        cw-button.internal_review::part(base) {
          background: var(--gate-pending-background);
          color: var(--gate-pending-color);
        }
        cw-button.internal_review::part(prefix) {
          align-items: baseline;
        }

        cw-button.na_requested::part(base) {
          background: var(--gate-pending-background);
          color: var(--gate-pending-color);
        }
        cw-button.na_requested::part(prefix) {
          align-items: baseline;
        }

        .abbrev {
          padding-left: var(--content-padding-quarter);
          font-weight: 900;
        }

        cw-button cw-icon.overdue {
          color: var(--slo-overdue-color);
        }
      `,
    ];
  }

  _fireEvent(eventName, detail) {
    const event = new CustomEvent(eventName, {
      bubbles: true,
      composed: true,
      detail,
    });
    this.dispatchEvent(event);
  }

  handleClick() {
    // Add the gate id to the URL.
    updateURLParams('gate', this.gate.id);
    // Handled in chromedash-app.js.
    this._fireEvent('show-gate-column', {
      feature: this.feature,
      stage: this.stage,
      gate: this.gate,
    });
  }

  render() {
    if (this.gate === undefined || this.gate == null) {
      return nothing;
    }
    const teamName = this.gate.team_name;
    const stateName = GATE_STATE_TO_NAME[this.gate.state];
    const className = stateName
      .toLowerCase()
      .replaceAll(' ', '_')
      .replaceAll('(', '')
      .replaceAll(')', '')
      .replaceAll('/', '');
    const selected = this.gate.id == this.selectedGateId ? 'selected' : '';

    const statusIconName = GATE_STATE_TO_ICON[this.gate.state];
    const abbrev = GATE_STATE_TO_ABBREV[this.gate.state] || stateName;
    let statusIcon = html`<b class="abbrev" slot="prefix">${abbrev}</b>`;
    if (statusIconName) {
      statusIcon = html`
        <cw-icon
          slot="prefix"
          library="material"
          name=${statusIconName}
        ></cw-icon>
      `;
    }

    const overdue = this.gate.slo_initial_response_remaining < 0;
    const overdueIcon = overdue
      ? html`<cw-icon
          slot="suffix"
          library="material"
          class="overdue"
          name="clock_loader_60_20px"
        ></cw-icon>`
      : nothing;
    const overdueTitle = overdue ? '. Overdue.' : '';

    return html`
      <cw-button
        pill
        size="small"
        class="${className} ${selected}"
        title="${teamName}: ${stateName}${overdueTitle}"
        @click=${this.handleClick}
      >
        ${statusIcon}
        <span class="teamname">${teamName}</span>
        ${overdueIcon}
      </cw-button>
    `;
  }
}
