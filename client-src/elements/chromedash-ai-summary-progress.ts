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
import {customElement, property, state} from 'lit/decorators.js';
import '@shoelace-style/shoelace/dist/components/spinner/spinner.js';
import '@shoelace-style/shoelace/dist/components/icon/icon.js';
import '@shoelace-style/shoelace/dist/components/button/button.js';
import '@shoelace-style/shoelace/dist/components/badge/badge.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {ProgressStep, SummarySuggestion} from '../js-src/cs-client.js';

export const STEP_LABELS: Readonly<Record<string, string>> = Object.freeze({
  READ_SPEC: 'Reading specification',
  READ_EXPLAINER: 'Analyzing explainer document',
  SEARCH_MDN: 'Searching MDN documentation',
  VERIFY_DOC_LINK: 'Verifying documentation links',
  UNKNOWN: 'Processing feature data',
});

@customElement('chromedash-ai-summary-progress')
export class ChromedashAiSummaryProgress extends LitElement {
  @property({type: Number})
  featureId = 0;

  @property({attribute: false})
  suggestion: SummarySuggestion | null = null;

  @property({attribute: false})
  progressSteps: ProgressStep[] = [];

  @property({type: Boolean})
  compact = false;

  @property({type: Boolean})
  loading = false;

  @property({type: String})
  error: string | null = null;

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        :host {
          display: block;
        }

        :host([hidden]) {
          display: none;
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

        .container.compact .header {
          margin-bottom: var(--sl-spacing-2x-small);
        }

        .title {
          display: flex;
          align-items: center;
          gap: var(--sl-spacing-x-small);
          font-size: var(--sl-font-size-small);
          font-weight: var(--sl-font-weight-semibold);
          color: var(--sl-color-neutral-700);
        }

        sl-spinner {
          font-size: var(--sl-font-size-small);
          --indicator-color: var(--sl-color-primary-600);
          --track-width: 2px;
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
        }

        .container.compact .step-item {
          padding: 1px 0;
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

        .step-item.retrying {
          color: var(--sl-color-warning-700);
        }

        .step-item sl-icon {
          font-size: var(--sl-font-size-medium);
          flex-shrink: 0;
        }

        .step-label {
          min-width: 0;
        }

        .step-message {
          font-size: var(--sl-font-size-x-small);
          color: var(--sl-color-neutral-500);
          word-break: break-word;
          overflow-wrap: anywhere;
        }

        .error-banner {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: var(--sl-spacing-small);
          margin-top: var(--sl-spacing-small);
          padding: var(--sl-spacing-2x-small) var(--sl-spacing-small);
          background: var(--sl-color-danger-50);
          border: 1px solid var(--sl-color-danger-200);
          color: var(--sl-color-danger-800);
          border-radius: var(--sl-border-radius-small);
          font-size: var(--sl-font-size-small);
        }

        .error-banner span {
          min-width: 0;
          word-break: break-word;
        }

        .error-banner sl-button {
          flex-shrink: 0;
        }

        .error-banner sl-button::part(base) {
          color: var(--sl-color-danger-800);
          font-weight: var(--sl-font-weight-semibold);
          padding: 0 var(--sl-spacing-2x-small);
        }
      `,
    ];
  }

  async handleTrigger(force = false) {
    if (!this.featureId || this.loading) return;

    try {
      this.loading = true;
      this.error = null;

      await window.csClient.triggerSummaryGeneration(this.featureId, force);
      if (!this.isConnected) return;

      this._dispatchStartedEvent(force);
    } catch (err) {
      if (!this.isConnected) return;
      const error = err instanceof Error ? err : new Error(String(err));
      this.error = error.message || 'Failed to trigger summary generation task';
    } finally {
      if (this.isConnected) {
        this.loading = false;
      }
    }
  }

  private _dispatchStartedEvent(force: boolean) {
    this.dispatchEvent(
      new CustomEvent('summary-generation-started', {
        bubbles: true,
        composed: true,
        detail: {featureId: this.featureId, force},
      })
    );
  }

  renderStepIcon(step: ProgressStep) {
    switch (step.status) {
      case 'IN_PROGRESS':
        return html`<sl-spinner></sl-spinner>`;
      case 'SUCCESS':
        return html`<sl-icon name="check-lg"></sl-icon>`;
      case 'FAILED':
        return html`<sl-icon name="x-circle-fill"></sl-icon>`;
      case 'RETRYING':
        return html`<sl-icon name="exclamation-circle-fill"></sl-icon>`;
      default:
        return html`<sl-icon name="dash-square"></sl-icon>`;
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
        ${this.renderStepIcon(step)}
        <span class="step-label">${label}</span>
        ${safeMessage ? html`<span class="step-message">(${safeMessage})</span>` : nothing}
      </li>
    `;
  }

  get isTaskRunning(): boolean {
    return (
      this.loading ||
      this.progressSteps.some(
        s => s.status === 'IN_PROGRESS' || s.status === 'RETRYING'
      )
    );
  }

  render() {
    if (!this.progressSteps.length && !this.loading && !this.error) {
      return nothing;
    }

    const running = this.isTaskRunning;

    return html`
      <div class="container ${this.compact ? 'compact' : ''}">
        <div class="header">
          <span class="title">
            ${running ? html`<sl-spinner></sl-spinner>` : nothing} AI Summary
            Generation
          </span>
          ${
            running
              ? html`<sl-badge
                  variant="primary"
                  pill
                  size=${this.compact ? 'small' : 'medium'}
                >
                  Running
                </sl-badge>`
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
