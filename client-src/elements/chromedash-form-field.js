import {LitElement, html, nothing} from 'lit';
import {ALL_FIELDS} from './form-field-specs';
import {ref} from 'lit/directives/ref.js';
import './chromedash-textarea';
import {STAGE_SPECIFIC_FIELDS} from './form-field-enums';
import {showToastMessage} from './utils.js';

export class ChromedashFormField extends LitElement {
  static get properties() {
    return {
      name: {type: String},
      stageId: {type: Number},
      value: {type: String},
      disabled: {type: Boolean},
      loading: {type: Boolean},
      fieldProps: {type: Object},
      forEnterprise: {type: Boolean},
      componentChoices: {type: Object}, // just for the blink component select field
    };
  }

  constructor() {
    super();
    this.name = '';
    this.stageId = 0;
    this.value = '';
    this.disabled = false;
    this.loading = false;
    this.forEnterprise = false;
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
    const fieldDisabled = this.fieldProps.disabled;

    // if no value is provided, use the initial value specified in form-field-spec
    const fieldValue = !this.value && this.fieldProps.initial ?
      this.fieldProps.initial : this.value;

    // form field name can be specified in form-field-spec to match DB field name
    let fieldName = this.fieldProps.name || this.name;
    if (STAGE_SPECIFIC_FIELDS.has(fieldName) && this.stageId) {
      fieldName = `${fieldName}__${this.stageId}`;
    }
    // choices can be specified in form-field-spec or fetched from API
    const choices = this.fieldProps.choices || this.componentChoices;

    let fieldHTML = '';
    if (type === 'checkbox') {
      // value can be a js or python boolean value converted to a string
      // or the initial value specified in form-field-spec
      fieldHTML = html`
        <sl-checkbox
          name="${fieldName}"
          id="id_${this.name}"
          size="small"
          ?checked=${fieldValue === 'true' || fieldValue === 'True'}
          ?disabled=${this.disabled || fieldDisabled}>
          ${this.fieldProps.label}
        </sl-checkbox>
      `;
    } else if (type === 'select') {
      fieldHTML = html`
        <sl-select
          name="${fieldName}"
          id="id_${this.name}"
          value="${fieldValue}"
          size="small"
          hoist
          ?disabled=${fieldDisabled || this.disabled || this.loading}>
          ${Object.values(choices).map(
            ([value, label]) => html`
              <sl-option value="${value}"> ${label} </sl-option>
            `,
          )}
        </sl-select>
      `;
    } else if (type === 'multiselect') {
      const valueArray = fieldValue.split(',');

      fieldHTML = html`
        <sl-select
          name="${fieldName}"
          id="id_${this.name}"
          .value=${valueArray}
          size="small"
          hoist
          multiple
          cleareable
          ?disabled=${fieldDisabled || this.disabled || this.loading}>
          ${Object.values(choices).map(
            ([value, label]) => html`
              <sl-option value="${value}"> ${label} </sl-option>
            `,
          )}
        </sl-select>
      `;
    } else if (type === 'input') {
      fieldHTML = html`
        <sl-input
          ${ref(this.updateAttributes)}
          name="${fieldName}"
          id="id_${this.name}"
          size="small"
          autocomplete="off"
          .value=${fieldValue}
          ?required=${this.fieldProps.required}>
        </sl-input>
      `;
    } else if (type === 'textarea') {
      fieldHTML = html`
        <chromedash-textarea
          ${ref(this.updateAttributes)}
          name="${fieldName}"
          id="id_${this.name}"
          size="small"
          .value=${fieldValue}
          ?required=${this.fieldProps.required}>
        </chromedash-textarea>
      `;
    } else if (type === 'radios') {
      fieldHTML = html`
        ${Object.values(choices).map(
          ([value, label, description]) => html`
            <input id="id_${this.name}_${value}" name="${fieldName}"
              value="${value}" type="radio" required>
            <label for="id_${this.name}_${value}">${label}</label>
            <p>${description}</p>
          `)}
      `;
    } else if (type === 'datalist') {
      fieldHTML = html`
        <div class="datalist-input-wrapper">
          <input
            ${ref(this.updateAttributes)}
            name="${fieldName}"
            id="id_${this.name}"
            value="${fieldValue}"
            class="datalist-input"
            type="search"
            list="${this.name}_list"
            ?required=${this.fieldProps.required} />
        </div>
        <datalist id="${this.name}_list">
          ${Object.values(choices).map(
            ([value]) => html`
              <option value="${value}"></option>
            `,
          )}
        </datalist>
      `;
    } else {
      console.error(`unknown form field type: ${type}`);
    }
    return fieldHTML;
  }

  render() {
    const helpText = this.forEnterprise && this.fieldProps.enterprise_help_text ?
      this.fieldProps.enterprise_help_text :
      this.fieldProps.help_text;
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
