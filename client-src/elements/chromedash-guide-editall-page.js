import {LitElement, css, html, nothing} from 'lit';
import {ref} from 'lit/directives/ref.js';
import {
  getStageValue,
  showToastMessage,
  flattenSections,
  setupScrollToHash,
  shouldShowDisplayNameField,
  renderHTMLIf} from './utils.js';
import './chromedash-form-table';
import './chromedash-form-field';
import {
  formatFeatureForEdit,
  FLAT_METADATA_FIELDS,
  FLAT_ENTERPRISE_METADATA_FIELDS,
  FORMS_BY_STAGE_TYPE,
  FLAT_TRIAL_EXTENSION_FIELDS,
} from './form-definition';
import {SHARED_STYLES} from '../css/shared-css.js';
import {FORM_STYLES} from '../css/forms-css.js';
import {STAGE_SHORT_NAMES, STAGE_SPECIFIC_FIELDS, STAGE_ENT_ROLLOUT} from './form-field-enums.js';
import {openAddStageDialog} from './chromedash-add-stage-dialog';


export class ChromedashGuideEditallPage extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      ...FORM_STYLES,
      css`
      .enterprise-help-text > *, .enterprise-help-text li {
        margin: revert;
        padding: revert;
        list-style: revert;
      }
    `];
  }

  static get properties() {
    return {
      featureId: {type: Number},
      feature: {type: Object},
      loading: {type: Boolean},
      appTitle: {type: String},
      nextPage: {type: String},
      nextStageToCreateId: {type: Number},
    };
  }

  constructor() {
    super();
    this.featureId = 0;
    this.feature = {};
    this.loading = true;
    this.appTitle = '';
    this.nextPage = '';
    this.previousStageTypeRendered = 0;
    this.sameTypeRendered = 0;
    this.nextStageToCreateId = 0;
  }

  connectedCallback() {
    super.connectedCallback();
    this.fetchData();
  }

  fetchData() {
    this.loading = true;
    Promise.all([
      window.csClient.getFeature(this.featureId),
    ]).then(([feature]) => {
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
  async registerHandlers(el) {
    if (!el) return;
    await el.updateComplete;

    const hiddenTokenField = this.shadowRoot.querySelector('input[name=token]');
    hiddenTokenField.form.addEventListener('submit', (event) => {
      this.handleFormSubmit(event, hiddenTokenField);
    });

    setupScrollToHash(this);
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
    return this.nextPage || this.feature.is_enterprise_feature ?
    `/feature/${this.featureId}` : `/guide/edit/${this.featureId}`;
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

  getHelpTextForStage(stageType) {
    switch (stageType) {
      case STAGE_ENT_ROLLOUT:
        return html`
        <section class="enterprise-help-text">
          <h3>Rollout steps</h3>
          <p>The enterprise release notes focus on changes to the stable channel.
          Please add a stage for each milestone where something is changing on the stable channel.
          For finch rollouts, use the milestone where the rollout starts.
          </p>
          <p>
            For example, you may only have a single stage where you roll out to 100% of users on milestone N.
          </p>
          <p>A more complex example might look like this:</p>
          <ul>
            <li>On milestone N-1, you introduce a flag for early testing of an upcoming change, or start a deprecation origin trial</li>
            <li>On milestone N, you start a finch rollout of a feature at 1% and introduce an enterprise policy for it</li>
            <li>On milestone N+3, you remove the enterprise policy</li>
          </ul>
        </section>
      `;
      default:
        return nothing;
    }
  }

  renderStageSection(formattedFeature, sectionBaseName, feStage, stageFields) {
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
    let sectionName = `${sectionBaseName}${numberDifferentiation}`;
    if (feStage.display_name) {
      sectionName = `${sectionBaseName}: ${feStage.display_name} `;
    }
    const formFieldEls = stageFields.map(field => {
      // Only show "display name" field if there is more than one stage of the same type.
      if (field === 'display_name' &&
          !shouldShowDisplayNameField(this.feature.stages, feStage.stage_type)) {
        return nothing;
      }
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
          stageType=${feStage.to_create ? feStage.stage_type : undefined}
          value=${value}
          ?forEnterprise=${formattedFeature.is_enterprise_feature}>
        </chromedash-form-field>
      `;
    });
    const id = `${STAGE_SHORT_NAMES[feStage.stage_type] || 'metadata'}${this.sameTypeRendered}`
      .toLowerCase();
    const isEnterpriseFeatureRollout = formattedFeature.is_enterprise_feature &&
      feStage.stage_type === STAGE_ENT_ROLLOUT;
    return html`
    ${renderHTMLIf(!isEnterpriseFeatureRollout, html`<h3 id="${id}">${sectionName}</h3>`)}
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
    let fieldsOnly = flattenSections(formattedFeature.is_enterprise_feature ?
      FLAT_ENTERPRISE_METADATA_FIELDS :
      FLAT_METADATA_FIELDS);
    const formsToRender = [
      this.renderStageSection(formattedFeature, FLAT_METADATA_FIELDS.name, {}, fieldsOnly)];

    // Generate a single array with the name of every field that is displayed.
    let allFormFields = [...fieldsOnly];


    let previousStageType = null;
    for (const feStage of feStages) {
      const stageForm = this.getStageForm(feStage.stage_type);
      if (!stageForm) {
        continue;
      }

      if (formattedFeature.is_enterprise_feature &&
          feStage.stage_type !== previousStageType) {
        formsToRender.push(this.getHelpTextForStage(feStage.stage_type));
        previousStageType = feStage.stage_type;
      }

      fieldsOnly = flattenSections(stageForm);
      formsToRender.push(this.renderStageSection(
        formattedFeature, stageForm.name, feStage, fieldsOnly));
      allFormFields = [...allFormFields, ...fieldsOnly];

      // If extension stages are associated with this stage,
      // render them in a separate section as well.
      const extensions = feStage.extensions || [];
      extensions.forEach(extensionStage => {
        fieldsOnly = flattenSections(FLAT_TRIAL_EXTENSION_FIELDS);
        let sectionName = FLAT_TRIAL_EXTENSION_FIELDS.name;
        if (feStage.display_name) {
          sectionName = ` ${FLAT_TRIAL_EXTENSION_FIELDS.name}: ${feStage.display_name} `;
        }
        formsToRender.push(this.renderStageSection(
          formattedFeature,
          sectionName,
          extensionStage,
          fieldsOnly));
        allFormFields = [...allFormFields, ...fieldsOnly];
      });
    }

    return [allFormFields, formsToRender];
  }

  getAllStageIds() {
    const stageIds = [];
    this.feature.stages.forEach(feStage => {
      if (feStage.to_create) return;
      stageIds.push(feStage.id);
      // Check if any trial extension exist, and collect their IDs as well.
      const extensions = feStage.extensions || [];
      extensions.forEach(extensionStage => stageIds.push(extensionStage.id));
    });
    return stageIds.join(',');
  }

  renderAddStageButton() {
    const text = this.feature.is_enterprise_feature ? 'Add Step': 'Add Stage';
    return html`
    <sl-button size="small" @click="${
        () => openAddStageDialog(this.feature.id, this.feature.feature_type_int, this.AddNewStageToCreate.bind(this))}">
      ${text}
    </sl-button>`;
  }

  AddNewStageToCreate(newStage) {
    const lastIndexOfType = this.feature.stages
      .findLastIndex((stage) => stage.stage_type === newStage.stage_type);
    if (lastIndexOfType === -1) {
      this.feature.stages.push({
        ...newStage,
        to_create: true,
        id: ++this.nextStageToCreateId});
    } else {
      this.feature.stages.splice(lastIndexOfType + 1, 0, {
        ...newStage,
        to_create: true,
        id: ++this.nextStageToCreateId});
    }
    this.feature = {...this.feature};
  }

  renderForm() {
    const formattedFeature = formatFeatureForEdit(this.feature);
    const stageIds = this.getAllStageIds();
    const [allFormFields, formsToRender] = this.getForms(formattedFeature, this.feature.stages);
    return html`
      <form name="feature_form" method="POST" action="/guide/editall/${this.featureId}">
        <input type="hidden" name="stages" value="${stageIds}">
        <input type="hidden" name="token">
        <input type="hidden" name="nextPage" value=${this.getNextPage()} >
        <input type="hidden" name="form_fields" value=${allFormFields.join(',')}>
        <chromedash-form-table ${ref(this.registerHandlers)}>
          ${formsToRender}
        </chromedash-form-table>
        ${this.renderAddStageButton()}

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
