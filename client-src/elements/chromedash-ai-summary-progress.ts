import {LitElement, css, html, nothing, TemplateResult} from 'lit';
import {customElement, property, state} from 'lit/decorators.js';
import {SHARED_STYLES} from '../css/shared-css.js';

export interface ProgressStep {
  step_id: string;
  start_timestamp: string;
  end_timestamp: string | null;
  message: string;
  status: 'in_progress' | 'success' | 'failed' | 'retrying';
}

export interface SuggestionData {
  status: string;
  status_message?: string;
  model_used?: string;
  progress_steps?: ProgressStep[];
}

@customElement('chromedash-ai-summary-progress')
export class ChromedashAiSummaryProgress extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        :host {
          display: block;
          width: 100%;
        }

        .progress-container {
          display: flex;
          flex-direction: column;
          gap: 8px;
          width: 100%;
          margin-top: var(--content-padding-half);
        }

        .collapsed-row {
          display: flex;
          align-items: center;
          gap: 8px;
          width: 100%;
        }

        .gemini-pulse-icon {
          width: 16px;
          height: 16px;
          animation: pulse-glow 2s infinite ease-in-out;
        }

        @keyframes pulse-glow {
          0%,
          100% {
            transform: scale(1);
            opacity: 0.8;
          }
          50% {
            transform: scale(1.15);
            opacity: 1;
          }
        }

        .active-step-preview {
          font-family: var(--sl-font-mono);
          font-size: 0.8rem;
          color: var(--sl-color-neutral-500);
          flex-grow: 1;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .details-toggle-btn {
          background: none;
          border: none;
          color: var(--sl-color-primary-600);
          font-size: 0.8rem;
          cursor: pointer;
          font-weight: 500;
          padding: 4px 8px;
          min-height: 32px;
          display: flex;
          align-items: center;
          gap: 4px;
        }

        .details-toggle-btn:hover {
          text-decoration: underline;
        }

        /* Micro-Progress Bar */
        .micro-progress-bar {
          display: flex;
          gap: 3px;
          width: 100%;
          height: 3px;
          background: var(--sl-color-neutral-200);
          border-radius: 2px;
          overflow: hidden;
        }

        .progress-segment {
          flex-grow: 1;
          height: 100%;
          transition: background-color 0.3s ease;
        }

        .progress-segment.complete {
          background: var(--sl-color-success-500);
        }

        .progress-segment.active {
          background: var(--sl-color-primary-500);
          animation: pulse-bar 1.5s infinite ease-in-out;
        }

        @keyframes pulse-bar {
          0%,
          100% {
            opacity: 0.6;
          }
          50% {
            opacity: 1;
          }
        }

        .progress-segment.pending {
          background: var(--sl-color-neutral-300);
        }

        /* Micro-Console Timeline Tray */
        .timeline-console-tray {
          width: 100%;
          max-height: 140px;
          overflow-y: auto;
          background: var(--sl-color-neutral-950);
          border: 1px solid var(--sl-color-neutral-800);
          border-radius: 4px;
          padding: 8px 12px;
          font-family: var(--sl-font-mono);
          font-size: 0.75rem;
          color: var(--sl-color-neutral-300);
          box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
        }

        /* Thin scrollbar for console tray */
        .timeline-console-tray::-webkit-scrollbar {
          width: 6px;
        }
        .timeline-console-tray::-webkit-scrollbar-track {
          background: var(--sl-color-neutral-950);
        }
        .timeline-console-tray::-webkit-scrollbar-thumb {
          background: var(--sl-color-neutral-800);
          border-radius: 3px;
        }

        .console-line {
          display: flex;
          align-items: flex-start;
          gap: 10px;
          line-height: 1.5;
          margin-bottom: 4px;
        }

        .console-line:last-child {
          margin-bottom: 0;
        }

        /* Status Colors & Icons */
        .console-icon {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 14px;
          height: 14px;
          margin-top: 2px;
        }

        .console-line.in_progress {
          color: var(--sl-color-primary-400);
        }
        .console-line.success {
          color: var(--sl-color-success-400);
        }
        .console-line.failed {
          color: var(--sl-color-danger-400);
        }
        .console-line.retrying {
          color: var(--sl-color-warning-400);
        }
        .console-line.pruned-marker-line {
          color: var(--sl-color-neutral-500);
          font-style: italic;
        }

        .timeline-spinner {
          width: 12px;
          height: 12px;
          border: 2px solid currentColor;
          border-right-color: transparent;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }

        .timeline-success-pop {
          animation: pop-in 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
        }

        @keyframes pop-in {
          0% {
            transform: scale(0);
            opacity: 0;
          }
          100% {
            transform: scale(1);
            opacity: 1;
          }
        }

        .timeline-error-shake {
          animation: shake 0.4s ease-in-out;
        }

        @keyframes shake {
          0%,
          100% {
            transform: translateX(0);
          }
          25% {
            transform: translateX(-2px);
          }
          75% {
            transform: translateX(2px);
          }
        }

        .console-time {
          color: var(--sl-color-neutral-600);
          user-select: none;
        }

        .console-msg {
          flex-grow: 1;
          word-break: break-word;
        }

        .console-elapsed {
          color: var(--sl-color-neutral-500);
          text-align: right;
          min-width: 45px;
          user-select: none;
        }

        /* Active checking indicator at top right */
        .checking-indicator {
          font-size: 0.7rem;
          color: var(--sl-color-neutral-500);
          display: flex;
          align-items: center;
          gap: 4px;
          margin-left: auto;
        }

        .checking-dot {
          width: 6px;
          height: 6px;
          background: var(--sl-color-primary-500);
          border-radius: 50%;
          animation: pulse-dot 1.2s infinite ease-in-out;
        }

        @keyframes pulse-dot {
          0%,
          100% {
            opacity: 0.4;
          }
          50% {
            opacity: 1;
          }
        }

        /* Responsive Mobile Layouts */
        @media (max-width: 767px) {
          .active-step-preview {
            display: none; /* Hide step description on mobile to prevent overflow */
          }

          .console-time {
            display: none; /* Hide absolute time column on mobile */
          }

          .timeline-console-tray {
            padding: 6px 8px;
            max-height: 120px;
          }

          .details-toggle-btn {
            margin-left: auto; /* Push toggle to the right */
            min-width: 44px;
            min-height: 44px; /* Accessible touch target */
          }
        }
      `,
    ];
  }

  @property({type: Number})
  featureId!: number;

  @state()
  suggestion: SuggestionData | null = null;

  @state()
  timelineExpanded = false;

  @state()
  isFetching = false;

  private _pollingInterval?: number;
  private _abortController?: AbortController;

  connectedCallback() {
    super.connectedCallback();
    void this.fetchSuggestion(true); // Initial fetch
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    this.stopPolling();
    if (this._abortController) {
      this._abortController.abort();
    }
  }

  async fetchSuggestion(isInitial = false) {
    if (this.isFetching) return;

    if (this._abortController) {
      this._abortController.abort();
    }
    this._abortController = new AbortController();
    const {signal} = this._abortController;

    this.isFetching = true;
    try {
      const sug = await window.csClient.getSummarySuggestion(this.featureId);

      if (signal.aborted) return;

      this.suggestion = sug;

      // Start/stop polling based on suggestion status
      if (sug.status === 'in_progress') {
        this.startPolling();
      } else {
        this.stopPolling();
        // If it transitioned from in_progress to a terminal state, dispatch finished event
        if (!isInitial) {
          this.dispatchEvent(
            new CustomEvent('suggestion-finished', {
              detail: {suggestion: sug},
              bubbles: true,
              composed: true,
            })
          );
        }
      }
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') return;
      console.error('Failed to poll AI progress:', err);
    } finally {
      if (!signal.aborted) {
        this.isFetching = false;
      }
    }
  }

  startPolling() {
    if (this._pollingInterval) return;
    this._pollingInterval = window.setInterval(() => {
      void this.fetchSuggestion(false);
    }, 3000); // Poll every 3 seconds driven by the SWR background fetch
  }

  stopPolling() {
    if (this._pollingInterval) {
      window.clearInterval(this._pollingInterval);
      this._pollingInterval = undefined;
    }
  }

  toggleTimeline() {
    this.timelineExpanded = !this.timelineExpanded;
  }

  // Calculate elapsed time from ISO strings
  getElapsedDuration(step: ProgressStep): string {
    if (!step.start_timestamp) return '';
    const start = new Date(step.start_timestamp).getTime();
    const end = step.end_timestamp
      ? new Date(step.end_timestamp).getTime()
      : Date.now();
    const diffMs = end - start;

    if (diffMs < 100) return '+0.1s'; // Floor very fast steps
    return `+${(diffMs / 1000).toFixed(1)}s`;
  }

  // Formatting date into absolute time string e.g. 10:42:15
  formatAbsoluteTime(isoString: string): string {
    if (!isoString) return '';
    try {
      const date = new Date(isoString);
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const time = date.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
      });
      return `${year}-${month}-${day} ${time}`;
    } catch {
      return '';
    }
  }

  shouldShowPrunedMarker(firstStep: ProgressStep | undefined): boolean {
    if (!firstStep) return false;
    if (firstStep.step_id.startsWith('separator_')) {
      const match = firstStep.message.match(/Attempt #(\d+)/);
      if (match && match[1] === '1') {
        return false;
      }
    }
    return true;
  }

  renderStatusIcon(status: ProgressStep['status']) {
    switch (status) {
      case 'in_progress':
        return html`<span class="console-icon"
          ><div class="timeline-spinner"></div
        ></span>`;
      case 'success':
        return html`
          <span class="console-icon success timeline-success-pop">
            <svg
              class="timeline-success-pop"
              width="12"
              height="12"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="3"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
          </span>
        `;
      case 'failed':
        return html`
          <span class="console-icon failed timeline-error-shake">
            <svg
              class="timeline-error-shake"
              width="12"
              height="12"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="3"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </span>
        `;
      case 'retrying':
        return html`<span class="console-icon retrying"
          ><div class="timeline-spinner" style="border-style: dotted;"></div
        ></span>`;
      default:
        return nothing;
    }
  }

  renderMicroProgressBar(steps: ProgressStep[]) {
    if (steps.length === 0) return nothing;

    const totalSegments = 4;
    const completedSteps = steps.filter(s => s.status === 'success').length;
    const activeStep = steps.find(
      s => s.status === 'in_progress' || s.status === 'retrying'
    );

    const filledSegments = Math.min(
      totalSegments - 1,
      Math.floor((completedSteps / steps.length) * totalSegments)
    );

    const segments: TemplateResult[] = [];
    for (let i = 0; i < totalSegments; i++) {
      let segmentClass = 'pending';
      if (i < filledSegments) {
        segmentClass = 'complete';
      } else if (i === filledSegments && activeStep) {
        segmentClass = 'active';
      }
      segments.push(html`<div class="progress-segment ${segmentClass}"></div>`);
    }

    return html`<div class="micro-progress-bar">${segments}</div>`;
  }

  render() {
    const sug = this.suggestion;
    if (!sug) {
      return html`
        <div class="progress-container">
          <sl-skeleton
            effect="sheen"
            style="width: 180px; height: 20px;"
          ></sl-skeleton>
        </div>
      `;
    }

    const status = sug.status || 'none';
    if (status !== 'in_progress') return nothing;

    const steps = sug.progress_steps || [];
    const activeStep = steps.find(
      s => s.status === 'in_progress' || s.status === 'retrying'
    );
    const latestStepMessage = activeStep
      ? activeStep.message
      : steps[steps.length - 1]?.message || 'Executing agent...';

    return html`
      <div class="progress-container">
        <div class="collapsed-row">
          <img
            class="gemini-pulse-icon"
            src="https://www.gstatic.com/images/branding/productlogos/gemini_2025/v1/192px.svg"
            alt="Gemini AI Logo"
          />

          <sl-tag variant="warning" pill size="small">
            <sl-spinner style="font-size: 8px; margin-right: 4px;"></sl-spinner>
            Generating
          </sl-tag>

          <span class="active-step-preview"> ${latestStepMessage} </span>

          ${this.isFetching
            ? html`
                <div class="checking-indicator">
                  <div class="checking-dot"></div>
                  Checking...
                </div>
              `
            : nothing}

          <button class="details-toggle-btn" @click=${this.toggleTimeline}>
            ${this.timelineExpanded
              ? html`Hide Details ▴`
              : html`Show Details ▾`}
          </button>
        </div>

        ${this.renderMicroProgressBar(steps)}
        ${this.timelineExpanded
          ? html`
              <div class="timeline-console-tray">
                ${this.shouldShowPrunedMarker(steps[0])
                  ? html`
                      <div class="console-line pruned-marker-line">
                        <span class="console-icon"></span>
                        <span class="console-time">...</span>
                        <span class="console-msg">
                          [Older attempts pruned to save space]
                        </span>
                        <span class="console-elapsed"></span>
                      </div>
                    `
                  : nothing}
                ${steps.map(
                  step => html`
                    <div class="console-line ${step.status}">
                      ${this.renderStatusIcon(step.status)}
                      <span class="console-time">
                        ${this.formatAbsoluteTime(step.start_timestamp)}
                      </span>
                      <span class="console-msg">${step.message}</span>
                      <span class="console-elapsed">
                        ${step.status === 'in_progress' ||
                        step.status === 'retrying'
                          ? 'active'
                          : this.getElapsedDuration(step)}
                      </span>
                    </div>
                  `
                )}
              </div>
            `
          : nothing}
      </div>
    `;
  }
}
