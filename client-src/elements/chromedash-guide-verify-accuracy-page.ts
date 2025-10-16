import {LitElement, css, html, nothing} from 'lit';
import {ref} from 'lit/directives/ref.js';
import {
  getDisabledHelpText,
  getStageValue,
  flattenSections,
  formatFeatureChanges,
  showToastMessage,
  FieldInfo,
} from './utils.js';
import './chromedash-form-field';
import './chromedash-form-table';
import {
  formatFeatureForEdit,
  VERIFY_ACCURACY_CONFIRMATION_FIELD,
  VERIFY_ACCURACY_FORMS_BY_STAGE_TYPE,
  VERIFY_ACCURACY_METADATA_FIELDS,
} from './form-definition';
import {STAGE_SHORT_NAMES, STAGE_SPECIFIC_FIELDS} from './form-field-enums.js';
import {ALL_FIELDS} from './form-field-specs';
import {SHARED_STYLES} from '../css/shared-css.js';
import {FORM_STYLES} from '../css/forms-css.js';
import {property, state} from 'lit/decorators.js';
import {Feature} from '../js-src/cs-client.js';

export class ChromedashGuideVerifyAccuracyPage extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      ...FORM_STYLES,
      css`
      .verify-banner {
          margin-bottom: 12px;
        }
      `
    ];
  }
  @property({attribute: false})
  featureId = 0;
  @property({type: String})
  appTitle = '';
  @state()
  feature = {} as Feature;
  @state()
  fieldValues: FieldInfo[] & {feature?: Feature} = [];
  @state()
  loading = true;
  @state()
  previousStageTypeRendered = 0;
  @state()
  sameTypeRendered = 0;
  @state()
  submitting = false;

  connectedCallback() {
    super.connectedCallback();
    this.fetchData();
  }

  fetchData() {
    this.loading = true;
    window.csClient
      .getFeature(this.featureId)
      .then(feature => {
        this.feature = feature;
        if (this.feature.name) {
          document.title = `${this.feature.name} - ${this.appTitle}`;
        }
        this.loading = false;
      })
      .catch(() => {
        showToastMessage(
          'Some errors occurred. Please refresh the page or try again later.'
        );
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
    const hiddenTokenField = this.renderRoot.querySelector(
      'input[name=token]'
    ) as HTMLInputElement;
    hiddenTokenField.form?.addEventListener('submit', event => {
      this.handleFormSubmit(event, hiddenTokenField);
    });
  }

  handleFormSubmit(e, hiddenTokenField) {
    e.preventDefault();
    const submitBody = formatFeatureChanges(this.fieldValues, this.featureId);

    // get the XSRF token and update it if it's expired before submission
    window.csClient
      .ensureTokenIsValid()
      .then(() => {
        hiddenTokenField.value = window.csClient.token;
        this.submitting = true;
        return window.csClient.updateFeature(submitBody);
      })
      .then(() => {
        window.location.href = `/feature/${this.featureId}`;
      })
      .catch(() => {
        this.submitting = false;
        showToastMessage(
          'Some errors occurred. Please refresh the page or try again later.'
        );
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

  renderSubheader() {
    return html`
      <div id="subheader">
        <h2 id="breadcrumbs">
          <a href="/feature/${this.featureId}">
            <sl-icon name="arrow-left"></sl-icon>
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
    if (
      this.previousStageTypeRendered &&
      this.previousStageTypeRendered === feStage.stage_type
    ) {
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
      const featureJSONKey = ALL_FIELDS[field].name || field;

      if (STAGE_SPECIFIC_FIELDS.has(field)) {
        value = getStageValue(feStage, featureJSONKey);
      } else if (this.sameTypeRendered > 1) {
        // Don't render fields that are not stage-specific if this is
        // a stage type that is already being rendered.
        // This is to avoid repeated fields on the edit-all page.
        return nothing;
      }

      // Add the field to this component's stage before creating the field component.
      const index = this.fieldValues.length;
      let touched = false;
      if (featureJSONKey === 'accurate_as_of') {
        touched = true;
      }
      this.fieldValues.push({
        name: featureJSONKey,
        touched,
        value,
        stageId: feStage.id,
      });

      return html`
        <chromedash-form-field
          name=${field}
          index=${index}
          value=${value}
          disabledReason="${getDisabledHelpText(field, feStage)}"
          .fieldValues=${this.fieldValues}
          .feature=${formattedFeature}
          ?forEnterprise=${formattedFeature.is_enterprise_feature}
          @form-field-update="${this.handleFormFieldUpdate}"
        >
        </chromedash-form-field>
      `;
    });
    const id =
      `${STAGE_SHORT_NAMES[feStage.stage_type] || 'metadata'}${this.sameTypeRendered}`.toLowerCase();
    return html`
      <h3 id="${id}">${sectionName}</h3>
      <section class="flat_form">${formFieldEls}</section>
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
        formattedFeature,
        VERIFY_ACCURACY_METADATA_FIELDS.name,
        {},
        fieldsOnly
      ),
    ];

    // Generate a single array with the name of every field that is displayed.
    let allFormFields = [...fieldsOnly];

    for (const feStage of feStages) {
      const stageForm = this.getStageForm(feStage.stage_type);
      if (!stageForm) {
        continue;
      }

      fieldsOnly = flattenSections(stageForm);
      formsToRender.push(
        this.renderStageSection(
          formattedFeature,
          stageForm.name,
          feStage,
          fieldsOnly
        )
      );
      allFormFields = [...allFormFields, ...fieldsOnly];
    }

    // Add the verify accuracy checkbox at the end of all forms.
    fieldsOnly = flattenSections(VERIFY_ACCURACY_CONFIRMATION_FIELD);
    formsToRender.push(
      this.renderStageSection(
        formattedFeature,
        `${VERIFY_ACCURACY_CONFIRMATION_FIELD.name}`,
        {},
        fieldsOnly
      )
    );
    allFormFields = [...allFormFields, ...fieldsOnly];

    return [allFormFields, formsToRender];
  }

  getAllStageIds() {
    return this.feature.stages.map(feStage => feStage.id);
  }

  renderForm() {
    const formattedFeature = formatFeatureForEdit(this.feature);
    this.fieldValues.feature = this.feature;

    const stageIds = this.getAllStageIds();
    const [allFormFields, formsToRender] = this.getForms(
      formattedFeature,
      this.feature.stages
    );

    const title = this.feature.accurate_as_of
      ? `Accuracy last verified ${this.feature.accurate_as_of.split(' ')[0]}.`
      : 'Accuracy last verified at time of creation.';
    const submitButtonTitle = (this.submitting) ? 'Submitting...' : 'Submit';
    return html`
      <form name="feature_form" method="post">
        <input type="hidden" name="stages" value="${stageIds}" />
        <input type="hidden" name="token" />
        <input
          type="hidden"
          name="form_fields"
          value=${allFormFields.join(',')}
        />
        <h3>${title}</h3>
        <sl-alert variant="warning" open class="verify-banner">
          <sl-icon slot="icon" name="info-circle"></sl-icon>
          <strong>Please submit this form to verify accuracy, even if no changes are made!</strong>
        </sl-alert>
        <chromedash-form-table ${ref(this.registerFormSubmitHandler)}>
          ${formsToRender}
        </chromedash-form-table>

        <section class="final_buttons">
          <input class="button" type="submit" value="${submitButtonTitle}" ?disabled=${this.submitting} />
          <button
            id="cancel-button"
            type="reset"
            @click=${this.handleCancelClick}
          >
            Cancel
          </button>
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

customElements.define(
  'chromedash-guide-verify-accuracy-page',
  ChromedashGuideVerifyAccuracyPage
);
