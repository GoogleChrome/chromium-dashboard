/**
 * Copyright 2026 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import {LitElement, css, html, nothing} from 'lit';
import {ref} from 'lit/directives/ref.js';
import './chromedash-form-table.js';
import './chromedash-form-field.js';
import {
  type ChromedashFormField,
  enumLabelToFeatureKey,
  fetchWebFeatureChoices,
  shouldDisplayFeatureLink,
  shouldDisplayWidelySupportedWarning,
} from './chromedash-form-field.js';
import type {WebFeatureInfo} from 'chromestatus-openapi';
import {
  NEW_FEATURE_FORM_FIELDS,
  ENTERPRISE_NEW_FEATURE_FORM_FIELDS,
} from './form-definition.js';
import {FEATURE_TYPES, ENTERPRISE_IMPACT} from './form-field-enums.js';

import {ALL_FIELDS} from './form-field-specs.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {FORM_STYLES} from '../css/forms-css.js';
import {
  setupScrollToHash,
  formatFeatureChanges,
  getDisabledHelpText,
  showToastMessage,
  FieldInfo,
  navigate,
} from './utils.js';
import {customElement, property, state} from 'lit/decorators.js';
import {Feature} from '../js-src/cs-client.js';

@customElement('chromedash-guide-new-page')
export class ChromedashGuideNewPage extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      ...FORM_STYLES,
      // The following style is a workaround to better support radio buttons
      // without sl-radio which does not yet do validation.
      // We do depend on sl-focus-ring being defined.
      css`
        table td label input[type='radio']:focus {
          box-shadow: 0 0 0 var(--sl-focus-ring-width)
            var(--sl-input-focus-ring-color);
        }
        .process-notice {
          margin: var(--content-padding-half) 0;
          padding: var(--content-padding-half);
          background: var(--light-accent-color);
          border-radius: 8px;
        }
        .process-notice p + p {
          margin-top: var(--content-padding-half);
        }
        #web_feature_row sl-select,
        #web_feature_row sl-input {
          margin: 6px 10px;
        }
        input[type='submit'] {
          margin: var(--content-padding) 0;
        }
      `,
    ];
  }

  @property({attribute: false})
  userEmail = '';
  @property({type: Boolean})
  isEnterpriseFeature = false;
  @property({type: Number})
  featureId!: number;
  @property({type: Object})
  feature!: Feature;
  @state()
  fieldValues: FieldInfo[] & {feature?: Feature} = [];
  @property({type: Boolean})
  submitting = false;
  @state()
  webFeatureMode: 'existing' | 'propose' = 'existing';
  @state()
  selectedWebFeature = '';
  @state()
  proposedWebFeature = '';
  @state()
  webFeatureInfos: WebFeatureInfo[] = [];
  @state()
  webFeatureChoices: Record<string, [string, string]> = {};
  @state()
  loadingWebFeatures = false;

  connectedCallback() {
    super.connectedCallback();
    if (!this.isEnterpriseFeature) {
      this.fetchWebFeatures();
    }
  }

  fetchWebFeatures() {
    this.loadingWebFeatures = true;
    fetchWebFeatureChoices()
      .then(({webFeatureInfos, choices}) => {
        this.webFeatureInfos = webFeatureInfos;
        this.webFeatureChoices = choices;
        this.loadingWebFeatures = false;
      })
      .catch(() => {
        showToastMessage(
          'Error fetching Web feature IDs. Please refresh the page or try again later.'
        );
        this.loadingWebFeatures = false;
      });
  }

  /* Add the form's event listener after Shoelace event listeners are attached
   * see more at https://github.com/GoogleChrome/chromium-dashboard/issues/2014 */
  async registerHandlers(el) {
    if (!el) return;

    await el.updateComplete;
    const hiddenTokenField = this.renderRoot.querySelector(
      'input[name=token]'
    ) as HTMLInputElement;
    hiddenTokenField.form?.addEventListener('submit', event => {
      this.handleFormSubmit(event, hiddenTokenField);
    });

    setupScrollToHash(this);
  }

  handleFormSubmit(event, hiddenTokenField?) {
    void hiddenTokenField;
    event.preventDefault();

    const form =
      (event.target as HTMLElement)?.closest('form') ||
      this.shadowRoot?.querySelector('form');
    if (
      form &&
      typeof form.checkValidity === 'function' &&
      !form.checkValidity()
    ) {
      if (typeof form.reportValidity === 'function') {
        form.reportValidity();
      }
      return;
    }

    const formControls = this.shadowRoot?.querySelectorAll<
      HTMLElement & {
        disabled?: boolean;
        checkValidity?: () => boolean;
        reportValidity?: () => boolean;
      }
    >(
      'sl-input, sl-select, sl-textarea, chromedash-textarea, input, select, textarea'
    );
    let hasInvalid = false;
    for (const control of formControls || []) {
      if (control.disabled || control.closest('[style*="display: none"]')) {
        continue;
      }
      if (
        typeof control.checkValidity === 'function' &&
        !control.checkValidity()
      ) {
        if (!hasInvalid) {
          if (typeof control.reportValidity === 'function') {
            control.reportValidity();
          }
          hasInvalid = true;
        }
      }
    }
    if (hasInvalid) {
      return;
    }

    const featureType = this.getFeatureType();
    if (
      !this.isEnterpriseFeature &&
      featureType !== FEATURE_TYPES.FEATURE_TYPE_CODE_CHANGE_ID[0]
    ) {
      const webFeatureVal =
        this.webFeatureMode === 'existing'
          ? this.selectedWebFeature
          : this.proposedWebFeature;
      if (!webFeatureVal) {
        const webFeatureControl = this.shadowRoot?.querySelector<
          HTMLElement & {reportValidity?: () => boolean}
        >('#id_web_feature');
        if (
          webFeatureControl &&
          typeof webFeatureControl.reportValidity === 'function'
        ) {
          webFeatureControl.reportValidity();
        }
        return;
      }
    }

    if (!this.isEnterpriseFeature && this.webFeatureMode === 'propose') {
      const explainerFv = this.fieldValues.find(
        fv => fv.name === 'explainer_links'
      );
      if (!explainerFv?.value) {
        const explainerControl = this.shadowRoot?.querySelector<
          HTMLElement & {reportValidity?: () => boolean}
        >('chromedash-form-field[name="explainer_links"]');
        if (explainerControl) {
          const textarea = explainerControl.querySelector<
            HTMLElement & {reportValidity?: () => boolean}
          >('chromedash-textarea');
          if (textarea && typeof textarea.reportValidity === 'function') {
            textarea.reportValidity();
          }
        }
        return;
      }
    }

    if (featureType == FEATURE_TYPES.FEATURE_TYPE_CODE_CHANGE_ID[0]) {
      this.fieldValues = this.fieldValues.filter(
        fv => fv.name !== 'web_feature'
      );
    }
    if (this.webFeatureMode === 'existing') {
      this.fieldValues = this.fieldValues.filter(
        fv => fv.name !== 'explainer_links'
      );
    }
    const changesBody = formatFeatureChanges(this.fieldValues, this.featureId);
    const createBody = changesBody.feature_changes;
    createBody.feature_type = featureType;
    this.submitting = true;
    window.csClient
      .createFeature(createBody)
      .then(resp => {
        this.navigate(
          this.isEnterpriseFeature
            ? `/guide/editall/${resp.feature_id}#id_rollout_milestone`
            : `/feature/${resp.feature_id}`
        );
      })
      .catch(() => {
        showToastMessage(
          'Some errors occurred. Please refresh the page or try again later.'
        );
      });
  }

  // Local wrapper method is needed to allow sinon to stub this.
  navigate(url) {
    navigate(url);
  }

  getFeatureType(): number {
    if (this.isEnterpriseFeature) {
      return FEATURE_TYPES.FEATURE_TYPE_ENTERPRISE_ID[0];
    }
    for (const fv of this.fieldValues) {
      if (
        fv.name === 'feature_type' &&
        fv.value !== undefined &&
        fv.value !== ''
      ) {
        return Number(fv.value);
      }
    }
    const selectedRadio = this.shadowRoot?.querySelector<HTMLInputElement>(
      'input[name="feature_type"]:checked'
    );
    if (selectedRadio) {
      return Number(selectedRadio.value);
    }
    return FEATURE_TYPES.FEATURE_TYPE_INCUBATE_ID[0];
  }

  shouldDisplayWidelySupportedWarning(): boolean {
    return shouldDisplayWidelySupportedWarning(
      this.webFeatureInfos,
      this.selectedWebFeature,
      this.getFeatureType()
    );
  }

  maybeMakeWebFeatureRequired() {
    const webFeatureRow =
      this.shadowRoot?.querySelector<HTMLElement>('#web_feature_row');
    const webFeatureHeaderRow = this.shadowRoot?.querySelector<HTMLElement>(
      '#web_feature_header_row'
    );
    if (!webFeatureRow) {
      return;
    }
    const featureType = this.getFeatureType();
    if (featureType == FEATURE_TYPES.FEATURE_TYPE_CODE_CHANGE_ID[0]) {
      webFeatureRow.style.display = 'none';
      if (webFeatureHeaderRow) {
        webFeatureHeaderRow.style.display = 'none';
      }
    } else {
      webFeatureRow.style.display = '';
      if (webFeatureHeaderRow) {
        webFeatureHeaderRow.style.display = '';
      }
    }
  }

  maybeMakeEnterpriseFeatureCategoriesRequired() {
    const enterpriseFeatureCategoriesField =
      this.shadowRoot?.querySelector<ChromedashFormField>(
        'chromedash-form-field[name="enterprise_feature_categories"]'
      );
    if (!enterpriseFeatureCategoriesField) {
      return;
    }
    let enterpriseImpact = ENTERPRISE_IMPACT.IMPACT_NONE[0];
    for (const fv of this.fieldValues) {
      if (fv.name === 'enterprise_impact' && fv.value !== undefined) {
        enterpriseImpact = fv.value;
        break;
      }
    }
    enterpriseFeatureCategoriesField.forceRequired =
      enterpriseImpact > ENTERPRISE_IMPACT.IMPACT_NONE[0] ||
      this.isEnterpriseFeature;
  }

  // Handler to update form values when a field update event is fired.
  handleFormFieldUpdate(event) {
    const value = event.detail.value;
    // Index represents which form was updated.
    const index = event.detail.index;
    if (index >= this.fieldValues.length) {
      throw new Error('Out of bounds index when updating field values.');
    }
    // The field has been updated, so it is considered touched.
    this.fieldValues[index].touched = true;
    this.fieldValues[index].value = value;
    this.fieldValues[index].isMarkdown = event.detail.isMarkdown;
    this.maybeMakeWebFeatureRequired();
    this.maybeMakeEnterpriseFeatureCategoriesRequired();
    this.requestUpdate();
  }

  handleWebFeatureModeChange(mode: 'existing' | 'propose') {
    this.webFeatureMode = mode;
    if (mode === 'existing') {
      this.setWebFeatureValue(this.selectedWebFeature);
      this.fieldValues = this.fieldValues.filter(
        fv => fv.name !== 'explainer_links'
      );
    } else {
      this.setWebFeatureValue(this.proposedWebFeature);
    }
  }

  handleSelectWebFeature(e: Event) {
    const target = e.target as HTMLSelectElement;
    const value = target.value || '';
    this.selectedWebFeature = value;
    this.setWebFeatureValue(value);
  }

  handleInputWebFeature(e: Event) {
    const target = e.target as HTMLInputElement;
    const value = target.value || '';
    this.proposedWebFeature = value;
    this.setWebFeatureValue(value);
  }

  setWebFeatureValue(value: string) {
    const fv = this.fieldValues.find(f => f.name === 'web_feature');
    if (fv) {
      fv.value = value;
      fv.touched = true;
    } else {
      this.fieldValues.push({
        name: 'web_feature',
        touched: true,
        value,
      });
    }
  }

  renderFormField(
    field: string,
    className?: string | null,
    forceRequired = false
  ) {
    const fieldProps = ALL_FIELDS[field];
    const featureJSONKey = fieldProps.name || field;
    const newFeatureInitialValues: Record<string, string | number | undefined> =
      {
        owner: this.userEmail,
        shipping_year: new Date().getFullYear(),
        feature_type: FEATURE_TYPES.FEATURE_TYPE_INCUBATE_ID[0],
        feature_type_radio_group: FEATURE_TYPES.FEATURE_TYPE_INCUBATE_ID[0],
      };
    const initialValue = this.isEnterpriseFeature
      ? (fieldProps.enterprise_initial ?? fieldProps.initial)
      : fieldProps.initial;
    let fvIndex = this.fieldValues.findIndex(fv => fv.name === featureJSONKey);
    let value: unknown;
    if (fvIndex === -1) {
      value = newFeatureInitialValues[field] ?? initialValue ?? '';
      fvIndex = this.fieldValues.length;
      this.fieldValues.push({
        name: featureJSONKey,
        touched: true, // Submit everything
        value,
      });
    } else {
      value = this.fieldValues[fvIndex].value;
    }

    return html`
      <chromedash-form-field
        name=${field}
        index=${fvIndex}
        .value=${value}
        disabledReason="${getDisabledHelpText(field)}"
        .fieldValues=${this.fieldValues}
        ?forEnterprise=${this.isEnterpriseFeature}
        ?forceRequired=${forceRequired}
        @form-field-update="${this.handleFormFieldUpdate}"
        class="${className || ''}"
      ></chromedash-form-field>
    `;
  }

  maybeRenderWebFeatureId() {
    if (this.isEnterpriseFeature) {
      return nothing;
    }

    this.setWebFeatureValue(
      this.webFeatureMode === 'existing'
        ? this.selectedWebFeature
        : this.proposedWebFeature
    );

    return html`
      <tr id="web_feature_header_row">
        <th class="form-field-header" colspan="2">
          <div>
            <b>${ALL_FIELDS['web_feature'].label || 'Web Feature ID'}:</b>
          </div>
        </th>
      </tr>
      <tr id="web_feature_row">
        <td>
          <div style="margin: var(--content-padding-half)">
            <label style="margin-right: 1em">
              <input
                type="radio"
                name="web_feature_mode"
                id="web_feature_mode_existing"
                value="existing"
                .checked=${this.webFeatureMode === 'existing'}
                @change=${() => this.handleWebFeatureModeChange('existing')}
              />
              Choose existing web-feature
            </label>
            <label>
              <input
                type="radio"
                name="web_feature_mode"
                id="web_feature_mode_propose"
                value="propose"
                .checked=${this.webFeatureMode === 'propose'}
                @change=${() => this.handleWebFeatureModeChange('propose')}
              />
              Propose web-feature
            </label>
          </div>

          ${
            this.webFeatureMode === 'existing'
              ? html`
                  <sl-select
                    name="web_feature"
                    id="id_web_feature"
                    size="small"
                    hoist
                    required
                    .value=${this.selectedWebFeature}
                    ?disabled=${this.loadingWebFeatures}
                    @sl-change=${this.handleSelectWebFeature}
                  >
                    ${Object.values(this.webFeatureChoices).map(
                      ([value, label]) => html`
                        <sl-option value="${value}"> ${label} </sl-option>
                      `
                    )}
                  </sl-select>
                  ${
                    shouldDisplayFeatureLink(
                      'web_feature',
                      this.selectedWebFeature
                    )
                      ? html`
                          <p style="margin: var(--content-padding-half)">
                            See web feature
                            <a
                              href="https://webstatus.dev/features/${enumLabelToFeatureKey(
                                this.selectedWebFeature
                              )}"
                              target="_blank"
                            >
                              ${this.selectedWebFeature}
                            </a>
                            in webstatus.dev
                          </p>
                        `
                      : nothing
                  }
                  ${
                    this.shouldDisplayWidelySupportedWarning()
                      ? html`
                          <p style="margin: var(--content-padding-half)">
                            This web feature is already widely supported, are
                            you sure that you are incubating a change to it?
                          </p>
                        `
                      : nothing
                  }
                `
              : html`
                  <sl-input
                    name="web_feature"
                    id="id_web_feature"
                    size="small"
                    autocomplete="off"
                    required
                    .value=${this.proposedWebFeature}
                    @sl-change=${this.handleInputWebFeature}
                    @sl-input=${this.handleInputWebFeature}
                  >
                  </sl-input>
                `
          }
        </td>
        <td>
          <span class="helptext"> ${ALL_FIELDS['web_feature'].help_text} </span>
        </td>
      </tr>
      ${
        this.webFeatureMode === 'propose'
          ? this.renderFormField('explainer_links', null, true)
          : nothing
      }
    `;
  }

  renderSubHeader() {
    return html`
      <div id="subheader" style="display:block">
        <span style="float:right; margin-right: 2em">
          <a
            href="https://github.com/GoogleChrome/chromium-dashboard/issues/new?labels=Feedback&amp;template=process-and-guide-ux-feedback.md"
            target="_blank"
            rel="noopener"
            >Process and UI feedback</a
          ></span
        >
        <h2 data-testid="add-a-feature">Add a feature</h2>
      </div>
    `;
  }

  renderWarnings() {
    if (this.isEnterpriseFeature) {
      return html`
        <div class="process-notice">
          <p>
            Use this form if your feature should be mentioned in the Enterprise
            Release Notes.
          </p>
        </div>
      `;
    } else {
      return html`
        <div class="process-notice">
          <p>
            Please see the
            <a
              href="https://www.chromium.org/blink/launching-features"
              target="_blank"
              rel="noopener"
              >Launching features</a
            >
            page for process instructions.
          </p>

          <p>
            Googlers: Please follow the instructions at
            <a
              href="https://goto.corp.google.com/wp-launch-guidelines"
              target="_blank"
              rel="noopener"
              >go/wp-launch-guidelines</a
            >
            (internal document) to determine whether you also require an
            internal review.
          </p>
        </div>
      `;
    }
  }

  renderForm() {
    this.fieldValues.feature = this.feature;

    const formFields = this.isEnterpriseFeature
      ? ENTERPRISE_NEW_FEATURE_FORM_FIELDS
      : NEW_FEATURE_FORM_FIELDS;

    const submitLabel = this.submitting
      ? 'Submitting...'
      : this.isEnterpriseFeature
        ? 'Continue'
        : 'Submit';
    return html`
      <section id="stage_form">
        <form>
          <input type="hidden" name="token" />
          <chromedash-form-table ${ref(this.registerHandlers)}>
            ${this.renderWarnings()}
            ${
              !this.isEnterpriseFeature
                ? this.renderFormField('feature_type_radio_group', 'choices')
                : nothing
            }
            ${formFields.map(field =>
              this.renderFormField(
                field,
                field === 'enterprise_product_category' ? 'choices' : null
              )
            )}
            ${this.maybeRenderWebFeatureId()}
          </chromedash-form-table>
          <input
            type="submit"
            class="primary"
            value=${submitLabel}
            style="margin: var(--content-padding) 0;"
            ?disabled=${this.submitting}
          />
        </form>
      </section>
    `;
  }

  render() {
    return html` ${this.renderSubHeader()} ${this.renderForm()} `;
  }
}
