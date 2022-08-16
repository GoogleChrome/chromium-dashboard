import {LitElement, html} from 'lit';
import {ALL_FIELDS} from './form-field-specs';
import {unsafeHTML} from 'lit/directives/unsafe-html.js';

export class ChromedashFormField extends LitElement {
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
    const choices = fieldProps.choices;

    // If type is checkbox, then generate locally.
    let fieldHTML = '';
    if (type === 'checkbox') {
      fieldHTML = html`
        <sl-checkbox
          name="${this.name}"
          id="id_${this.name}"
          size="small"
          ?checked=${this.value === 'True' ? true : false}
          ?disabled=${this.disabled}
        >
          ${label}
        </sl-checkbox>
      `;
      this.generateFieldLocally = true;
    } else if (type === 'select') {
      fieldHTML = html`
        <sl-select
          name="${this.name}"
          id="id_${this.name}"
          value="${this.value}"
          size="small"
          ?disabled=${this.disabled}
        >
          ${Object.values(choices).map(
            ([intValue, label]) => html`
              <sl-menu-item value="${intValue}"> ${label} </sl-menu-item>
            `,
          )}
        </sl-select>
      `;
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
          <b> ${label ? label + ':' : ''} </b>
        </th>
      </tr>
      <tr>
        <td>${fieldHTML} ${errorsHTML}</td>
        <td>
          <span class="helptext"> ${helpText} </span>
          ${extraHelpText ?
            html`
                <sl-icon-button
                  name="plus-square"
                  label="Toggle extra help"
                  @click="${this.toggleExtraHelp}"
                  >+</sl-icon-button
                >
              ` :
            ''}
        </td>
      </tr>

      ${extraHelpText ?
        html` <tr>
            <td colspan="2" class="extrahelp">
              <sl-details summary=""> ${extraHelpText} </sl-details>
            </td>
          </tr>` :
        ''}
    `;
  }
}

customElements.define('chromedash-form-field', ChromedashFormField);
