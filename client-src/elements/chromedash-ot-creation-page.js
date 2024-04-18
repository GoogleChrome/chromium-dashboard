import {LitElement, css, html, nothing} from 'lit';
import {ref} from 'lit/directives/ref.js';
import {
  formatFeatureChanges,
  getStageValue,
  showToastMessage,
  setupScrollToHash,
} from './utils.js';
import './chromedash-form-table.js';
import './chromedash-form-field.js';
import {ORIGIN_TRIAL_CREATION_FIELDS} from './form-definition.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {FORM_STYLES} from '../css/forms-css.js';
import {ALL_FIELDS} from './form-field-specs.js';
import json5 from 'json5';

const WEBFEATURE_FILE_URL =
  'https://chromium.googlesource.com/chromium/src/+/main/third_party/blink/public/mojom/use_counter/metrics/web_feature.mojom?format=TEXT';
const ENABLED_FEATURES_FILE_URL =
  'https://chromium.googlesource.com/chromium/src/+/main/third_party/blink/renderer/platform/runtime_enabled_features.json5?format=TEXT';
const GRACE_PERIOD_FILE =
  'https://chromium.googlesource.com/chromium/src/+/main/third_party/blink/common/origin_trials/manual_completion_origin_trial_features.cc?format=TEXT';

export class ChromedashOTCreationPage extends LitElement {
  static get styles() {
    return [...SHARED_STYLES, ...FORM_STYLES, css``];
  }

  static get properties() {
    return {
      stageId: {type: Number},
      featureId: {type: Number},
      userEmail: {type: String},
      feature: {type: Object},
      loading: {type: Boolean},
      appTitle: {type: String},
      fieldValues: {type: Array},
      showApprovalsFields: {type: Boolean},

      // Chromium file contents for validating inputs.
      webfeatureFile: {type: String},
      enabledFeaturesJson: {type: Object},
      gracePeriodFile: {type: String},
    };
  }

  constructor() {
    super();
    this.stageId = 0;
    this.featureId = 0;
    this.feature = {};
    this.loading = true;
    this.appTitle = '';
    this.fieldValues = [];
    this.showApprovalsFields = false;
    this.webfeatureFile = '';
    this.enabledFeaturesJson = undefined;
    this.gracePeriodFile = '';
  }

  connectedCallback() {
    super.connectedCallback();
    this.fetchData();
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

    // Toggle the display of the registration approval fields when the box is checked.
    if (this.fieldValues[index].name === 'ot_require_approvals') {
      this.showApprovalsFields = !this.showApprovalsFields;
      this.requestUpdate();
    }
  }

  fetchData() {
    this.loading = true;
    Promise.all([
      window.csClient.getFeature(this.featureId),
      window.csClient.getStage(this.featureId, this.stageId),
    ]).then(([feature, stage]) => {
      this.feature = feature;
      this.stage = stage;

      if (this.feature.name) {
        document.title = `${this.feature.name} - ${this.appTitle}`;
      }
      this.setFieldValues();
      this.loading = false;
    });
  }

  // Add the togglable registration approvals fields to the fieldValues array.
  addOptionalApprovalsFields() {
    // Approval requirement fields are always hidden unless the feature owner
    // opts in to using them.
    const insertIndex =
      this.fieldValues.findIndex(
        fieldInfo => fieldInfo.name === 'ot_require_approvals'
      ) + 1;
    this.fieldValues.splice(
      insertIndex,
      0,
      {
        name: 'ot_approval_buganizer_component',
        touched: false,
        value: '',
        stageId: this.stage.id,
        isApprovalsField: true,
      },
      {
        name: 'ot_approval_group_email',
        touched: false,
        value: '',
        stageId: this.stage.id,
        isApprovalsField: true,
      },
      {
        name: 'ot_approval_criteria_url',
        touched: false,
        value: '',
        stageId: this.stage.id,
        isApprovalsField: true,
      }
    );
  }

  addHiddenFields() {
    // Add a field for updating that an OT creation request has been submitted.
    this.fieldValues.push({
      name: 'ot_action_requested',
      touched: true,
      value: true,
      stageId: this.stage.id,
      alwaysHidden: true,
    });
  }

  // Create the array that tracks the value of fields.
  setFieldValues() {
    // OT creation page only has one section.
    const section = ORIGIN_TRIAL_CREATION_FIELDS.sections[0];

    this.fieldValues = section.fields.map(field => {
      const featureJSONKey = ALL_FIELDS[field].name || field;
      let value = getStageValue(this.stage, featureJSONKey);
      let touched = false;

      // The requester's email should be a contact by default.
      if (featureJSONKey === 'ot_owner_email' && !value) {
        value = [this.userEmail];
        touched = true;
        // Display registration approvals fields by default if the value is checked already.
      } else if (featureJSONKey === 'ot_require_approvals') {
        this.showApprovalsFields = !!value;
      }

      // Add the field to this component's stage before creating the field component.
      return {
        name: featureJSONKey,
        touched,
        value,
        stageId: this.stage.id,
      };
    });
    this.addOptionalApprovalsFields();
    this.addHiddenFields();
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    document.title = this.appTitle;
  }

  async registerHandlers(el) {
    if (!el) return;

    /* Add the form's event listener after Shoelace event listeners are attached
     * see more at https://github.com/GoogleChrome/chromium-dashboard/issues/2014 */
    await el.updateComplete;
    const submitButton = this.shadowRoot.querySelector(
      'input[id=submit-button]'
    );
    submitButton.form.addEventListener('submit', event => {
      this.handleFormSubmit(event);
    });

    setupScrollToHash(this);
  }

  async getChromiumFile(url) {
    const resp = await fetch(url);
    const respJson = await resp.text();
    return atob(respJson);
  }

  // Check that the code has landed that is used to monitor feature usage.
  async checkWebfeatureUseCounter(field) {
    if (!this.webfeatureFile) {
      this.webfeatureFile = await this.getChromiumFile(WEBFEATURE_FILE_URL);
    }
    const webfeatureCounterExists = this.webfeatureFile.includes(
      `${field.value} =`
    );
    if (!webfeatureCounterExists) {
      field.checkMessage = html` <span class="check-error">
        <b>Error</b>: UseCounter name not found in file.
      </span>`;
      return true;
    } else {
      field.checkMessage = nothing;
    }
    return false;
  }

  // Check that code has landed that is required for the origin trial feature.
  async checkChromiumTrialName(field) {
    if (!this.enabledFeaturesJson) {
      const enabledFeaturesFileText = await this.getChromiumFile(
        ENABLED_FEATURES_FILE_URL
      );
      this.enabledFeaturesJson = json5.parse(enabledFeaturesFileText);
    }
    const existingTrials = await window.csClient.getOriginTrials();

    if (
      !this.enabledFeaturesJson.data.some(
        feature => feature.origin_trial_feature_name === field.value
      )
    ) {
      field.checkMessage = html` <span class="check-error">
        <b>Error</b>: Name not found in file.
      </span>`;
      return true;
    } else if (
      existingTrials.some(
        trial => trial.origin_trial_feature_name === field.value
      )
    ) {
      field.checkMessage = html` <span class="check-error">
        <b>Error</b>: This name is used by an existing origin trial.
      </span>`;
      return true;
    } else {
      field.checkMessage = nothing;
    }
    return false;
  }

  // Check that code has landed that is required for third party support.
  async checkThirdPartySupport(field) {
    if (!field.value) {
      field.checkMessage = nothing;
      return false;
    }
    const chromiumTrialName = this.fieldValues.find(
      field => field.name === 'ot_chromium_trial_name'
    ).value;
    if (!this.enabledFeaturesJson) {
      const enabledFeaturesFileText = await this.getChromiumFile(
        ENABLED_FEATURES_FILE_URL
      );
      this.enabledFeaturesJson = json5.parse(enabledFeaturesFileText);
    }

    const thirdPartySupportEnabled = this.enabledFeaturesJson.data.every(
      feature => {
        return (
          feature.origin_trial_feature_name !== chromiumTrialName ||
          feature.origin_trial_allows_third_party
        );
      }
    );
    if (!thirdPartySupportEnabled) {
      field.checkMessage = html` <br />
        <span class="check-error">
          <b>Error</b>: Property not set in file.
        </span>`;
      return true;
    } else {
      field.checkMessage = nothing;
    }
    return false;
  }

  // Check that code has landed that is required for critical trials.
  async checkCriticalTrial(field) {
    if (!field.value) {
      field.checkMessage = nothing;
      return false;
    }
    const chromiumTrialName = this.fieldValues.find(
      field => field.name === 'ot_chromium_trial_name'
    ).value;
    if (!this.gracePeriodFile) {
      this.gracePeriodFile = await this.getChromiumFile(GRACE_PERIOD_FILE);
    }
    const includedInGracePeriodArray = this.gracePeriodFile.includes(
      `blink::mojom::OriginTrialFeature::k${chromiumTrialName}`
    );
    if (!includedInGracePeriodArray) {
      field.checkMessage = html` <br />
        <span class="check-error">
          <b>Error</b>: Trial name not found in file.
        </span>`;
      return true;
    } else {
      field.checkMessage = nothing;
    }
    return false;
  }

  /**
   * Check that given args related to Chromium are valid.
   * @returns Whether any inputs cannot be found in Chromium files.
   */
  async handleChromiumChecks() {
    // Clear saved file info in order to fetch the most recent version.
    this.webfeatureFile = '';
    this.enabledFeaturesJson = undefined;
    this.gracePeriodFile = '';
    let hasErrors = false;

    for (const field of this.fieldValues) {
      if (field.name === 'ot_webfeature_use_counter') {
        hasErrors = hasErrors || (await this.checkWebfeatureUseCounter(field));
      } else if (field.name === 'ot_chromium_trial_name') {
        hasErrors = hasErrors || (await this.checkChromiumTrialName(field));
      } else if (field.name === 'ot_has_third_party_support') {
        hasErrors = hasErrors || (await this.checkThirdPartySupport(field));
      } else if (field.name === 'ot_is_critical_trial') {
        hasErrors = hasErrors || (await this.checkCriticalTrial(field));
      }
    }
    return hasErrors;
  }

  async handleFormSubmit(e) {
    e.preventDefault();
    // If registration approvals is not enabled, ignore all fields related to that setting.
    if (!this.showApprovalsFields) {
      this.fieldValues.forEach(fieldInfo => {
        if (fieldInfo.isApprovalsField) {
          fieldInfo.touched = false;
        }
      });
    }

    const hasErrors = await this.handleChromiumChecks();
    this.requestUpdate();
    if (hasErrors) {
      showToastMessage(
        'Some issues were found with the given inputs. Check input errors and try again.'
      );
      return;
    }

    const featureSubmitBody = formatFeatureChanges(
      this.fieldValues,
      this.featureId
    );
    // We only need the single stage changes.
    const stageSubmitBody = featureSubmitBody.stages[0];

    window.csClient
      .updateStage(this.featureId, this.stageId, stageSubmitBody)
      .then(() => {
        showToastMessage('Creation request submitted!');
        setTimeout(() => {
          window.location.href = `/feature/${this.featureId}`;
        }, 1000);
      });
  }

  handleCancelClick() {
    window.location.href = `/feature/${this.featureId}`;
  }

  renderSkeletons() {
    return html`
      <h3><sl-skeleton effect="sheen"></sl-skeleton></h3>
      <section id="metadata">
        <h3><sl-skeleton effect="sheen"></sl-skeleton></h3>
        <p>
          <sl-skeleton effect="sheen"></sl-skeleton>
          <sl-skeleton effect="sheen"></sl-skeleton>
          <sl-skeleton effect="sheen"></sl-skeleton>
          <sl-skeleton effect="sheen"></sl-skeleton>
          <sl-skeleton effect="sheen"></sl-skeleton>
          <sl-skeleton effect="sheen"></sl-skeleton>
          <sl-skeleton effect="sheen"></sl-skeleton>
          <sl-skeleton effect="sheen"></sl-skeleton>
        </p>
      </section>
    `;
  }

  getNextPage() {
    return `/feature/${this.featureId}`;
  }

  renderSubheader() {
    return html`
      <div id="subheader">
        <h2 id="breadcrumbs">
          <a href=${this.getNextPage()}>
            <iron-icon icon="chromestatus:arrow-back"></iron-icon>
            Request origin trial creation: ${this.feature.name}
          </a>
        </h2>
      </div>
    `;
  }

  renderFields() {
    const fields = this.fieldValues.map((fieldInfo, i) => {
      if (
        fieldInfo.alwaysHidden ||
        (fieldInfo.isApprovalsField && !this.showApprovalsFields)
      ) {
        return nothing;
      }
      // Fade in transition for the approvals fields if they're being displayed.
      const shouldFadeIn = fieldInfo.isApprovalsField;

      return html`
        <chromedash-form-field
          name=${fieldInfo.name}
          index=${i}
          value=${fieldInfo.value}
          .checkMessage=${fieldInfo.checkMessage}
          .fieldValues=${this.fieldValues}
          .shouldFadeIn=${shouldFadeIn}
          @form-field-update="${this.handleFormFieldUpdate}"
        >
        </chromedash-form-field>
      `;
    });
    return fields;
  }

  renderForm() {
    this.fieldValues.feature = this.feature;

    // OT creation page only has one section.
    const section = ORIGIN_TRIAL_CREATION_FIELDS.sections[0];
    return html`
      <form name="feature_form">
        <chromedash-form-table ${ref(this.registerHandlers)}>
          <section class="stage_form">${this.renderFields(section)}</section>
        </chromedash-form-table>
        <div class="final_buttons">
          <input
            id="submit-button"
            class="button"
            type="submit"
            value="Submit"
          />
          <button
            id="cancel-button"
            type="reset"
            @click=${this.handleCancelClick}
          >
            Cancel
          </button>
        </div>
      </form>
    `;
  }

  render() {
    return html`
      ${this.renderSubheader()}
      ${this.loading ? this.renderSkeletons() : this.renderForm()}
    `;
  }
}

customElements.define('chromedash-ot-creation-page', ChromedashOTCreationPage);
