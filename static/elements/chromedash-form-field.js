import {LitElement, html} from 'lit';
import {ALL_FIELDS} from './form-field-specs';
import {unsafeHTML} from 'lit/directives/unsafe-html.js';
import {ref} from 'lit/directives/ref.js';


export class ChromedashFormField extends LitElement {
  static get properties() {
    return {
      name: {type: String},
      value: {type: String},
      field: {type: String},
      errors: {type: String},
      stage: {type: String},
      disabled: {type: Boolean},
      loading: {type: Boolean},
      fieldProps: {type: Object},
      componentChoices: {type: Object}, // just for the blink component select field
    };
  }

  constructor() {
    super();
    this.name = '';
    this.value = '';
    this.field = '';
    this.errors = '';
    this.stage = '';
    this.disabled = false;
    this.loading = false;
    this.componentChoices = {};
  }

  connectedCallback() {
    super.connectedCallback();
    this.fieldProps = ALL_FIELDS[this.name] || {};

    if (this.name !== 'blink_components') return;

    // get the choice values from API when the field is blink component select field
    this.loading = true;
    window.csClient.getBlinkComponents().then((componentChoices) => {
      this.componentChoices = componentChoices;
      this.loading = false;
    }).catch(() => {
      showToastMessage('Some errors occurred. Please refresh the page or try again later.');
    });
  }

  updateAttributes(el) {
    if (!el) return;

    const attrs = this.fieldProps.attrs || {};
    Object.keys(attrs).map((attr) => {
      el.setAttribute(attr, attrs[attr]);
    });
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
    const label = this.fieldProps.label;
    const helpText = this.fieldProps.help_text || '';
    const extraHelpText = this.fieldProps.extra_help || '';
    const type = this.fieldProps.type;
    const choices = this.fieldProps.choices || this.componentChoices;

    // If type is checkbox, select, or input, then generate locally.
    let fieldHTML = '';
    if (type === 'checkbox') {
      // value can be a js or python boolean value converted to a string
      fieldHTML = html`
        <sl-checkbox
          name="${this.name}"
          id="id_${this.name}"
          size="small"
          ?checked=${this.value === 'true' || this.value === 'True'}
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
          ?disabled=${this.disabled || this.loading}
        >
          ${Object.values(choices).map(
            ([value, label]) => html`
              <sl-menu-item value="${value}"> ${label} </sl-menu-item>
            `,
          )}
        </sl-select>
      `;
    } else if (type === 'input') {
      fieldHTML = html`
        <sl-input
          ${ref(this.updateAttributes)}
          name="${this.name}"
          id="id_${this.name}"
          size="small"
          autocomplete="off"
          .value=${this.value === 'None' ? '' : this.value}
          ?required=${this.fieldProps.required}>
        </sl-input>
      `;
    } else if (type === 'textarea') {
      fieldHTML = html`
        <chromedash-textarea
          ${ref(this.updateAttributes)}
          name="${this.name}"
          size="small"
          .value=${this.value === 'None' ? '' : this.value}
          ?required=${this.fieldProps.required}>
        </chromedash-textarea>
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
                  style="position:absolute"
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
              <sl-details summary="">
                <span class="helptext">
                  ${extraHelpText}
                </span>
              </sl-details>
            </td>
          </tr>` :
        ''}
    `;
  }
}

customElements.define('chromedash-form-field', ChromedashFormField);
