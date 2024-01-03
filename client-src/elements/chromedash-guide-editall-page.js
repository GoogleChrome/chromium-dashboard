import {LitElement, css, html, nothing} from 'lit';
import {ref} from 'lit/directives/ref.js';
import {repeat} from 'lit/directives/repeat.js';
import {
  formatFeatureChanges,
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
import {ALL_FIELDS} from './form-field-specs';
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
      fieldValues: {type: Array},
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
    this.fieldValues = [];
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

  handleFormSubmit(e, hiddenTokenField) {
    e.preventDefault();
    const submitBody = formatFeatureChanges(this.fieldValues, this.featureId);

    // get the XSRF token and update it if it's expired before submission
    window.csClient.ensureTokenIsValid().then(() => {
      hiddenTokenField.value = window.csClient.token;
      return csClient.updateFeature(submitBody);
    }).then(() => {
      window.location.href = this.getNextPage();
    }).catch(() => {
      showToastMessage('Some errors occurred. Please refresh the page or try again later.');
    });
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
    if (this.nextPage) {
      return this.nextPage;
    }
    if (this.feature.is_enterprise_feature) {
      return `/feature/${this.featureId}`;
    }
    return `/guide/edit/${this.featureId}`;
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
      const featureJSONKey = ALL_FIELDS[field].name || field;
      if (featureJSONKey === 'display_name' &&
          !shouldShowDisplayNameField(this.feature.stages, feStage.stage_type)) {
        return nothing;
      }
      let value = formattedFeature[field];
      let stageId = null;
      if (STAGE_SPECIFIC_FIELDS.has(featureJSONKey)) {
        value = getStageValue(feStage, featureJSONKey);
        stageId = feStage.id;
      } else if (this.sameTypeRendered > 1) {
        // Don't render fields that are not stage-specific if this is
        // a stage type that is already being rendered.
        // This is to avoid repeated fields on the edit-all page.
        return nothing;
      }
      const index = this.fieldValues.length;
      this.fieldValues.push({name: featureJSONKey, touched: false, value, stageId});

      return html`
        <chromedash-form-field
          name=${field}
          index=${index}
          stageId=${stageId}
          value=${value}
          .fieldValues=${this.fieldValues}
          ?forEnterprise=${formattedFeature.is_enterprise_feature}
          @form-field-update="${this.handleFormFieldUpdate}">
        </chromedash-form-field>
      `;
    });
    const id = `${STAGE_SHORT_NAMES[feStage.stage_type] || 'metadata'}${this.sameTypeRendered}`
      .toLowerCase();
    const isEnterpriseFeatureRollout = formattedFeature.is_enterprise_feature &&
      feStage.stage_type === STAGE_ENT_ROLLOUT;
    return {
      id: feStage.id,
      item: html`
        ${renderHTMLIf(!isEnterpriseFeatureRollout, html`<h3 id="${id}">${sectionName}</h3>`)}
        <section class="flat_form" stage="${feStage.stage_type}">
          ${renderHTMLIf(feStage.stage_type === STAGE_ENT_ROLLOUT,
            html`
            <sl-button stage="${feStage.stage_type}" size="small" @click="${() => this.deleteStage(feStage)}">
              Delete
            </sl-button>`)}
          ${formFieldEls}
        </section>
    `};
  }

  /**
   * Builds the HTML elements for rendering the form sections.
   * @param {Object} formattedFeature Object describing the feature.
   * @param {Array} feStages List of stages associated with the feature.
   *
   * @return {Array} formsToRender, All HTML elements to render in the form.
   */
  getForms(formattedFeature, feStages) {
    // All features display the metadata section.
    let fieldsOnly = flattenSections(formattedFeature.is_enterprise_feature ?
      FLAT_ENTERPRISE_METADATA_FIELDS :
      FLAT_METADATA_FIELDS);
    const formsToRender = [
      this.renderStageSection(formattedFeature, FLAT_METADATA_FIELDS.name, {id: -1}, fieldsOnly)];

    let previousStageType = null;
    for (const feStage of feStages) {
      const stageForm = this.getStageForm(feStage.stage_type);
      if (!stageForm) {
        continue;
      }

      if (formattedFeature.is_enterprise_feature &&
          feStage.stage_type !== previousStageType) {
        formsToRender.push({
          id: -2,
          item: this.getHelpTextForStage(feStage.stage_type)});
        previousStageType = feStage.stage_type;
      }

      fieldsOnly = flattenSections(stageForm);
      formsToRender.push(this.renderStageSection(
        formattedFeature, stageForm.name, feStage, fieldsOnly));

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
      });
    }

    return formsToRender;
  }

  // render the button to add a new stage. Displays for enterprise features only.
  renderAddStageButton() {
    const clickHandler = () => {
      openAddStageDialog(
        this.feature.id,
        this.feature.feature_type_int,
        this.createNewStage.bind(this));
    };
    return renderHTMLIf(
      this.feature.is_enterprise_feature,
      html`
      <sl-button size="small" @click="${clickHandler}">
        Add Step
      </sl-button>`);
  }

  // Create a stage requested on the edit all page.
  createNewStage(newStage) {
    window.csClient.createStage(
      this.featureId, {stage_type: newStage.stage_type})
      .then(() => window.csClient.getFeature(this.featureId))
      .then(feature => {
        this.feature = feature;
      }).catch(() => {
        showToastMessage('Some errors occurred. Please refresh the page or try again later.');
      });
  }

  deleteStage(stage) {
    if (!confirm('Delete feature?')) return;

    window.csClient.deleteStage(this.featureId, stage.id)
      .then(() => window.csClient.getFeature(this.featureId))
      .then(feature => {
        this.feature = feature;
      }).catch(() => {
        showToastMessage('Some errors occurred. Please refresh the page or try again later.');
      });
  }


  renderForm() {
    const formattedFeature = formatFeatureForEdit(this.feature);
    this.fieldValues.feature = this.feature;

    const formsToRender = this.getForms(formattedFeature, this.feature.stages);
    return html`
      <form name="feature_form">
        <input type="hidden" name="token">
        <chromedash-form-table ${ref(this.registerHandlers)}>
          ${repeat(formsToRender, form => form.id, (_, i) => formsToRender[i].item)}
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
