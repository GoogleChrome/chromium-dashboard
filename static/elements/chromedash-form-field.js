import {LitElement, html} from 'lit';
import {ALL_FIELDS} from './form-field-specs';
import {unsafeHTML} from 'lit/directives/unsafe-html.js';


/* Patterns from https://www.oreilly.com/library/view/regular-expressions-cookbook/9781449327453/ch04s01.html
 * Removing single quote ('), backtick (`), and pipe (|) since they are risky unless properly escaped everywhere.
 * Also removing ! and % because they have special meaning for some older email routing systems. */
const USER_REGEX = '[A-Za-z0-9_#$&*+/=?{}~^.-]+';
const DOMAIN_REGEX = String.raw`(([A-Za-z0-9-]+\.)+[A-Za-z]{2,6})`;

const EMAIL_ADDRESS_REGEX = USER_REGEX + '@' + DOMAIN_REGEX;
const EMAIL_ADDRESSES_REGEX = EMAIL_ADDRESS_REGEX + '([ ]*,[ ]*' + EMAIL_ADDRESS_REGEX + ')*';

// Simple http URLs
const PORTNUM_REGEX = '(:[0-9]+)?';
const URL_REGEX = '(https?)://' + DOMAIN_REGEX + PORTNUM_REGEX + String.raw`(/[^\s]*)?`;
const URL_PADDED_REGEX = String.raw`\s*` + URL_REGEX + String.raw`\s*`;


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
    const attrs = fieldProps.attrs || {};
    const choices = fieldProps.choices || this.componentChoices;

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
      let inputType = '';
      let title = '';
      let placeholder;
      let pattern;
      switch (fieldProps.input_type) {
        case 'text':
          inputType = 'text';
          break;

        case 'url':
          inputType = 'url';
          title = 'Enter a full URL https://...';
          placeholder = 'https://...';
          pattern = URL_PADDED_REGEX;
          break;

        case 'multi-email':
          /* Don't specify type="email" because browsers consider multiple emails
          * invalid, regardles of the multiple attribute. */
          inputType = 'text';
          title = 'Enter one or more comma-separated complete email addresses.';
          placeholder = 'user1@domain.com, user2@chromium.org';
          pattern = EMAIL_ADDRESSES_REGEX;
          break;

        case 'milestone-number':
          inputType = 'number';
          placeholder = 'Milestone number';
          break;

        default:
          console.error(`Invalid input type: ${fieldProps.input_type}`);
      }
      fieldHTML = html`
        <sl-input 
          type="${inputType}"
          name="${this.name}"
          id="id_${this.name}"
          size="small"
          autocomplete="off"
          .title=${title}
          .placeholder=${placeholder}
          .pattern=${pattern}
          .value=${this.value === 'None' ? '' : this.value}
          ?required=${fieldProps.required}>
        </sl-input>
      `;
    } else if (type === 'textarea') {
      fieldHTML = html`
        <chromedash-textarea
          name="${this.name}"
          size="small"
          .value=${this.value === 'None' ? '' : this.value}
          .attrs=${attrs}
          ?required=${fieldProps.required}>
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
