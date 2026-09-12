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
import type CwDialog from '@cordwainer/cw-elements/dist/components/dialog/dialog.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {ChromeStatusHttpError} from '../js-src/cs-client.js';
import {
  SummarySuggestion,
  SummarySuggestionPatchRequest,
  SummarySuggestionStatusEnum,
} from 'chromestatus-openapi';
import './chromedash-summary-diff-view.js';
import {showToastMessage} from './utils.js';

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
  newerSuggestionAvailable = false;

  @state()
  errorMessage: string | null = null;

  @query('cw-dialog')
  dialogEl?: CwDialog;

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        cw-dialog {
          --width: min(900px, 95vw);
        }

        cw-alert {
          margin-bottom: var(--cw-spacing-medium);
        }

        .dialog-footer {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: var(--cw-spacing-small);
          width: 100%;
        }

        .footer-left {
          display: flex;
          align-items: center;
          gap: var(--cw-spacing-x-small);
        }

        .footer-right {
          display: flex;
          align-items: center;
          gap: var(--cw-spacing-small);
        }

        @media (max-width: 768px) {
          .dialog-footer {
            flex-direction: column-reverse;
            align-items: stretch;
            gap: var(--cw-spacing-medium);
          }

          .footer-left,
          .footer-right {
            width: 100%;
            display: flex;
            flex-wrap: wrap;
            gap: var(--cw-spacing-small);
          }

          .footer-left cw-button {
            width: 100%;
          }

          .footer-right cw-button {
            flex: 1 1 110px;
            min-width: 0;
          }
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
      const newSuggested = this.suggestion?.suggested_summary || '';
      if (this.isEditing && this.editedSummary !== newSuggested) {
        // User has uncommitted edits in flight. Preserve them to avoid silent data loss,
        // and notify the user that a newer server suggestion was received.
        this.newerSuggestionAvailable = true;
      } else {
        this.editedSummary = newSuggested;
        this.isEditing = false;
        this.newerSuggestionAvailable = false;
        this.occConflict = false;
        this.errorMessage = null;
      }
    }
  }

  handleLoadNewestSuggestion() {
    this.editedSummary = this.suggestion?.suggested_summary || '';
    this.isEditing = false;
    this.newerSuggestionAvailable = false;
  }

  handleDismissNewerSuggestion() {
    this.newerSuggestionAvailable = false;
  }

  // Extracted API client delegates for modular testing and component extension
  async applySuggestion(
    featureId: number,
    patch: SummarySuggestionPatchRequest
  ) {
    return window.csClient.updateSummarySuggestion(featureId, patch);
  }

  async rejectSuggestion(
    featureId: number,
    patch: SummarySuggestionPatchRequest
  ) {
    return window.csClient.updateSummarySuggestion(featureId, patch);
  }

  async fetchSuggestion(featureId: number) {
    return window.csClient.getSummarySuggestion(featureId);
  }

  async triggerRegeneration(featureId: number, force: boolean) {
    return window.csClient.triggerSummaryGeneration(featureId, force);
  }

  async handleAccept() {
    if (
      !this.featureId ||
      typeof this.suggestion?.version_token !== 'number' ||
      this.loading
    ) {
      return;
    }

    try {
      this.loading = true;
      this.errorMessage = null;
      this.occConflict = false;

      // OCC version_token guards against mid-air collision overwrites if another
      // editor or background task modified the suggestion during review.
      const patch: SummarySuggestionPatchRequest = {
        status: SummarySuggestionStatusEnum.APPLIED,
        suggested_summary: this.editedSummary,
        version_token: this.suggestion.version_token,
      };
      const resp = await this.applySuggestion(this.featureId, patch);

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
    if (
      !this.featureId ||
      typeof this.suggestion?.version_token !== 'number' ||
      this.loading
    ) {
      return;
    }

    try {
      this.loading = true;
      this.errorMessage = null;
      this.occConflict = false;

      const patch: SummarySuggestionPatchRequest = {
        status: SummarySuggestionStatusEnum.REJECTED,
        version_token: this.suggestion.version_token,
      };
      const resp = await this.rejectSuggestion(this.featureId, patch);

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

      await this.triggerRegeneration(this.featureId, true);

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
      this.newerSuggestionAvailable = false;

      const resp = await this.fetchSuggestion(this.featureId);
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

  private _renderAlertBanner() {
    if (this.occConflict) {
      return html`
        <cw-alert variant="warning" open>
          <cw-icon slot="icon" name="exclamation-triangle"></cw-icon>
          <span>${this.errorMessage}</span>
          <cw-button
            size="small"
            variant="text"
            @click=${this.handleRefresh}
            ?disabled=${this.loading}
          >
            Refresh
          </cw-button>
        </cw-alert>
      `;
    }

    if (this.newerSuggestionAvailable) {
      return html`
        <cw-alert variant="primary" open>
          <cw-icon slot="icon" name="info-circle"></cw-icon>
          <span>A newer suggestion is available on the server.</span>
          <cw-button
            size="small"
            variant="text"
            @click=${this.handleLoadNewestSuggestion}
          >
            Load Newest
          </cw-button>
          <cw-button
            size="small"
            variant="text"
            @click=${this.handleDismissNewerSuggestion}
          >
            Keep My Edits
          </cw-button>
        </cw-alert>
      `;
    }

    if (this.errorMessage) {
      return html`
        <cw-alert variant="danger" open>
          <cw-icon slot="icon" name="exclamation-octagon"></cw-icon>
          <span>${this.errorMessage}</span>
        </cw-alert>
      `;
    }

    return nothing;
  }

  private _renderFooter() {
    const isAcceptDisabled =
      this.loading ||
      !this.suggestion ||
      typeof this.suggestion.version_token !== 'number' ||
      this.occConflict;

    const isDiscardDisabled =
      this.loading ||
      !this.suggestion ||
      typeof this.suggestion.version_token !== 'number';

    return html`
      <div slot="footer" class="dialog-footer">
        <div class="footer-left">
          <cw-button
            variant="default"
            size="small"
            @click=${this.handleRegenerate}
            ?loading=${this.loading}
            ?disabled=${this.loading}
          >
            <cw-icon slot="prefix" name="arrow-clockwise"></cw-icon>
            Regenerate
          </cw-button>
        </div>
        <div class="footer-right">
          <cw-button
            variant="default"
            size="small"
            @click=${this.hide}
            ?disabled=${this.loading}
          >
            Cancel
          </cw-button>
          <cw-button
            variant="danger"
            size="small"
            @click=${this.handleReject}
            ?loading=${this.loading}
            ?disabled=${isDiscardDisabled}
          >
            Discard
          </cw-button>
          <cw-button
            variant="primary"
            size="small"
            @click=${this.handleAccept}
            ?loading=${this.loading}
            ?disabled=${isAcceptDisabled}
          >
            Accept & Apply
          </cw-button>
        </div>
      </div>
    `;
  }

  render() {
    return html`
      <cw-dialog label="Review AI Summary Suggestion">
        ${this._renderAlertBanner()}

        <chromedash-summary-diff-view
          .currentSummary=${this.currentSummary}
          .suggestedSummary=${this.editedSummary}
          .suggestedDocLinks=${this.suggestion?.suggested_doc_links ?? []}
          .isEditing=${this.isEditing}
          .disabled=${this.loading}
          @summary-edit-toggle=${(
            e: CustomEvent<{isEditing: boolean; value: string}>
          ) => {
            this.isEditing = e.detail.isEditing;
            this.editedSummary = e.detail.value;
          }}
          @summary-value-change=${(e: CustomEvent<{value: string}>) => {
            this.editedSummary = e.detail.value;
          }}
        ></chromedash-summary-diff-view>

        ${this._renderFooter()}
      </cw-dialog>
    `;
  }
}
