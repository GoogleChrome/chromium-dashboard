import {LitElement, css, html, nothing} from 'lit';
import {ref} from 'lit/directives/ref.js';
import {showToastMessage} from './utils.js';
import './chromedash-form-table';
import './chromedash-form-field';
import {
  formatFeatureForEdit,
  FLAT_METADATA_FIELDS,
  FORMS_BY_STAGE_TYPE} from './form-definition';
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

  getStageForm(stageType) {
    return FORMS_BY_STAGE_TYPE[stageType] || null;
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

  // Flatten the sections to create a single array with all fields.
  flattenSections(stageSections) {
    return stageSections.reduce((combined, section) => [...combined, ...section.fields], []);
  }

  renderStageSection(formattedFeature, name, stageFields) {
    return html`
    <h3>${name}</h3>
    <section class="flat_form">
      ${stageFields.map(field => html`
        <chromedash-form-field
          name=${field}
          value=${formattedFeature[field]}>
        </chromedash-form-field>
      `)}
    </section>
    `;
  }

  getForms(formattedFeature, feStages) {
    // All features display the metadata section.
    let fieldsOnly = this.flattenSections(FLAT_METADATA_FIELDS.sections);
    const formsToRender = [
      this.renderStageSection(formattedFeature, FLAT_METADATA_FIELDS.name, fieldsOnly)];

    // Generate a single array of every field that is displayed.
    let allFormFields = [...fieldsOnly];


    for (const feStage of feStages) {
      const stageForm = this.getStageForm(feStage.stage_type);
      if (!stageForm) {
        continue;
      }

      fieldsOnly = this.flattenSections(stageForm.sections);
      formsToRender.push(this.renderStageSection(
        formattedFeature, stageForm.name, fieldsOnly));
      allFormFields = [...allFormFields, ...fieldsOnly];
    }

    return [allFormFields, formsToRender];
  }

  renderForm() {
    const formattedFeature = formatFeatureForEdit(this.feature);
    const stageIds = this.feature.stages.map(stage => stage.stage_id);
    const [allFormFields, formsToRender] = this.getForms(formattedFeature, this.feature.stages);
    console.log(allFormFields);
    console.log(formsToRender);
    return html`
      <form name="feature_form" method="POST" action="/guide/editall/${this.featureId}">
        <input type="hidden" name="stages" value="${stageIds}">
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
