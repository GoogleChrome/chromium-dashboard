import {LitElement, css, html} from 'lit';
import {customElement, property} from 'lit/decorators.js';

@customElement('chromedash-form-table')
export class ChromedashFormTable extends LitElement {
  @property({type: String})
  class;

  static get styles() {
    return [
      css`
        :host {
          display: table;
          max-width: 80em;
        }
      `,
    ];
  }

  render() {
    return html` <slot>fallback content</slot> `;
  }
}
