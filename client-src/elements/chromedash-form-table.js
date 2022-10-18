import {LitElement, css, html} from 'lit';


export class ChromedashFormTable extends LitElement {
  static get properties() {
    return {
      class: {type: String},
    };
  }

  static get styles() {
    return [
      css`
      :host {
        display: table;
        max-width: 80em;
      }

  `];
  }

  render() {
    return html`
      <slot>fallback content</slot>
    `;
  }
}

customElements.define('chromedash-form-table', ChromedashFormTable);
