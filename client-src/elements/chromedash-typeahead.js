import {LitElement, css, html} from 'lit';
import {ref, createRef} from 'lit/directives/ref.js';
import {live} from 'lit/directives/live.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import SlDropdown from '@shoelace-style/shoelace/dist/components/dropdown/dropdown.js';

/* This file consists of 3 classes that together implement a "typeahead"
   text field with autocomplete:

   1. Chromedash-typeahead represents the overall UI widget, accepts a
   `vocabulary` list of words, exposes a `value` string, and emits a
   `sl-change` event when the user hits enter to submit the value.
   Internally, it is responsible for narrowing the vocabulary down to a list
   of candidates based on the prefix that the user has typed.

   2. Private class ChromedashTypeaheadDropdown subclasses SlDropdown and
   removes code that would change the keyboard focus.

   3. Private class ChromedashTypeaheadItem renders a single item in the
   typeahead menu.  We do not use SlMenuItem because it steals keyboard focus.
*/

export class ChromedashTypeahead extends LitElement {
  slDropdownRef = createRef();
  slInputRef = createRef();

  static get properties() {
    return {
      value: {type: String},
      placeholder: {type: String},
      candidates: {type: Array},
      vocabulary: {type: Array, attribute: false},
      prefix: {type: String, attribute: false},
      chunkStart: {type: Number, attribute: false},
      chunkEnd: {type: Number, attribute: false},
    };
  }

  constructor() {
    super();
    this.value = '';
    this.placeholder = '';
    this.candidates = [];
    this.vocabulary = [];
    this.prefix = null;
    this.chunkStart = 0;
    this.chunkEnd = 0;
    // If the user hits Escape, keep the menu closed until they use up or down.
    this.wasDismissed = false;
  }

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        chromedash-typeahead-dropdown {
          width: 100%;
        }
        #inputfield::part(base) {
          background: #eee;
          border: none;
          border-radius: 8px;
        }
      `,
    ];
  }

  _fireEvent(eventName, detail) {
    const event = new CustomEvent(eventName, {
      bubbles: true,
      composed: true,
      detail,
    });
    this.dispatchEvent(event);
  }

  reflectValue(event) {
    if (event) {
      event.stopPropagation();
    }
    const slInput = this.slInputRef.value;
    this.value = slInput.value;
  }

  hide() {
    this.slDropdownRef.value.hide();
  }

  show() {
    this.slDropdownRef.value.show();
  }

  findPrefix() {
    const inputEl = this.slInputRef.value.input;
    const wholeStr = inputEl.value;
    const caret = inputEl.selectionStart;
    if (caret != inputEl.selectionEnd) {
      // User has a range selected.
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
    prefix = prefix.toLowerCase();
    const lowerName = candidate.name.toLowerCase();
    const lowerDoc = candidate.doc.toLowerCase();
    return (
      lowerName.split(/\s+/).some(w => w.startsWith(prefix)) ||
      lowerDoc.split(/\s+/).some(w => w.startsWith(prefix)) ||
      lowerName.split(/\W+/).some(w => w.startsWith(prefix)) ||
      lowerDoc.split(/\W+/).some(w => w.startsWith(prefix))
    );
  }

  async handleCandidateSelected(e) {
    const candidateValue = e.detail.item.value;
    const inputEl = this.slInputRef.value.input;
    const wholeStr = inputEl.value;
    const maybeAddSpace =
      !candidateValue.endsWith('=') && wholeStr[this.chunkEnd] !== ' '
        ? ' '
        : '';
    const newWholeStr =
      wholeStr.substring(0, this.chunkStart) +
      candidateValue +
      maybeAddSpace +
      wholeStr.substring(this.chunkEnd, wholeStr.length);
    this.slInputRef.value.value = newWholeStr;
    this.reflectValue();
    // Wait for the sl-input to propagate its new value to its <input> before
    // setting or accessing the text selection.
    await this.updateComplete;

    this.chunkStart =
      this.chunkStart + candidateValue.length + maybeAddSpace.length;
    this.chunkEnd = this.chunkStart;
    inputEl.selectionStart = this.chunkStart;
    inputEl.selectionEnd = this.chunkEnd;
    this.calcCandidates();
    // The user may have clicked a menu item, causing the sl-input to lose
    // keyboard focus.  So, focus on the sl-input again.
    inputEl.focus();
  }

  // Check if the user is pressing Enter to send a query.  This is detected
  // on keyDown so that the handler is run before the dropdown keyDown is run.
  handleInputFieldKeyDown(event) {
    if (event.key === 'Enter') {
      const slDropdown = this.slDropdownRef.value;
      if (!slDropdown.open || !slDropdown.getCurrentItem()) {
        this._fireEvent('sl-change', this);
        event.stopPropagation();
      }
    }
  }

  // As the user types and moves the caret, keep recalculating a-c choices.
  // Left and right movement is handled on keyUp so that caret has already been
  // moved to its new position before this handler is run.
  handleInputFieldKeyUp(event) {
    if (['Escape'].includes(event.key)) {
      this.wasDismissed = true;
      return;
    }
    if (['ArrowDown', 'ArrowUp', 'Enter'].includes(event.key)) {
      this.wasDismissed = false;
      return;
    }
    this.calcCandidates();
  }

  calcCandidates(event) {
    if (event) {
      event.stopPropagation();
    }
    this.findPrefix();
    this.candidates = this.vocabulary.filter(c =>
      this.shouldShowCandidate(c, this.prefix)
    );
    const slDropdown = this.slDropdownRef.value;
    if (this.candidates.length > 0 && !this.wasDismissed) {
      slDropdown.show();
    } else {
      slDropdown.hide();
    }
  }

  renderInputField() {
    return html`
      <sl-input
        id="inputfield"
        slot="trigger"
        placeholder=${this.placeholder}
        value=${live(this.value)}
        ${ref(this.slInputRef)}
        autocomplete="off"
        spellcheck="false"
        @keydown="${this.handleInputFieldKeyDown}"
        @keyup="${this.handleInputFieldKeyUp}"
        @focus="${this.calcCandidates}"
        @click="${this.calcCandidates}"
        @sl-change="${this.reflectValue}"
        @sl-input="${this.reflectValue}"
      >
        <slot name="prefix" slot="prefix"></slot>
        <slot name="suffix" slot="suffix"></slot>
      </sl-input>
    `;
  }

  renderAutocompleteMenu() {
    return html`
      <sl-menu
        @click=${e => e.preventDefault()}
        @sl-select=${this.handleCandidateSelected}
      >
        ${this.candidates.map(
          c => html`
            <chromedash-typeahead-item
              value=${c.name}
              doc=${c.doc}
              prefix=${this.prefix}
            ></chromedash-typeahead-item>
          `
        )}
      </sl-menu>
    `;
  }

  render() {
    return html`
      <chromedash-typeahead-dropdown
        stay-open-on-select
        sync="width"
        ${ref(this.slDropdownRef)}
      >
        ${this.renderInputField()} ${this.renderAutocompleteMenu()}
      </chromedash-typeahead-dropdown>
    `;
  }
}
customElements.define('chromedash-typeahead', ChromedashTypeahead);

export class ChromedashTypeaheadDropdown extends SlDropdown {
  constructor() {
    super();
  }

  getCurrentItem() {
    return this.getMenu()?.getCurrentItem();
  }

  setCurrentItem(newCurrentItem) {
    const menu = this.getMenu();
    menu.setCurrentItem(newCurrentItem);
    newCurrentItem.scrollIntoView({block: 'nearest', behavior: 'smooth'});
  }

  resetSelection() {
    const currentItem = this.getCurrentItem();
    currentItem?.setAttribute('tabindex', -1);
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
    const currentItem = menu.getCurrentItem();

    // Handle menu selection keys.
    if (['Enter'].includes(event.key)) {
      event.preventDefault();

      if (this.open && currentItem) {
        currentItem.click();
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
      }

      if (currentItem) {
        const currentItemIndex = menuItems.indexOf(currentItem);
        if (event.key === 'ArrowDown' && menuItems[currentItemIndex + 1]) {
          this.setCurrentItem(menuItems[currentItemIndex + 1]);
        }
        if (event.key === 'ArrowUp' && menuItems[currentItemIndex - 1]) {
          this.setCurrentItem(menuItems[currentItemIndex - 1]);
        }
      } else {
        if (event.key === 'ArrowDown') {
          this.setCurrentItem(menuItems[0]);
        }
        if (event.key === 'ArrowUp') {
          this.setCurrentItem(menuItems[menuItems.length - 1]);
        }
      }
      // Note: We keep keyboard focus on #inputfield.
    }
  }
}
customElements.define(
  'chromedash-typeahead-dropdown',
  ChromedashTypeaheadDropdown
);

export class ChromedashTypeaheadItem extends LitElement {
  static get properties() {
    return {
      value: {type: String},
      doc: {type: String},
      prefix: {type: String},
      role: {type: String, reflect: true},
      tabindex: {type: Number},
    };
  }

  constructor() {
    super();
    this.value = '';
    this.doc = '';
    this.prefix = '';
    this.role = 'menuitem'; // SlMenu looks for on this attribute.
  }

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        .menu-item {
          display: flex;
          flex-wrap: wrap;
          font-family: var(--sl-font-sans);
          font-size: var(--sl-font-size-medium);
          font-weight: var(--sl-font-weight-normal);
          line-height: var(--sl-line-height-normal);
          letter-spacing: var(--sl-letter-spacing-normal);
          color: var(--sl-color-neutral-700);
          padding: var(--sl-spacing-2x-small) var(--sl-spacing-2x-small);
          transition: var(--sl-transition-fast) fill;
          user-select: none;
          -webkit-user-select: none;
          white-space: nowrap;
          cursor: pointer;
        }

        .active {
          outline: none;
          background-color: var(--sl-color-primary-200);
          opacity: 1;
        }
        #value {
          width: 24em;
          overflow-x: hidden;
        }
        code {
          font-size: 85%;
          background: #eee;
          padding: var(--content-padding-quarter);
        }
      `,
    ];
  }

  handleMouseOver(event) {
    this.parentElement?.setCurrentItem(this);
    event.stopPropagation();
  }

  highlight(s) {
    const start = s.toLowerCase().indexOf(this.prefix.toLowerCase());
    if (start === -1) return s;
    const before = s.substring(0, start);
    const matching = s.substring(start, start + this.prefix.length);
    const after = s.substring(start + this.prefix.length);
    return html`${before}<b>${matching}</b>${after}`;
  }

  render() {
    const highlightedValue = this.highlight(this.value);
    const highlightedDoc = this.highlight(this.doc);
    return html`
      <div
        class="menu-item ${this.tabindex === 0 ? 'active' : ''}"
        @mouseover=${this.handleMouseOver}
      >
        <span id="value"><code>${highlightedValue}</code></span>
        <span id="doc">${highlightedDoc}</span>
      </div>
    `;
  }
}
customElements.define('chromedash-typeahead-item', ChromedashTypeaheadItem);
