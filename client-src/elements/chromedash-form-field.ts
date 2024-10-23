import {SlDetails, SlIconButton, SlInput} from '@shoelace-style/shoelace';
import {LitElement, TemplateResult, html, nothing} from 'lit';
import {customElement, property, state} from 'lit/decorators.js';
import {ref} from 'lit/directives/ref.js';

import {ChromedashApp} from './chromedash-app';
import './chromedash-textarea';
import {ALL_FIELDS, resolveFieldForFeature} from './form-field-specs';
import {
  FieldInfo,
  getFieldValueFromFeature,
  showToastMessage,
} from './utils.js';
import {Feature, StageDict} from '../js-src/cs-client';
import {FormattedFeature} from './form-definition';

interface getFieldValue {
  (fieldName: string, stageOrId: any): any;
  feature?: Feature;
}

@customElement('chromedash-form-field')
export class ChromedashFormField extends LitElement {
  @property({type: String})
  name = '';
  @property({type: Number}) // Represents which field this is on the form.
  index = -1;
  @property({type: Object}) // All other field value objects in current form.
  fieldValues!: FieldInfo[] & {feature: Feature};
  @property({type: Object, attribute: false})
  feature!: FormattedFeature;
  @property({type: String}) // Optional override of default label.
  checkboxLabel = '';
  @property({type: Boolean})
  disabled = false;
  @property({type: Boolean})
  shouldFadeIn = false;
  @property({type: Boolean})
  forEnterprise = false;
  @property({type: String})
  disabledReason = '';
  @property({type: Number})
  stageId;
  @property({type: Number})
  stageType;
  @property({type: String})
  value = '';

  @state()
  initialValue = '';
  @state()
  loading = false;
  @state()
  componentChoices: Record<string, [string, string]> = {}; // just for the blink component select field
  @state()
  checkMessage: TemplateResult | string = '';
  @state()
  fieldProps;

  getValue() {
    // value can be a js or python boolean value converted to a string
    // or the initial value specified in form-field-spec
    // If value is falsy, it will be replaced by the initial value, if any.
    const useEnterpriseDefault =
      this.forEnterprise && this.fieldProps.enterprise_initial !== undefined;
    const initialValue = useEnterpriseDefault
      ? this.fieldProps.enterprise_initial
      : this.fieldProps.initial;
    return !this.value && initialValue ? initialValue : this.value;
  }

  connectedCallback() {
    super.connectedCallback();
    this.fieldProps = resolveFieldForFeature(
      ALL_FIELDS[this.name] || {},
      this.feature
    );

    // Register this form field component with the page component.
    const app: ChromedashApp | null = document.querySelector('chromedash-app');
    if (app?.pageComponent) {
      app.pageComponent.allFormFieldComponentsList.push(this);
    }

    if (this.name === 'blink_components') {
      // get the choice values from API when the field is blink component select field
      this.loading = true;
      window.csClient
        .getBlinkComponents()
        .then(componentChoices => {
          this.componentChoices = componentChoices;
          this.loading = false;
        })
        .catch(() => {
          showToastMessage(
            'Some errors occurred. Please refresh the page or try again later.'
          );
        });
    }
  }

  firstUpdated() {
    this.initialValue = JSON.parse(JSON.stringify(this.value));
    // We need to wait until the entire page is rendered, so later dependents
    // are available to do the semantic check, hence firstUpdated is too soon.
    // Do first semantic check after the document is ready.
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () =>
        setTimeout(() => {
          this.doSemanticCheck();
        })
      );
    } else {
      this.doSemanticCheck();
    }
  }

  updateAttributes(el) {
    if (!el) return;

    const attrs = this.fieldProps.attrs || {};
    Object.keys(attrs).map(attr => {
      el.setAttribute(attr, attrs[attr]);
    });
  }

  toggleExtraHelp() {
    const details: SlDetails = this.renderRoot.querySelector('sl-details')!;
    details.open = !details.open;
    const button: SlIconButton =
      this.renderRoot.querySelector('sl-icon-button')!;
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
    let fieldValue: string;
    if (type === 'checkbox') {
      fieldValue = e.target.checked;
    } else if (type === 'multiselect') {
      fieldValue = e.target.value.join(',');
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
    const app: ChromedashApp | null = document.querySelector('chromedash-app');
    if (app?.pageComponent) {
      app.pageComponent.allFormFieldComponentsList.forEach(formFieldComponent =>
        formFieldComponent.doSemanticCheck()
      );
    } else {
      // Do the semantic check for unit testing.  Only works for isolated field.
      this.doSemanticCheck();
    }
  }

  async doSemanticCheck() {
    // Define function to get any other field value relative to this field.
    // stageOrId is either a stage object or an id, or the special value
    // 'current stage' which means use the same stage as for this field.

    const getFieldValue: getFieldValue = (fieldName, stageOrId) => {
      if (stageOrId === 'current stage') {
        stageOrId = this.stageId;
      }
      return getFieldValueWithStage(
        fieldName,
        stageOrId,
        this.fieldValues || []
      );
    };
    // Attach the feature to the getFieldValue function, which is needed to
    // iterate through stages not in the form.
    getFieldValue.feature = this.fieldValues?.feature;

    const checkFunctionWrapper = async checkFunction => {
      const fieldValue = this.getValue();
      const initialValue = this.initialValue;

      if (fieldValue == null) return false; // Assume there is nothing to check.

      // Call the checkFunction and await result, in case it is async.
      const checkResult = await checkFunction(
        fieldValue,
        getFieldValue,
        initialValue
      );
      if (checkResult == null) {
        // Don't clear this.checkMessage here.
        return false;
      } else {
        this.checkMessage = html` <span
          class="check-${checkResult.message
            ? 'message'
            : checkResult.warning
              ? 'warning'
              : checkResult.error
                ? 'error'
                : 'unknown'}"
        >
          ${checkResult.message
            ? checkResult.message
            : checkResult.warning
              ? html`<b>Warning</b>: ${checkResult.warning}`
              : checkResult.error
                ? html`<b>Error</b>: ${checkResult.error}`
                : ''}
        </span>`;
        // Return from doSemanticCheck with the first non-empty message.
        return true;
      }
    };

    // Get the check function(s) to run.
    const checkFunctionOrArray = this.fieldProps.check || [];
    const checkFunctions =
      typeof checkFunctionOrArray === 'function'
        ? [checkFunctionOrArray]
        : checkFunctionOrArray;
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
    }
  }

  renderWidget() {
    const type = this.fieldProps.type;
    const fieldDisabled = this.fieldProps.disabled;
    const fieldValue = this.getValue();

    // form field name can be specified in form-field-spec to match DB field name
    const fieldName = this.fieldProps.name || this.name;
    // choices can be specified in form-field-spec or fetched from API
    const choices: [number, string][] | [number, string, string][] =
      this.fieldProps.choices || this.componentChoices;

    let fieldHTML = html``;
    if (type === 'checkbox') {
      const label = this.checkboxLabel || this.fieldProps.label;
      fieldHTML = html`
        <sl-checkbox
          name="${fieldName}"
          id="id_${this.name}"
          size="small"
          ?checked=${fieldValue === 'true' || fieldValue === 'True'}
          ?disabled=${this.disabled || fieldDisabled}
          @sl-change="${this.handleFieldUpdated}"
        >
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
          @sl-change="${this.handleFieldUpdated}"
        >
          ${Object.values(choices).map(
            ([value, label]) => html`
              <sl-option value="${value}"> ${label} </sl-option>
            `
          )}
        </sl-select>
      `;
    } else if (type === 'multiselect') {
      const valueArray: string[] = fieldValue.split(',');
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
          @sl-change="${this.handleFieldUpdated}"
        >
          ${Object.values(choices).map(
            ([value, label]) => html`
              <sl-option value="${value}"> ${label} </sl-option>
            `
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
          help-text="${this.disabledReason}"
          ?disabled=${this.disabled || this.disabledReason || fieldDisabled}
          ?required=${this.fieldProps.required}
          @sl-change="${this.handleFieldUpdated}"
        >
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
          @sl-change="${this.handleFieldUpdated}"
        >
        </chromedash-textarea>
      `;
    } else if (type === 'radios') {
      fieldHTML = html`
        ${Object.values(choices).map(
          ([value, label, description]) => html`
            <input
              id="id_${this.name}_${value}"
              name="${fieldName}"
              value="${value}"
              .checked="${value === fieldValue}"
              type="radio"
              required
              @change=${this.handleFieldUpdated}
            />
            <label for="id_${this.name}_${value}">${label}</label>
            <p>${description}</p>
          `
        )}
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
            @change=${this.handleFieldUpdated}
          />
        </div>
        <datalist id="${this.name}_list">
          ${Object.values(choices).map(
            ([value]) => html` <option value="${value}"></option> `
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
      this.forEnterprise && this.fieldProps.enterprise_help_text !== undefined
        ? this.fieldProps.enterprise_help_text
        : this.fieldProps.help_text;
    const extraHelpText =
      this.forEnterprise && this.fieldProps.enterprise_extra_help !== undefined
        ? this.fieldProps.enterprise_extra_help
        : this.fieldProps.extra_help;
    const fadeInClass = this.shouldFadeIn ? 'fade-in' : '';
    return html`
      ${this.fieldProps.label
        ? html`
            <tr class="${fadeInClass}">
              <th colspan="2">
                <b>${this.fieldProps.label}:</b>
              </th>
            </tr>
          `
        : nothing}
      <tr class=${fadeInClass}>
        <td>${this.renderWidget()} ${this.checkMessage}</td>
        <td>
          ${helpText
            ? html`<span class="helptext"> ${helpText} </span>`
            : nothing}
          ${extraHelpText
            ? html`
                <sl-icon-button
                  name="plus-square"
                  label="Toggle extra help"
                  style="position:absolute"
                  @click="${this.toggleExtraHelp}"
                >
                  +
                </sl-icon-button>
              `
            : nothing}
        </td>
      </tr>

      ${extraHelpText
        ? html`
            <tr>
              <td colspan="2" class="extrahelp">
                <sl-details summary="">
                  <span class="helptext"> ${extraHelpText} </span>
                </sl-details>
              </td>
            </tr>
          `
        : nothing}
    `;
  }
}

/**
 * Gets the value of a field from a feature entry form, or from the feature.
 * Looks up the field name in the provided form field values, using the stageOrId
 * if the field is stage-specific, and returns the corresponding value.
 * Returns null if not defined or not found.
 * Handles special cases like shipping milestones and mapped stage fields.
 */
function getFieldValueWithStage(
  fieldName: string,
  stageOrId: number | StageDict | undefined,
  formFieldValues: FieldInfo[] & {feature?: Feature}
) {
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
  const feature = formFieldValues?.feature;
  if (feature == null) {
    return null;
  }

  // Get the stage object for the field.
  const feStage =
    typeof stageOrId === 'object'
      ? stageOrId
      : stageId != null
        ? feature.stages.find(s => s.id == stageId)
        : feature.stages[0];
  if (!feStage) {
    return null;
  }
  // Lookup fieldName by following the stage specific path starting from feature.
  const value = getFieldValueFromFeature(fieldName, feStage, feature);
  return value;
}
