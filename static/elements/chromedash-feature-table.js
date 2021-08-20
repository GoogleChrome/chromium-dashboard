import {LitElement, css, html} from 'lit-element';
// import {nothing} from 'lit-html';
import SHARED_STYLES from '../css/shared.css';

class ChromedashFeatureTable extends LitElement {
  static get properties() {
    return {
      query: {type: String},
      rows: {type: Number},
      columns: {type: String},
      signedIn: {type: Boolean},
      starredFeatures: {type: Object},
      noResultsMessage: {type: String},
    };
  }

  constructor() {
    super();
    this.starredFeatures = new Set();
    // TODO(jrobbins): use query to fetch features from server
    this.features = ['One', 'Two', 'Three', 'Four'];
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

  renderFeature(feature) {
    // TODO(jrobbins): Add correct links and icons
    return html`
      <tr>
        <td><a href="#">${feature}</a></td>
      </tr>
    `;
  }

  render() {
    return html`
      <table>
        ${this.features.map(this.renderFeature)}
      </table>
    `;
  }
}

customElements.define('chromedash-feature-table', ChromedashFeatureTable);
