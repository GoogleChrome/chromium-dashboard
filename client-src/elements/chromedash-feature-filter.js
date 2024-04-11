import {LitElement, css, html} from 'lit';
import {ref, createRef} from 'lit/directives/ref.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {openSearchHelpDialog} from './chromedash-search-help-dialog.js';
import {QUERIABLE_FIELDS} from './queriable-fields.js';
import SlDropdown from '@shoelace-style/shoelace/dist/components/dropdown/dropdown.js';

const VOCABULARY = QUERIABLE_FIELDS.map((qf) => {
  return {name: qf.name + '=', doc: qf.doc};
});


class NerfedSlDropdown extends SlDropdown {
  constructor() {
    super();
    this.currentItemIndex = null;
  }

  async handleTriggerKeyDown(event) {
    const menu = this.getMenu();
    if (!menu) {
      return;
    }
    const menuItems = menu.getAllItems();
    if (menuItems.length === 0) {
      return;
    }

    // Handle menu selection keys.
    if (['Enter'].includes(event.key)) {
      event.preventDefault();

      if (this.currentItemIndex !== null) {
        console.log('clicking item');
        menuItems[this.currentItemIndex]?.click();
        this.resetSelection();
      }
    }

    // Handle menu navigation keys.
    if (['ArrowDown', 'ArrowUp'].includes(event.key)) {
      event.preventDefault();
      event.stopPropagation();

      // Show the menu if it's not already open
      if (!this.open) {
        this.show();

        // Wait for the dropdown to open before focusing, but not the animation
        await this.updateComplete;
      }

      if (this.currentItemIndex === null) {
        if (event.key === 'ArrowDown') {
          this.currentItemIndex = 0;
        }
        if (event.key === 'ArrowUp') {
          this.currentItemIndex = menuItems.length - 1;
        }
      } else {
        menuItems[this.currentItemIndex].style.backgroundColor = '';
        if (event.key === 'ArrowDown') {
          this.currentItemIndex = Math.min(this.currentItemIndex + 1, menuItems.length - 1);
        }
        if (event.key === 'ArrowUp') {
          this.currentItemIndex = Math.max(this.currentItemIndex - 1, 0);
        }
      }

      // Select and highlight the new current menu item.
      this.updateComplete.then(() => {
        console.log(this.currentItemIndex);
        const selectedItem = menuItems[this.currentItemIndex];
        menu.setCurrentItem(selectedItem);
        selectedItem.style.backgroundColor = 'var(--sl-color-primary-200)';
        // Note: We keep keyboard focus on the search box.
      });
    }
  }

  resetSelection() {
    const menu = this.getMenu();
    const menuItems = menu.getAllItems();
    if (this.currentItemIndex != null && menuItems[this.currentItemIndex]) {
      menuItems[this.currentItemIndex].style.backgroundColor = '';
      this.currentItemIndex = null;
    }
  }
}
customElements.define('nerfed-sl-dropdown', NerfedSlDropdown);


class ChromedashFeatureFilter extends LitElement {
  slDropdownRef = createRef();
  slInputRef = createRef();

  static get properties() {
    return {
      query: {type: String},
      candidates: {type: Array},
      narrowCandidates: {attribute: false},
      prefix: {attribute: false},
      chunkStart: {attribute: false},
      chunkEnd: {attribute: false},
    };
  }

  constructor() {
    super();
    this.query = '';
    this.candidates = [];
    this.prefix = null;
    this.chunkStart = 0;
    this.chunkEnd = 0;
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

  findPrefix() {
    const inputEl = this.slInputRef.value.input;
    const wholeStr = inputEl.value;
    const caret = inputEl.selectionStart;
    if (caret != inputEl.selectionEnd) { // User has a range selected.
      this.chunk = null;
      this.prefix = null;
      return;
    }
    this.chunkStart = wholeStr.lastIndexOf(' ', caret - 1) + 1;
    this.chunkEnd = wholeStr.indexOf(' ', caret);
    if (this.chunkEnd === -1) this.chunkEnd = wholeStr.length;
    this.prefix = wholeStr.substring(this.chunkStart, caret);
  }

  shouldShowCandidate(candidate, prefix) {
    if (prefix === null) return false;
    return (candidate.name.split(/\s+/).some(w => w.startsWith(prefix)) ||
            candidate.doc.split(/\s+/).some(w => w.startsWith(prefix)) ||
            candidate.name.split(/\W+/).some(w => w.startsWith(prefix)) ||
            candidate.doc.split(/\W+/).some(w => w.startsWith(prefix)));
  }

  async handleCandidateSelected(e) {
    console.log(e);
    const candidateValue = e.detail.item.value;
    const inputEl = this.slInputRef.value.input;
    const wholeStr = inputEl.value;
    console.log('maybe:' + wholeStr[this.chunkEnd] + '.');
    const maybeAddSpace =
          (!candidateValue.endsWith('=') && wholeStr[this.chunkEnd] !== ' ') ? ' ' : '';
    const newWholeStr = (
      wholeStr.substring(0, this.chunkStart) +
          candidateValue + maybeAddSpace +
          wholeStr.substring(this.chunkEnd, wholeStr.length));
    console.log({candidateValue, inputEl, wholeStr, newWholeStr});
    this.slInputRef.value.value = newWholeStr;
    // Wait for the sl-input to propagate its new value to its <input>.
    await this.updateComplete;

    console.log(this.chunkStart + ' + ' + candidateValue.length);
    this.chunkStart = this.chunkStart + candidateValue.length + maybeAddSpace.length;
    this.chunkEnd = this.chunkStart;
    inputEl.selectionStart = this.chunkStart;
    inputEl.selectionEnd = this.chunkEnd;
    this.calcCandidates();
  }

  handleSearchKeyDown(event) {
    if (event.key === 'Enter') {
      console.log('fire 1');
      if (!this.slDropdownRef.open || this.slDropdownRef.value.currentItemIndex === null) {
        console.log('fire 2');
        // this.handleSearchClick();
      }
    }
  }

  handleSearchKeyUp(event) {
    if (['ArrowDown', 'ArrowUp', 'Enter'].includes(event.key)) {
      return;
    }
    if (event.key === 'Enter') {
      console.log('fire 1');
      if (!this.slDropdownRef.open || this.slDropdownRef.value.currentItemIndex === null) {
        console.log('fire 2');
        this.handleSearchClick();
      }
    } else {
      this.calcCandidates();
    }
  }

  calcCandidates() {
    console.log('calcCandidates');
    this.findPrefix();
    this.candidates = VOCABULARY.filter(c => this.shouldShowCandidate(c, this.prefix));
    this.slDropdownRef.value.resetSelection();
  }

  handleSearchClick() {
    const newQuery = this.computeQuery();
    console.log({newQuery});
    this._fireEvent('search', {query: newQuery});
  }

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
      nerfed-sl-dropdown {
        width: 100%;
      }
      sl-icon-button {
        font-size: 1.6rem;
        margin: 0 !important;
      }
      #searchbar::part(base) {
       background: #eee;
       border: none;
       border-radius: 8px;
      }
      sl-menu-item span {
        display: inline-flex;
        width: 26em;
        overflow-x: hidden;
      }
      code {
        font-size: 85%;
        background: #eee;
        padding: 0 var(--content-padding-quarter);
      }

    `];
  }

  showHelp() {
    openSearchHelpDialog();
  }


  renderSearchBar() {
    return html`
      <sl-input id="searchbar" slot="trigger" placeholder="Search"
          value=${this.query} ${ref(this.slInputRef)}
          autocomplete=off spellcheck="false"
          @keydown="${this.handleSearchKeyDown}"
          @keyup="${this.handleSearchKeyUp}"
          @focus="${this.calcCandidates}"
        >
        <sl-icon-button library="material" name="search" slot="prefix"
            @click="${this.handleSearchClick}">
        </sl-icon-button>
        <sl-icon-button library="material" name="help_20px" slot="suffix"
            @click="${this.showHelp}">
        </sl-icon-button>
      </sl-input>
    `;
  }

  highlight(s) {
    const start = s.indexOf(this.prefix);
    if (start === -1) return s;
    const before = s.substring(0, start);
    const after = s.substring(start + this.prefix.length);
    return html`${before}<b>${this.prefix}</b>${after}`;
  }

  renderCandidate(candidate) {
    const highlightedName = this.highlight(candidate.name);
    const highlightedDoc = this.highlight(candidate.doc);
    return html`
      <sl-menu-item value=${candidate.name}>
        <span><code>${highlightedName}</code></span>
        ${highlightedDoc}
      </sl-menu-item>
    `;
  }

  renderAutocompleteMenu() {
    return html`
      <sl-menu
        @sl-select=${(e) => {
      this.handleCandidateSelected(e);
    }}
      >
        ${this.candidates.map(c => this.renderCandidate(c))}
      </sl-menu>
    `;
  }


  render() {
    return html`
      <nerfed-sl-dropdown
          stay-open-on-select
          ${ref(this.slDropdownRef)}>
        ${this.renderSearchBar()}
        ${this.renderAutocompleteMenu()}
      </nerfed-sl-dropdown>
    `;
  }
}


customElements.define('chromedash-feature-filter', ChromedashFeatureFilter);
