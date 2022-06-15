import {LitElement, html, nothing} from 'lit';

import {FEATURE_CSS} from '../sass/elements/chromedash-feature-css.js';
// import {SHARED_STYLES} from '../sass/shared-css.js';

class ChromedashFeaturePage extends LitElement {
  static styles = FEATURE_CSS;

  static get properties() {
    return {
      feature: {type: Object},
      featureId: {type: Number},
      loading: {attribute: false},
    };
  }

  constructor() {
    super();
    this.feature = {};
    this.featureId = 0;
    this.loading = true;
  }

  connectedCallback() {
    super.connectedCallback();
    this.fetchFeature();
  }

  fetchFeature() {
    this.loading = true;
    // this.shadowRoot.querySelector('sl-dialog').show();
    window.csClient.getFeature(this.featureId).then(
      (feature) => {
        this.loading = false;
        this.feature = feature;
        console.info(this.feature);
      }).catch(() => {
      const toastEl = document.querySelector('chromedash-toast');
      toastEl.showMessage('Some errors occurred. Please refresh the page or try again later.');
      this.handleCancel();
    });
  }

  handleCancel() {
    // this.shadowRoot.querySelector('sl-dialog').hide();
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
          <p class="preformatted">${this.feature.summary}</p>
        </section>
      `: nothing}

      ${this.feature.motivation ? html`
        <section id="motivation">
          <h3>Motivation</h3>
          <p class="preformatted">${feature.motivation}</p>
        </section>
      `: nothing}

      ${this.feature.resources && this.feature.resources.samples ? html`
        <section id="demo">
          <h3>${this.feature.resources.length == 1 ? 'Demo' : 'Demos'}</h3>
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
            <a href=${this.feature.browsers.chrome.bug} target="_blank" rel="noopener">
              tracking bug
            </a>
          `: nothing}
          <chromedash-gantt feature=${this.feature}></chromedash-gantt>
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
              <label>Firefox:</label>
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
          <p class="preformatted">${feature.comments}</p>
        </section>
      `: nothing}

      ${this.feature.tags ? html`
        <section>
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

  render() {
    return html`
      <div id="feature">
        ${this.renderFeatureContent()}
        ${this.renderFeatureStatus()}
      </div>
    `;
  }
}

customElements.define('chromedash-feature-page', ChromedashFeaturePage);
