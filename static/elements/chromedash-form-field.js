import {LitElement, html, css} from 'lit';
import {ALL_FIELDS} from './form-field-specs';
import {unsafeHTML} from 'lit/directives/unsafe-html.js';
import {SHARED_STYLES} from '../sass/shared-css.js';


export class ChromedashFormField extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
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
      `];
  }

  static get properties() {
    return {
      name: {type: String},
      value: {type: String},
      field: {type: String},
      errors: {type: String},
      stage: {type: String},
      disabled: {type: Boolean},
    };
  }

  toggleExtraHelp() {
    const details = this.renderRoot.querySelector('sl-details');
    details.open = !details.open;
    const button = this.renderRoot.querySelector('sl-icon-button');
    button.name = details.open ? 'dash-square' : 'plus-square';
  }

  // Must render to light DOM, so sl-form-fields work as intended.
  createRenderRoot() {
    return this;
  }

  render() {
    const fieldProps = ALL_FIELDS[this.name] || {};
    const label = fieldProps.label;
    const helpText = fieldProps.help_text || '';
    const extraHelpText = fieldProps.extra_help || '';
    const type = fieldProps.type;

    // If type is checkbox, then generate locally.
    let fieldHTML = '';
    if (type === 'checkbox') {
      fieldHTML = html`
          <sl-checkbox
            name="${this.name}"
            id="id_${this.name}"
            size="small"
            ?checked=${ this.value === 'True' ? true : false }
            ?disabled=${ this.disabled }
            >
          ${label}
        </sl-checkbox>
        `;
      this.generateFieldLocally = true;
    } else {
      // Temporary workaround until we migrate the generation of
      // all the form fields to be done here.
      // We pass the escaped html for the low-level form field
      // through the field attribute, so it must be unescaped,
      // and then we use unsafeHTML so it isn't re-escaped.
      fieldHTML = unsafeHTML(unescape(this.field || ''));
    }

    // Similar to above, but maybe we can guarantee that the errors
    // will never contain HTML.
    const errorsHTML = unsafeHTML(unescape(this.errors || ''));

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
          ${fieldHTML}
          ${errorsHTML}
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
