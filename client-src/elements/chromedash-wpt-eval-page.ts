import {LitElement, TemplateResult, css, html, nothing} from 'lit';
import {customElement, property, state} from 'lit/decorators.js';
import {unsafeHTML} from 'lit/directives/unsafe-html.js';
import {marked} from 'marked';
import {SHARED_STYLES} from '../css/shared-css.js';
import {Feature} from '../js-src/cs-client.js';
import {showToastMessage} from './utils.js';
import {AITestEvaluationStatus} from './form-field-enums.js';
import {ifDefined} from 'lit/directives/if-defined.js';

// Matches http or https, followed by wpt.fyi/results, followed by any non-whitespace and non-question mark characters.
const WPT_RESULTS_REGEX = /(https?:\/\/wpt\.fyi\/results[^\s?]+)/g;

// 30 minute cooldown for regenerating the evaluation report.
const COOLDOWN_MS = 30 * 60 * 1000;

// 1 hour timeout to allow retrying if the process hangs.
const HANGING_TIMEOUT_MS = 60 * 60 * 1000;

@customElement('chromedash-wpt-eval-page')
export class ChromedashWPTEvalPage extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        :host {
          display: block;
          min-height: 100vh;
          background: var(--sl-color-neutral-50);
          padding: 2em;
        }

        h1 {
          font-size: 2rem;
          font-weight: 300;
          margin-bottom: 1.5rem;
          padding-bottom: 0.5rem;
        }

        h2 {
          font-size: 1.5rem;
          font-weight: 400;
          margin-top: 0;
          margin-bottom: 1rem;
        }

        h3 {
          margin-top: 1.5em;
        }

        .experimental-tag {
          font-size: 0.6em;
          font-weight: normal;
          vertical-align: middle;
          background: var(--sl-color-neutral-200);
          padding: 2px 8px;
          border-radius: 12px;
          margin-left: 8px;
        }

        .card {
          background: var(--sl-color-neutral-0);
          border: 1px solid var(--sl-color-neutral-200);
          border-radius: var(--sl-border-radius-medium);
          padding: var(--sl-spacing-x-large);
          box-shadow: var(--sl-shadow-x-small);
          margin-bottom: var(--sl-spacing-large);
        }

        .description ul {
          line-height: 1.6;
        }
        .description li {
          margin-bottom: 0.5em;
        }

        .requirements-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .requirement-item {
          display: flex;
          align-items: center;
          gap: 12px;
          font-size: 16px;
          padding: 8px;
          border-radius: var(--sl-border-radius-medium);
          transition: background 0.2s ease;
        }
        .requirement-item:hover {
          background: var(--sl-color-neutral-50);
        }

        .requirement-item sl-icon {
          font-size: 1.4em;
          flex-shrink: 0;
        }
        .requirement-item .success {
          color: var(--sl-color-success-600);
        }
        .requirement-item .danger {
          color: var(--sl-color-danger-600);
        }

        .edit-link {
          font-size: 0.9em;
          margin-left: auto;
          padding: 4px 12px;
          background: var(--sl-color-primary-50);
          border-radius: 12px;
          text-decoration: none;
          font-weight: 600;
        }
        .edit-link:hover {
          background: var(--sl-color-primary-100);
        }

        .url-list-container {
          margin-left: 44px;
        }
        .url-list {
          list-style: none;
          margin: 0;
          padding: 12px;
          font-size: 0.85em;
          background: var(--sl-color-neutral-100);
          border-radius: 4px;
          border: 1px solid var(--sl-color-neutral-200);
          max-height: 150px;
          overflow-y: auto;
        }
        .url-list li {
          margin-bottom: 4px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        .url-list a {
          text-decoration: none;
        }
        .url-list a:hover {
          text-decoration: underline;
        }

        .action-section {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          text-align: center;
          min-height: 120px;
        }

        .generate-button {
          font-size: 1.1rem;
          padding-left: 2rem;
          padding-right: 2rem;
        }
        .generate-button sl-icon {
          font-size: 1.3em;
        }

        .cooldown-message {
          margin-top: 12px;
          color: var(--sl-color-neutral-600);
          font-size: 0.9em;
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .help-text {
          margin-top: 8px;
          color: var(--sl-color-neutral-600);
          font-size: 0.9rem;
          max-width: 400px;
          line-height: 1.4;
        }

        .status-in-progress,
        .status-complete {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 16px;
          font-size: 1.1rem;
        }
        .status-in-progress {
          color: var(--sl-color-primary-600);
        }
        .status-in-progress sl-spinner {
          font-size: 3rem;
          --track-width: 4px;
        }
        .status-complete {
          color: var(--sl-color-success-700);
        }
        .status-complete sl-icon {
          font-size: 3rem;
          color: var(--sl-color-success-600);
        }

        .report-content {
          overflow-wrap: break-word;
          line-height: 1.6;
        }
        .report-content h1,
        .report-content h2,
        .report-content h3 {
          margin-top: 1.5em;
          margin-bottom: 0.75em;
          color: var(--sl-color-neutral-1000);
        }
        .report-content *:first-child {
          margin-top: 0;
        }
        .report-content pre {
          background: var(--sl-color-neutral-900);
          padding: 16px;
          border-radius: 6px;
          overflow-x: auto;
        }
        .report-content code {
          background: var(--sl-color-neutral-200);
          padding: 2px 4px;
          border-radius: 4px;
          font-size: 0.9em;
          font-family: monospace;
        }
        .report-content pre code {
          background: transparent;
          padding: 0;
          color: inherit;
        }

        .prewrap {
          white-space: pre-wrap;
        }

        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .fade-in {
          animation: fadeIn 0.8s ease-out forwards;
        }
        .delay-title {
          animation-delay: 0.1s;
        }
        .delay-content {
          animation-delay: 0.4s;
        }

        sl-alert {
          margin-bottom: var(--sl-spacing-large);
        }
      `,
    ];
  }

  @property({type: Number})
  featureId = 0;

  @state()
  feature: Feature | null = null;

  @state()
  loading = false;

  @state()
  isRequirementsFulfilled = false;

  @state()
  completedInThisSession = false;

  // Milliseconds remaining before another run can be requested
  @state()
  private _cooldownRemaining = 0;

  @state()
  private _reportContentChanged = false;

  private _pollIntervalId: number | null = null;
  private _cooldownIntervalId: number | null = null;
  private _previousReportContent: string | null = null;

  async fetchData() {
    if (!this.feature) {
      this.loading = true;
    }
    try {
      this.feature = await window.csClient.getFeature(this.featureId);
      this.checkRequirements();
      this.managePolling();
      this.updateCooldown();
    } catch (error) {
      showToastMessage(
        'Some errors occurred. Please refresh the page or try again later.'
      );
    } finally {
      this.loading = false;
    }
  }

  updated(changedProperties: Map<string | symbol, unknown>) {
    if (changedProperties.has('feature') && this.feature) {
      const currentReport = this.feature.ai_test_eval_report || null;
      // Check if report content has actually changed
      if (currentReport && currentReport !== this._previousReportContent) {
        this._reportContentChanged = true;
        // Reset the animation trigger after a short delay
        setTimeout(() => {
          this._reportContentChanged = false;
        }, 100); // Small delay to allow CSS to register the class removal
      }
      this._previousReportContent = currentReport;
    }
  }

  connectedCallback() {
    super.connectedCallback();
    this.fetchData();
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    this.stopPolling();
    this.stopCooldownTimer();
  }

  checkRequirements() {
    if (!this.feature) {
      this.isRequirementsFulfilled = false;
      return;
    }
    // Name and summary are required for all features,
    // so they are assumed to exist.
    const hasSpecLink = !!this.feature.spec_link;
    const hasWptDescr = !!this.feature.wpt_descr;
    const hasValidUrls =
      (this.feature.wpt_descr || '').match(WPT_RESULTS_REGEX) !== null;

    this.isRequirementsFulfilled = hasSpecLink && hasWptDescr && hasValidUrls;
  }

  updateCooldown() {
    if (
      this.feature?.ai_test_eval_run_status ===
        AITestEvaluationStatus.COMPLETE &&
      this.feature.ai_test_eval_status_timestamp
    ) {
      const completedAt = new Date(
        this.feature.ai_test_eval_status_timestamp
      ).getTime();
      const now = Date.now();
      const elapsed = now - completedAt;

      if (elapsed < COOLDOWN_MS) {
        this._cooldownRemaining = COOLDOWN_MS - elapsed;
        this.startCooldownTimer();
      } else {
        this._cooldownRemaining = 0;
        this.stopCooldownTimer();
      }
    } else {
      this._cooldownRemaining = 0;
      this.stopCooldownTimer();
    }
  }

  startCooldownTimer() {
    if (!this._cooldownIntervalId) {
      // Update cooldown every minute to refresh the UI.
      this._cooldownIntervalId = window.setInterval(() => {
        this.updateCooldown();
      }, 60000);
    }
  }

  stopCooldownTimer() {
    if (this._cooldownIntervalId) {
      window.clearInterval(this._cooldownIntervalId);
      this._cooldownIntervalId = null;
    }
  }

  managePolling() {
    const status = this.feature?.ai_test_eval_run_status;
    if (status === AITestEvaluationStatus.IN_PROGRESS) {
      this.startPolling();
    } else {
      if (this._pollIntervalId && status === AITestEvaluationStatus.COMPLETE) {
        this.completedInThisSession = true;
      }
      this.stopPolling();
    }
  }

  startPolling() {
    if (!this._pollIntervalId) {
      this._pollIntervalId = window.setInterval(() => {
        this.fetchData();
      }, 5000);
    }
  }

  stopPolling() {
    if (this._pollIntervalId) {
      window.clearInterval(this._pollIntervalId);
      this._pollIntervalId = null;
    }
  }

  async handleGenerateClick() {
    if (
      !this.isRequirementsFulfilled ||
      !this.feature ||
      this._cooldownRemaining > 0
    )
      return;

    try {
      this.feature = {
        ...this.feature,
        ai_test_eval_run_status: AITestEvaluationStatus.IN_PROGRESS,
        ai_test_eval_status_timestamp: new Date().toString(),
      };
      this.completedInThisSession = false; // Reset if user tries to regenerate.
      this.managePolling();

      await window.csClient.generateWPTCoverageEvaluation(this.featureId);
    } catch (e) {
      showToastMessage('Failed to start evaluation. Please try again later.');
      this.fetchData();
    }
  }

  renderRequirementItem(
    isFulfilled: boolean,
    label: string,
    urlHash: string
  ): TemplateResult {
    const icon = isFulfilled
      ? html`<sl-icon
          class="success"
          library="material"
          name="check_circle_20px"
        ></sl-icon>`
      : html`<sl-icon name="x-circle-fill" class="danger"></sl-icon>`;

    const text = isFulfilled ? `${label} provided` : `Missing ${label}`;

    return html`
      <div class="requirement-item">
        ${icon}
        <span>${text}</span>
        <a class="edit-link" href="/guide/editall/${this.featureId}#${urlHash}">
          Edit
        </a>
      </div>
    `;
  }

  /**
   * Renders pre-formatted text within a div, applying `prettier-ignore`
   * to prevent unwanted whitespace from being introduced by Prettier's
   * formatting when `white-space: pre-wrap` is used.
   * @param content The text content to render.
   * @returns A TemplateResult containing the pre-formatted text, or nothing if content is undefined.
   */
  private _renderPreformattedText(
    content: string | undefined
  ): TemplateResult | typeof nothing {
    if (!content) {
      return nothing;
    }
    // prettier-ignore
    return html`<div class="url-list prewrap">${content}</div>`;
  }

  renderRequirementsChecks(): TemplateResult {
    if (!this.feature) {
      return html`${nothing}`;
    }

    const hasSpecLink = !!this.feature.spec_link;
    const hasWptDescr = !!this.feature.wpt_descr;
    const wptUrls =
      (this.feature.wpt_descr || '').match(WPT_RESULTS_REGEX) || [];
    const hasValidUrls = wptUrls.length > 0;

    return html`
      <section class="card">
        <h2>Prerequisites Checklist</h2>
        <div class="requirements-list">
          <!-- Name and summary are assumed to always be filled -->
          ${this.renderRequirementItem(true, 'Feature name', 'id_name')}
          <div class="url-list-container">
            <div class="url-list">${this.feature.name}</div>
          </div>
          ${this.renderRequirementItem(true, 'Feature summary', 'id_summary')}
          <div class="url-list-container">
            ${this._renderPreformattedText(this.feature.summary)}
          </div>
          ${this.renderRequirementItem(hasSpecLink, 'Spec URL', 'id_spec_link')}
          ${hasSpecLink
            ? html`
                <div class="url-list-container">
                  <div class="url-list">
                    <a
                      href="${ifDefined(this.feature.spec_link)}"
                      target="_blank"
                      >${this.feature.spec_link}</a
                    >
                  </div>
                </div>
              `
            : nothing}
          ${this.renderRequirementItem(
            hasWptDescr,
            'WPT description',
            'id_wpt_descr'
          )}
          ${hasWptDescr
            ? html`
                <div class="url-list-container">
                  ${this._renderPreformattedText(this.feature.wpt_descr)}
                </div>
              `
            : nothing}
          ${this.renderRequirementItem(
            hasValidUrls,
            'Valid wpt.fyi results URLs',
            'id_wpt_descr'
          )}
          ${hasValidUrls
            ? html`
                <div class="url-list-container">
                  <ul class="url-list">
                    ${wptUrls.map(
                      url => html`
                        <li>
                          <a href="${url}" target="_blank" title="${url}"
                            >${url}</a
                          >
                        </li>
                      `
                    )}
                  </ul>
                </div>
              `
            : nothing}
        </div>
      </section>
    `;
  }

  renderActionSection(): TemplateResult {
    if (!this.feature) return html`${nothing}`;

    const status = this.feature.ai_test_eval_run_status;
    let isHanging = false;

    // Check if IN_PROGRESS but hanging (older than 1 hour).
    if (
      status === AITestEvaluationStatus.IN_PROGRESS &&
      this.feature.ai_test_eval_status_timestamp
    ) {
      const startedAt = new Date(
        this.feature.ai_test_eval_status_timestamp
      ).getTime();
      const now = Date.now();
      if (now - startedAt > HANGING_TIMEOUT_MS) {
        isHanging = true;
      }
    }

    // Only show the spinner if it is in progress AND NOT hanging
    if (status === AITestEvaluationStatus.IN_PROGRESS && !isHanging) {
      return html`
        <section class="card action-section">
          <div class="status-in-progress">
            <sl-spinner></sl-spinner>
            <span>Evaluation in progress... This may take a few minutes.</span>
          </div>
        </section>
      `;
    }

    // Show success message if completed in this session.
    if (
      this.completedInThisSession &&
      status !== AITestEvaluationStatus.IN_PROGRESS
    ) {
      return html`
        <section class="card action-section">
          <div class="status-complete fade-in">
            <sl-icon library="material" name="check_circle_20px"></sl-icon>
            <span>Evaluation complete! The report is available above.</span>
          </div>
        </section>
      `;
    }

    const isCooldownActive = this._cooldownRemaining > 0;
    const minutesRemaining = Math.ceil(this._cooldownRemaining / 60000);

    let buttonLabel = 'Evaluate test coverage';
    if (isHanging) {
      buttonLabel = 'Retry evaluation (Process timed out)';
    } else if (this.feature.ai_test_eval_report) {
      buttonLabel = 'Discard this report and reevaluate test coverage';
    }

    return html`
      <section class="card action-section">
        ${status === AITestEvaluationStatus.FAILED
          ? html`
              <sl-alert variant="danger" open>
                The previous evaluation run failed. Please try again.
              </sl-alert>
            `
          : nothing}

        <sl-button
          variant="${this.feature.ai_test_eval_report ? 'danger' : 'primary'}"
          size="large"
          class="generate-button"
          ?disabled=${!this.isRequirementsFulfilled || isCooldownActive}
          @click=${this.handleGenerateClick}
        >
          ${buttonLabel}
        </sl-button>

        ${isHanging
          ? html`
              <div class="help-text">
                The previous evaluation seems to be stuck. You can try starting
                a new one.
              </div>
            `
          : nothing}
        ${isCooldownActive
          ? html`
              <div class="cooldown-message">
                <sl-icon name="hourglass-split"></sl-icon>
                Available in ${minutesRemaining}
                minute${minutesRemaining !== 1 ? 's' : ''}
              </div>
            `
          : nothing}
      </section>
    `;
  }

  renderReport(): TemplateResult {
    if (!this.feature?.ai_test_eval_report) {
      return html`${nothing}`;
    }

    const rawHtml = marked.parse(this.feature.ai_test_eval_report) as string;

    // Apply fade-in only if _reportContentChanged is true
    const titleClass = this._reportContentChanged ? 'fade-in delay-title' : '';
    const contentClass = this._reportContentChanged
      ? 'fade-in delay-content'
      : '';

    return html`
      <section class="card report-section">
        <h2 class="${titleClass}">Evaluation Report</h2>
        <div class="report-content ${contentClass}">${unsafeHTML(rawHtml)}</div>
      </section>
    `;
  }

  renderSkeletonSection() {
    return html`
      <section class="card">
        <h3><sl-skeleton effect="sheen" style="width: 50%"></sl-skeleton></h3>
        <p>
          <sl-skeleton effect="sheen"></sl-skeleton>
          <sl-skeleton effect="sheen"></sl-skeleton>
          <sl-skeleton effect="sheen"></sl-skeleton>
        </p>
      </section>
    `;
  }

  renderSkeletons() {
    return html`
      <div style="margin-top: 2em;">
        ${this.renderSkeletonSection()} ${this.renderSkeletonSection()}
      </div>
    `;
  }

  render() {
    return html`
      <div>
        <h1>
          AI-powered WPT coverage evaluation
          <span class="experimental-tag">Experimental</span>
        </h1>

        <sl-alert variant="primary" open>
          <sl-icon slot="icon" name="info-circle"></sl-icon>
          This feature is experimental and reports may be inaccurate. Please
          <a
            href="https://github.com/GoogleChrome/chromium-dashboard/issues/new?labels=Feedback,WPT-AI"
            target="_blank"
            >file an issue</a
          >
          if you have feedback or suggestions.
        </sl-alert>

        <section class="card description">
          <h2>About</h2>
          <p>
            Here you can generate an AI-powered test coverage report for your
            feature using Gemini. Gemini will analyze your feature's details,
            specification, and listed Web Platform Tests to evaluate if it meets
            standard minimum test coverage criteria.
          </p>

          <h3>Before you begin</h3>
          <p>
            To ensure an accurate report, please verify the following feature
            details:
          </p>
          <ul>
            <li>
              <strong>Metadata:</strong> Ensure the feature name and summary are
              accurate.
            </li>
            <li>
              <strong>Specification:</strong> A valid Spec URL must be provided.
            </li>
            <li>
              <strong>Test Results:</strong> Add relevant
              <code>wpt.fyi</code> URLs to the
              <i>Web Platform Tests</i> description field.
              <ul>
                <li>
                  URLs must begin with <code>https://wpt.fyi/results/</code>.
                </li>
                <li>
                  Individual test file URLs are accepted (e.g.,
                  <code>dom/historical.html</code>).
                </li>
                <li>
                  Directory URLs are accepted, but <strong>only</strong> if
                  every test in that directory is relevant to your feature.
                </li>
                <li>
                  There is a limit of <strong>50 individual test files</strong>
                  In the Web Platform Tests repository. If more than 50 relevant
                  test files are found via the listed URLs, the test suite size
                  is too big for automated test coverage evaluation.
                </li>
                <li>
                  <em
                    >Note: Subdirectories within listed directories are not
                    scanned.</em
                  >
                </li>
              </ul>
            </li>
          </ul>
        </section>

        ${this.loading
          ? this.renderSkeletons()
          : html`
              ${this.renderRequirementsChecks()} ${this.renderReport()}
              ${this.renderActionSection()}
            `}
      </div>
    `;
  }
}
