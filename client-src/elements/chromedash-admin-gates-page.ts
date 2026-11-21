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

import {DefaultApiInterface, GateDefAdmin} from 'chromestatus-openapi';
import {LitElement, css, html, nothing} from 'lit';
import {customElement, property, state} from 'lit/decorators.js';
import type SlSelect from '@shoelace-style/shoelace/dist/components/select/select.js';
import type SlTextarea from '@shoelace-style/shoelace/dist/components/textarea/textarea.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {VARS} from '../css/_vars-css.js';
import {LAYOUT_CSS} from '../css/_layout-css.js';
import {User} from '../js-src/cs-client.js';
import {showToastMessage} from './utils.js';

@customElement('chromedash-admin-gates-page')
export class ChromedashAdminGatesPage extends LitElement {
  static get styles() {
    return [
      SHARED_STYLES,
      VARS,
      LAYOUT_CSS,
      css`
        .content {
          max-width: var(--max-content-width);
          padding: var(--content-padding);
        }
        .gate-selector {
          max-width: 480px;
          margin-bottom: var(--content-padding);
        }
        .gate-card {
          background: var(--card-background);
          border: var(--card-border);
          border-radius: var(--border-radius);
          padding: var(--content-padding);
          max-width: 720px;
        }
        .gate-details {
          display: grid;
          grid-template-columns: 180px 1fr;
          gap: var(--content-padding-half) var(--content-padding);
          margin: 0 0 var(--content-padding) 0;
        }
        .gate-details dt {
          font-weight: 500;
          color: var(--unimportant-text-color);
        }
        .gate-details dd {
          margin: 0;
          word-break: break-word;
        }
        .approvers-section {
          margin-top: var(--content-padding);
        }
        .readonly-note {
          margin: var(--content-padding-half) 0;
          color: var(--unimportant-text-color);
          font-size: 13px;
        }
        .actions {
          margin-top: var(--content-padding);
          display: flex;
          gap: var(--content-padding-half);
          align-items: center;
        }
      `,
    ];
  }

  private _client: DefaultApiInterface = window.csOpenApiClient;

  @property({type: Object})
  user?: User;

  @state()
  loading = true;

  @state()
  saving = false;

  @state()
  gates: GateDefAdmin[] = [];

  @state()
  selectedGateType: number | null = null;

  @state()
  editedApproversText = '';

  connectedCallback() {
    super.connectedCallback();
    this.fetchData();
  }

  async fetchData() {
    this.loading = true;
    try {
      const response = await this._client.getGateDefs();
      this.gates = response.gates;
      if (this.gates.length > 0 && this.selectedGateType === null) {
        this.selectGate(this.gates[0].gate_type);
      }
    } catch {
      showToastMessage(
        'Some errors occurred. Please refresh the page or try again later.'
      );
    } finally {
      this.loading = false;
    }
  }

  get selectedGate(): GateDefAdmin | undefined {
    return this.gates.find(g => g.gate_type === this.selectedGateType);
  }

  selectGate(gateType: number) {
    this.selectedGateType = gateType;
    const gate = this.gates.find(g => g.gate_type === gateType);
    this.editedApproversText = gate ? gate.approvers.join('\n') : '';
  }

  parseApprovers(text: string): string[] {
    return text
      .split('\n')
      .map(line => line.trim())
      .filter(line => line.length > 0);
  }

  get hasChanges(): boolean {
    const gate = this.selectedGate;
    if (!gate || !gate.is_editable) {
      return false;
    }
    const edited = this.parseApprovers(this.editedApproversText);
    if (edited.length !== gate.approvers.length) {
      return true;
    }
    return edited.some((email, idx) => email !== gate.approvers[idx]);
  }

  handleGateChange(e: Event) {
    const select = e.target as SlSelect;
    const value = Number(select.value);
    if (!Number.isNaN(value)) {
      this.selectGate(value);
    }
  }

  handleApproversInput(e: Event) {
    const textarea = e.target as SlTextarea;
    this.editedApproversText = textarea.value;
  }

  async handleSave() {
    const gate = this.selectedGate;
    if (!gate || !gate.is_editable || !this.hasChanges || this.saving) {
      return;
    }

    this.saving = true;
    try {
      const updated = await this._client.updateGateDef({
        id: gate.gate_type,
        updateGateDefRequest: {
          approvers: this.parseApprovers(this.editedApproversText),
        },
      });
      this.gates = this.gates.map(g =>
        g.gate_type === updated.gate_type ? updated : g
      );
      this.editedApproversText = updated.approvers.join('\n');
      showToastMessage(`Saved reviewers for ${updated.name}.`);
    } catch {
      showToastMessage(
        'Failed to save reviewers. Please verify all email addresses and try again.'
      );
    } finally {
      this.saving = false;
    }
  }

  renderSubheader() {
    return html`
      <div id="subheader">
        <h2>Review gates</h2>
      </div>
    `;
  }

  renderGateDetails(gate: GateDefAdmin) {
    return html`
      <div class="gate-card">
        <dl class="gate-details">
          <dt>Name</dt>
          <dd>${gate.name}</dd>
          <dt>Gate type ID</dt>
          <dd>${gate.gate_type}</dd>
          <dt>Team</dt>
          <dd>${gate.team_name}</dd>
          <dt>Description</dt>
          <dd>${gate.description}</dd>
          <dt>Approval rule</dt>
          <dd>${gate.rule}</dd>
          <dt>Escalation email</dt>
          <dd>${gate.escalation_email || 'None'}</dd>
          <dt>Rotation URL</dt>
          <dd>
            ${
              gate.rotation_url
                ? html`<a
                    href=${gate.rotation_url}
                    target="_blank"
                    rel="noopener"
                    >${gate.rotation_url}</a
                  >`
                : 'None'
            }
          </dd>
          <dt>Initial response SLO</dt>
          <dd>${gate.slo_initial_response} weekdays</dd>
          <dt>Resolution SLO</dt>
          <dd>${gate.slo_resolve} weekdays</dd>
        </dl>

        <div class="approvers-section">
          <sl-textarea
            id="approvers-input"
            label="Reviewers (one email address per line)"
            rows="10"
            resize="auto"
            .value=${this.editedApproversText}
            ?readonly=${!gate.is_editable}
            ?disabled=${this.saving}
            @sl-input=${this.handleApproversInput}
          ></sl-textarea>

          ${
            !gate.is_editable
              ? html`
                  <p class="readonly-note">
                    Reviewers for this gate are managed externally and cannot be
                    edited here.
                    ${
                      gate.approvers_url
                        ? html`Source:
                            <a
                              href=${gate.approvers_url}
                              target="_blank"
                              rel="noopener"
                              >${gate.approvers_url}</a
                            >`
                        : nothing
                    }
                  </p>
                `
              : nothing
          }

          <div class="actions">
            <sl-button
              id="save-button"
              variant="primary"
              ?disabled=${!gate.is_editable || !this.hasChanges || this.saving}
              ?loading=${this.saving}
              @click=${this.handleSave}
            >
              Save
            </sl-button>
          </div>
        </div>
      </div>
    `;
  }

  renderContent() {
    if (this.user && !this.user.is_admin) {
      return html`<p>You must be a site admin to view this page.</p>`;
    }

    if (this.loading) {
      return html`
        <sl-skeleton effect="sheen"></sl-skeleton>
        <sl-skeleton effect="sheen"></sl-skeleton>
      `;
    }

    if (this.gates.length === 0) {
      return html`<p>No gates found.</p>`;
    }

    const gate = this.selectedGate;
    return html`
      <div class="gate-selector">
        <sl-select
          id="gate-select"
          label="Gate type"
          .value=${
            this.selectedGateType !== null ? String(this.selectedGateType) : ''
          }
          @sl-change=${this.handleGateChange}
        >
          ${this.gates.map(
            g => html`
              <sl-option value=${String(g.gate_type)}>
                ${g.name} (${g.team_name})
              </sl-option>
            `
          )}
        </sl-select>
      </div>
      ${gate ? this.renderGateDetails(gate) : nothing}
    `;
  }

  render() {
    return html`
      ${this.renderSubheader()}
      <div class="content">${this.renderContent()}</div>
    `;
  }
}
