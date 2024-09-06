import {LitElement, TemplateResult, css, html, nothing} from 'lit';
import {customElement, property, state} from 'lit/decorators.js';
import {ref} from 'lit/directives/ref.js';
import {FORM_STYLES} from '../css/forms-css.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {Feature, StageDict} from '../js-src/cs-client.js';
import './chromedash-form-field.js';
import {ORIGIN_TRIAL_CREATION_FIELDS} from './form-definition.js';
import {
  OT_SETUP_STATUS_OPTIONS,
  VOTE_OPTIONS,
  USE_COUNTER_TYPE_WEBFEATURE,
} from './form-field-enums.js';
import {ALL_FIELDS} from './form-field-specs.js';
import {
  FieldInfo,
  formatFeatureChanges,
  getDisabledHelpText,
  getStageValue,
  setupScrollToHash,
  showToastMessage,
} from './utils.js';

@customElement('chromedash-ot-creation-page')
export class ChromedashOTCreationPage extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      ...FORM_STYLES,
      css`
        .choices label {
          font-weight: bold;
        }
        .choices div {
          margin-top: 1em;
        }
        .choices p {
          margin: 0.5em 1.5em 1em;
        }

        #overlay {
          position: fixed;
          width: 100%;
          height: 100%;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background-color: rgba(0, 0, 0, 0.3);
          z-index: 2;
          cursor: pointer;
        }
        .submission-spinner {
          position: fixed;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          height: 300px;
        }

        .warning {
          border: 2px solid #555555;
          border-radius: 10px;
          padding: 4px;
          margin-bottom: 32px;
        }
        .warning h3 {
          text-align: center;
          color: #555555;
          font-weight: 300;
        }
      `,
    ];
  }

  @property({type: Number})
  stageId = 0;
  @property({type: Number})
  featureId = 0;
  @property({attribute: false})
  feature!: Feature;
  @property({type: String})
  appTitle = '';
  @property({type: String})
  userEmail = '';
  @state()
  loading = true;
  @state()
  submitting = false;
  @state()
  fieldValues: FieldInfo[] & {feature?: Feature} = [];
  @state()
  showApprovalsFields = false;
  @state()
  isDeprecationTrial = false;
  @state()
  webfeatureUseCounterType: Number = USE_COUNTER_TYPE_WEBFEATURE;
  @state()
  stage!: StageDict;

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
    } else if (this.fieldValues[index].name === 'ot_is_deprecation_trial') {
      this.isDeprecationTrial = value;
      this.requestUpdate();
    }
  }

  handleUseCounterTypeUpdate(event) {
    this.webfeatureUseCounterType = parseInt(event.detail.value);
  }

  fetchData() {
    this.loading = true;
    Promise.all([
      window.csClient.getFeature(this.featureId),
      window.csClient.getStage(this.featureId, this.stageId),
      window.csClient.getGates(this.featureId),
    ]).then(([feature, stage, gatesRes]) => {
      this.feature = feature;
      this.stage = stage;

      // Redirect if stage creation form has already been submitted.
      if (
        this.stage.ot_setup_status &&
        this.stage.ot_setup_status !== OT_SETUP_STATUS_OPTIONS.OT_NOT_CREATED
      ) {
        window.location.href = `/feature/${this.featureId}`;
      }
      // Check that necessary approvals have been obtained.
      const relevantGates = gatesRes.gates.filter(
        g => g.stage_id === this.stage.id
      );
      relevantGates.forEach(g => {
        if (
          g.state !== VOTE_OPTIONS.APPROVED[0] &&
          g.state !== VOTE_OPTIONS.NA[0]
        ) {
          // Redirect if approvals have not been obtained.
          window.location.href = `/feature/${this.featureId}`;
        }
      });
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
        touched: true,
        value: '',
        stageId: this.stage.id,
        isApprovalsField: true,
      },
      {
        name: 'ot_approval_buganizer_custom_field_id',
        touched: true,
        value: '',
        stageId: this.stage.id,
        isApprovalsField: true,
      },
      {
        name: 'ot_approval_group_email',
        touched: true,
        value: '',
        stageId: this.stage.id,
        isApprovalsField: true,
      },
      {
        name: 'ot_approval_criteria_url',
        touched: true,
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

      // The requester's email should be a contact by default.
      if (featureJSONKey === 'ot_owner_email' && !value) {
        value = [this.userEmail];
        // Display registration approvals fields by default if the value is checked already.
      } else if (featureJSONKey === 'ot_require_approvals') {
        this.showApprovalsFields = !!value;
      }

      // Add the field to this component's stage before creating the field component.
      return {
        name: featureJSONKey,
        touched: true,
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
    const submitButton: HTMLInputElement | null = this.renderRoot.querySelector(
      'input[id=submit-button]'
    );
    submitButton?.form?.addEventListener('submit', event => {
      this.handleFormSubmit(event);
    });

    setupScrollToHash(this);
  }

  // Check that the code has landed that is used to monitor feature usage.
  checkWebfeatureUseCounter(field, errors) {
    if (errors.ot_webfeature_use_counter) {
      field.checkMessage = html` <span class="check-error">
        <b>Error</b>: ${errors.ot_webfeature_use_counter}
      </span>`;
    } else {
      field.checkMessage = nothing;
    }
  }

  // Check that code has landed that is required for the origin trial feature.
  checkChromiumTrialName(field, errors) {
    if (errors.ot_chromium_trial_name) {
      field.checkMessage = html` <span class="check-error">
        <b>Error</b>: ${errors.ot_chromium_trial_name}
      </span>`;
    } else {
      field.checkMessage = nothing;
    }
  }

  // Check that code has landed that is required for third party support.
  checkThirdPartySupport(field, errors) {
    if (errors.ot_has_third_party_support) {
      field.checkMessage = html` <br />
        <span class="check-error">
          <b>Error</b>: ${errors.ot_has_third_party_support}
        </span>`;
    } else {
      field.checkMessage = nothing;
    }
  }

  // Check that code has landed that is required for critical trials.
  checkCriticalTrial(field, errors) {
    if (errors.ot_is_critical_trial) {
      field.checkMessage = html` <br />
        <span class="check-error">
          <b>Error</b>: ${errors.ot_is_critical_trial}
        </span>`;
    } else {
      field.checkMessage = nothing;
    }
  }

  /**
   * Check that given args related to Chromium are valid.
   * @returns Whether any inputs cannot be found in Chromium files.
   */
  handleChromiumChecks(errors) {
    for (const field of this.fieldValues) {
      if (field.name === 'ot_webfeature_use_counter') {
        this.checkWebfeatureUseCounter(field, errors);
      } else if (field.name === 'ot_chromium_trial_name') {
        this.checkChromiumTrialName(field, errors);
      } else if (field.name === 'ot_has_third_party_support') {
        this.checkThirdPartySupport(field, errors);
      } else if (field.name === 'ot_is_critical_trial') {
        this.checkCriticalTrial(field, errors);
      }
    }
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
    const useCounterField = this.fieldValues.find(
      fv => fv.name === 'ot_webfeature_use_counter'
    );
    if (this.isDeprecationTrial) {
      useCounterField!.touched = false;
    }

    const featureSubmitBody = formatFeatureChanges(
      this.fieldValues,
      this.featureId
    );
    // We only need the single stage changes.
    const stageSubmitBody = featureSubmitBody.stages[0];

    if ('ot_webfeature_use_counter' in stageSubmitBody) {
      // Add on the appropriate use counter prefix.
      const useCounterPrefix =
        this.webfeatureUseCounterType === USE_COUNTER_TYPE_WEBFEATURE
          ? ''
          : 'WebDXFeature::';
      stageSubmitBody.ot_webfeature_use_counter.value = `${useCounterPrefix}${stageSubmitBody.ot_webfeature_use_counter.value}`;
    }

    this.submitting = true;
    window.csClient
      .createOriginTrial(this.featureId, this.stageId, stageSubmitBody)
      .then(resp => {
        if (resp.errors) {
          this.handleChromiumChecks(resp.errors);
          showToastMessage(
            'Some issues were found with the given inputs. Check input errors and try again.'
          );
          this.submitting = false;
          this.requestUpdate();
        } else {
          this.submitting = false;
          showToastMessage('Creation request submitted!');
          setTimeout(() => {
            window.location.href = `/feature/${this.featureId}`;
          }, 1000);
        }
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
    const link = this.loading
      ? nothing
      : html`
          <a href=${this.getNextPage()}>
            <iron-icon icon="chromestatus:arrow-back"></iron-icon>
            Request origin trial creation: ${this.feature.name}
          </a>
        `;
    return html`
      <div id="subheader">
        <h2 id="breadcrumbs">${link}</h2>
      </div>
    `;
  }

  renderFields() {
    const fields = this.fieldValues.map((fieldInfo, i) => {
      if (
        fieldInfo.alwaysHidden ||
        (fieldInfo.isApprovalsField && !this.showApprovalsFields) ||
        (fieldInfo.name === 'ot_webfeature_use_counter' &&
          this.isDeprecationTrial)
      ) {
        return nothing;
      }
      // Fade in transition for the approvals fields or use counter field
      // if they're being displayed.
      const shouldFadeIn =
        fieldInfo.isApprovalsField ||
        fieldInfo.name === 'ot_webfeature_use_counter';

      let additionalInfo: TemplateResult | symbol = nothing;
      if (fieldInfo.name == 'ot_webfeature_use_counter') {
        additionalInfo = html`
          <chromedash-form-field
            name="ot_webfeature_use_counter__type"
            index=${i}
            .value=${this.webfeatureUseCounterType}
            .fieldValues=${this.fieldValues}
            ?shouldFadeIn=${shouldFadeIn}
            @form-field-update="${this.handleUseCounterTypeUpdate}"
            class="choices"
          >
          </chromedash-form-field>
        `;
      }

      return html`
        ${additionalInfo}
        <chromedash-form-field
          name=${fieldInfo.name}
          index=${i}
          value=${fieldInfo.value}
          disabledReason="${getDisabledHelpText(fieldInfo.name, this.stage)}"
          .checkMessage=${fieldInfo.checkMessage}
          .fieldValues=${this.fieldValues}
          ?shouldFadeIn=${shouldFadeIn}
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
        ${this.submitting
          ? html`<div id="overlay">
              <div class="loading">
                <div id="spinner">
                  <img class="submission-spinner" src="/static/img/ring.svg" />
                </div>
              </div>
            </div>`
          : nothing}
        <chromedash-form-table ${ref(this.registerHandlers)}>
          <section class="stage_form">
            <div class="warning warning-div">
              <h3>
                Please make sure this data is correct before submission! If you
                are not sure about any information on this form, contact
                <strong>origin-trials-support@google.com</strong>
              </h3>
            </div>
            ${this.renderFields()}
          </section>
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
