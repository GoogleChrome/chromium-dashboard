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
import '@shoelace-style/shoelace/dist/components/spinner/spinner.js';
import '@shoelace-style/shoelace/dist/components/icon/icon.js';
import '@shoelace-style/shoelace/dist/components/button/button.js';
import '@shoelace-style/shoelace/dist/components/badge/badge.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {
  SummaryProgressStep as ProgressStep,
  SummaryProgressStepStatusEnum,
  SummaryProgressStepStepEnum,
  SummarySuggestion,
  SummarySuggestionResponse,
} from 'chromestatus-openapi';
import {TaskProgressMonitor} from '../js-src/task-progress-monitor.js';
import {ChromeStatusHttpError} from '../js-src/cs-client.js';

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

  @property({type: Boolean})
  hideIdleTrigger = false;

  @state()
  loading = false;

  @state()
  error: string | null = null;

  @state()
  retryCooldownSeconds = 0;

  private _cooldownInterval: number | null = null;

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
        maxInitial404Retries: 1,
        onProgress: resp => {
          this.suggestion = resp.suggestion ?? null;
          this.progressSteps = resp.progress_steps ?? [];
        },
      });

      try {
        const resp = await this._monitor.run(signal);
        this.suggestion = resp.suggestion ?? null;
        this.progressSteps = resp.progress_steps ?? [];

        const failedStep = this.progressSteps.find(
          s => s.status === SummaryProgressStepStatusEnum.FAILED
        );
        if (failedStep) {
          this.error = this._formatErrorMessage(
            failedStep.message,
            DEFAULT_TRIGGER_ERROR_MESSAGE
          );
          this._dispatchFailedEvent(this.error);
        } else {
          this.error = null;
          this._dispatchCompletedEvent();
        }
        return resp;
      } catch (err) {
        const isAbort =
          signal?.aborted ||
          (err instanceof DOMException && err.name === 'AbortError') ||
          (err instanceof Error && err.name === 'AbortError');
        if (isAbort) return null;

        const is404 =
          (err instanceof ChromeStatusHttpError && err.status === 404) ||
          (err &&
            typeof err === 'object' &&
            'status' in err &&
            (err as {status: number}).status === 404);
        if (is404) {
          this.suggestion = null;
          this.progressSteps = [];
          this.error = null;
          this._clearCooldown();
          return null;
        }

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
        this._startCooldown(this._determineCooldownSeconds(errorMsg));
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

        .gemini-icon {
          width: 1.25rem;
          height: 1.25rem;
          flex-shrink: 0;
          transform-origin: center center;
          transition: transform 0.7s ease-in-out;
        }

        sl-button:hover .gemini-icon {
          transform: rotate(360deg);
        }

        @media (prefers-reduced-motion: reduce) {
          .gemini-icon {
            transition: none;
          }
          sl-button:hover .gemini-icon {
            transform: none;
          }
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

  private _isStepsActive(steps?: ProgressStep[]): boolean {
    if (!steps || steps.length === 0) return false;

    // Steps from the API are ordered descending by start_timestamp (newest first).
    // If the latest step has failed or completed, the task is no longer running.
    const latestStep = steps[0];
    if (
      latestStep.status === SummaryProgressStepStatusEnum.FAILED ||
      latestStep.status === SummaryProgressStepStatusEnum.SUCCESS
    ) {
      return false;
    }

    const now = Date.now();
    const STALE_STEP_TIMEOUT_MS = 5 * 60 * 1000; // 5 minutes

    return steps.some(s => {
      if (
        s.status !== SummaryProgressStepStatusEnum.IN_PROGRESS &&
        s.status !== SummaryProgressStepStatusEnum.RETRYING
      ) {
        return false;
      }
      if (s.start_timestamp) {
        const startTime =
          s.start_timestamp instanceof Date
            ? s.start_timestamp.getTime()
            : new Date(s.start_timestamp).getTime();
        if (!isNaN(startTime) && now - startTime > STALE_STEP_TIMEOUT_MS) {
          return false;
        }
      }
      return true;
    });
  }

  get isTaskRunning(): boolean {
    return (
      this.loading ||
      (this._monitor?.isRunning ?? false) ||
      this._isStepsActive(this.progressSteps)
    );
  }

  private _determineCooldownSeconds(errorMsg: string): number {
    const lower = errorMsg.toLowerCase();
    if (
      lower.includes('429') ||
      lower.includes('rate limit') ||
      lower.includes('quota') ||
      lower.includes('resource_exhausted') ||
      lower.includes('too many requests')
    ) {
      return 30;
    }
    return 5;
  }

  public _startCooldown(seconds: number) {
    this._clearCooldown();
    if (seconds <= 0) return;

    this.retryCooldownSeconds = seconds;
    this._cooldownInterval = window.setInterval(() => {
      if (this.retryCooldownSeconds > 1) {
        this.retryCooldownSeconds--;
      } else {
        this.retryCooldownSeconds = 0;
        this._clearCooldown();
      }
    }, 1000);
  }

  private _clearCooldown() {
    if (this._cooldownInterval !== null) {
      clearInterval(this._cooldownInterval);
      this._cooldownInterval = null;
    }
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    this._clearCooldown();
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
      this._clearCooldown();
    }
    if (changedProperties.has('progressSteps')) {
      const failedStep = this.progressSteps.find(
        s => s.status === SummaryProgressStepStatusEnum.FAILED
      );
      if (failedStep && !this.error) {
        this.error = this._formatErrorMessage(
          failedStep.message,
          DEFAULT_TRIGGER_ERROR_MESSAGE
        );
      }
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
    if (this.loading || this.retryCooldownSeconds > 0) return;

    try {
      this.loading = true;
      this.error = null;
      this.progressSteps = [];
      this.suggestion = null;
      this._clearCooldown();

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
      this._startCooldown(this._determineCooldownSeconds(errorMsg));
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
    const isCooldown = this.retryCooldownSeconds > 0;
    const retryLabel = isCooldown
      ? `Retry in ${this.retryCooldownSeconds}s`
      : 'Retry';

    return html`
      <div class="error-banner" role="alert">
        <span>${this.error}</span>
        <sl-button
          size="small"
          variant="text"
          ?disabled=${this.loading || isCooldown}
          ?loading=${this.loading}
          @click=${() => this.handleTrigger(true)}
          data-testid="ai-summary-banner-retry-button"
        >
          ${retryLabel}
        </sl-button>
      </div>
    `;
  }

  private _dispatchOpenDialogEvent() {
    this.dispatchEvent(
      new CustomEvent('summary-dialog-requested', {
        bubbles: true,
        composed: true,
      })
    );
  }

  private _renderCompactButton() {
    if (this.isTaskRunning) {
      return html`
        <sl-button
          size="small"
          variant="default"
          loading
          @click=${() => this._dispatchOpenDialogEvent()}
          title="AI generation in progress. Click to view status."
          data-testid="ai-summary-generating-button"
        >
          Generating summary...
        </sl-button>
      `;
    }

    if (this.error) {
      if (this.retryCooldownSeconds > 0) {
        return html`
          <sl-button
            size="small"
            variant="default"
            disabled
            title="${this.error}. Retry available in ${this.retryCooldownSeconds}s."
            data-testid="ai-summary-cooldown-button"
          >
            <sl-icon slot="prefix" name="hourglass-split"></sl-icon>
            Retry in ${this.retryCooldownSeconds}s
          </sl-button>
        `;
      }

      return html`
        <sl-button
          size="small"
          variant="danger"
          outline
          @click=${() => this.handleTrigger(true)}
          title="${this.error}. Click to retry."
          data-testid="ai-summary-retry-button"
        >
          <sl-icon slot="prefix" name="exclamation-triangle"></sl-icon>
          Failed · Retry
        </sl-button>
      `;
    }

    if (
      this.suggestion?.status === 'PENDING' &&
      this.suggestion.suggested_summary
    ) {
      return html`
        <sl-button
          size="small"
          variant="primary"
          @click=${() => this._dispatchCompletedEvent()}
          data-testid="review-ai-summary-button"
        >
          <sl-icon slot="prefix" name="pencil"></sl-icon>
          Review AI summary
        </sl-button>
      `;
    }

    if (this.hideIdleTrigger) {
      return nothing;
    }

    return html`
      <sl-button
        size="small"
        variant="default"
        ?disabled=${this.loading}
        @click=${() => this.handleTrigger(false)}
        data-testid="generate-ai-summary-button"
      >
        <img
          slot="prefix"
          class="gemini-icon"
          src="https://www.gstatic.com/images/branding/productlogos/gemini_2025/v1/192px.svg"
          alt="Gemini AI Logo"
        />
        Generate AI summary
      </sl-button>
    `;
  }

  render() {
    if (this.compact) {
      return this._renderCompactButton();
    }

    if (!this.progressSteps.length && !this.loading && !this.error) {
      if (this.hideIdleTrigger) {
        return nothing;
      }
      if (
        this.suggestion?.status === 'PENDING' &&
        this.suggestion.suggested_summary
      ) {
        return html`
          <sl-button
            variant="primary"
            size="medium"
            @click=${() => this._dispatchCompletedEvent()}
            data-testid="review-ai-summary-button"
          >
            <sl-icon slot="prefix" name="pencil"></sl-icon>
            Review AI summary
          </sl-button>
        `;
      }
      return html`
        <sl-button
          variant="default"
          size="medium"
          ?disabled=${this.loading}
          @click=${() => this.handleTrigger(false)}
          data-testid="generate-ai-summary-button"
        >
          <img
            slot="prefix"
            class="gemini-icon"
            src="https://www.gstatic.com/images/branding/productlogos/gemini_2025/v1/192px.svg"
            alt="Gemini AI Logo"
          />
          Generate AI summary
        </sl-button>
      `;
    }

    const running = this.isTaskRunning;

    return html`
      <div class="container" aria-live="polite">
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
