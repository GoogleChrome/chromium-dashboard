import {SlDetails, SlIconButton, SlInput} from '@shoelace-style/shoelace';
import {LitElement, TemplateResult, css, html, nothing} from 'lit';
import {customElement, property, state} from 'lit/decorators.js';
import {ref} from 'lit/directives/ref.js';
import {repeat} from 'lit/directives/repeat.js';

import {ChromedashApp} from './chromedash-app';
import './chromedash-attachments';
import './chromedash-textarea';
import {
  ALL_FIELDS,
  FieldUsage,
  resolveFieldForFeature,
} from './form-field-specs';
import {
  FieldInfo,
  getFieldValueFromFeature,
  showToastMessage,
} from './utils.js';
import {Feature, StageDict} from '../js-src/cs-client';
import {FormattedFeature} from './form-definition';
import {ALL_INTENT_USAGE_BY_FEATURE_TYPE, UsageType} from './form-field-enums';
import {WEB_FEATURES_MANIFEST} from './WEB_FEATURES_MANIFEST';

interface getFieldValue {
  (fieldName: string, stageOrId: any): any;
  feature?: Feature;
}

interface UsageTypeDetail {
  abbreviation: string;
  className: string;
  title: string;
}

// Helper map to store details for each intent type.
const USAGE_TYPE_DETAILS: Record<UsageType, UsageTypeDetail> = {
  [UsageType.Prototype]: {
    abbreviation: 'I2P',
    className: 'usage-tag--prototype',
    title: 'Intent to Prototype',
  },
  [UsageType.DeveloperTesting]: {
    abbreviation: 'R4DT',
    className: 'usage-tag--dev-testing',
    title: 'Ready for Developer Testing',
  },
  [UsageType.Experiment]: {
    abbreviation: 'I2E',
    className: 'usage-tag--experiment',
    title: 'Intent to Experiment',
  },
  [UsageType.Ship]: {
    abbreviation: 'I2S',
    className: 'usage-tag--ship',
    title: 'Intent to Ship',
  },
  [UsageType.PSA]: {
    abbreviation: 'PSA',
    className: 'usage-tag--psa',
    title: 'Web-Facing Change PSA',
  },
  [UsageType.DeprecateAndRemove]: {
    abbreviation: 'I2D',
    className: 'usage-tag--deprecate',
    title: 'Intent to Deprecate and Remove',
  },
  [UsageType.ReleaseNotes]: {
    abbreviation: 'RN',
    className: 'usage-tag--rn',
    title: 'Release Notes',
  },
  [UsageType.CrossFunctionReview]: {
    abbreviation: 'XFN',
    className: 'usage-tag-xfn',
    title: 'Cross-Functional Review',
  },
};

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
  @property({type: Boolean})
  forceRequired = false;
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
  fetchedChoices: Record<string, [string, string]> = {}; // just for the blink component & web features select field
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
      this.fetchChoices(
        window.csClient.getBlinkComponents(),
        'Error fetching Blink Components. Please refresh the page or try again later.'
      );
    } else if (this.name === 'wpt_tests') {
      console.log(WEB_FEATURES_MANIFEST.data);
      console.log(this.feature.web_feature);
      console.log(WEB_FEATURES_MANIFEST.data[this.feature.web_feature]);
      const possible = WEB_FEATURES_MANIFEST.data[this.feature.web_feature] || [];
      const choices = {};
      for (let p of possible) {
        choices[p] = [p, p];
      }
      this.fetchedChoices = choices;
    } else if (this.name === 'web_feature') {
      this.fetchChoices(
        window.csClient.getWebFeatureIDs().then((feature_ids: string[]) => {
          let choices = {
            missing_feature: ['Missing feature', 'Missing feature'],
          };
          for (let id of feature_ids) {
            choices[id] = [id, id];
          }
          return choices;
        }),
        'Error fetching Web feature IDs. Please refresh the page or try again later.'
      );
    }
  }

  fetchChoices(fetchPromise, errorMessage) {
    this.loading = true;
    fetchPromise
      .then(choices => {
        this.fetchedChoices = choices;
        this.loading = false;
      })
      .catch(() => {
        showToastMessage(errorMessage);
      });
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

  shouldDisplayFeatureLink(field_name: string, feature_value: string) {
    if (field_name !== 'web_feature') {
      return false;
    }
    if (!feature_value) {
      return false;
    }
    if (feature_value === 'Missing feature' || feature_value == 'TBD') {
      return false;
    }

    return true;
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
    let isMarkdown: undefined | boolean = undefined;
    if (e.target.offerMarkdown) {
      isMarkdown = e.target.isMarkdown;
    }
    const eventOptions = {
      detail: {
        value: fieldValue,
        index: this.index,
        isMarkdown,
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

  addMultidatalistItem(valueToAdd: string) {
    console.log('add');
    const fieldValue = this.getValue();
    const valueArray: string[] = fieldValue.split(',').filter(v => v.length > 0);
    if (!valueArray.includes(valueToAdd)) {
      valueArray.push(valueToAdd);
      valueArray.sort();
      this.value = valueArray.join(',');
    }
  }

  multidatalistChanged() {
    console.log('changed');
    const input = this.renderRoot.querySelector<HTMLInputElement>('#id_' + this.name);
    if (!input) {console.log('renderRoot'); return;}
    const valueToAdd = (input.value || '').trim();
    console.log(valueToAdd);
    if (valueToAdd == '') {console.log('empty'); return;}
    if (Object.keys(this.fetchedChoices).includes(valueToAdd)) {
      this.addMultidatalistItem(valueToAdd);
      input.value = '';
    }
  }

  removeMultidatalistItem(valueToRemove: string) {
    console.log('remove ' + valueToRemove);
    const fieldValue = this.getValue();
    const valueArray: string[] = fieldValue.split(',');
    const index = valueArray.indexOf(valueToRemove);
    if (index > -1) { // Only splice if the value is found
      valueArray.splice(index, 1);
    }
    this.value = valueArray.join(',');
    console.log(this.value);
  }

  renderWidget() {
    const type = this.fieldProps.type;
    const fieldDisabled = this.fieldProps.disabled;
    const fieldValue = this.getValue();
    const isRequired = this.fieldProps.required || this.forceRequired;
    const offerMarkdown = Boolean(
      this.forEnterprise
        ? this.fieldProps.enterprise_offer_markdown
        : this.fieldProps.offer_markdown
    );

    // form field name can be specified in form-field-spec to match DB field name
    const fieldName = this.fieldProps.name || this.name;
    const isMarkdown = (this.feature?.markdown_fields || []).includes(
      fieldName
    );

    // choices can be specified in form-field-spec or fetched from API
    const choices: [number, string][] | [number, string, string][] =
      this.fieldProps.choices || this.fetchedChoices;

    let fieldHTML = html``;
    if (type === 'checkbox') {
      const label = this.checkboxLabel || this.fieldProps.label;
      fieldHTML = html`
        <sl-checkbox
          name="${fieldName}"
          id="id_${this.name}"
          size="small"
          ?checked=${fieldValue === true ||
          fieldValue === 'true' ||
          fieldValue === 'True'}
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
      const availableOptions = Object.values(choices).filter(
        ([value, label, obsolete]) =>
          !obsolete || valueArray.includes('' + value)
      );
      fieldHTML = html`
        <sl-select
          name="${fieldName}"
          id="id_${this.name}"
          .value=${valueArray}
          size="small"
          hoist
          multiple
          cleareable
          ?required=${isRequired}
          ?disabled=${fieldDisabled || this.disabled || this.loading}
          @sl-change="${this.handleFieldUpdated}"
        >
          ${availableOptions.map(
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
          ?required=${isRequired}
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
          resize="auto"
          value=${fieldValue}
          index=${this.index}
          ?required=${isRequired}
          ?offerMarkdown=${offerMarkdown}
          ?isMarkdown=${isMarkdown}
          @sl-change="${this.handleFieldUpdated}"
        >
        </chromedash-textarea>
      `;
    } else if (type === 'attachments') {
      fieldHTML = html`
        <chromedash-attachments
          ${ref(this.updateAttributes)}
          name="${fieldName}"
          featureId=${this.feature.id}
          id="id_${this.name}"
          size="small"
          value=${fieldValue}
          ?required=${isRequired}
          @sl-change="${this.handleFieldUpdated}"
        >
        </chromedash-attachments>
      `;
    } else if (type === 'radios') {
      fieldHTML = html`
        ${Object.values(choices).map(
          ([value, label, description]) => html`
            <input
              id="id_${this.name}_${value}"
              name="${fieldName}"
              value="${value}"
              .checked="${value === Number(fieldValue)}"
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
        <div class="datalist-input-wrapper" data-testid="${this.name}_wrapper">
          <input
            ${ref(this.updateAttributes)}
            name="${fieldName}"
            id="id_${this.name}"
            value="${fieldValue}"
            class="datalist-input"
            type="search"
            list="${this.name}_list"
            ?required=${isRequired}
            @change=${this.handleFieldUpdated}
          />
        </div>
        <datalist id="${this.name}_list">
          ${Object.values(choices).map(
            ([value]) => html` <option value="${value}"></option> `
          )}
        </datalist>
      `;
    } else if (type === 'multidatalist') {
      const valueArray: string[] = fieldValue.length ? fieldValue.split(',') : [];
      fieldHTML = html`
      <div class="hbox" style="nowrap" data-testid="${this.name}_wrapper">
          <input
            ${ref(this.updateAttributes)}
            name="${fieldName}"
            placeholder="Type here and select to add a test path"
            id="id_${this.name}"
            value=""
            class="datalist-input"
            style="flex-grow:1;"
            type="search"
            list="${this.name}_list"
            ?required=${isRequired}
            @keyup=${e => this.multidatalistChanged()}
            @click=${e => this.multidatalistChanged()}
            />
        </div>
        <datalist id="${this.name}_list">
          ${Object.values(choices)
          .filter(([value]) => !valueArray.includes(value))
          .map(
            ([value]) => html` <option value="${value}"></option> `
          )}
          </datalist>
          <div>
          ${valueArray.length ?
            repeat(
              valueArray, (v) => v, (v) =>
                html`<div style="margin-bottom: 4px;"><sl-checkbox checked @sl-change=${e => this.removeMultidatalistItem(v)}>${v}</sl-checkbox></div>`) :
            ''}
          </div>
      `;
    } else {
      console.error(`unknown form field type: ${type}`);
    }
    return fieldHTML;
  }

  /**
   * Generates an array of Lit TemplateResults for intent tags.
   * @param fieldUsageInfo An object containing the intent usage for a field.
   * @param featureType The type of the current feature.
   * @return An array of TemplateResults, each rendering a <span> tag.
   */
  renderUsageIcons(
    fieldUsageInfo: FieldUsage,
    featureType: number | undefined
  ): TemplateResult[] {
    if (featureType === undefined) {
      return [];
    }
    const intentTypesUsed = fieldUsageInfo[featureType];
    if (!intentTypesUsed) {
      return [];
    }

    // If the field is used in ALL intents, render a special "All" tag.
    if (
      ALL_INTENT_USAGE_BY_FEATURE_TYPE[featureType]?.isSubsetOf(intentTypesUsed)
    ) {
      return [
        html`<span
          class="usage-tag usage-tag--all"
          title="This field is used to populate all intent templates when provided"
        >
          All
        </span>`,
      ];
    }

    const intentIcons: TemplateResult[] = [];
    for (const intentType of intentTypesUsed) {
      const details = USAGE_TYPE_DETAILS[intentType];
      if (details) {
        const tooltipText = `This field is used to populate the ${details.title} template`;
        intentIcons.push(html`
          <span class="usage-tag ${details.className}" title="${tooltipText}"
            >${details.abbreviation}</span
          >
        `);
      }
    }

    return intentIcons;
  }

  render() {
    if (this.fieldProps.deprecated && !this.value) {
      return nothing;
    }
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
              <th class="form-field-header">
                <div>
                  <b>${this.fieldProps.label}:</b>
                </div>
                <div>
                  ${this.renderUsageIcons(
                    this.fieldProps.usage,
                    this.feature?.feature_type_int
                  )}
                </div>
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
      ${this.shouldDisplayFeatureLink(this.name, this.value)
        ? html`
            <tr>
              <td colspan="2" class="webdx">
                See web feature
                <a
                  href="https://webstatus.dev/features/${enumLabelToFeatureKey(
                    this.value
                  )}"
                  target="_blank"
                >
                  ${this.value}
                </a>
                in webstatus.dev
              </td>
            </tr>
          `
        : nothing}
    `;
  }
}

/**
 * enumLabelToFeatureKey converts Webdx enum labels to
 * web feature IDs. This function is rewritten from
 * https://github.com/GoogleChrome/webstatus.dev/blob/6ae7ecf7c26e2563a6e1685cc6d92fc12bcc7941/lib/gcpspanner/spanneradapters/chromium_historgram_enum_consumer.go#L102-L125
 */
export function enumLabelToFeatureKey(label: string) {
  let result = '';
  for (let i = 0; i < label.length; i++) {
    const char = label[i];
    if (i === 0) {
      result += char.toLowerCase();
      continue;
    }
    if (char === char.toUpperCase() && /[a-zA-Z]/.test(char)) {
      result += '-' + char.toLowerCase();
      continue;
    }
    if (i > 0 && /[a-zA-Z]/.test(label[i - 1]) && char >= '0' && char <= '9') {
      result += '-';
    }
    result += char;
  }
  return result;
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
