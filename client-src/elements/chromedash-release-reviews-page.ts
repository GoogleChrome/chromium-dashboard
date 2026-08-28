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
import '@shoelace-style/shoelace/dist/components/spinner/spinner.js';
import '@shoelace-style/shoelace/dist/components/button/button.js';
import '@shoelace-style/shoelace/dist/components/badge/badge.js';
import '@shoelace-style/shoelace/dist/components/icon/icon.js';
import '@shoelace-style/shoelace/dist/components/alert/alert.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {FORM_STYLES} from '../css/forms-css.js';
import {User, ChromeStatusHttpError} from '../js-src/cs-client.js';
import {
  SummarySuggestion,
  SummarySuggestionListResponse,
} from 'chromestatus-openapi';
import './chromedash-summary-review-dialog.js';
import type {ChromedashSummaryReviewDialog} from './chromedash-summary-review-dialog.js';
import './chromedash-release-feature-card.js';
import {showToastMessage} from './utils.js';

export interface PendingSuggestionItem extends SummarySuggestion {
  feature_id: number;
  feature_name?: string;
  hover_snippet?: string;
}

@customElement('chromedash-release-reviews-page')
export class ChromedashReleaseReviewsPage extends LitElement {
  @property({attribute: false})
  user?: User;

  @state()
  loading = true;

  @state()
  error: string | null = null;

  @state()
  suggestions: PendingSuggestionItem[] = [];

  @state()
  totalCount = 0;

  @state()
  nextCursor: string | null = null;

  @state()
  loadingMore = false;

  @state()
  activeReviewSuggestion: PendingSuggestionItem | null = null;

  @state()
  activeFeatureSummary = '';

  @query('chromedash-summary-review-dialog')
  reviewDialog?: ChromedashSummaryReviewDialog;

  static get styles() {
    return [
      ...SHARED_STYLES,
      ...FORM_STYLES,
      css`
        :host {
          display: block;
          padding: var(--content-padding);
          max-width: var(--max-content-width);
          margin: 0 auto;
        }

        .header-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: var(--sl-spacing-large);
          border-bottom: var(--default-border);
          padding-bottom: var(--sl-spacing-medium);
        }

        .header-left {
          display: flex;
          align-items: baseline;
          gap: var(--sl-spacing-small);
        }

        h1 {
          font-size: var(--sl-font-size-2x-large);
          font-weight: var(--sl-font-weight-semibold);
          color: var(--sl-color-neutral-900);
          margin: 0;
        }

        .queue-container {
          display: flex;
          flex-direction: column;
          gap: var(--sl-spacing-medium);
        }

        .queue-item-card {
          border: var(--default-border);
          border-radius: var(--sl-border-radius-medium);
          background: var(--card-background);
          padding: var(--content-padding);
          display: flex;
          flex-direction: column;
          gap: var(--sl-spacing-small);
          transition: box-shadow 0.2s ease-in-out;
        }

        .queue-item-card:hover {
          box-shadow: var(--card-box-shadow);
        }

        .item-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: var(--sl-spacing-small);
        }

        .feature-title {
          font-size: var(--sl-font-size-large);
          font-weight: var(--sl-font-weight-semibold);
          color: var(--sl-color-primary-700);
          text-decoration: none;
        }

        .feature-title:hover {
          text-decoration: underline;
        }

        .suggestion-preview {
          color: var(--sl-color-neutral-700);
          font-size: var(--sl-font-size-medium);
          line-height: var(--sl-line-height-dense);
          background: var(--sl-color-neutral-50);
          padding: var(--sl-spacing-small);
          border-radius: var(--sl-border-radius-small);
          border-left: 3px solid var(--sl-color-primary-500);
        }

        .item-footer {
          display: flex;
          align-items: center;
          justify-content: flex-end;
          gap: var(--sl-spacing-small);
          margin-top: var(--sl-spacing-2x-small);
        }

        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          text-align: center;
          padding: var(--sl-spacing-3x-large) var(--sl-spacing-large);
          border: var(--default-border);
          border-radius: var(--sl-border-radius-large);
          background: var(--card-background);
          color: var(--sl-color-neutral-600);
          gap: var(--sl-spacing-medium);
        }

        .empty-icon {
          font-size: 3rem;
          color: var(--sl-color-success-500);
        }

        .loading-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: var(--sl-spacing-3x-large);
          gap: var(--sl-spacing-medium);
        }

        .load-more-container {
          display: flex;
          justify-content: center;
          margin-top: var(--sl-spacing-large);
        }
      `,
    ];
  }

  connectedCallback() {
    super.connectedCallback();
    this.fetchPendingQueue();
  }

  override updated(changedProperties: PropertyValues) {
    if (changedProperties.has('user') && this.user) {
      this.fetchPendingQueue();
    }
  }

  async fetchPendingQueue(cursor?: string) {
    if (!cursor) {
      this.loading = true;
      this.error = null;
    } else {
      this.loadingMore = true;
    }

    try {
      const resp: SummarySuggestionListResponse =
        await window.csClient.getPendingSuggestionsQueue(25, cursor);
      const incoming = (resp.suggestions || []) as PendingSuggestionItem[];

      if (cursor) {
        this.suggestions = [...this.suggestions, ...incoming];
      } else {
        this.suggestions = incoming;
      }
      this.totalCount = resp.total_count || this.suggestions.length;
      this.nextCursor = resp.next_cursor || null;
    } catch (err) {
      if (err instanceof ChromeStatusHttpError && err.status === 403) {
        this.error = 'You do not have permission to view the review queue.';
      } else {
        this.error =
          'Failed to load pending summary suggestions. Please try again.';
      }
    } finally {
      this.loading = false;
      this.loadingMore = false;
    }
  }

  async handleOpenReview(item: PendingSuggestionItem) {
    this.activeReviewSuggestion = item;
    this.activeFeatureSummary = item.original_summary || '';
    await this.updateComplete;
    this.reviewDialog?.show();
  }

  handleSuggestionApplied(
    e: CustomEvent<{featureId: number; summary: string}>
  ) {
    const {featureId} = e.detail;
    this.suggestions = this.suggestions.filter(s => s.feature_id !== featureId);
    this.totalCount = Math.max(0, this.totalCount - 1);
    window.dispatchEvent(new CustomEvent('refetch-needed'));
  }

  handleSuggestionRejected(e: CustomEvent<{featureId: number}>) {
    const {featureId} = e.detail;
    this.suggestions = this.suggestions.filter(s => s.feature_id !== featureId);
    this.totalCount = Math.max(0, this.totalCount - 1);
    window.dispatchEvent(new CustomEvent('refetch-needed'));
  }

  renderQueueItem(item: PendingSuggestionItem) {
    return html`
      <div class="queue-item-card" data-testid="queue-item-${item.feature_id}">
        <div class="item-header">
          <a
            class="feature-title"
            href="/feature/${item.feature_id}"
            target="_blank"
            rel="noopener noreferrer"
          >
            ${item.feature_name || `Feature #${item.feature_id}`} ↗
          </a>
          <sl-badge variant="neutral" pill
            >Feature #${item.feature_id}</sl-badge
          >
        </div>

        <div class="suggestion-preview">
          ${item.suggested_summary || 'No summary text proposed.'}
        </div>

        <div class="item-footer">
          <sl-button
            variant="primary"
            size="small"
            @click=${() => this.handleOpenReview(item)}
            data-testid="review-button-${item.feature_id}"
          >
            <sl-icon slot="prefix" name="pencil"></sl-icon>
            Review suggestion
          </sl-button>
        </div>
      </div>
    `;
  }

  render() {
    if (this.loading) {
      return html`
        <div class="loading-container">
          <sl-spinner style="font-size: 2.5rem;"></sl-spinner>
          <div>Loading pending review queue...</div>
        </div>
      `;
    }

    if (this.error) {
      return html`
        <sl-alert variant="danger" open>
          <sl-icon slot="icon" name="exclamation-octagon"></sl-icon>
          <strong>Error:</strong> ${this.error}
          <div style="margin-top: var(--sl-spacing-small);">
            <sl-button size="small" @click=${() => this.fetchPendingQueue()}>
              Retry
            </sl-button>
          </div>
        </sl-alert>
      `;
    }

    return html`
      <div class="header-row">
        <div class="header-left">
          <h1>Release Notes Review Queue</h1>
          <sl-badge variant="primary" pill>${this.totalCount}</sl-badge>
        </div>
        <sl-button
          variant="default"
          size="small"
          @click=${() => this.fetchPendingQueue()}
        >
          <sl-icon slot="prefix" name="arrow-clockwise"></sl-icon>
          Refresh
        </sl-button>
      </div>

      ${
        this.suggestions.length === 0
          ? html`
              <div class="empty-state">
                <sl-icon class="empty-icon" name="check-circle"></sl-icon>
                <h2>All caught up!</h2>
                <p>
                  There are no pending AI summary suggestions awaiting editorial
                  review.
                </p>
              </div>
            `
          : html`
              <div class="queue-container">
                ${this.suggestions.map(item => this.renderQueueItem(item))}
              </div>

              ${
                this.nextCursor
                  ? html`
                      <div class="load-more-container">
                        <sl-button
                          variant="default"
                          ?loading=${this.loadingMore}
                          @click=${() => this.fetchPendingQueue(this.nextCursor!)}
                        >
                          Load more
                        </sl-button>
                      </div>
                    `
                  : nothing
              }
            `
      }

      <chromedash-summary-review-dialog
        .featureId=${this.activeReviewSuggestion?.feature_id || 0}
        .currentSummary=${this.activeFeatureSummary}
        .suggestion=${this.activeReviewSuggestion}
        @summary-suggestion-applied=${this.handleSuggestionApplied}
        @summary-suggestion-rejected=${this.handleSuggestionRejected}
      ></chromedash-summary-review-dialog>
    `;
  }
}
