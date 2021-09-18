import {LitElement, css, html} from 'lit-element';
import {nothing} from 'lit-html';
import SHARED_STYLES from '../css/shared.css';

class ChromedashFeatureTable extends LitElement {
  static get properties() {
    return {
      query: {type: String},
      features: {type: Array},
      loading: {type: Boolean},
      rows: {type: Number},
      columns: {type: String},
      signedIn: {type: Boolean},
      starredFeatures: {type: Object},
      noResultsMessage: {type: String},
    };
  }

  constructor() {
    super();
    this.loading = true;
    this.starredFeatures = new Set();
    this.features = [];
    this.noResultsMessage = 'No results';
  }

  connectedCallback() {
    super.connectedCallback();
    window.csClient.searchFeatures(this.query).then((features) => {
      this.features = features;
      this.loading = false;
    });
  }

  static get styles() {
    return [
      SHARED_STYLES,
      css`
      table {
        width: 50em;
      }
      tr {
        background: var(--table-row-background);
      }
      td {
        padding: var(--content-padding-half);
        border-bottom: var(--table-divider);
      }
    `];
  }

  renderMessages() {
    if (this.loading) {
      return html`
        <tr><td>Loading...</td></tr>
      `;
    }
    if (this.features.length == 0) {
      return html`
        <tr><td>${this.noResultsMessage}</td></tr>
      `;
    }
    return nothing;
  }

  renderFeature(feature) {
    // TODO(jrobbins): Add correct links and icons
    return html`
      <tr>
        <td><a href="/feature/${feature.id}">${feature.name}</a></td>
      </tr>
    `;
  }

  render() {
    return html`
      <table>
        ${this.features.map(this.renderFeature)}
        ${this.renderMessages()}
      </table>
    `;
  }
}

customElements.define('chromedash-feature-table', ChromedashFeatureTable);
