import {LitElement, TemplateResult, css, html, nothing} from 'lit';
import {customElement, property, state} from 'lit/decorators.js';
import {unsafeHTML} from 'lit/directives/unsafe-html.js';
import {marked} from 'marked';
import {SHARED_STYLES} from '../css/shared-css.js';
import {Feature, FeatureNotFoundError} from '../js-src/cs-client.js';
import {showToastMessage} from './utils.js';

// Matches http or https, followed by wpt.fyi/results, followed by any non-whitespace and non-question mark characters.
const WPT_RESULTS_REGEX = /(https?:\/\/wpt\.fyi\/results[^\s?]+)/g;

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
          color: var(--sl-color-neutral-900);
        }

        h3 {
          margin-top: 1.5em;
          color: var(--sl-color-neutral-700);
        }

        .experimental-tag {
          color: var(--sl-color-neutral-500);
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
          color: var(--sl-color-neutral-700);
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
          color: var(--sl-color-neutral-700);
        }
        .url-list li {
          margin-bottom: 4px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        .url-list a {
          color: var(--sl-color-primary-700);
          text-decoration: none;
        }
        .url-list a:hover {
          text-decoration: underline;
        }

        .report-content {
          overflow-wrap: break-word;
          color: var(--sl-color-neutral-900);
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
          color: var(--sl-color-neutral-50);
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

  async fetchData() {
    this.loading = true;
    try {
      this.feature = await window.csClient.getFeature(this.featureId);
      this.loading = false;
    } catch (error) {
      if (error instanceof FeatureNotFoundError) {
        this.loading = false;
      } else {
        showToastMessage(
          'Some errors occurred. Please refresh the page or try again later.'
        );
      }
    }
  }

  connectedCallback() {
    super.connectedCallback();
    this.fetchData();
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

    // Ensure label capitalization is consistent in output
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
          ${this.renderRequirementItem(hasSpecLink, 'Spec URL', 'id_spec_link')}
          ${this.renderRequirementItem(
            hasWptDescr,
            'WPT description',
            'id_wpt_descr'
          )}
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

  renderReport(): TemplateResult {
    if (!this.feature?.ai_test_eval_report) {
      return html`${nothing}`;
    }

    const rawHtml = marked.parse(this.feature.ai_test_eval_report) as string;

    return html`
      <section class="card report-section">
        <h2>Evaluation Report</h2>
        <div class="report-content">${unsafeHTML(rawHtml)}</div>
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
            Here, you can generate an AI-powered test coverage report for your
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
          : html` ${this.renderRequirementsChecks()} ${this.renderReport()} `}
      </div>
    `;
  }
}
