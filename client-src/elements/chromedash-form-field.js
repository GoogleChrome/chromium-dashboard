import {LitElement, html, nothing} from 'lit';
import {ALL_FIELDS} from './form-field-specs';
import {ref} from 'lit/directives/ref.js';
import './chromedash-textarea';
import {showToastMessage, getStageValue} from './utils.js';
import {
  STAGE_FIELD_NAME_MAPPING,
  STAGE_TYPES_SHIPPING,
  SHIPPED_MILESTONE_FIELDS,
} from './form-field-enums.js';

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
    this.stageType = undefined;
    this.componentChoices = {};
    this.checkMessage = '';
  }

  getValue() {
    // value can be a js or python boolean value converted to a string
    // or the initial value specified in form-field-spec
    return !this.value && this.fieldProps.initial ?
      this.fieldProps.initial : this.value;
  }

  connectedCallback() {
    super.connectedCallback();
    this.fieldProps = ALL_FIELDS[this.name] || {};

    const app = document.querySelector('chromedash-app');
    if (app?.pageComponent) {
      app.pageComponent.allFormFieldComponents[this.name] = this;
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
    // We need to wait until the entire page is rendered, so later dependents
    // are available to do the semantic check.  So firstUpdated is too soon.
    this.doSemanticCheck();
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

    // Run semantic check on this field.  Must be after above dispatch.
    this.doSemanticCheck();

    // Also doSemanticCheck on known dependent form fields.
    // We can't do this as part of doSemanticCheck without infinite loop.
    const app = document.querySelector('chromedash-app');
    const dependents = ALL_FIELDS[this.name].dependents;
    if (dependents && app?.pageComponent) {
      dependents.forEach((dependent) => {
        const dependentField = app.pageComponent.allFormFieldComponents[dependent];
        if (dependentField) {
          dependentField.doSemanticCheck();
        }
      });
    }
  }

  doSemanticCheck() {
    const checkFunction = this.fieldProps.check;
    if (checkFunction) {
      const fieldValue = this.getValue();
      const checkResult = checkFunction(fieldValue,
        (name) => getFieldValue(name, this.fieldValues));
      if (checkResult == null) {
        this.checkMessage = '';
      } else {
        this.checkMessage = html`
          <span class="check-${
              checkResult.message ? 'message' :
              checkResult.warning ? 'warning' :
                checkResult.error ? 'error' : 'unknown'
            }">
            ${
              checkResult.message ? checkResult.message :
              checkResult.warning ? html`<b>Warning</b>: ${checkResult.warning}` :
                checkResult.error ? html`<b>Error</b>: ${checkResult.error}` :
                  ''
            }
          </span>`;
      }
      // Find the form-field component in order to set custom validity.
      const fieldSelector = `#id_${this.name}`;
      const formFieldElement = this.renderRoot.querySelector(fieldSelector);

      // // The id is not unique for multi-stage origin trials.
      // // So let's try qualifying the selector with this.stageId.
      // if (!formFieldElement && this.stageId) {
      //   fieldSelector = `#id_${this.name}[stageId="${this.stageId}"]`;
      //   formFieldElement = this.renderRoot.querySelector(fieldSelector);
      // }

      // For 'input' elements.
      if (formFieldElement?.setCustomValidity && formFieldElement.input) {
        formFieldElement.setCustomValidity(
          (checkResult && checkResult.error) ? checkResult.error : '');
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


// Find the shipped stage with the minimum shipped milestone.
function findMinShippedMilestone(fieldName, feature) {
  let minMilestone = Infinity;
  const shippedMilestoneStageName = STAGE_FIELD_NAME_MAPPING[fieldName];
  // Iterate through all stages that are shipping stages.
  for (const stage of feature.stages) {
    if (STAGE_TYPES_SHIPPING.has(stage.stage_type)) {
      const shippedMilestone = stage[shippedMilestoneStageName];
      minMilestone = Math.min(minMilestone, shippedMilestone);
    }
  }
  return minMilestone;
}

/**
 * Gets the value of a field from a feature entry form.
 * Looks up the field name in the provided form field values,
 * and returns the corresponding value.
 * Handles special cases like shipping milestones and mapped stage fields.
 * @param {string} fieldName
 * @param {Array<{name:string, value:*}>} formFieldValues
 * @return {*}
 */
function getFieldValue(fieldName, formFieldValues) {
  // Add direct lookup of formFieldValues objects by name, if not already done.
  // Problem: This might be too soon, if more fields are coming.
  if (!formFieldValues.byName) {
    formFieldValues.byName = {};
    for (const obj of formFieldValues) {
      formFieldValues.byName[obj.name] = obj;
    }
  }

  if (fieldName in formFieldValues.byName) {
    return formFieldValues.byName[fieldName].value;
  }

  // // Iterate through formFieldValues looking for element with name==fieldName
  // for (const {name, value} of formFieldValues) {
  //   if (name === fieldName) {
  //     return value;
  //   }
  // }

  const feature = formFieldValues.feature;
  if (SHIPPED_MILESTONE_FIELDS.has(fieldName)) {
    const minShippedMilestone = findMinShippedMilestone(fieldName, feature);
    return minShippedMilestone;
  }

  if (!feature) return undefined;

  // Otherwise, we have to look up the fieldName in the feature.
  if (fieldName in feature) {
    return feature[fieldName];
  }

  // Map from stage specific field name to feature field path.
  const fieldNameMapping = {
    owner: 'browsers.chrome.owners',
    editors: 'editors',
    search_tags: 'tags',
    spec_link: 'standards.spec',
    standard_maturity: 'standards.maturity.text',
    sample_links: 'resources.samples',
    docs_links: 'resources.docs',
    bug_url: 'browsers.chrome.bug',
    blink_components: 'browsers.chrome.blink_components',
    devrel: 'browsers.chrome.devrel',
    prefixed: 'browsers.chrome.prefixed',
    impl_status_chrome: 'browsers.chrome.status.text',
    shipped_milestone: 'browsers.chrome.desktop',
    shipped_android_milestone: 'browsers.chrome.android',
    shipped_webview_milestone: 'browsers.chrome.webview',
    shipped_ios_milestone: 'browsers.chrome.ios',
    ff_views: 'browsers.ff.view.text',
    ff_views_link: 'browsers.ff.view.url',
    ff_views_notes: 'browsers.ff.view.notes',
    safari_views: 'browsers.safari.view.text',
    safari_views_link: 'browsers.safari.view.url',
    safari_views_notes: 'browsers.safari.view.notes',
    web_dev_views: 'browsers.webdev.view.text',
    web_dev_views_link: 'browsers.webdev.view.url',
    web_dev_views_notes: 'browsers.webdev.view.notes',
    other_views_notes: 'browsers.other.view.notes',
  };

  // Lookup fieldName by following the path starting from feature.
  if (fieldNameMapping[fieldName]) {
    let obj = feature;
    for (const property of fieldNameMapping[fieldName].split('.')) {
      if (obj) {
        obj = obj[property];
      }
    }
  }
  const stageId = formFieldValues.stageId;
  const feStage =
    stageId != null ?
      feature.stages.find((s) => s.id == stageId) :
      feature.stages[0];
  const value = feStage == null ? undefined : getStageValue(feStage, fieldName);
  // if (fieldName === 'rollout_impact' && value) {
  //   return ROLLOUT_IMPACT_DISPLAYNAME[value];
  // } if (fieldName === 'rollout_platforms' && value) {
  //   return value.map(platformId => PLATFORMS_DISPLAYNAME[platformId]);
  // } else if (fieldName in OT_MILESTONE_END_FIELDS) {
  //   // If an origin trial end date is being displayed, handle extension milestones as well.
  //   return this.getMilestoneExtensionValue(feStage, fieldName);
  // }
  return value;

  // if (fieldName === 'enterprise_feature_categories' && value) {
  //   return value.map(categoryId =>
  //     ENTERPRISE_FEATURE_CATEGORIES_DISPLAYNAME[categoryId]);
  // }
  // return value;
}
customElements.define('chromedash-form-field', ChromedashFormField);
