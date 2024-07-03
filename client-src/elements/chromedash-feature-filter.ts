import {LitElement, css, html} from 'lit';
import {customElement, property} from 'lit/decorators.js';
import {createRef, Ref, ref} from 'lit/directives/ref.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {openSearchHelpDialog} from './chromedash-search-help-dialog.js';
import {QUERIABLE_FIELDS} from './queriable-fields.js';
import {ChromedashTypeahead} from './chromedash-typeahead.js';

const VOCABULARY = QUERIABLE_FIELDS.map(qf => {
  return {name: qf.name + '=', doc: qf.doc};
});

@customElement('chromedash-typeahead')
class ChromedashFeatureFilter extends LitElement {
  typeaheadRef = createRef<ChromedashTypeahead>();

  @property({type: String})
  query = '';

  _fireEvent(eventName, detail) {
    const event = new CustomEvent(eventName, {
      bubbles: true,
      composed: true,
      detail,
    });
    this.dispatchEvent(event);
  }

  handleSearchClick() {
    const typeahead = this.typeaheadRef.value;
    if (!typeahead) return;
    typeahead.hide();
    const newQuery = typeahead.value.trim();
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
      `,
    ];
  }

  showHelp(event) {
    event.stopPropagation();
    const typeahead = this.typeaheadRef.value;
    if (!typeahead) return;
    typeahead.hide();
    openSearchHelpDialog();
  }

  render() {
    return html`
      <chromedash-typeahead
        ${ref(this.typeaheadRef)}
        value=${this.query}
        placeholder="Search"
        .vocabulary=${VOCABULARY}
        @sl-change=${this.handleSearchClick}
      >
        <sl-icon-button
          library="material"
          name="search"
          slot="prefix"
          @click="${this.handleSearchClick}"
        >
        </sl-icon-button>
        <sl-icon-button
          library="material"
          name="help_20px"
          slot="suffix"
          @click="${this.showHelp}"
        >
        </sl-icon-button>
      </chromedash-typeahead>
    `;
  }
}
