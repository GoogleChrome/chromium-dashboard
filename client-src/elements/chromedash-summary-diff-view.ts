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

import {LitElement, PropertyValues, css, html, nothing} from 'lit';
import {customElement, property, query, state} from 'lit/decorators.js';
import SlTextarea from '@shoelace-style/shoelace/dist/components/textarea/textarea.js';
import '@shoelace-style/shoelace/dist/components/button/button.js';
import '@shoelace-style/shoelace/dist/components/badge/badge.js';
import '@shoelace-style/shoelace/dist/components/icon/icon.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {autolink} from './utils.js';

/**
 * Controlled presentational component displaying side-by-side comparisons of current
 * and AI-generated feature summaries, with an inline markdown edit/preview mode.
 * Commit and decision workflows (Apply, Reject, Regenerate) are managed by the parent
 * host container via `summary-value-change` and `summary-edit-toggle` events.
 */
@customElement('chromedash-summary-diff-view')
export class ChromedashSummaryDiffView extends LitElement {
  @property({type: String})
  currentSummary = '';

  @property({type: String})
  suggestedSummary = '';

  @property({attribute: false})
  suggestedDocLinks: string[] = [];

  @property({type: Boolean})
  isEditing = false;

  @property({type: Boolean})
  disabled = false;

  @state()
  editBuffer = '';

  @query('sl-textarea')
  textareaEl?: SlTextarea;

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        :host {
          display: block;
        }

        .comparison-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: var(--sl-spacing-medium);
          margin-bottom: var(--sl-spacing-medium);
        }

        @media (max-width: 768px) {
          .comparison-grid {
            grid-template-columns: 1fr;
          }
        }

        .column-card {
          border: 1px solid var(--sl-color-neutral-200);
          border-radius: var(--sl-border-radius-medium);
          background: var(--sl-color-neutral-50);
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }

        .column-header {
          padding: var(--sl-spacing-small) var(--sl-spacing-medium);
          background: var(--sl-color-neutral-100);
          border-bottom: 1px solid var(--sl-color-neutral-200);
          font-weight: var(--sl-font-weight-semibold);
          font-size: var(--sl-font-size-small);
          color: var(--sl-color-neutral-700);
          display: flex;
          align-items: center;
          justify-content: space-between;
          min-height: 2.25rem;
        }

        .column-content {
          padding: var(--sl-spacing-medium);
          font-size: var(--sl-font-size-small);
          color: var(--sl-color-neutral-800);
          line-height: var(--sl-line-height-normal);
          flex-grow: 1;
          min-height: 140px;
        }

        .column-content.empty {
          color: var(--sl-color-neutral-400);
          font-style: italic;
        }

        .column-content sl-textarea {
          width: 100%;
        }

        .column-content sl-textarea::part(textarea) {
          font-family: inherit;
          font-size: var(--sl-font-size-small);
          min-height: 140px;
        }

        .sources-section {
          margin-top: var(--sl-spacing-small);
          padding-top: var(--sl-spacing-small);
          border-top: 1px solid var(--sl-color-neutral-200);
        }

        .sources-title {
          font-weight: var(--sl-font-weight-semibold);
          font-size: var(--sl-font-size-x-small);
          color: var(--sl-color-neutral-600);
          text-transform: uppercase;
          letter-spacing: var(--sl-letter-spacing-loose);
          margin-bottom: var(--sl-spacing-2x-small);
        }

        .sources-list {
          display: flex;
          flex-wrap: wrap;
          gap: var(--sl-spacing-2x-small);
          list-style: none;
          margin: 0;
          padding: 0;
        }

        .source-link {
          text-decoration: none;
        }
      `,
    ];
  }

  override willUpdate(changedProperties: PropertyValues) {
    if (changedProperties.has('suggestedSummary') && !this.isEditing) {
      this.editBuffer = this.suggestedSummary;
    }
  }

  async toggleEdit() {
    if (this.isEditing && this.textareaEl) {
      this.editBuffer = this.textareaEl.value;
    }
    this.isEditing = !this.isEditing;
    this.dispatchEvent(
      new CustomEvent('summary-edit-toggle', {
        bubbles: true,
        composed: true,
        detail: {isEditing: this.isEditing, value: this.editBuffer},
      })
    );
    if (this.isEditing) {
      await this.updateComplete;
      this.textareaEl?.focus();
    }
  }

  private _handleInput(e: Event) {
    const value =
      this.textareaEl?.value ??
      (e.target as SlTextarea | HTMLInputElement)?.value ??
      '';
    this.editBuffer = value;
    this.dispatchEvent(
      new CustomEvent('summary-value-change', {
        bubbles: true,
        composed: true,
        detail: {value: this.editBuffer},
      })
    );
  }

  private _renderCurrentSummaryColumn() {
    return html`
      <div
        class="column-card"
        role="region"
        aria-labelledby="current-summary-header"
      >
        <div class="column-header" id="current-summary-header">
          <span>Current Feature Summary</span>
        </div>
        <div class="column-content ${!this.currentSummary ? 'empty' : ''}">
          ${
            this.currentSummary
              ? autolink(this.currentSummary, [], true)
              : '(No existing summary)'
          }
        </div>
      </div>
    `;
  }

  private _renderSuggestedSummaryColumn() {
    const displayText = this.editBuffer || this.suggestedSummary;

    return html`
      <div
        class="column-card"
        role="region"
        aria-labelledby="suggested-summary-header"
      >
        <div class="column-header" id="suggested-summary-header">
          <span>AI Suggested Summary</span>
          <sl-button
            size="small"
            variant="text"
            @click=${this.toggleEdit}
            ?disabled=${this.disabled}
          >
            <sl-icon
              slot="prefix"
              name=${this.isEditing ? 'eye' : 'pencil'}
            ></sl-icon>
            ${this.isEditing ? 'Preview' : 'Edit'}
          </sl-button>
        </div>
        <div class="column-content">
          ${
            this.isEditing
              ? html`
                  <sl-textarea
                    .value=${this.editBuffer}
                    rows="6"
                    placeholder="Edit summary..."
                    label="AI Suggested Summary Editor"
                    ?disabled=${this.disabled}
                    @input=${this._handleInput}
                  ></sl-textarea>
                `
              : autolink(displayText, [], true)
          }
          ${this._renderDocLinks()}
        </div>
      </div>
    `;
  }

  private _renderDocLinks() {
    if (!this.suggestedDocLinks || this.suggestedDocLinks.length === 0) {
      return nothing;
    }

    return html`
      <div class="sources-section">
        <div class="sources-title">Referenced Resources</div>
        <ul class="sources-list">
          ${this.suggestedDocLinks.map(
            url => html`
              <li>
                <a
                  class="source-link"
                  href="${url}"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <sl-badge variant="neutral" pill>${url}</sl-badge>
                </a>
              </li>
            `
          )}
        </ul>
      </div>
    `;
  }

  render() {
    return html`
      <div class="comparison-grid">
        ${this._renderCurrentSummaryColumn()}
        ${this._renderSuggestedSummaryColumn()}
      </div>
    `;
  }
}
