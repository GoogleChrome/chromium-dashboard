import {LitElement, css, html} from 'lit';
import {ref} from 'lit/directives/ref.js';
import {
  formatFeatureChanges,
  showToastMessage,
  setupScrollToHash} from './utils.js';
import './chromedash-form-table.js';
import './chromedash-form-field.js';
import {
  ORIGIN_TRIAL_EXTENSION_FIELDS} from './form-definition.js';
import {OT_EXTENSION_STAGE_MAPPING} from './form-field-enums.js';
import {ALL_FIELDS} from './form-field-specs';
import {SHARED_STYLES} from '../css/shared-css.js';
import {FORM_STYLES} from '../css/forms-css.js';


export class ChromedashOTExtensionPage extends LitElement {
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
      this.loading = false;
    }).catch(() => {
      showToastMessage('Some errors occurred. Please refresh the page or try again later.');
    });
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
    const featureSubmitBody = formatFeatureChanges(this.fieldValues, this.featureId);
    // We only need the single stage changes.
    const stageSubmitBody = featureSubmitBody.stages[0];

    window.csClient.createStage(this.featureId, stageSubmitBody).then(() => {
      showToastMessage('Extension request submitted!');
      setTimeout(() => {
        window.location.href = this.nextPage || `/feature/${this.featureId}`;
      }, 1000);
    }).catch(() => {
      showToastMessage('Some errors occurred. Please refresh the page or try again later.');
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
            Request origin trial extension: ${this.feature.name}
          </a>
        </h2>
      </div>
    `;
  }

  // Add a set of field information that will be sent with a request submission.
  // These fields are always considered touched, and are not visible to the user.
  addDefaultRequestFields() {
    // Add "ot_owner_email" field to represent the requester email.
    this.fieldValues.push({
      name: 'ot_owner_email',
      touched: true,
      value: this.userEmail,
      stageId: this.stage.id,
    });

    // Add a field for updating that an OT extension request has been submitted.
    this.fieldValues.push({
      name: 'ot_action_requested',
      touched: true,
      value: true,
      stageId: this.stage.id,
    });

    // Add "stage_type" field to create extension stage properly.
    const extensionStageType = OT_EXTENSION_STAGE_MAPPING[this.stage.stage_type];
    this.fieldValues.push({
      name: 'stage_type',
      touched: true,
      value: extensionStageType,
      stageId: this.stage.id,
    });

    // Add "ot_stage_id" field to link extension stage to OT stage.
    this.fieldValues.push({
      name: 'ot_stage_id',
      touched: true,
      value: this.stage.id,
      stageId: this.stage.id,
    });
  }

  renderFields(section) {
    const fields = section.fields.map(field => {
      const featureJSONKey = ALL_FIELDS[field].name || field;
      // Add the field to this component's stage before creating the field component.
      const index = this.fieldValues.length;
      this.fieldValues.push({
        name: featureJSONKey,
        touched: false,
        value: null,
        stageId: this.stage.id,
      });

      return html`
      <chromedash-form-field
        name=${featureJSONKey}
        index=${index}
        stageId="${this.stageId}"
        .fieldValues=${this.fieldValues}
        @form-field-update="${this.handleFormFieldUpdate}">
      </chromedash-form-field>
    `;
    });

    // Add additional default hidden fields.
    this.addDefaultRequestFields();

    return fields;
  }

  renderForm() {
    this.fieldValues.allFields = this.feature;

    // OT extension page only has one section.
    const section = ORIGIN_TRIAL_EXTENSION_FIELDS.sections[0];
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

customElements.define('chromedash-ot-extension-page', ChromedashOTExtensionPage);
