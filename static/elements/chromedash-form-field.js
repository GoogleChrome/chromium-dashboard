import {LitElement, css, html} from 'lit';
import {ifDefined} from 'lit/directives/if-defined.js';
// import {live} from 'lit/directives/live.js';
import {SHARED_STYLES} from '../sass/shared-css.js';

export class ChromedashFormField extends LitElement {
  static get properties() {
    return {
      id: {type: String},
      name: {type: String},
      label: {type: String},
      class: {type: String},
      error_text: {type: String},
      field_text: {type: String},
    };
  }

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        :host {
          display: table-row-group;
        }

        /* :host,
        tr {
          width: 100%;
        } */

        tr[hidden] th,
        tr[hidden] td {
          padding: 0;
        }

        th {
          padding: 12px 10px 5px 0;
          vertical-align: top;
        }

        td {
          padding: 6px 10px;
          vertical-align: top;
        }

        td:first-of-type {
          width: 60%;
        }

        .helptext {
          display: block;
          font-size: small;
          max-width: 40em;
          margin-top: 2px;
        }

      `,
    ];
  }

  render() {
    return html`
      <tr class="${ifDefined(this.class)}">
        <th colspan="2">
          <b>
          ${this.label}
          <slot name="label"></slot>
          </b>
        </th>
      </tr>
      <tr class="${ifDefined(this.class)}">
        <td>
          <slot name="field"></slot>
          <slot name="error"></slot>
        </td>
        <td>
          <slot name="help" class="helptext"></slot>
        </td>
      </tr>`;
  }
}

customElements.define('chromedash-form-field', ChromedashFormField);

