import {LitElement, html, nothing} from 'lit';
import {ALL_FIELDS} from './form-field-specs';
import {ref} from 'lit/directives/ref.js';
import './chromedash-textarea';


export class ChromedashFormField extends LitElement {
  static get properties() {
    return {
      name: {type: String},
      value: {type: String},
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

  renderWidgets() {
    const type = this.fieldProps.type;
    const choices = this.fieldProps.choices || this.componentChoices;

    let fieldHTML = '';
    if (type === 'checkbox') {
      // value can be a js or python boolean value converted to a string
      fieldHTML = html`
        <sl-checkbox
          name="${this.name}"
          id="id_${this.name}"
          size="small"
          ?checked=${this.value === 'true' || this.value === 'True'}
          ?disabled=${this.disabled}>
          ${this.fieldProps.label}
        </sl-checkbox>
      `;
    } else if (type === 'select') {
      fieldHTML = html`
        <sl-select
          name="${this.name}"
          id="id_${this.name}"
          value="${this.value}"
          size="small"
          ?disabled=${this.disabled || this.loading}>
          ${Object.values(choices).map(
            ([value, label]) => html`
              <sl-menu-item value="${value}"> ${label} </sl-menu-item>
            `
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
    } else if (type === 'radios') {
      const fieldName = this.fieldProps.name || this.name;
      fieldHTML = html`
        ${Object.values(choices).map(
          ([value, label, description]) => html`
            <input id="id_${fieldName}_${value}" name="${fieldName}"
              value="${value}" type="radio" required>
            <label for="id_${fieldName}_${value}">${label}</label>
            <p>${description}</p>
          `)}
      `;
    } else if (type === 'blink-component-dialog') {
      fieldHTML = html`
      <input name=${this.name} type="hidden" value=${this.value}>
      <p style="font-size: 16px">${this.value}
        <sl-button size="small" style="margin-left: 10px;"
          @click=${() => this.renderRoot.querySelector('sl-dialog').show()}>
          <iron-icon slot="prefix" icon="chromestatus:create"></iron-icon>
          Choose component
        </sl-button>
      </p>
      <sl-dialog label="Select a Blink component:" style="--width:fit-content">
        <div style="display: flex; flex-direction: column; gap: 5px">
          ${Object.values(choices).map(
            ([value]) => html`
            <a @click=${()=> {
              this.value = value;
              this.renderRoot.querySelector('sl-dialog').hide();
            }}> ${value} </a>
            `,
          )}
        </div>
      </sl-dialog>`;
    } else {
      console.error(`unknown form field type: ${type}`);
    }
    return fieldHTML;
  }

  render() {
    const helpText = this.fieldProps.help_text;
    const extraHelpText = this.fieldProps.extra_help;

    return html`
      ${this.fieldProps.label ? html`
        <tr>
          <th colspan="2">
            <b>${this.fieldProps.label}:</b>
          </th>
        </tr>
      `:nothing}
      <tr>
        <td>${this.renderWidgets()}</td>
        <td>
          ${helpText ? html`<span class="helptext"> ${helpText} </span>`: nothing}
          ${extraHelpText ? html`
            <sl-icon-button
              name="plus-square"
              label="Toggle extra help"
              style="position:absolute"
              @click="${this.toggleExtraHelp}">
              +
            </sl-icon-button>
          `: nothing}
        </td>
      </tr>

      ${extraHelpText ? html`
        <tr>
          <td colspan="2" class="extrahelp">
            <sl-details summary="">
              <span class="helptext">
                ${extraHelpText}
              </span>
            </sl-details>
          </td>
        </tr>`:
      nothing}
    `;
  }
}

customElements.define('chromedash-form-field', ChromedashFormField);
