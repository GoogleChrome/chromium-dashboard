import {LitElement, css, html, nothing} from 'lit';
import {ref} from 'lit/directives/ref.js';
import {
  formatFeatureChanges,
  getStageValue,
  showToastMessage,
  setupScrollToHash,
  shouldShowDisplayNameField,
} from './utils.js';
import './chromedash-form-table';
import './chromedash-form-field';
import {
  FLAT_TRIAL_EXTENSION_FIELDS,
  formatFeatureForEdit,
  FORMS_BY_STAGE_TYPE,
} from './form-definition';
import {
  IMPLEMENTATION_STATUS,
  OT_EXTENSION_STAGE_TYPES,
  STAGE_SPECIFIC_FIELDS,
} from './form-field-enums';
import {ALL_FIELDS} from './form-field-specs';
import {SHARED_STYLES} from '../css/shared-css.js';
import {FORM_STYLES} from '../css/forms-css.js';

export class ChromedashGuideStagePage extends LitElement {
  static get styles() {
    return [...SHARED_STYLES, ...FORM_STYLES, css``];
  }

  static get properties() {
    return {
      stageId: {type: Number},
      intentStage: {type: Number},
      stageName: {type: String},
      featureId: {type: Number},
      feature: {type: Object},
      isActiveStage: {type: Boolean},
      featureFormFields: {type: Array},
      implStatusFormFields: {type: Array},
      implStatusOffered: {type: String},
      loading: {type: Boolean},
      appTitle: {type: String},
      fieldValues: {type: Array},
    };
  }

  constructor() {
    super();
    this.stageId = 0;
    this.intentStage = 0;
    this.stageName = '';
    this.featureId = 0;
    this.feature = {};
    this.isActiveStage = false;
    this.featureFormFields = [];
    this.implStatusFormFields = [];
    this.implStatusOffered = '';
    this.loading = true;
    this.appTitle = '';
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
  }

  fetchData() {
    this.loading = true;
    Promise.all([
      window.csClient.getFeature(this.featureId),
      window.csClient.getStage(this.featureId, this.stageId),
    ])
      .then(([feature, stage]) => {
        this.feature = feature;
        this.stage = stage;

        if (this.feature.name) {
          document.title = `${this.feature.name} - ${this.appTitle}`;
        }
        if (this.feature.active_stage_id === this.stage.id) {
          this.isActiveStage = true;
        }
        this.featureFormFields = FORMS_BY_STAGE_TYPE[stage.stage_type] || {
          name: '',
          sections: [],
        };
        this.stageName = this.featureFormFields.name;
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

  async registerHandlers(el) {
    if (!el) return;

    /* Add the form's event listener after Shoelace event listeners are attached
     * see more at https://github.com/GoogleChrome/chromium-dashboard/issues/2014 */
    await el.updateComplete;
    const hiddenTokenField = this.shadowRoot.querySelector('input[name=token]');
    hiddenTokenField.form.addEventListener('submit', event => {
      this.handleFormSubmit(event, hiddenTokenField);
    });

    this.miscSetup();
    setupScrollToHash(this);
  }

  handleFormSubmit(e, hiddenTokenField) {
    e.preventDefault();
    const submitBody = formatFeatureChanges(this.fieldValues, this.featureId);

    // get the XSRF token and update it if it's expired before submission
    window.csClient
      .ensureTokenIsValid()
      .then(() => {
        hiddenTokenField.value = window.csClient.token;
        return csClient.updateFeature(submitBody);
      })
      .then(() => {
        window.location.href = `/feature/${this.featureId}`;
      })
      .catch(() => {
        showToastMessage(
          'Some errors occurred. Please refresh the page or try again later.'
        );
      });
  }

  miscSetup() {
    // Allow editing if there was already a value specified in this
    // deprecated field.
    const timelineField = this.shadowRoot.querySelector(
      '#id_experiment_timeline'
    );
    if (timelineField && timelineField.value) {
      timelineField.disabled = '';
    }
  }

  handleCancelClick() {
    window.location.href = `/feature/${this.featureId}`;
  }

  // get a comma-spearated list of field names
  getFormFields() {
    const fields = this.featureFormFields.sections.reduce(
      (combined, section) => [...combined, ...section.fields],
      []
    );
    return fields.join();
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
            Edit feature: ${this.feature.name}
          </a>
        </h2>
      </div>
    `;
  }

  renderFields(formattedFeature, section, feStage) {
    if (!feStage) {
      feStage = this.stage;
    }
    return section.fields.map(field => {
      // Only show "display name" field if there is more than one stage of the same type.
      if (
        field === 'display_name' &&
        !shouldShowDisplayNameField(this.feature.stages, feStage.stage_type)
      ) {
        return nothing;
      }
      const featureJSONKey = ALL_FIELDS[field].name || field;
      let value = formattedFeature[featureJSONKey];
      // The stage ID is only defined for the form field if it is a stage-specific field.
      let stageId = undefined;
      if (STAGE_SPECIFIC_FIELDS.has(featureJSONKey)) {
        value = getStageValue(feStage, featureJSONKey);
        stageId = feStage.id;
      }

      // Add the field to this component's stage before creating the field component.
      const index = this.fieldValues.length;
      this.fieldValues.push({
        name: featureJSONKey,
        touched: false,
        value,
        stageId,
      });

      return html`
        <chromedash-form-field
          name=${field}
          index=${index}
          value=${value}
          .fieldValues=${this.fieldValues}
          stageId=${feStage.id}
          ?forEnterprise=${formattedFeature.is_enterprise_feature}
          @form-field-update="${this.handleFormFieldUpdate}"
        >
        </chromedash-form-field>
      `;
    });
  }

  renderSections(formattedFeature, stageSections) {
    const formSections = [];
    if (!formattedFeature.is_enterprise_feature) {
      // Add the field to this component's stage before creating the field component.
      const index = this.fieldValues.length;
      this.fieldValues.push({
        name: 'active_stage_id',
        touched: false,
        value: this.isActiveStage,
        implicitValue: this.stage.id,
      });

      // Don't show "set_stage" field for extension stages.
      if (!OT_EXTENSION_STAGE_TYPES.has(this.stage.stage_type)) {
        formSections.push(
          html` <section class="stage_form">
            <chromedash-form-field
              name="set_stage"
              index=${index}
              value=${this.isActiveStage}
              .fieldValues=${this.fieldValues}
              ?disabled=${this.isActiveStage}
              ?forEnterprise=${formattedFeature.is_enterprise_feature}
              @form-field-update="${this.handleFormFieldUpdate}"
            >
            </chromedash-form-field>
          </section>`
        );
      }
    }

    stageSections.forEach(section => {
      if (section.isImplementationSection) {
        formSections.push(
          this.renderImplStatusFormSection(formattedFeature, section)
        );
      } else {
        formSections.push(html`
          <h3>${section.name}</h3>
          <section class="stage_form">
            ${this.renderFields(formattedFeature, section)}
          </section>
        `);
      }
    });

    if (this.stage.extensions) {
      let i = 1;
      for (const extensionStage of this.stage.extensions) {
        for (const section of FLAT_TRIAL_EXTENSION_FIELDS.sections) {
          formSections.push(html`
            <h3>${section.name} ${i}</h3>
            <section class="stage_form">
              ${this.renderFields(formattedFeature, section, extensionStage)}
            </section>
          `);
        }
        i++;
      }
    }

    return formSections;
  }

  // Render the checkbox to set to this implementation stage.
  renderSetImplField(implStatusName, section) {
    // Don't render this checkbox if there's no associated implementation stage name.
    if (!implStatusName) {
      return nothing;
    }

    const alreadyOnThisImplStatus =
      section.implStatusValue === this.feature.browsers.chrome.status.val;
    // Set the checkbox label based on the current implementation status.
    let label = `Set implementation status to: ${implStatusName}`;
    if (alreadyOnThisImplStatus) {
      label = `This feature already has implementation status: ${implStatusName}`;
    }
    const index = this.fieldValues.length;
    this.fieldValues.push({
      name: 'impl_status_chrome',
      touched: false,
      value: alreadyOnThisImplStatus,
      implicitValue: section.implStatusValue,
    });

    return html` <chromedash-form-field
      name="set_impl_status"
      index=${index}
      value=${alreadyOnThisImplStatus}
      .fieldValues=${this.fieldValues}
      checkboxLabel=${label}
      ?disabled=${alreadyOnThisImplStatus}
      @form-field-update="${this.handleFormFieldUpdate}"
    >
    </chromedash-form-field>`;
  }

  renderImplStatusFormSection(formattedFeature, section) {
    const implStatusKey = Object.keys(IMPLEMENTATION_STATUS).find(
      key => IMPLEMENTATION_STATUS[key][0] === section.implStatusValue
    );
    const implStatusName = implStatusKey
      ? IMPLEMENTATION_STATUS[implStatusKey][1]
      : null;

    if (!implStatusName && !this.implStatusFormFields) return nothing;

    return html`
      <h3>${section.name}</h3>
      <section class="stage_form">
        <!-- TODO(jrobbins): When checked, make some milestone fields required. -->
        ${this.renderSetImplField(implStatusName, section)}
        ${this.renderFields(formattedFeature, section)}
      </section>
    `;
  }

  renderForm() {
    const formattedFeature = formatFeatureForEdit(this.feature);
    this.fieldValues.feature = this.feature;

    return html`
      <form name="feature_form">
        <input type="hidden" name="token" />
        <chromedash-form-table ${ref(this.registerHandlers)}>
          ${this.renderSections(
            formattedFeature,
            this.featureFormFields.sections
          )}
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

customElements.define('chromedash-guide-stage-page', ChromedashGuideStagePage);
