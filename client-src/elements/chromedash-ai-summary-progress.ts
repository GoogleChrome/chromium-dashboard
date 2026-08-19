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
import {customElement, property} from 'lit/decorators.js';
import '@shoelace-style/shoelace/dist/components/spinner/spinner.js';
import '@shoelace-style/shoelace/dist/components/icon/icon.js';
import '@shoelace-style/shoelace/dist/components/button/button.js';
import '@shoelace-style/shoelace/dist/components/badge/badge.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {
  SummaryProgressStep as ProgressStep,
  SummaryProgressStepStatusEnum,
  SummaryProgressStepStepEnum,
} from 'chromestatus-openapi';

const MAX_STEP_MESSAGE_LENGTH = 300;
const DEFAULT_TRIGGER_ERROR_MESSAGE =
  'Failed to trigger summary generation task';
const DEFAULT_STEP_LABEL = 'Processing feature data';

/** Compile-time exhaustive map from pipeline step enum to human-readable label. */
export const STEP_LABELS: Readonly<
  Record<SummaryProgressStepStepEnum, string>
> = Object.freeze({
  [SummaryProgressStepStepEnum.READ_SPEC]: 'Reading specification',
  [SummaryProgressStepStepEnum.READ_EXPLAINER]: 'Analyzing explainer document',
  [SummaryProgressStepStepEnum.SEARCH_MDN]: 'Searching MDN documentation',
  [SummaryProgressStepStepEnum.VERIFY_DOC_LINK]:
    'Verifying documentation links',
  [SummaryProgressStepStepEnum.UNKNOWN]: DEFAULT_STEP_LABEL,
});

/** Compile-time exhaustive map from step execution status to CSS class names. */
export const STEP_STATUS_CSS_CLASSES: Readonly<
  Record<SummaryProgressStepStatusEnum, string>
> = Object.freeze({
  [SummaryProgressStepStatusEnum.IN_PROGRESS]: 'in-progress',
  [SummaryProgressStepStatusEnum.SUCCESS]: 'success',
  [SummaryProgressStepStatusEnum.FAILED]: 'failed',
  [SummaryProgressStepStatusEnum.RETRYING]: 'retrying',
});

/** Compile-time exhaustive map from step execution status to Shoelace icon names. */
export const STEP_STATUS_ICONS: Readonly<
  Record<
    Exclude<
      SummaryProgressStepStatusEnum,
      typeof SummaryProgressStepStatusEnum.IN_PROGRESS
    >,
    string
  >
> = Object.freeze({
  [SummaryProgressStepStatusEnum.SUCCESS]: 'check-lg',
  [SummaryProgressStepStatusEnum.FAILED]: 'x-circle-fill',
  [SummaryProgressStepStatusEnum.RETRYING]: 'exclamation-circle-fill',
});

/** Human-readable status descriptions for screen reader accessibility announcements. */
export const STATUS_LABELS: Readonly<
  Record<SummaryProgressStepStatusEnum, string>
> = Object.freeze({
  [SummaryProgressStepStatusEnum.IN_PROGRESS]: 'In progress',
  [SummaryProgressStepStatusEnum.SUCCESS]: 'Succeeded',
  [SummaryProgressStepStatusEnum.FAILED]: 'Failed',
  [SummaryProgressStepStatusEnum.RETRYING]: 'Retrying',
});

/**
 * UI presentational component displaying the live progress timeline of AI summary generation.
 *
 * @fires summary-generation-started - Dispatched when background generation is triggered.
 *   detail: { featureId: number, force: boolean }
 *
 * @example
 * ```html
 * <chromedash-ai-summary-progress
 *   .featureId=${123}
 *   .progressSteps=${steps}
 *   @summary-generation-started=${(e) => {
 *     console.log('Started generation for feature:', e.detail.featureId);
 *   }}
 * ></chromedash-ai-summary-progress>
 * ```
 */
@customElement('chromedash-ai-summary-progress')
export class ChromedashAiSummaryProgress extends LitElement {
  @property({type: Number})
  featureId = 0;

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

        .visually-hidden {
          position: absolute;
          width: 1px;
          height: 1px;
          padding: 0;
          margin: -1px;
          overflow: hidden;
          clip: rect(0, 0, 0, 0);
          white-space: nowrap;
          border: 0;
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

  get badgeSize(): 'small' | 'medium' {
    return this.compact ? 'small' : 'medium';
  }

  get isTaskRunning(): boolean {
    if (this.loading) return true;
    return this.progressSteps.some(
      s =>
        s.status === SummaryProgressStepStatusEnum.IN_PROGRESS ||
        s.status === SummaryProgressStepStatusEnum.RETRYING
    );
  }

  async handleTrigger(force = false) {
    if (!this.featureId || this.featureId <= 0) {
      console.warn(
        '[chromedash-ai-summary-progress] handleTrigger called with invalid featureId:',
        this.featureId
      );
      return;
    }
    if (this.loading) return;

    try {
      this.loading = true;
      this.error = null;

      await window.csClient.triggerSummaryGeneration(this.featureId, force);
      if (!this.isConnected) return;

      this._dispatchStartedEvent(force);
    } catch (err) {
      if (!this.isConnected) return;
      const errorMsg =
        err instanceof Error
          ? err.message
          : typeof err === 'object'
            ? JSON.stringify(err)
            : String(err);
      this.error = errorMsg || DEFAULT_TRIGGER_ERROR_MESSAGE;
    } finally {
      this.loading = false;
    }
  }

  /**
   * Dispatches composed event when generation task is successfully triggered.
   * @param force Whether this was a forced regeneration request.
   */
  private _dispatchStartedEvent(force: boolean) {
    this.dispatchEvent(
      new CustomEvent('summary-generation-started', {
        bubbles: true,
        composed: true,
        detail: {featureId: this.featureId, force},
      })
    );
  }

  renderStepIcon(status: SummaryProgressStepStatusEnum) {
    if (status === SummaryProgressStepStatusEnum.IN_PROGRESS) {
      return html`<sl-spinner aria-hidden="true"></sl-spinner>`;
    }
    const iconName =
      STEP_STATUS_ICONS[status as keyof typeof STEP_STATUS_ICONS];
    return iconName
      ? html`<sl-icon name="${iconName}" aria-hidden="true"></sl-icon>`
      : nothing;
  }

  renderStep(step: ProgressStep) {
    const label = STEP_LABELS[step.step] || step.step || DEFAULT_STEP_LABEL;
    const rawMsg = String(step.message || '');
    const safeMessage =
      rawMsg.length > MAX_STEP_MESSAGE_LENGTH
        ? `${rawMsg.slice(0, MAX_STEP_MESSAGE_LENGTH)}...`
        : rawMsg;
    const statusClass =
      STEP_STATUS_CSS_CLASSES[step.status] || 'unknown-status';
    const statusLabel = STATUS_LABELS[step.status] || String(step.status);

    return html`
      <li class="step-item ${statusClass}" role="listitem">
        ${this.renderStepIcon(step.status)}
        <span class="visually-hidden">Status: ${statusLabel}</span>
        <span class="step-label">${label}</span>
        ${
          safeMessage
            ? html`<span class="step-message">(${safeMessage})</span>`
            : nothing
        }
      </li>
    `;
  }

  private _renderHeader(running: boolean) {
    return html`
      <div class="header">
        <span class="title">
          ${
            running
              ? html`<sl-spinner aria-hidden="true"></sl-spinner>`
              : nothing
          }
          AI Summary Generation
        </span>
        ${
          running
            ? html`<sl-badge variant="primary" pill size=${this.badgeSize}>
                Running
              </sl-badge>`
            : nothing
        }
      </div>
    `;
  }

  private _renderErrorBanner() {
    if (!this.error) return nothing;
    return html`
      <div class="error-banner" role="alert">
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
    `;
  }

  render() {
    if (!this.progressSteps.length && !this.loading && !this.error) {
      return nothing;
    }

    const running = this.isTaskRunning;

    return html`
      <div
        class="container ${this.compact ? 'compact' : ''}"
        aria-live="polite"
      >
        ${this._renderHeader(running)}
        ${
          this.progressSteps.length
            ? html`
                <ul class="steps-list" role="list">
                  ${this.progressSteps.map(step => this.renderStep(step))}
                </ul>
              `
            : nothing
        }
        ${this._renderErrorBanner()}
      </div>
    `;
  }
}
