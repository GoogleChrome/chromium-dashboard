import {LitElement, css, html, nothing} from 'lit';
import {autolink} from './utils.js';

import {SHARED_STYLES} from '../sass/shared-css.js';

export class ChromedashFeaturePage extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        #feature {
          background: var(--card-background);
          border-radius: var(--default-border-radius);
          border: var(--card-border);
          box-shadow: var(--card-box-shadow);

          box-sizing: border-box;
          word-wrap: break-word;
          margin-bottom: var(--content-padding);
          max-width: var(--max-content-width);
        }
        #feature ul {
          list-style-position: inside;
          list-style: none;
        }
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
        
        #consensus li {
          display: flex;
        }
        #consensus li label {
          width: 125px;
        }
        
        @media only screen and (max-width: 700px) {
          #feature {
            border-radius: 0 !important;
            margin: 7px initial !important;
          }
        }
        
        @media only screen and (min-width: 701px) {
          #feature {
            padding: 30px 40px;
          }
        }
    `];
  }

  static get properties() {
    return {
      featureId: {type: Number},
      feature: {type: Object},
      process: {type: Object},
      fieldDefs: {type: Object},
      dismissedCues: {type: Array},
      loading: {attribute: false},
    };
  }

  constructor() {
    super();
    this.featureId = 0;
    this.feature = {};
    this.process = {};
    this.fieldDefs = {};
    this.dismissedCues = [];
    this.loading = true;
  }

  connectedCallback() {
    super.connectedCallback();
    this.fetchFeatureData();
  }

  fetchFeatureData() {
    this.loading = true;
    Promise.all([
      window.csClient.getFeature(this.featureId),
      window.csClient.getProcess(this.featureId),
      window.csClient.getFieldDefs(),
      window.csClient.getDismissedCues(),
    ]).then(([feature, process, fieldDefs, dismissedCues]) => {
      this.feature = feature;
      this.process = process;
      this.fieldDefs = fieldDefs;
      this.dismissedCues = dismissedCues;
      this.loading = false;
    }).catch(() => {
      const toastEl = document.querySelector('chromedash-toast');
      toastEl.showMessage('Some errors occurred. Please refresh the page or try again later.');
    });
  }

  renderFeatureContent() {
    return html`
      ${this.feature.unlisted ? html`
        <section id="access">
        <p><b>This feature is only shown in the feature list to users with
        edit access.</b></p>
        </section>
      `: nothing}
   
      ${this.feature.summary ? html`
        <section id="summary">
          <p class="preformatted">${autolink(this.feature.summary)}</p>
        </section>
      `: nothing}

      ${this.feature.motivation ? html`
        <section id="motivation">
          <h3>Motivation</h3>
          <p class="preformatted">${autolink(this.feature.motivation)}</p>
        </section>
      `: nothing}

      ${this.feature.resources && this.feature.resources.samples ? html`
        <section id="demo">
          <h3>${this.feature.resources.samples.length == 1 ? 'Demo' : 'Demos'}</h3>
          <ul>
            ${this.feature.resources.samples.map((sampleLink) => html`
              <li><a href="${sampleLink}">${sampleLink}</a></li>
            `)}
          </ul>
        </section>
      `: nothing}

      ${this.feature.resources && this.feature.resources.docs ? html`
        <section id="documentation">
          <h3>Documentation</h3>
          <ul>
            ${this.feature.resources.docs.map((docLink) => html`
              <li><a href="${docLink}">${docLink}</a></li>
            `)}
          </ul>
        </section>
      `: nothing}

      ${this.feature.standards.spec ? html`
        <section id="specification">
          <h3>Specification</h3>
          <p><a href=${this.feature.standards.spec} target="_blank" rel="noopener">
            Specification link
          </a></p>
          <br>
          <p>
            <label>Status:</label>
            ${this.feature.standards.maturity.text}
          </p>
        </section>
      `: nothing}
    `;
  }

  renderFeatureStatus() {
    return html`
      <section id="status">
        <h3>Status in Chromium</h3>
        ${this.feature.browsers.chrome.blink_components ? html`
          <p>
            <label>Blink components:</label>
            ${this.feature.browsers.chrome.blink_components.map((c) => html`
              <a href="https://bugs.chromium.org/p/chromium/issues/list?q=component:${c}"
               target="_blank" rel="noopener">${c}</a>
            `)}
          </p>
        `: nothing}
        <br>
        <p>
          <label>Implementation status:</label>
          <b>${this.feature.browsers.chrome.status.text}</b>
          ${this.feature.browsers.chrome.bug ? html`
            (<a href=${this.feature.browsers.chrome.bug} target="_blank" rel="noopener">tracking bug</a>)
          `: nothing}
          <chromedash-gantt .feature=${this.feature}></chromedash-gantt>
        </p>
      </section>
  
      <section id="consensus">
        <h3>Consensus &amp; Standardization</h3>
        <div style="font-size:smaller;">After a feature ships in Chrome, the values listed here are not guaranteed to be up to date.</div>
        <br>
        <ul>
          ${this.feature.browsers.ff.view.val ? html`
            <li>
              <label>Firefox:</label>
              ${this.feature.browsers.ff.view.url ? html`
                <a href=${this.feature.browsers.ff.view.url}>${this.feature.browsers.ff.view.text}</a>
              `: html`
                ${this.feature.browsers.ff.view.text}
              `}
            </li>
          `: nothing}
          ${this.feature.browsers.safari.view.val ? html`
            <li>
              <label>Safari:</label>
              ${this.feature.browsers.safari.view.url ? html`
                <a href=${this.feature.browsers.safari.view.url}>${this.feature.browsers.safari.view.text}</a>
              `: html`
                ${this.feature.browsers.safari.view.text}
              `}
            </li>
          `: nothing}
          <li><label>Web Developers:</label> ${this.feature.browsers.webdev.view.text}</li>
        </ul>
      </section>

      ${this.feature.browsers.chrome.owners ? html`
        <section id="owner">
          <h3>${this.feature.browsers.chrome.owners.length == 1 ? 'Owner' : 'Owners'}</h3>
          <ul>
            ${this.feature.browsers.chrome.owners.map((owner) => html`
              <li><a href="mailto:${owner}">${owner}</a></li>
            `)}
          </ul>
        </section>
      `: nothing}

      ${this.feature.intent_to_implement_url ? html`
        <section id="intent_to_implement_url">
          <h3>Intent to Prototype url</h3>
          <a href=${this.feature.intent_to_implement_url }>Intent to Prototype thread</a>
        </section>
      `: nothing}

      ${this.feature.comments ? html`
        <section id="comments">
          <h3>Comments</h3>
          <p class="preformatted">${autolink(this.feature.comments)}</p>
        </section>
      `: nothing}

      ${this.feature.tags ? html`
        <section id="tags">
          <h3>Search tags</h3>
            ${this.feature.tags.map((tag) => html`
              <a href="/features#tags:${tag}">${tag}</a><span
                class="conditional-comma">, </span>
            `)}
        </section>
      `: nothing}
  
      <section id="updated">
        <p><span>Last updated on ${this.feature.updated_display}</span></p>
      </section>
    `;
  }

  renderFeatureDetails() {
    return html`
      <sl-details
        id="details"
        summary="Additional fields by process phase">
        <chromedash-feature-detail
          .feature=${this.feature}
          .process=${this.process}
          .fieldDefs=${this.fieldDefs}
          .dismissedCues=${this.dismissedCues}>
        </chromedash-feature-detail>
      </sl-details>
    `;
  }

  render() {
    return html`
      ${this.loading ?
        html`
          <div class="loading">
            <div id="spinner"><img src="/static/img/ring.svg"></div>
          </div>` :
        html`
          <div id="feature">
            ${this.renderFeatureContent()}
            ${this.renderFeatureStatus()}
          </div>
          ${this.renderFeatureDetails()}
      `}
    `;
  }
}

customElements.define('chromedash-feature-page', ChromedashFeaturePage);
