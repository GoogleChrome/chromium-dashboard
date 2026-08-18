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
import {customElement, property, state} from 'lit/decorators.js';
import '@shoelace-style/shoelace/dist/components/spinner/spinner.js';
import '@shoelace-style/shoelace/dist/components/icon/icon.js';
import '@shoelace-style/shoelace/dist/components/button/button.js';
import '@shoelace-style/shoelace/dist/components/badge/badge.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {
  ChromeStatusHttpError,
  ProgressStep,
  SummarySuggestion,
} from '../js-src/cs-client.js';

export const STEP_LABELS: Readonly<Record<string, string>> = Object.freeze({
  READ_SPEC: 'Reading specification',
  READ_EXPLAINER: 'Analyzing explainer document',
  SEARCH_MDN: 'Searching MDN documentation',
  VERIFY_DOC_LINK: 'Verifying documentation links',
  UNKNOWN: 'Processing feature data',
});

const POLL_INTERVAL_MS = 2000;
const MAX_POLL_DURATION_MS = 5 * 60 * 1000; // 5 minutes max polling ceiling
const MAX_INITIAL_404_RETRIES = 5;

@customElement('chromedash-ai-summary-progress')
export class ChromedashAiSummaryProgress extends LitElement {
  @property({type: Number})
  featureId = 0;

  @property({type: Object})
  suggestion: SummarySuggestion | null = null;

  @property({type: Array})
  progressSteps: ProgressStep[] = [];

  @property({type: Boolean})
  autoPoll = true;

  @property({type: Boolean})
  compact = false;

  @state()
  loading = false;

  @state()
  error: string | null = null;

  @state()
  polling = false;

  private _pollTimer: number | null = null;
  private _pollStartTime = 0;
  private _consecutive404Count = 0;
  private _isFetching = false;
  private _pollGeneration = 0;

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        :host {
          display: block;
        }

        .container {
          background: var(--sl-color-neutral-50);
          border: 1px solid var(--sl-color-neutral-200);
          border-radius: var(--sl-border-radius-medium);
          padding: var(--sl-spacing-medium);
        }

        .container.compact {
          padding: var(--sl-spacing-small);
        }

        .header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: var(--sl-spacing-small);
        }

        .title {
          font-weight: var(--sl-font-weight-semibold);
          font-size: var(--sl-font-size-small);
          color: var(--sl-color-neutral-700);
          display: flex;
          align-items: center;
          gap: var(--sl-spacing-2x-small);
        }

        .steps-list {
          display: flex;
          flex-direction: column;
          gap: var(--sl-spacing-2x-small);
          list-style: none;
          margin: 0;
          padding: 0;
        }

        .step-item {
          display: flex;
          align-items: center;
          gap: var(--sl-spacing-x-small);
          font-size: var(--sl-font-size-small);
          color: var(--sl-color-neutral-600);
          padding: var(--sl-spacing-2x-small) 0;
        }

        .step-item.in-progress {
          color: var(--sl-color-primary-700);
          font-weight: var(--sl-font-weight-medium);
        }

        .step-item.success {
          color: var(--sl-color-success-700);
        }

        .step-item.failed {
          color: var(--sl-color-danger-700);
        }

        .step-icon {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 1.25rem;
          height: 1.25rem;
          flex-shrink: 0;
        }

        .success-icon {
          color: var(--sl-color-success-600);
        }

        .failed-icon {
          color: var(--sl-color-danger-600);
        }

        .pending-icon {
          color: var(--sl-color-neutral-400);
        }

        .retrying-icon {
          color: var(--sl-color-warning-600);
        }

        .step-message {
          font-size: var(--sl-font-size-2x-small);
          color: var(--sl-color-neutral-500);
          margin-left: var(--sl-spacing-2x-small);
        }

        .error-banner {
          background: var(--sl-color-danger-50);
          border: 1px solid var(--sl-color-danger-200);
          color: var(--sl-color-danger-800);
          border-radius: var(--sl-border-radius-small);
          padding: var(--sl-spacing-2x-small) var(--sl-spacing-x-small);
          font-size: var(--sl-font-size-small);
          margin-top: var(--sl-spacing-2x-small);
          display: flex;
          align-items: center;
          justify-content: space-between;
        }
      `,
    ];
  }

  connectedCallback() {
    super.connectedCallback();
    if (this.autoPoll && this.featureId > 0) {
      this.fetchStatus();
    }
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    this.stopPolling();
    this._isFetching = false;
  }

  override willUpdate(changedProperties: PropertyValues) {
    if (
      changedProperties.has('featureId') &&
      changedProperties.get('featureId') !== undefined
    ) {
      this.stopPolling();
      this.suggestion = null;
      this.progressSteps = [];
      this.error = null;
      this._consecutive404Count = 0;
      this._isFetching = false;
    }
  }

  override updated(changedProperties: PropertyValues) {
    if (
      changedProperties.has('featureId') &&
      changedProperties.get('featureId') !== undefined &&
      this.autoPoll &&
      this.featureId > 0
    ) {
      this.fetchStatus();
    }
  }

  async fetchStatus() {
    if (
      !this.featureId ||
      this.featureId <= 0 ||
      this._isFetching ||
      !this.isConnected
    ) {
      return;
    }

    const currentFeatureId = this.featureId;
    const currentGen = this._pollGeneration;

    try {
      this._isFetching = true;
      if (!this.polling) {
        this.loading = true;
      }
      const resp = await window.csClient.getSummarySuggestion(this.featureId);
      if (
        !this.isConnected ||
        this.featureId !== currentFeatureId ||
        this._pollGeneration !== currentGen
      ) {
        return;
      }

      this.suggestion = resp?.suggestion ?? null;
      this.progressSteps = Array.isArray(resp?.progress_steps)
        ? resp.progress_steps
        : [];
      this.error = null;
      this._consecutive404Count = 0;

      const hasActiveStep = this.progressSteps.some(
        s => s.status === 'IN_PROGRESS' || s.status === 'RETRYING'
      );
      const hasFailedStep = this.progressSteps.some(s => s.status === 'FAILED');

      if (hasActiveStep && !this.polling) {
        this.startPolling();
      } else if (
        !hasActiveStep &&
        (this.progressSteps.length > 0 || this.suggestion)
      ) {
        this.stopPolling();
        if (hasFailedStep) {
          this.dispatchEvent(
            new CustomEvent('summary-generation-failed', {
              bubbles: true,
              composed: true,
              detail: {
                featureId: this.featureId,
                suggestion: this.suggestion,
                progressSteps: this.progressSteps,
              },
            })
          );
        } else {
          this.dispatchCompletedEvent();
        }
      }
    } catch (err: any) {
      if (
        !this.isConnected ||
        this.featureId !== currentFeatureId ||
        this._pollGeneration !== currentGen
      ) {
        return;
      }

      const is404 =
        err instanceof ChromeStatusHttpError
          ? err.status === 404
          : err?.status === 404;

      if (is404) {
        this._consecutive404Count++;
        if (!this.polling) {
          this.stopPolling();
        } else if (this._consecutive404Count >= MAX_INITIAL_404_RETRIES) {
          this.stopPolling();
          this.error =
            'Summary generation task did not start or expired. Please retry.';
          this.dispatchEvent(
            new CustomEvent('summary-generation-failed', {
              bubbles: true,
              composed: true,
              detail: {
                featureId: this.featureId,
                suggestion: null,
                progressSteps: this.progressSteps,
                error: this.error,
              },
            })
          );
        }
      } else {
        const rawMsg = String(err?.message || '');
        this.error =
          rawMsg.length > 200
            ? `${rawMsg.slice(0, 200)}...`
            : rawMsg || 'Failed to fetch summary generation status';
        this.stopPolling();
      }
    } finally {
      this._isFetching = false;
      if (this.isConnected && !this.polling) {
        this.loading = false;
      }
    }
  }

  startPolling() {
    this.stopPolling();
    this.polling = true;
    const cycle = ++this._pollGeneration;
    this._pollStartTime = Date.now();
    this._scheduleNextPoll(cycle);
  }

  private _scheduleNextPoll(generation: number) {
    if (!this.polling || this._pollGeneration !== generation) return;

    this._pollTimer = window.setTimeout(async () => {
      this._pollTimer = null;
      if (!this.polling || this._pollGeneration !== generation) return;

      if (Date.now() - this._pollStartTime > MAX_POLL_DURATION_MS) {
        this.error = 'Summary generation timed out. Please retry.';
        this.stopPolling();
        return;
      }

      await this.fetchStatus();
      if (this.polling && this._pollGeneration === generation) {
        this._scheduleNextPoll(generation);
      }
    }, POLL_INTERVAL_MS);
  }

  stopPolling() {
    if (this._pollTimer) {
      window.clearTimeout(this._pollTimer);
      this._pollTimer = null;
    }
    this._pollGeneration++;
    this.polling = false;
  }

  async handleTrigger(force = false) {
    if (!this.featureId || this.loading) return;

    try {
      this.loading = true;
      this.error = null;
      this.progressSteps = [];
      this._consecutive404Count = 0;

      await window.csClient.triggerSummaryGeneration(this.featureId, force);
      if (!this.isConnected) return;

      this.startPolling();
      this.dispatchEvent(
        new CustomEvent('summary-generation-started', {
          bubbles: true,
          composed: true,
          detail: {featureId: this.featureId, force},
        })
      );
    } catch (err: any) {
      if (!this.isConnected) return;
      const rawMsg = String(err?.message || '');
      this.error =
        rawMsg.length > 200
          ? `${rawMsg.slice(0, 200)}...`
          : rawMsg || 'Failed to trigger summary generation task';
      this.stopPolling();
    } finally {
      if (this.isConnected) {
        this.loading = false;
      }
    }
  }

  private dispatchCompletedEvent() {
    this.dispatchEvent(
      new CustomEvent('summary-generation-completed', {
        bubbles: true,
        composed: true,
        detail: {
          featureId: this.featureId,
          suggestion: this.suggestion,
          progressSteps: this.progressSteps,
        },
      })
    );
  }

  renderStepIcon(step: ProgressStep) {
    switch (step.status) {
      case 'IN_PROGRESS':
        return html`<sl-spinner style="font-size: 0.85rem;"></sl-spinner>`;
      case 'SUCCESS':
        return html`<sl-icon name="check-lg" class="success-icon"></sl-icon>`;
      case 'FAILED':
        return html`<sl-icon
          name="x-circle-fill"
          class="failed-icon"
        ></sl-icon>`;
      case 'RETRYING':
        return html`<sl-icon
          name="exclamation-circle-fill"
          class="retrying-icon"
        ></sl-icon>`;
      default:
        return html`<sl-icon
          name="dash-square"
          class="pending-icon"
        ></sl-icon>`;
    }
  }

  renderStep(step: ProgressStep) {
    const stepKey = String(step.step || '');
    const label = Object.prototype.hasOwnProperty.call(STEP_LABELS, stepKey)
      ? STEP_LABELS[stepKey]
      : stepKey;
    const rawMsg = String(step.message || '');
    const safeMessage =
      rawMsg.length > 300 ? `${rawMsg.slice(0, 300)}...` : rawMsg;
    const statusClass = (step.status || '').toLowerCase().replace(/_/g, '-');

    return html`
      <li class="step-item ${statusClass}">
        <span class="step-icon">${this.renderStepIcon(step)}</span>
        <span class="step-label">${label}</span>
        ${safeMessage ? html`<span class="step-message">(${safeMessage})</span>` : nothing}
      </li>
    `;
  }

  render() {
    if (!this.progressSteps.length && !this.loading && !this.error) {
      return nothing;
    }

    return html`
      <div class="container ${this.compact ? 'compact' : ''}">
        <div class="header">
          <span class="title">
            ${this.polling ? html`<sl-spinner style="font-size: 0.85rem;"></sl-spinner>` : nothing}
            AI Summary Generation
          </span>
          ${
            this.polling
              ? html`<sl-badge variant="primary" pill>Running</sl-badge>`
              : nothing
          }
        </div>

        ${
          this.progressSteps.length
            ? html`
                <ul class="steps-list">
                  ${this.progressSteps.map(step => this.renderStep(step))}
                </ul>
              `
            : nothing
        }
        ${
          this.error
            ? html`
                <div class="error-banner">
                  <span>${this.error}</span>
                  <sl-button
                    size="small"
                    variant="text"
                    ?disabled=${this.loading}
                    ?loading=${this.loading}
                    @click=${() => this.handleTrigger(true)}
                  >
                    Retry
                  </sl-button>
                </div>
              `
            : nothing
        }
      </div>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'chromedash-ai-summary-progress': ChromedashAiSummaryProgress;
  }
}
