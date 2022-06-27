import {LitElement, css, html} from 'lit';
// import {ifDefined} from 'lit/directives/if-defined.js';
// import {live} from 'lit/directives/live.js';
import {SHARED_STYLES} from '../sass/shared-css.js';

export class ChromedashFormTable extends LitElement {
  static get properties() {
    return {
      class: {type: String},
    };
  }

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
      :host {
        display: table;
        max-width: 80em;
      }

  `];
  }

  render() {
    return html`
<table><tbody><slot></slot></tbody></table>
`;
  }
}

customElements.define('chromedash-form-table', ChromedashFormTable);
