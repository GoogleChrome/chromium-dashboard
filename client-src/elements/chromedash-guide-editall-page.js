import {LitElement, css, html, nothing} from 'lit';
import {ref} from 'lit/directives/ref.js';
import {showToastMessage, findProcessStage} from './utils.js';
import './chromedash-form-table';
import './chromedash-form-field';
import {
  formatFeatureForEdit,
  METADATA_FORM_FIELDS,
  FLAT_FORMS_BY_INTENT_TYPE} from './form-definition';
import {SHARED_STYLES} from '../sass/shared-css.js';
import {FORM_STYLES} from '../sass/forms-css.js';


export class ChromedashGuideEditallPage extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      ...FORM_STYLES,
      css`
    `];
  }

  static get properties() {
    return {
      featureId: {type: Number},
      feature: {type: Object},
      process: {type: Object},
      loading: {type: Boolean},
      appTitle: {type: String},
      nextPage: {type: String},
    };
  }

  constructor() {
    super();
    this.featureId = 0;
    this.feature = {};
    this.loading = true;
    this.appTitle = '';
    this.nextPage = '';
  }

  connectedCallback() {
    super.connectedCallback();
    this.fetchData();
  }

  fetchData() {
    this.loading = true;
    Promise.all([
      window.csClient.getFeature(this.featureId),
      window.csClient.getFeatureProcess(this.featureId),
    ]).then(([feature, process]) => {
      this.feature = feature;
      this.process = process;
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

  /* Add the form's event listener after Shoelace event listeners are attached
   * see more at https://github.com/GoogleChrome/chromium-dashboard/issues/2014 */
  async registerFormSubmitHandler(el) {
    if (!el) return;

    await el.updateComplete;
    const hiddenTokenField = this.shadowRoot.querySelector('input[name=token]');
    hiddenTokenField.form.addEventListener('submit', (event) => {
      this.handleFormSubmit(event, hiddenTokenField);
    });
  }

  handleFormSubmit(event, hiddenTokenField) {
    event.preventDefault();

    // get the XSRF token and update it if it's expired before submission
    window.csClient.ensureTokenIsValid().then(() => {
      hiddenTokenField.value = window.csClient.token;
      event.target.submit();
    });
  }

  handleCancelClick() {
    window.location.href = `/guide/edit/${this.featureId}`;
  }

  renderSkeletons() {
    return html`
      <h3><sl-skeleton effect="sheen"></sl-skeleton></h3>
      <section class="flat_form">
        <h3><sl-skeleton effect="sheen"></sl-skeleton></h3>
        <p>
          <sl-skeleton effect="sheen"></sl-skeleton>
          <sl-skeleton effect="sheen"></sl-skeleton>
          <sl-skeleton effect="sheen"></sl-skeleton>
          <sl-skeleton effect="sheen"></sl-skeleton>
        </p>
      </section>
      <h3><sl-skeleton effect="sheen"></sl-skeleton></h3>
      <section class="flat_form">
        <h3><sl-skeleton effect="sheen"></sl-skeleton></h3>
        <p>
          <sl-skeleton effect="sheen"></sl-skeleton>
          <sl-skeleton effect="sheen"></sl-skeleton>
          <sl-skeleton effect="sheen"></sl-skeleton>
          <sl-skeleton effect="sheen"></sl-skeleton>
        </p>
      </section>
    `;
  }

  getNextPage() {
    return this.nextPage || `/guide/edit/${this.featureId}`;
  }

  renderSubheader() {
    return html`
      <div id="subheader">
        <h2 id="breadcrumbs">
          <a href=${this.getNextPage()}>
            <iron-icon icon="chromestatus:arrow-back"></iron-icon>
            Edit feature: ${this.loading ? 'loading...' : this.feature.name}
          </a>
        </h2>
      </div>
    `;
  }

  getStageFormFields(processStage) {
    return FLAT_FORMS_BY_INTENT_TYPE[processStage.outgoing_stage] || [];
  }

  renderStageFormFields(formattedFeature, processStage, feStage, formFields) {
    if (!formFields) return nothing;

    return html`
      <h3>${processStage.name}</h3>
      <section class="flat_form">
        ${formFields.map((field) => html`
          <chromedash-form-field
            name=${field}
            stageId=${feStage.stage_id}
            value=${formattedFeature[field]}>
          </chromedash-form-field>
        `)}
      </section>
    `;
  }

  getForms(formattedFeature, feStages) {
    const formsToRender = [html`
    <h3>Feature metadata</h3>
    <section class="flat_form">
      ${METADATA_FORM_FIELDS.map((field) => html`
        <chromedash-form-field
          name=${field}
          value=${formattedFeature[field]}>
        </chromedash-form-field>
      `)}
    </section>
    `];

    let allFormFields = [...METADATA_FORM_FIELDS];
    for (const feStage of feStages) {
      const processStage = findProcessStage(feStage, this.process);
      if (!processStage) {
        continue;
      }
      const formFields = this.getStageFormFields(processStage);
      formsToRender.push(this.renderStageFormFields(
        formattedFeature, processStage, feStage, formFields));
      allFormFields = [...allFormFields, ...formFields];
    }

    return [allFormFields, formsToRender];
  }

  renderForm() {
    const formattedFeature = formatFeatureForEdit(this.feature);
    const stages = this.feature.stages.map(stage => stage.stage_id);
    const [allFormFields, formsToRender] = this.getForms(formattedFeature, this.feature.stages);
    return html`
      <form name="feature_form" method="POST" action="/guide/editall/${this.featureId}">
        <input type="hidden" name="stages" value="${stages}">
        <input type="hidden" name="token">
        <input type="hidden" name="nextPage" value=${this.getNextPage()} >
        <input type="hidden" name="form_fields" value=${allFormFields.join(',')}>
        <chromedash-form-table ${ref(this.registerFormSubmitHandler)}>
          ${formsToRender}
        </chromedash-form-table>

        <section class="final_buttons">
          <input class="button" type="submit" value="Submit">
          <button id="cancel-button" type="reset"
            @click=${this.handleCancelClick}>Cancel</button>
        </section>
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

customElements.define('chromedash-guide-editall-page', ChromedashGuideEditallPage);
