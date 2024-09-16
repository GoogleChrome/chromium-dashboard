import {LitElement, css, html, nothing} from 'lit';
import {ref} from 'lit/directives/ref.js';
import {
  formatFeatureChanges,
  getDisabledHelpText,
  showToastMessage,
  setupScrollToHash,
  FieldInfo,
} from './utils.js';
import './chromedash-form-table';
import './chromedash-form-field';
import {
  FLAT_METADATA_FIELDS,
  FLAT_ENTERPRISE_METADATA_FIELDS,
  formatFeatureForEdit,
} from './form-definition';
import {ALL_FIELDS} from './form-field-specs';
import {SHARED_STYLES} from '../css/shared-css.js';
import {FORM_STYLES} from '../css/forms-css.js';
import {customElement, property, state} from 'lit/decorators.js';
import {Feature} from '../js-src/cs-client.js';

@customElement('chromedash-guide-metadata-page')
export class ChromedashGuideMetadataPage extends LitElement {
  static get styles() {
    return [...SHARED_STYLES, ...FORM_STYLES, css``];
  }

  @property({type: Number})
  featureId = 0;
  @property({type: String})
  appTitle = '';
  @state()
  feature!: Feature;
  @state()
  loading = true;
  @state()
  fieldValues: FieldInfo[] & {feature?: Feature} = [];

  connectedCallback() {
    super.connectedCallback();
    this.fetchData();
  }

  fetchData() {
    this.loading = true;
    Promise.resolve(window.csClient.getFeature(this.featureId))
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

  async registerHandlers(el) {
    if (!el) return;

    /* Add the form's event listener after Shoelace event listeners are attached
     * see more at https://github.com/GoogleChrome/chromium-dashboard/issues/2014 */
    await el.updateComplete;
    const hiddenTokenField = this.renderRoot.querySelector(
      'input[name=token]'
    ) as HTMLInputElement;
    hiddenTokenField.form?.addEventListener('submit', event => {
      this.handleFormSubmit(event, hiddenTokenField);
    });

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
        return window.csClient.updateFeature(submitBody);
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

  // Handler to update form field values when a field update event is fired.
  handleFormFieldUpdate(event) {
    const value = event.detail.value;
    // Index represents which form field was updated.
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

  // get a comma-spearated list of field names
  getFormFields() {
    const sections = this.feature.is_enterprise_feature
      ? FLAT_ENTERPRISE_METADATA_FIELDS.sections
      : FLAT_METADATA_FIELDS.sections;
    const fields = sections.reduce<string[]>(
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
    const link = this.loading
      ? nothing
      : html`
          <a href=${this.getNextPage()}>
            <iron-icon icon="chromestatus:arrow-back"></iron-icon>
            Edit feature: ${this.feature.name}
          </a>
        `;
    return html`
      <div id="subheader">
        <h2 id="breadcrumbs">${link}</h2>
      </div>
    `;
  }

  renderFields(formattedFeature, section) {
    return section.fields.map(field => {
      const featureJSONKey = ALL_FIELDS[field].name || field;
      const value = formattedFeature[featureJSONKey];
      // Add the field to this component's stage before creating the field component.
      const index = this.fieldValues.length;
      this.fieldValues.push({name: featureJSONKey, touched: false, value});

      return html`
        <chromedash-form-field
          name=${field}
          index=${index}
          value=${value}
          disabledReason="${getDisabledHelpText(field)}"
          .fieldValues=${this.fieldValues}
          .feature=${formattedFeature}
          ?forEnterprise=${formattedFeature.is_enterprise_feature}
          @form-field-update="${this.handleFormFieldUpdate}"
        >
        </chromedash-form-field>
      `;
    });
  }

  renderSections(formattedFeature, sections) {
    return sections.map(section => {
      return html`
        <h3>${section.name}</h3>
        <section class="stage_form">
          ${this.renderFields(formattedFeature, section)}
        </section>
      `;
    });
  }

  renderForm() {
    const formattedFeature = formatFeatureForEdit(this.feature);
    this.fieldValues.feature = this.feature;

    let sections = FLAT_METADATA_FIELDS.sections;
    if (formattedFeature.is_enterprise_feature) {
      sections = FLAT_ENTERPRISE_METADATA_FIELDS.sections;
    }

    return html`
      <form name="feature_form">
        <input type="hidden" name="token" />
        <chromedash-form-table ${ref(this.registerHandlers)}>
          ${this.renderSections(formattedFeature, sections)}
        </chromedash-form-table>

        <div class="final_buttons">
          <input class="button" type="submit" value="Submit" />
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
