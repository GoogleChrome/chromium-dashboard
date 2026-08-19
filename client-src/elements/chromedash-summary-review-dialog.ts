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
import '@shoelace-style/shoelace/dist/components/dialog/dialog.js';
import '@shoelace-style/shoelace/dist/components/button/button.js';
import '@shoelace-style/shoelace/dist/components/textarea/textarea.js';
import '@shoelace-style/shoelace/dist/components/badge/badge.js';
import '@shoelace-style/shoelace/dist/components/alert/alert.js';
import '@shoelace-style/shoelace/dist/components/icon/icon.js';
import '@shoelace-style/shoelace/dist/components/spinner/spinner.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {ChromeStatusHttpError, SummarySuggestion} from '../js-src/cs-client.js';
import {autolink, showToastMessage} from './utils.js';

@customElement('chromedash-summary-review-dialog')
export class ChromedashSummaryReviewDialog extends LitElement {
  @property({type: Number})
  featureId = 0;

  @property({type: String})
  currentSummary = '';

  @property({attribute: false})
  suggestion: SummarySuggestion | null = null;

  @state()
  editedSummary = '';

  @state()
  isEditing = false;

  @state()
  loading = false;

  @state()
  occConflict = false;

  @state()
  errorMessage: string | null = null;

  @query('sl-dialog')
  dialogEl?: HTMLElement & {show: () => void; hide: () => void};

  @query('sl-textarea')
  textareaEl?: HTMLElement & {value: string};

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        sl-dialog {
          --width: 900px;
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

        .dialog-footer {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: var(--sl-spacing-small);
          width: 100%;
        }

        .footer-left {
          display: flex;
          align-items: center;
          gap: var(--sl-spacing-x-small);
        }

        .footer-right {
          display: flex;
          align-items: center;
          gap: var(--sl-spacing-small);
        }

        sl-alert {
          margin-bottom: var(--sl-spacing-medium);
        }
      `,
    ];
  }

  show() {
    this.dialogEl?.show();
  }

  hide() {
    this.dialogEl?.hide();
  }

  override willUpdate(changedProperties: PropertyValues) {
    if (changedProperties.has('suggestion')) {
      this.editedSummary = this.suggestion?.suggested_summary || '';
      this.isEditing = false;
      this.occConflict = false;
      this.errorMessage = null;
    }
  }

  toggleEdit() {
    if (this.isEditing && this.textareaEl) {
      this.editedSummary = this.textareaEl.value;
    }
    this.isEditing = !this.isEditing;
  }

  async handleAccept() {
    if (!this.featureId || !this.suggestion?.version_token || this.loading) {
      return;
    }

    if (this.isEditing && this.textareaEl) {
      this.editedSummary = this.textareaEl.value;
    }

    try {
      this.loading = true;
      this.errorMessage = null;
      this.occConflict = false;

      const resp = await window.csClient.updateSummarySuggestion(
        this.featureId,
        {
          status: 'APPLIED',
          suggested_summary: this.editedSummary,
          version_token: this.suggestion.version_token,
        }
      );

      this.dispatchEvent(
        new CustomEvent('summary-suggestion-applied', {
          bubbles: true,
          composed: true,
          detail: {
            featureId: this.featureId,
            summary: this.editedSummary,
            response: resp,
          },
        })
      );

      showToastMessage('AI summary applied successfully.');
      this.hide();
    } catch (err) {
      this._handleApiError(err);
    } finally {
      this.loading = false;
    }
  }

  async handleReject() {
    if (!this.featureId || !this.suggestion?.version_token || this.loading) {
      return;
    }

    try {
      this.loading = true;
      this.errorMessage = null;
      this.occConflict = false;

      const resp = await window.csClient.updateSummarySuggestion(
        this.featureId,
        {
          status: 'REJECTED',
          version_token: this.suggestion.version_token,
        }
      );

      this.dispatchEvent(
        new CustomEvent('summary-suggestion-rejected', {
          bubbles: true,
          composed: true,
          detail: {
            featureId: this.featureId,
            response: resp,
          },
        })
      );

      showToastMessage('AI summary discarded.');
      this.hide();
    } catch (err) {
      this._handleApiError(err);
    } finally {
      this.loading = false;
    }
  }

  async handleRegenerate() {
    if (!this.featureId || this.loading) return;

    try {
      this.loading = true;
      this.errorMessage = null;
      this.occConflict = false;

      await window.csClient.triggerSummaryGeneration(this.featureId, true);

      this.dispatchEvent(
        new CustomEvent('summary-generation-requested', {
          bubbles: true,
          composed: true,
          detail: {featureId: this.featureId, force: true},
        })
      );

      showToastMessage('Summary regeneration enqueued.');
      this.hide();
    } catch (err) {
      this._handleApiError(err);
    } finally {
      this.loading = false;
    }
  }

  async handleRefresh() {
    if (!this.featureId || this.loading) return;

    try {
      this.loading = true;
      this.errorMessage = null;
      this.occConflict = false;

      const resp = await window.csClient.getSummarySuggestion(this.featureId);
      this.suggestion = resp.suggestion ?? null;
      this.editedSummary = this.suggestion?.suggested_summary || '';
      this.isEditing = false;
    } catch (err) {
      this._handleApiError(err);
    } finally {
      this.loading = false;
    }
  }

  private _handleApiError(err: unknown) {
    if (err instanceof ChromeStatusHttpError && err.status === 409) {
      this.occConflict = true;
      this.errorMessage =
        'This suggestion was modified in another session. Please refresh to view the latest version.';
    } else {
      const error = err instanceof Error ? err : new Error(String(err));
      this.errorMessage = error.message || 'An unexpected error occurred.';
    }
  }

  renderDocLinks() {
    const links = this.suggestion?.suggested_doc_links;
    if (!links || !links.length) return nothing;

    return html`
      <div class="sources-section">
        <div class="sources-title">Referenced Resources</div>
        <ul class="sources-list">
          ${links.map(
            url => html`
              <li>
                <a
                  class="source-link"
                  href="${url}"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <sl-badge variant="neutral" pill> ${url} </sl-badge>
                </a>
              </li>
            `
          )}
        </ul>
      </div>
    `;
  }

  render() {
    const suggestedText =
      this.editedSummary || this.suggestion?.suggested_summary || '';

    return html`
      <sl-dialog label="Review AI Summary Suggestion">
        ${
          this.occConflict
            ? html`
                <sl-alert variant="warning" open>
                  <sl-icon slot="icon" name="exclamation-triangle"></sl-icon>
                  <span>${this.errorMessage}</span>
                  <sl-button
                    size="small"
                    variant="text"
                    @click=${this.handleRefresh}
                    ?disabled=${this.loading}
                  >
                    Refresh
                  </sl-button>
                </sl-alert>
              `
            : this.errorMessage
              ? html`
                  <sl-alert variant="danger" open>
                    <sl-icon slot="icon" name="exclamation-octagon"></sl-icon>
                    <span>${this.errorMessage}</span>
                  </sl-alert>
                `
              : nothing
        }

        <div class="comparison-grid">
          <div class="column-card">
            <div class="column-header">
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

          <div class="column-card">
            <div class="column-header">
              <span>AI Suggested Summary</span>
              <sl-button
                size="small"
                variant="text"
                @click=${this.toggleEdit}
                ?disabled=${this.loading}
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
                        .value=${this.editedSummary}
                        rows="6"
                        placeholder="Edit summary..."
                        @input=${(e: Event) => {
                          this.editedSummary = (
                            e.target as HTMLInputElement
                          ).value;
                        }}
                      ></sl-textarea>
                    `
                  : autolink(suggestedText, [], true)
              }
              ${this.renderDocLinks()}
            </div>
          </div>
        </div>

        <div slot="footer" class="dialog-footer">
          <div class="footer-left">
            <sl-button
              variant="default"
              size="small"
              @click=${this.handleRegenerate}
              ?loading=${this.loading}
              ?disabled=${this.loading}
            >
              <sl-icon slot="prefix" name="arrow-clockwise"></sl-icon>
              Regenerate
            </sl-button>
          </div>
          <div class="footer-right">
            <sl-button
              variant="default"
              size="small"
              @click=${this.hide}
              ?disabled=${this.loading}
            >
              Cancel
            </sl-button>
            <sl-button
              variant="danger"
              size="small"
              @click=${this.handleReject}
              ?loading=${this.loading}
              ?disabled=${this.loading || !this.suggestion}
            >
              Discard
            </sl-button>
            <sl-button
              variant="primary"
              size="small"
              @click=${this.handleAccept}
              ?loading=${this.loading}
              ?disabled=${this.loading || !this.suggestion || this.occConflict}
            >
              Accept & Apply
            </sl-button>
          </div>
        </div>
      </sl-dialog>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'chromedash-summary-review-dialog': ChromedashSummaryReviewDialog;
  }
}
