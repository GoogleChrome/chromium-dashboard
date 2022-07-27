import {LitElement, css, html} from 'lit';
import {ALL_FIELDS} from './form-field-specs';

export class ChromedashFormField extends LitElement {
  static get properties() {
    return {
      name: {type: String},
      value: {type: String},
    };
  }

  static get styles() {
    // Remove vertical padding for extrahelp row cell.
    // Rely on padding of sl-details, when it's displayed.

    // If first child of helptext and sl-details content has
    // margin-top, typically only block elements do,
    // then make it 0.
    // Similarly for last-child and margin-bottom.
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
          max-width: 35em;
        }

        td.extrahelp {
          padding: 0 10px;
        }

        .helptext {
          display: block;
          font-size: small;
          max-width: 40em;
          margin-top: 2px;
        }

        .helptext > *:first-child {
          margin-top: 0;
        }
        .helptext > *:last-child {
          margin-bottom: 0;
        }

        .errorlist {
          color: red;
        }

        sl-details::part(base) {
          border-width: 0;
        }

        sl-details::part(header) {
          padding: 0;
          display: none;
        }

        sl-details::part(content) {
          padding-top: 0;
        }

        sl-icon-button::part(base) {
          font-size: 16px;
          color: var(--link-color);
          padding: 0;
          margin: 4px;
        }

        sl-details > *:first-child {
          margin-top: 0;
        }
        sl-details > *:last-child {
          margin-bottom: 0;
        }
      `,
    ];
  }

  toggleExtraHelp() {
    const details = this.renderRoot.querySelector('sl-details');
    details.open = !details.open;
    const button = this.renderRoot.querySelector('sl-icon-button');
    button.name = details.open ? 'dash-square' : 'plus-square';
  }

  render() {
    const fieldProps = ALL_FIELDS[this.name] || {};
    const label = fieldProps.label;
    const helpText = fieldProps.help_text || '';
    const extraHelpText = fieldProps.extra_help || '';
    const type = fieldProps.type;

    let field = '';
    // If type is checkbox, then generate locally.
    if (type === 'checkbox') {
      field = html`
        <sl-checkbox
            name="${this.name}"
            size="small"
            value="${ this.value }"
            >
            ${label}
        </sl-checkbox>
        `;
    } else {
      field = html`<slot name="field"></slot>`;
    }

    return html`
      <tr>
        <th colspan="2">
          <b>
            ${label ? label + ':' : ''}
          </b>
        </th>
      </tr>
      <tr>
        <td>
          ${field}
          <slot name="error" class="errorlist"></slot>
        </td>
        <td>
          <span class="helptext">
            ${helpText}
          </span>
          ${extraHelpText ? html`
          <sl-icon-button name="plus-square"
            label="Toggle extra help"
            @click="${this.toggleExtraHelp}">+</sl-icon-button>
          ` : ''}
        </td>
      </tr>
                  
      ${extraHelpText ? html`
      <tr>
        <td colspan="2" class="extrahelp">
          <sl-details summary="">
            ${extraHelpText}
          </sl-details>
        </td>
      </tr>` : ''}
    `;
  }
}

customElements.define('chromedash-form-field', ChromedashFormField);
