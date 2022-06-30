import {LitElement, css, html} from 'lit';

export class ChromedashFormField extends LitElement {
  static get styles() {
    return [
      css`
        :host {
          display: table-row-group;
        }

        tr[hidden] th,
        tr[hidden] td {
          padding: 0;
        }

        th, td {
          text-align: left;
          vertical-align: top;
        }

        th {
          padding: 12px 10px 5px 0;
        }

        td {
          padding: 6px 10px;
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

        .errorlist {
          color: red;
        }
      `,
    ];
  }

  render() {
    return html`
      <tr>
        <th colspan="2">
          <b>
          <slot name="label">the label goes here</slot>
          </b>
        </th>
      </tr>
      <tr>
        <td>
          <slot name="error" class="errorlist"></slot>
          <slot name="field"></slot>
        </td>
        <td>
          <slot name="help" class="helptext"></slot>
        </td>
      </tr>`;
  }
}

customElements.define('chromedash-form-field', ChromedashFormField);

