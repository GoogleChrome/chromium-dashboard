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
      featureLinksStats: {type: Object},
    };
  }

  constructor() {
    super();
    this.featureLinks = [];
  }

  connectedCallback() {
    super.connectedCallback();
    this.fetchData();
  }

  async fetchData() {
    try {
      this.loading = true;
      this.featureLinks = await window.csClient.getFeatureLinksSummary();
      this.featureLinksStats = this.statsFilter();
    } catch {
      showToastMessage('Some errors occurred. Please refresh the page or try again later.');
    } finally {
      this.loading = false;
    }
  }

  statsFilter() {
    const groupBy = (list, keyGetter) => {
      const map = new Map();
      for (const item of list) {
        try {
          const key = keyGetter(item);
          const collection = map.get(key) || [];
          collection.push(item);
          map.set(key, collection);
        } catch {
          console.log('Encounter error in groupBy, skipping:', item);
          continue;
        }
      }
      return Object.fromEntries(map);
    };

    const countAndSortGroupBy = (obj) => {
      return Object.entries(obj).map(([key, value]) => ({
        key,
        count: value.length,
      })).sort((a, b) => b.count - a.count);
    };

    const webLinks = this.featureLinks.filter(link => link.type === 'web');
    const groups = {
      types: groupBy(this.featureLinks, item => item['type']),
      uncoveredDomains: groupBy(webLinks, item => new URL(item.url).hostname),
    };
    return {
      stats: {
        total: this.featureLinks.length,
        covered: this.featureLinks.length - webLinks.length,
        uncovered: webLinks.length,
        types: countAndSortGroupBy(groups.types),
        uncoveredDomains: countAndSortGroupBy(groups.uncoveredDomains),
      },
      groupBy,
    };
  }

  renderComponents() {
    return html`<pre>${JSON.stringify(this.featureLinksStats.stats, null, 2)}}</pre>`;
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
