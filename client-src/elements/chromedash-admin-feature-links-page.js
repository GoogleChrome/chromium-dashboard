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
      css``];
  }
  static get properties() {
    return {
      loading: {type: Boolean},
      featureLinks: {type: Array},
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

  renderComponents() {
    return html`<pre>${JSON.stringify(this.featureLinkSummary, null, 2)}}</pre>`;
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
