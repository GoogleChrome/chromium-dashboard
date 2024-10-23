import {LitElement, css, html, nothing} from 'lit';
import {customElement, property} from 'lit/decorators.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import type {FeatureLink} from '../js-src/cs-client.js';
import {DETAILS_STYLES} from './chromedash-feature-detail.js';
import './chromedash-gantt.js';
import {enhanceUrl} from './chromedash-link.js';
import './chromedash-vendor-views.js';
import {autolink, renderAbsoluteDate, renderRelativeDate} from './utils.js';

@customElement('chromedash-feature-highlights')
export class ChromedashFeatureHighlights extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      ...DETAILS_STYLES,
      css`
        section {
          margin-bottom: 1em;
        }
        section h3 {
          margin: 24px 0 12px;
        }
        section label {
          font-weight: 500;
          margin-right: 5px;
        }

        li {
          list-style: none;
        }

        #consensus li {
          display: flex;
        }
        #consensus li label {
          width: 125px;
        }

        #history p {
          margin-top: var(--content-padding-half);
        }

        sl-dropdown {
          float: right;
          margin-right: -16px;
          margin-top: -20px;
        }
      `,
    ];
  }

  @property({attribute: false})
  feature: any = {};

  @property({attribute: false})
  featureLinks: FeatureLink[] = [];

  @property({type: Boolean})
  canDeleteFeature = false;

  handleDeleteFeature() {
    this.dispatchEvent(new Event('delete', {bubbles: true, composed: true}));
  }

  renderEnterpriseFeatureContent() {
    return html`
      ${this.feature.summary
        ? html`
            <section id="summary">
              <!-- prettier-ignore -->
              <p class="preformatted">${autolink(
                this.feature.summary,
                this.featureLinks
              )}</p>
            </section>
          `
        : nothing}
    `;
  }

  renderFeatureContent() {
    return html`
      ${this.feature.summary
        ? html`
            <section id="summary">
              <!-- prettier-ignore -->
              <p class="preformatted">${autolink(
                this.feature.summary,
                this.featureLinks
              )}</p>
            </section>
          `
        : nothing}
      ${this.feature.motivation
        ? html`
            <section id="motivation">
              <h3>Motivation</h3>
              <!-- prettier-ignore -->
              <p class="preformatted">${autolink(
                this.feature.motivation,
                this.featureLinks
              )}</p>
            </section>
          `
        : nothing}
      ${this.feature.resources?.samples?.length
        ? html`
            <section id="demo">
              <h3>Demos and samples</h3>
              <ul>
                ${this.feature.resources.samples.map(
                  sampleLink => html`
                    <li>${enhanceUrl(sampleLink, this.featureLinks)}</li>
                  `
                )}
              </ul>
            </section>
          `
        : nothing}
      ${this.feature.resources?.docs?.length
        ? html`
            <section id="documentation">
              <h3>Documentation</h3>
              <ul>
                ${this.feature.resources.docs.map(
                  docLink => html`
                    <li>${enhanceUrl(docLink, this.featureLinks)}</li>
                  `
                )}
              </ul>
            </section>
          `
        : nothing}
      ${this.feature.standards.spec
        ? html`
            <section id="specification">
              <h3>Specification</h3>
              <p>
                ${enhanceUrl(this.feature.standards.spec, this.featureLinks)}
              </p>
              <p>Spec status: ${this.feature.standards.maturity.text}</p>
            </section>
          `
        : this.feature.explainer_links?.length
          ? html`
              <section id="specification">
                <h3>Explainer(s)</h3>
                ${this.feature.explainer_links?.map(
                  link => html`<p>${enhanceUrl(link, this.featureLinks)}</p>`
                )}
              </section>
            `
          : nothing}
    `;
  }

  renderEnterpriseFeatureStatus() {
    return html`
      ${this.feature.browsers.chrome.owners
        ? html`
            <section id="owner">
              <h3>
                ${this.feature.browsers.chrome.owners.length == 1
                  ? 'Owner'
                  : 'Owners'}
              </h3>
              <ul>
                ${this.feature.browsers.chrome.owners.map(
                  owner => html`
                    <li><a href="mailto:${owner}">${owner}</a></li>
                  `
                )}
              </ul>
            </section>
          `
        : nothing}
    `;
  }

  renderFeatureStatus() {
    return html`
      <section id="status">
        <h3>Status in Chromium</h3>
        ${this.feature.browsers.chrome.blink_components
          ? html`
              <p>
                <label>Blink components:</label>
                ${this.feature.browsers.chrome.blink_components.map(
                  c => html`
                    <a
                      href="https://bugs.chromium.org/p/chromium/issues/list?q=component:${c}"
                      target="_blank"
                      rel="noopener"
                      >${c}</a
                    >
                  `
                )}
              </p>
            `
          : nothing}
        <br />
        <p>
          <label>Implementation status:</label>
          <b>${this.feature.browsers.chrome.status.text}</b>
          ${this.feature.browsers.chrome.bug
            ? html`<chromedash-link
                href=${this.feature.browsers.chrome.bug}
                .featureLinks=${this.featureLinks}
                alwaysInTag
                >tracking bug</chromedash-link
              >`
            : nothing}
          <chromedash-gantt .feature=${this.feature}></chromedash-gantt>
        </p>
      </section>

      <section id="consensus">
        <h3>Consensus &amp; Standardization</h3>
        <div style="font-size:smaller;">
          After a feature ships in Chrome, the values listed here are not
          guaranteed to be up to date.
        </div>
        <br />
        <ul>
          ${this.feature.browsers.ff.view.val
            ? html`
                <li>
                  <label>Firefox:</label>
                  <chromedash-vendor-views
                    href=${this.feature.browsers.ff.view.url || nothing}
                    .featureLinks=${this.featureLinks}
                    >${this.feature.browsers.ff.view
                      .text}</chromedash-vendor-views
                  >
                </li>
              `
            : nothing}
          ${this.feature.browsers.safari.view.val
            ? html`
                <li>
                  <label>Safari:</label>
                  <chromedash-vendor-views
                    href=${this.feature.browsers.safari.view.url || nothing}
                    .featureLinks=${this.featureLinks}
                    >${this.feature.browsers.safari.view
                      .text}</chromedash-vendor-views
                  >
                </li>
              `
            : nothing}
          <li>
            <label>Web Developers:</label> ${this.feature.browsers.webdev.view
              .text}
          </li>
        </ul>
      </section>

      ${this.feature.browsers.chrome.owners
        ? html`
            <section id="owner">
              <h3>
                ${this.feature.browsers.chrome.owners.length == 1
                  ? 'Owner'
                  : 'Owners'}
              </h3>
              <ul>
                ${this.feature.browsers.chrome.owners.map(
                  owner => html`
                    <li><a href="mailto:${owner}">${owner}</a></li>
                  `
                )}
              </ul>
            </section>
          `
        : nothing}
      ${this.feature.intent_to_implement_url
        ? html`
            <section id="intent_to_implement_url">
              <h3>Intent to Prototype url</h3>
              <a href=${this.feature.intent_to_implement_url}
                >Intent to Prototype thread</a
              >
            </section>
          `
        : nothing}
      ${this.feature.comments
        ? html`
            <section id="comments">
              <h3>Comments</h3>
              <!-- prettier-ignore -->
              <p class="preformatted">${autolink(
                this.feature.comments,
                this.featureLinks
              )}</p>
            </section>
          `
        : nothing}
      ${this.feature.tags
        ? html`
            <section id="tags">
              <h3>Search tags</h3>
              ${this.feature.tags.map(
                tag => html`
                  <a href="/features#tags:${tag}">${tag}</a
                  ><span class="conditional-comma">, </span>
                `
              )}
            </section>
          `
        : nothing}
    `;
  }

  renderHistory() {
    return html`
      <section id="history">
        <h3>History</h3>
        <p>
          Entry created on
          ${renderAbsoluteDate(this.feature.created?.when, true)}
          ${renderRelativeDate(this.feature.created?.when)}
        </p>
        <p>
          Last updated on
          ${renderAbsoluteDate(this.feature.updated?.when, true)}
          ${renderRelativeDate(this.feature.updated?.when)}
        </p>

        <p>
          <a href="/feature/${this.feature.id}/activity">
            All comments &amp; activity
          </a>
        </p>
      </section>
    `;
  }

  render() {
    return html`
      <sl-details summary="Overview" ?open=${true}>
        <section class="card">
          ${this.canDeleteFeature
            ? html`
                <sl-dropdown placement="left-start">
                  <sl-icon-button
                    library="material"
                    name="more_vert_24px"
                    label="Feature menu"
                    style="font-size: 1.3rem;"
                    slot="trigger"
                  ></sl-icon-button>
                  <sl-menu-item value="undo">
                    <a
                      id="delete-feature"
                      class="delete-button"
                      @click=${this.handleDeleteFeature}
                    >
                      Delete
                    </a>
                  </sl-menu-item>
                </sl-dropdown>
              `
            : nothing}
          ${this.feature.is_enterprise_featqcure
            ? this.renderEnterpriseFeatureContent()
            : this.renderFeatureContent()}
          ${this.feature.is_enterprise_feature
            ? this.renderEnterpriseFeatureStatus()
            : this.renderFeatureStatus()}
          ${this.renderHistory()}
        </section>
      </sl-details>
    `;
  }
}
