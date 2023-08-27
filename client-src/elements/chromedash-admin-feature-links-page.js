import {LitElement, css, html} from 'lit';
import {showToastMessage} from './utils.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {VARS} from '../css/_vars-css.js';
import {LAYOUT_CSS} from '../css/_layout-css.js';

export class ChromedashAdminFeatureLinksPage extends LitElement {
  static get styles() {
    return [
      SHARED_STYLES,
      VARS,
      LAYOUT_CSS,
      css`
      .feature-links-summary .line {
        padding: var(--content-padding-half);
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 16px;
      }
      sl-icon-button::part(base) {
        padding: 0;
        margin-left: 8px;
      }
      `];
  }
  static get properties() {
    return {
      loading: {type: Boolean},
      samplesLoading: {type: Boolean},
      featureLinkSummary: {type: Object},
    };
  }

  constructor() {
    super();
    this.featureLinkSummary = [];
  }

  connectedCallback() {
    super.connectedCallback();
    this.fetchData();
  }

  async fetchData() {
    try {
      this.loading = true;
      this.featureLinkSummary = await window.csClient.getFeatureLinkSummary();
    } catch {
      showToastMessage('Some errors occurred. Please refresh the page or try again later.');
    } finally {
      this.loading = false;
    }
  }
  async fetchLinkSamples(domain, type, isError) {
    try {
      this.samplesLoading = true;
      await window.csClient.getFeatureLinkSamples(domain, type, isError);
    } catch {
      showToastMessage('Some errors occurred. Please refresh the page or try again later.');
    } finally {
      this.samplesLoading = false;
    }
  }

  renderComponents() {
    return html`
    <div class="feature-links-summary">
      <sl-details summary="Link Summary" open>
        <div class="line">All Links <b>${this.featureLinkSummary.total_count}</b></div>
        <div class="line">Covered Links <b>${this.featureLinkSummary.covered_count}</b></div>
        <div class="line">Uncovered (aka "web") Links <b>${this.featureLinkSummary.uncovered_count}</b></div>
        <div class="line">All Error Links<b>${this.featureLinkSummary.error_count}</b></div>
        <div class="line">HTTP Error Links<b>${this.featureLinkSummary.http_error_count}</b></div>
      </sl-details>
      <sl-details summary="Link Types" open>
        ${this.featureLinkSummary.link_types.map((linkType) => html`
          <div class="line">${(linkType.key).toUpperCase()} <b>${linkType.count}</b></div>
        `)}
      </sl-details>
      <sl-details summary="Uncovered Link Domains" open>
        ${this.featureLinkSummary.uncovered_link_domains.map((domain) => html`
          <div class="line">
            <div>
              <a href=${domain.key}>${domain.key}</a>
              <sl-icon-button library="material" name="search" slot="prefix" title="Samples"
              @click=${() => this.fetchLinkSamples(domain.key, 'web', undefined)}>
              ></sl-icon-button>
          </div>
            <b>${domain.count}</b>
          </div>
        `)}
      </sl-details>
      <sl-details summary="Error Link Domains" open>
      ${this.featureLinkSummary.error_link_domains.map((domain) => html`
      <div class="line">
        <div>
          <a href=${domain.key}>${domain.key}</a>
          <sl-icon-button library="material" name="search" slot="prefix" title="Samples"
          @click=${() => this.fetchLinkSamples(domain.key, undefined, true)}>
          ></sl-icon-button>
      </div>
        <b>${domain.count}</b>
      </div>
    `)}
    </sl-details>
    </div>
    `;
  }
  render() {
    return html`
      ${this.loading ?
              html`` :
              this.renderComponents()
      }
    `;
  }
}

customElements.define('chromedash-admin-feature-links-page', ChromedashAdminFeatureLinksPage);
