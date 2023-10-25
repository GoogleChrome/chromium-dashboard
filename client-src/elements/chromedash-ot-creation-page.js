import {LitElement, css, html, nothing} from 'lit';
import {ref} from 'lit/directives/ref.js';
import {
  formatFeatureChanges,
  getStageValue,
  showToastMessage,
  setupScrollToHash} from './utils.js';
import './chromedash-form-table.js';
import './chromedash-form-field.js';
import {ORIGIN_TRIAL_CREATION_FIELDS} from './form-definition.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {FORM_STYLES} from '../css/forms-css.js';
import {ALL_FIELDS} from './form-field-specs.js';


export class ChromedashOTCreationPage extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      ...FORM_STYLES,
      css`
      `];
  }

  static get properties() {
    return {
      stageId: {type: Number},
      featureId: {type: Number},
      userEmail: {type: String},
      feature: {type: Object},
      loading: {type: Boolean},
      appTitle: {type: String},
      nextPage: {type: String},
      fieldValues: {type: Array},
      showApprovalsFields: {type: Boolean},
    };
  }

  constructor() {
    super();
    this.stageId = 0;
    this.featureId = 0;
    this.feature = {};
    this.loading = true;
    this.appTitle = '';
    this.nextPage = '';
    this.fieldValues = [];
    this.showApprovalsFields = false;
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
  };

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
    const insertIndex = this.fieldValues.findIndex(
      fieldInfo => fieldInfo.name === 'ot_require_approvals') + 1;
    this.fieldValues.splice(insertIndex, 0,
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
      });
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
    const submitButton = this.shadowRoot.querySelector('input[id=submit-button]');
    submitButton.form.addEventListener('submit', (event) => {
      this.handleFormSubmit(event);
    });

    setupScrollToHash(this);
  }

  handleFormSubmit(e) {
    e.preventDefault();
    // If registration approvals is not enabled, ignore all fields related to that setting.
    if (!this.showApprovalsFields) {
      this.fieldValues.forEach(fieldInfo => {
        if (fieldInfo.isApprovalsField) {
          fieldInfo.touched = false;
        }
      });
    }

    const featureSubmitBody = formatFeatureChanges(this.fieldValues, this.featureId);
    // We only need the single stage changes.
    const stageSubmitBody = featureSubmitBody.stages[0];

    window.csClient.updateStage(this.featureId, this.stageId, stageSubmitBody).then(() => {
      showToastMessage('Creation request submitted!');
      setTimeout(() => {
        window.location.href = this.nextPage || `/feature/${this.featureId}`;
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
    return this.nextPage || `/feature/${this.featureId}`;
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
      if (fieldInfo.alwaysHidden || (fieldInfo.isApprovalsField && !this.showApprovalsFields)) {
        return nothing;
      }
      // Fade in transition for the approvals fields if they're being displayed.
      const shouldFadeIn = fieldInfo.isApprovalsField;

      return html`
      <chromedash-form-field
        name=${fieldInfo.name}
        .shouldFadeIn=${shouldFadeIn}
        value=${fieldInfo.value}
        index=${i}
        @form-field-update="${this.handleFormFieldUpdate}">
      </chromedash-form-field>
    `;
    });
    return fields;
  }

  renderForm() {
    // OT creation page only has one section.
    const section = ORIGIN_TRIAL_CREATION_FIELDS.sections[0];
    return html`
      <form name="feature_form">
        <chromedash-form-table ${ref(this.registerHandlers)}>
          <section class="stage_form">
            ${this.renderFields(section)}
          </section>
        </chromedash-form-table>
        <div class="final_buttons">
          <input
            id='submit-button'
            class="button"
            type="submit"
            value="Submit">
          <button id="cancel-button" @click=${this.handleCancelClick}>Cancel</button>
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
