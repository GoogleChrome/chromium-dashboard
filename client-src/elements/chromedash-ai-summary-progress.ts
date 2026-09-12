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

import {Task} from '@lit/task';
import {LitElement, PropertyValues, css, html, nothing} from 'lit';
import {customElement, property, state} from 'lit/decorators.js';
import '@cordwainer/cw-elements/dist/components/spinner/spinner.js';
import '@cordwainer/cw-elements/dist/components/icon/icon.js';
import '@cordwainer/cw-elements/dist/components/button/button.js';
import '@cordwainer/cw-elements/dist/components/badge/badge.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {
  SummaryProgressStep as ProgressStep,
  SummaryProgressStepStatusEnum,
  SummaryProgressStepStepEnum,
  SummarySuggestion,
  SummarySuggestionResponse,
} from 'chromestatus-openapi';
import {TaskProgressMonitor} from '../js-src/task-progress-monitor.js';

const MAX_STEP_MESSAGE_LENGTH = 300;
const MAX_ERROR_MESSAGE_LENGTH = 200;
const DEFAULT_TRIGGER_ERROR_MESSAGE =
  'Failed to trigger summary generation task';
const DEFAULT_FETCH_ERROR_MESSAGE = 'Failed to fetch summary generation status';
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
 * Component displaying live progress timeline and background execution polling for AI summary generation.
 *
 * @fires summary-generation-started - Dispatched when background generation is triggered.
 *   detail: { featureId: number, force: boolean }
 * @fires summary-generation-completed - Dispatched when generation completes successfully.
 *   detail: { featureId: number, suggestion: SummarySuggestion | null, progressSteps: ProgressStep[] }
 * @fires summary-generation-failed - Dispatched when a pipeline step fails.
 *   detail: { featureId: number, suggestion: SummarySuggestion | null, progressSteps: ProgressStep[], error?: string }
 */
@customElement('chromedash-ai-summary-progress')
export class ChromedashAiSummaryProgress extends LitElement {
  @property({type: Number})
  featureId = 0;

  @property({attribute: false})
  suggestion: SummarySuggestion | null = null;

  @property({attribute: false})
  progressSteps: ProgressStep[] = [];

  @property({type: Boolean})
  autoPoll = true;

  @property({type: Boolean})
  compact = false;

  @state()
  loading = false;

  @state()
  error: string | null = null;

  private _monitor: TaskProgressMonitor<SummarySuggestionResponse> | null =
    null;

  /**
   * Reactive @lit/task managing background polling and lifecycle integration.
   * Exposed with a leading underscore as a public lifecycle and testing hook so
   * test suites and integration harnesses can inspect execution state or trigger
   * manual task runs deterministically.
   */
  public _statusTask = new Task(this, {
    task: async ([featureId, autoPoll], {signal}) => {
      if (!featureId || featureId <= 0 || !autoPoll) {
        return null;
      }

      this.error = null;
      this._monitor = new TaskProgressMonitor<SummarySuggestionResponse>({
        fetcher: () => window.csClient.getSummarySuggestion(featureId),
        shouldContinue: resp => this._isStepsActive(resp.progress_steps),
        onProgress: resp => {
          this.suggestion = resp.suggestion ?? null;
          this.progressSteps = resp.progress_steps ?? [];
        },
      });

      try {
        const resp = await this._monitor.run(signal);
        this.suggestion = resp.suggestion ?? null;
        this.progressSteps = resp.progress_steps ?? [];

        const hasFailed = this.progressSteps.some(
          s => s.status === SummaryProgressStepStatusEnum.FAILED
        );
        if (hasFailed) {
          this._dispatchFailedEvent();
        } else {
          this._dispatchCompletedEvent();
        }
        return resp;
      } catch (err) {
        const isAbort =
          signal?.aborted ||
          (err instanceof DOMException && err.name === 'AbortError') ||
          (err instanceof Error && err.name === 'AbortError');
        if (isAbort) return null;

        const errorMsg =
          err instanceof Error
            ? err.message
            : typeof err === 'object'
              ? JSON.stringify(err)
              : String(err);
        this.error = this._formatErrorMessage(
          errorMsg,
          DEFAULT_FETCH_ERROR_MESSAGE
        );
        this._dispatchFailedEvent(this.error);
        throw err;
      } finally {
        this._monitor = null;
      }
    },
    args: () => [this.featureId, this.autoPoll],
  });

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
          background: var(--cw-color-neutral-50);
          border: 1px solid var(--cw-color-neutral-200);
          border-radius: var(--cw-border-radius-medium);
          padding: var(--cw-spacing-medium);
        }

        .container.compact {
          padding: var(--cw-spacing-small);
        }

        .header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: var(--cw-spacing-small);
        }

        .container.compact .header {
          margin-bottom: var(--cw-spacing-2x-small);
        }

        .title {
          display: flex;
          align-items: center;
          gap: var(--cw-spacing-x-small);
          font-size: var(--cw-font-size-small);
          font-weight: var(--cw-font-weight-semibold);
          color: var(--cw-color-neutral-700);
        }

        cw-spinner {
          font-size: var(--cw-font-size-small);
          --indicator-color: var(--cw-color-primary-600);
          --track-width: 2px;
        }

        .steps-list {
          display: flex;
          flex-direction: column;
          gap: var(--cw-spacing-2x-small);
          list-style: none;
          margin: 0;
          padding: 0;
        }

        .step-item {
          display: flex;
          align-items: center;
          gap: var(--cw-spacing-x-small);
          font-size: var(--cw-font-size-small);
          color: var(--cw-color-neutral-600);
        }

        .container.compact .step-item {
          padding: 1px 0;
        }

        .step-item.in-progress {
          color: var(--cw-color-primary-700);
          font-weight: var(--cw-font-weight-medium);
        }

        .step-item.success {
          color: var(--cw-color-success-700);
        }

        .step-item.failed {
          color: var(--cw-color-danger-700);
        }

        .step-item.retrying {
          color: var(--cw-color-warning-700);
        }

        .step-item cw-icon {
          font-size: var(--cw-font-size-medium);
          flex-shrink: 0;
        }

        .step-label {
          min-width: 0;
        }

        .step-message {
          font-size: var(--cw-font-size-x-small);
          color: var(--cw-color-neutral-500);
          word-break: break-word;
          overflow-wrap: anywhere;
        }

        .error-banner {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: var(--cw-spacing-small);
          margin-top: var(--cw-spacing-small);
          padding: var(--cw-spacing-2x-small) var(--cw-spacing-small);
          background: var(--cw-color-danger-50);
          border: 1px solid var(--cw-color-danger-200);
          color: var(--cw-color-danger-800);
          border-radius: var(--cw-border-radius-small);
          font-size: var(--cw-font-size-small);
        }

        .error-banner span {
          min-width: 0;
          word-break: break-word;
        }

        .error-banner cw-button {
          flex-shrink: 0;
        }

        .error-banner cw-button::part(base) {
          color: var(--cw-color-danger-800);
          font-weight: var(--cw-font-weight-semibold);
          padding: 0 var(--cw-spacing-2x-small);
        }
      `,
    ];
  }

  get badgeSize(): 'small' | 'medium' {
    return this.compact ? 'small' : 'medium';
  }

  private _isStepsActive(steps?: ProgressStep[]): boolean {
    if (!steps || steps.length === 0) return false;
    return steps.some(
      s =>
        s.status === SummaryProgressStepStatusEnum.IN_PROGRESS ||
        s.status === SummaryProgressStepStatusEnum.RETRYING
    );
  }

  get isTaskRunning(): boolean {
    return (
      this.loading ||
      (this._monitor?.isRunning ?? false) ||
      this._isStepsActive(this.progressSteps)
    );
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    if (this._monitor) {
      this._monitor.stop();
      this._monitor = null;
    }
  }

  override willUpdate(changedProperties: PropertyValues) {
    if (
      changedProperties.has('featureId') &&
      changedProperties.get('featureId') !== undefined
    ) {
      if (this._monitor) {
        this._monitor.stop();
        this._monitor = null;
      }
      this.suggestion = null;
      this.progressSteps = [];
      this.error = null;
    }
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
      this.progressSteps = [];
      this.suggestion = null;

      await window.csClient.triggerSummaryGeneration(this.featureId, force);
      if (!this.isConnected) return;

      this._dispatchStartedEvent(force);
      await this._statusTask.run();
    } catch (err) {
      if (!this.isConnected) return;
      const errorMsg =
        err instanceof Error
          ? err.message
          : typeof err === 'object'
            ? JSON.stringify(err)
            : String(err);
      this.error = this._formatErrorMessage(
        errorMsg,
        DEFAULT_TRIGGER_ERROR_MESSAGE
      );
    } finally {
      this.loading = false;
    }
  }

  private _formatErrorMessage(
    rawMsg: string | undefined | null,
    fallback: string
  ): string {
    const trimmed = (rawMsg || '').trim();
    if (!trimmed) return fallback;
    return trimmed.length > MAX_ERROR_MESSAGE_LENGTH
      ? `${trimmed.slice(0, MAX_ERROR_MESSAGE_LENGTH)}...`
      : trimmed;
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

  private _dispatchCompletedEvent() {
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

  private _dispatchFailedEvent(error?: string | null) {
    this.dispatchEvent(
      new CustomEvent('summary-generation-failed', {
        bubbles: true,
        composed: true,
        detail: {
          featureId: this.featureId,
          suggestion: this.suggestion,
          progressSteps: this.progressSteps,
          ...(error !== undefined && {error}),
        },
      })
    );
  }

  renderStepIcon(status: SummaryProgressStepStatusEnum) {
    if (status === SummaryProgressStepStatusEnum.IN_PROGRESS) {
      return html`<cw-spinner aria-hidden="true"></cw-spinner>`;
    }
    const iconName =
      STEP_STATUS_ICONS[status as keyof typeof STEP_STATUS_ICONS];
    return iconName
      ? html`<cw-icon name="${iconName}" aria-hidden="true"></cw-icon>`
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
              ? html`<cw-spinner aria-hidden="true"></cw-spinner>`
              : nothing
          }
          AI Summary Generation
        </span>
        ${
          running
            ? html`<cw-badge variant="primary" pill size=${this.badgeSize}>
                Running
              </cw-badge>`
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
        <cw-button
          size="small"
          variant="text"
          ?disabled=${this.loading}
          ?loading=${this.loading}
          @click=${() => this.handleTrigger(true)}
        >
          Retry
        </cw-button>
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
