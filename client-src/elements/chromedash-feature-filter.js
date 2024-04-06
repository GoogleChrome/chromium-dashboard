import {LitElement, css, html} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';
import {openSearchHelpDialog} from './chromedash-search-help-dialog.js';

const ENTER_KEY_CODE = 13;


class ChromedashFeatureFilter extends LitElement {
  static get properties() {
    return {
      query: {type: String},
    };
  }

  constructor() {
    super();
    this.query = '';
  }

  _fireEvent(eventName, detail) {
    const event = new CustomEvent(eventName, {
      bubbles: true,
      composed: true,
      detail,
    });
    this.dispatchEvent(event);
  }

  computeQuery() {
    const searchBarEl = this.shadowRoot.querySelector('#searchbar');
    return searchBarEl.value.trim();
  }

  handleSearchKey(event) {
    if (event.keyCode == ENTER_KEY_CODE) {
      const newQuery = this.computeQuery();
      this._fireEvent('search', {query: newQuery});
    }
  }

  handleSearchClick() {
    const newQuery = this.computeQuery();
    this._fireEvent('search', {query: newQuery});
  }

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
      sl-icon-button {
        font-size: 1.6rem;
        margin: 0 !important;
      }
      #searchbar::part(base), #filterwidgets {
       background: #eee;
       border: none;
       border-radius: 8px;
      }
    `];
  }

  showHelp() {
    openSearchHelpDialog();
  }

  renderSearchBar() {
    return html`
      <div>
        <sl-input id="searchbar" placeholder="Search"
            value=${this.query}
            @keyup="${this.handleSearchKey}">
          <sl-icon-button library="material" name="search" slot="prefix"
              @click="${this.handleSearchClick}">
          </sl-icon-button>
          <sl-icon-button library="material" name="help_20px" slot="suffix"
              @click="${this.showHelp}">
          </sl-icon-button>
        </sl-input>
      </div>
    `;
  }


  render() {
    return html`
      ${this.renderSearchBar()}
    `;
  }
}


customElements.define('chromedash-feature-filter', ChromedashFeatureFilter);
