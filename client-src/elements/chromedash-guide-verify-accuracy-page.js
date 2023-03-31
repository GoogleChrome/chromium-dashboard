import {LitElement, css, html} from 'lit';
import {ref} from 'lit/directives/ref.js';
import {getStageValue, flattenSections, showToastMessage} from './utils.js';
import './chromedash-form-field';
import './chromedash-form-table';
import {formatFeatureForEdit,
  STAGE_SHORT_NAMES,
  VERIFY_ACCURACY_CONFIRMATION_FIELD,
  VERIFY_ACCURACY_FORMS_BY_STAGE_TYPE,
  VERIFY_ACCURACY_METADATA_FIELDS,
  VERIFY_ACCURACY_TRIAL_EXTENSION_FIELDS} from './form-definition';
import {STAGE_SPECIFIC_FIELDS} from './form-field-enums.js';
import {SHARED_STYLES} from '../sass/shared-css.js';
import {FORM_STYLES} from '../sass/forms-css.js';


export class ChromedashGuideVerifyAccuracyPage extends LitElement {
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
      loading: {type: Boolean},
      appTitle: {type: String},
    };
  }

  constructor() {
    super();
    this.featureId = 0;
    this.feature = {};
    this.loading = true;
    this.appTitle = '';
    this.previousStageTypeRendered = 0;
    this.sameTypeRendered = 0;
  }

  connectedCallback() {
    super.connectedCallback();
    this.fetchData();
  }

  fetchData() {
    this.loading = true;
    window.csClient.getFeature(this.featureId).then((feature) => {
      this.feature = feature;
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

  renderSubheader() {
    return html`
      <div id="subheader">
        <h2 id="breadcrumbs">
          <a href="/guide/edit/${this.featureId}">
            <iron-icon icon="chromestatus:arrow-back"></iron-icon>
            Verify feature data for ${this.feature.name}
          </a>
        </h2>
      </div>
    `;
  }

  getStageForm(stageType) {
    return VERIFY_ACCURACY_FORMS_BY_STAGE_TYPE[stageType] || null;
  }

  renderStageSection(formattedFeature, name, feStage, stageFields) {
    if (!stageFields) return nothing;

    // Add a number differentiation if this stage type is the same as another stage.
    let numberDifferentiation = '';
    if (this.previousStageTypeRendered && this.previousStageTypeRendered === feStage.stage_type) {
      this.sameTypeRendered += 1;
      numberDifferentiation = ` ${this.sameTypeRendered}`;
    } else {
      this.previousStageTypeRendered = feStage.stage_type;
      this.sameTypeRendered = 1;
    }
    let sectionName = `${name}${numberDifferentiation}`;
    if (feStage.display_name) {
      sectionName = `${name}: ${feStage.display_name}`;
    }

    const formFieldEls = stageFields.map(field => {
      let value = formattedFeature[field];
      if (STAGE_SPECIFIC_FIELDS.has(field)) {
        value = getStageValue(feStage, field);
      } else if (this.sameTypeRendered > 1) {
        // Don't render fields that are not stage-specific if this is
        // a stage type that is already being rendered.
        // This is to avoid repeated fields on the edit-all page.
        return nothing;
      }
      return html`
        <chromedash-form-field
          name=${field}
          stageId=${feStage.id}
          value=${value}
          ?forEnterprise=${formattedFeature.is_enterprise_feature}>
        </chromedash-form-field>
      `;
    });
    const id = `${STAGE_SHORT_NAMES[feStage.stage_type] || 'metadata'}${this.sameTypeRendered}`
      .toLowerCase();
    return html`
    <h3 id="${id}">${sectionName}</h3>
    <section class="flat_form">
      ${formFieldEls}
    </section>
    `;
  }

  /**
   * Builds the HTML elements for rendering the form sections.
   * @param {Object} formattedFeature Object describing the feature.
   * @param {Array} feStages List of stages associated with the feature.
   *
   * @return {Array} allFormFields, an array of strings representing all the field
   *   names that will exist on the page.
   * @return {Array} formsToRender, All HTML elements to render in the form.
   */
  getForms(formattedFeature, feStages) {
    // All features display the metadata section.
    let fieldsOnly = flattenSections(VERIFY_ACCURACY_METADATA_FIELDS);
    const formsToRender = [
      this.renderStageSection(
        formattedFeature, VERIFY_ACCURACY_METADATA_FIELDS.name, {}, fieldsOnly)];

    // Generate a single array with the name of every field that is displayed.
    let allFormFields = [...fieldsOnly];


    for (const feStage of feStages) {
      const stageForm = this.getStageForm(feStage.stage_type);
      if (!stageForm) {
        continue;
      }

      fieldsOnly = flattenSections(stageForm);
      formsToRender.push(this.renderStageSection(
        formattedFeature, stageForm.name, feStage, fieldsOnly));
      allFormFields = [...allFormFields, ...fieldsOnly];

      // If extension stages are associated with this stage,
      // render them in a separate section as well.
      const extensions = feStage.extensions || [];
      extensions.forEach(extensionStage => {
        fieldsOnly = flattenSections(VERIFY_ACCURACY_TRIAL_EXTENSION_FIELDS);
        let sectionName = VERIFY_ACCURACY_TRIAL_EXTENSION_FIELDS.name;
        if (feStage.display_name) {
          sectionName = `${feStage.display_name} ${VERIFY_ACCURACY_TRIAL_EXTENSION_FIELDS.name}`;
        }
        formsToRender.push(this.renderStageSection(
          formattedFeature,
          sectionName,
          extensionStage,
          fieldsOnly));
        allFormFields = [...allFormFields, ...fieldsOnly];
      });
    }

    // Add the verify accuracy checkbox at the end of all forms.
    fieldsOnly = flattenSections(VERIFY_ACCURACY_CONFIRMATION_FIELD);
    formsToRender.push(this.renderStageSection(
      formattedFeature, `${VERIFY_ACCURACY_CONFIRMATION_FIELD.name}`, {}, fieldsOnly));
    allFormFields = [...allFormFields, ...fieldsOnly];

    return [allFormFields, formsToRender];
  }

  getAllStageIds() {
    const stageIds = [];
    this.feature.stages.forEach(feStage => {
      stageIds.push(feStage.id);
      // Check if any trial extension exist, and collect their IDs as well.
      const extensions = feStage.extensions || [];
      extensions.forEach(extensionStage => stageIds.push(extensionStage.id));
    });
    return stageIds.join(',');
  }

  renderForm() {
    const formattedFeature = formatFeatureForEdit(this.feature);
    const stageIds = this.getAllStageIds();
    const [allFormFields, formsToRender] = this.getForms(formattedFeature, this.feature.stages);

    const title = this.feature.accurate_as_of ?
      `Accuracy last verified ${this.feature.accurate_as_of.split(' ')[0]}.` :
      'Accuracy last verified at time of creation.';

    return html`
      <form name="feature_form" method="POST" action="/guide/verify_accuracy/${this.featureId}">
        <input type="hidden" name="stages" value="${stageIds}">
        <input type="hidden" name="token">
        <input type="hidden" name="form_fields" value=${allFormFields.join(',')}>
        <h3>${title}</h3>
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

customElements.define('chromedash-guide-verify-accuracy-page', ChromedashGuideVerifyAccuracyPage);
