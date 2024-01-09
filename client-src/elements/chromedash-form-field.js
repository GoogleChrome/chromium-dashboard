import {LitElement, html, nothing} from 'lit';
import {ALL_FIELDS} from './form-field-specs';
import {ref} from 'lit/directives/ref.js';
import './chromedash-textarea';
import {showToastMessage, getFieldValueFromFeature} from './utils.js';

export class ChromedashFormField extends LitElement {
  static get properties() {
    return {
      name: {type: String},
      index: {type: Number}, // Represents which field this is on the form.
      stageId: {type: Number},
      value: {type: String},
      fieldValues: {type: Array}, // All other field value objects in current form.
      disabled: {type: Boolean},
      checkboxLabel: {type: String}, // Optional override of default label.
      shouldFadeIn: {type: Boolean},
      loading: {type: Boolean},
      fieldProps: {type: Object},
      forEnterprise: {type: Boolean},
      stageType: {type: Number},
      componentChoices: {type: Object}, // just for the blink component select field
      checkMessage: {type: String},
    };
  }

  constructor() {
    super();
    this.name = '';
    this.index = -1;
    this.value = '';
    this.fieldValues = [];
    this.checkboxLabel = '';
    this.disabled = false;
    this.shouldFadeIn = false;
    this.loading = false;
    this.forEnterprise = false;
    this.stageId = undefined;
    this.stageType = undefined;
    this.componentChoices = {};
    this.checkMessage = '';
  }

  getValue() {
    // value can be a js or python boolean value converted to a string
    // or the initial value specified in form-field-spec
    return this.value == null && this.fieldProps.initial ?
      this.fieldProps.initial : this.value;
  }

  connectedCallback() {
    super.connectedCallback();
    this.fieldProps = ALL_FIELDS[this.name] || {};

    // Register this form field component with the page component.
    const app = document.querySelector('chromedash-app');
    if (app?.pageComponent) {
      app.pageComponent.allFormFieldComponentsList.push(this);
    }

    if (this.name === 'blink_components') {
      // get the choice values from API when the field is blink component select field
      this.loading = true;
      window.csClient.getBlinkComponents().then((componentChoices) => {
        this.componentChoices = componentChoices;
        this.loading = false;
      }).catch(() => {
        showToastMessage('Some errors occurred. Please refresh the page or try again later.');
      });
    }
  }

  firstUpdated() {
    // We only want to do the following one time.
    this.setupSemanticCheck();

    // We need to wait until the entire page is rendered, so later dependents
    // are available to do the semantic check, hence firstUpdated is too soon.
    // Do first semantic check after the document is ready.
    document.addEventListener('DOMContentLoaded', () => (setTimeout(() => {
      this.doSemanticCheck();
    })));
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

  // Event handler whenever the input field is changed by the user.
  handleFieldUpdated(e) {
    // Determine the value based on the input type.
    const type = this.fieldProps.type;
    let fieldValue;
    if (type === 'checkbox') {
      fieldValue = e.target.checked;
    } else {
      fieldValue = e.target.value;
    }
    this.value = fieldValue; // TODO: Is this safe?


    // Dispatch a new event to notify other components of the changes.
    const eventOptions = {
      detail: {
        value: fieldValue,
        index: this.index,
      },
    };
    this.dispatchEvent(new CustomEvent('form-field-update', eventOptions));

    // Run semantic checks on entire page.  Must be after above dispatch.
    const app = document.querySelector('chromedash-app');
    if (app?.pageComponent) {
      app.pageComponent.allFormFieldComponentsList.forEach((formFieldComponent) =>
        formFieldComponent.doSemanticCheck());
    } else {
      // Do the semantic check for unit testing.  Only works for isolated field.
      this.doSemanticCheck();
    }
  }

  setupSemanticCheck() {
    // Find the form-field component in order to set custom validity.
    const fieldSelector = `#id_${this.name}`;
    const formFieldElements = this.renderRoot.querySelectorAll(fieldSelector);
    if (formFieldElements.length > 1) {
      if (this.stageId) {
        // The id is not unique for fields in multiple stages, e.g. origin trials.
        // So let's try qualifying the selector with this.stageId in a container.
        fieldSelector = `[stageId="${this.stageId} #id_${this.name}"]`;
        formFieldElements = this.renderRoot.querySelectorAll(fieldSelector);
      } else {
        throw new Error(`Name of field, "${this.name}", is not unique and no stage Id was provided.`);
      }
    }
    // There should only be one now.
    const formFieldElement = formFieldElements[0];

    // For 'input' elements.
    if (formFieldElement?.setCustomValidity && formFieldElement.input) {
      formFieldElement.setCustomValidity(
        (checkResult && checkResult.error) ? checkResult.error : '');
    }
    // TODO: handle other form field types.
  }

  async doSemanticCheck() {
    // Define function to get any other field value relative to this field.
    // stageOrId is either a stage object or an id, or the special value
    // 'current stage' which means use the same stage as for this field.
    const getFieldValue = (fieldName, stageOrId) =>
      getFieldValueWithStage(fieldName,
        (stageOrId === 'current stage' ? this.stageId : stageOrId),
        this.fieldValues || []);
      // Attach the feature to the getFieldValue function, in case it is needed.
    getFieldValue.feature = this.fieldValues?.feature;

    const checkFunctionWrapper = async (checkFunction) => {
      const fieldValue = this.getValue();
      if (fieldValue == null) return false; // Assume there is nothing to check.

      // Call the checkFunction and await result, in case it is async.
      const checkResult = await checkFunction(fieldValue, getFieldValue);
      if (checkResult == null) {
        // Don't clear this.checkMessage here.
        return false;
      } else {
        this.checkMessage = html`
          <span class="check-${checkResult.message ? 'message' :
            checkResult.warning ? 'warning' :
              checkResult.error ? 'error' : 'unknown'
          }">
            ${checkResult.message ? checkResult.message :
            checkResult.warning ? html`<b>Warning</b>: ${checkResult.warning}` :
              checkResult.error ? html`<b>Error</b>: ${checkResult.error}` :
                ''
          }
          </span>`;
        // Return from doSemanticCheck with the first non-empty message.
        return true;
      }
    };

    // Get the check function(s) to run.
    const checkFunctionOrArray = this.fieldProps.check || [];
    const checkFunctions =
      (typeof checkFunctionOrArray === 'function') ?
        [checkFunctionOrArray] : checkFunctionOrArray;
    // If there are any check functions,
    // then first clear this.checkMessage before running the checks.
    if (checkFunctions.length > 0) {
      this.checkMessage = '';
    }

    // Run each check function, and return after the first non-empty message.
    for (const checkFunction of checkFunctions) {
      if (await checkFunctionWrapper(checkFunction)) {
        return;
      }
    };
  }

  renderWidget() {
    const type = this.fieldProps.type;
    const fieldDisabled = this.fieldProps.disabled;
    const fieldValue = this.getValue();

    // form field name can be specified in form-field-spec to match DB field name
    const fieldName = this.fieldProps.name || this.name;
    // choices can be specified in form-field-spec or fetched from API
    const choices = this.fieldProps.choices || this.componentChoices;

    let fieldHTML = '';
    if (type === 'checkbox') {
      const label = this.checkboxLabel || this.fieldProps.label;
      fieldHTML = html`
        <sl-checkbox
          name="${fieldName}"
          id="id_${this.name}"
          size="small"
          ?checked=${fieldValue === 'true' || fieldValue === 'True'}
          ?disabled=${this.disabled || fieldDisabled}
          @sl-change="${this.handleFieldUpdated}">
          ${label}
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
          ?disabled=${fieldDisabled || this.disabled || this.loading}
          @sl-change="${this.handleFieldUpdated}">
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
          ?required=${this.fieldProps.required}
          ?disabled=${fieldDisabled || this.disabled || this.loading}
          @sl-change="${this.handleFieldUpdated}">
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
          stageId="${this.stageId}"
          size="small"
          autocomplete="off"
          .value=${fieldValue}
          ?required=${this.fieldProps.required}
          @sl-change="${this.handleFieldUpdated}">
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
          ?required=${this.fieldProps.required}
          @sl-change="${this.handleFieldUpdated}">
        </chromedash-textarea>
      `;
    } else if (type === 'radios') {
      fieldHTML = html`
        ${Object.values(choices).map(
          ([value, label, description]) => html`
            <input id="id_${this.name}_${value}" name="${fieldName}"
              value="${value}" type="radio" required
              @change=${this.handleFieldUpdated}>
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
            ?required=${this.fieldProps.required}
            @change=${this.handleFieldUpdated}/>
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
    const helpText =
      this.forEnterprise && (this.fieldProps.enterprise_help_text !== undefined) ?
        this.fieldProps.enterprise_help_text :
        this.fieldProps.help_text;
    const extraHelpText =
      this.forEnterprise && (this.fieldProps.enterprise_extra_help !== undefined) ?
        this.fieldProps.enterprise_extra_help :
        this.fieldProps.extra_help;
    const fadeInClass = (this.shouldFadeIn) ? 'fade-in' : '';
    return html`
      ${this.fieldProps.label ? html`
        <tr class="${fadeInClass}">
          <th colspan="2">
            <b>${this.fieldProps.label}:</b>
          </th>
        </tr>
      `: nothing}
      <tr class=${fadeInClass}>
        <td>
          ${this.renderWidget()}
          ${this.checkMessage}
        </td>
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
        </tr>
      `: nothing}
    `;
  }
}


/**
 * Gets the value of a field from a feature entry form, or from the feature.
 * Looks up the field name in the provided form field values, using the stageOrId
 * if the field is stage-specific, and returns the corresponding value.
 * Returns null if not defined or not found.
 * Handles special cases like shipping milestones and mapped stage fields.
 * @param {string} fieldName
 * @param {number|Object|undefined} stageOrId
 * @param {Array<{name:string, value:*}>} formFieldValues
 * @return {*}
 */
function getFieldValueWithStage(fieldName, stageOrId, formFieldValues) {
  // Iterate through formFieldValues looking for element with name==fieldName
  // and stage == stageId, if there is a non-null stageId
  let stageId;
  if (typeof stageOrId === 'number') {
    stageId = stageOrId;
  } else if (typeof stageOrId === 'object') {
    stageId = stageOrId.id;
  }

  for (const obj of formFieldValues) {
    if (obj.name === fieldName && (stageId == null || obj.stageId == stageId)) {
      return obj.value;
    }
  }

  // The remainder looks for the field in the feature.
  const feature = formFieldValues.feature;
  if (feature == null) { return null; }

  // Get the stage object for the field.
  const feStage = (typeof stageOrId === 'object') ? stageOrId :
    (stageId != null ?
      feature.stages.find((s) => s.id == stageId) :
      feature.stages[0]);

  // Lookup fieldName by following the stage specific path starting from feature.
  const value = getFieldValueFromFeature(fieldName, feStage, feature);
  return value;
}

customElements.define('chromedash-form-field', ChromedashFormField);
