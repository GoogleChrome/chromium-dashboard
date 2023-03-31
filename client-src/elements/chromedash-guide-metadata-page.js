import {LitElement, css, html} from 'lit';
import {ref} from 'lit/directives/ref.js';
import {showToastMessage, setupScrollToHash} from './utils.js';
import './chromedash-form-table';
import './chromedash-form-field';
import {
  FLAT_METADATA_FIELDS,
  FLAT_ENTERPRISE_METADATA_FIELDS,
  formatFeatureForEdit} from './form-definition';
import {ALL_FIELDS} from './form-field-specs';
import {SHARED_STYLES} from '../sass/shared-css.js';
import {FORM_STYLES} from '../sass/forms-css.js';


export class ChromedashGuideMetadataPage extends LitElement {
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
    Promise.resolve(window.csClient.getFeature(this.featureId))
      .then((feature) => {
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

  async registerHandlers(el) {
    if (!el) return;

    /* Add the form's event listener after Shoelace event listeners are attached
    * see more at https://github.com/GoogleChrome/chromium-dashboard/issues/2014 */
    await el.updateComplete;
    const hiddenTokenField = this.shadowRoot.querySelector('input[name=token]');
    hiddenTokenField.form.addEventListener('submit', (event) => {
      this.handleFormSubmit(event, hiddenTokenField);
    });

    this.addMiscEventListeners();
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

  addMiscEventListeners() {
    const fields = this.shadowRoot.querySelectorAll('input, textarea');
    for (let i = 0; i < fields.length; ++i) {
      fields[i].addEventListener('input', (e) => {
        e.target.classList.add('interacted');
      });
    }
  }

  handleCancelClick() {
    window.location.href = `/guide/edit/${this.featureId}`;
  }

  // get a comma-spearated list of field names
  getFormFields() {
    const sections = this.feature.is_enterprise_feature ?
      FLAT_ENTERPRISE_METADATA_FIELDS.sections :
      FLAT_METADATA_FIELDS.sections;
    const fields = sections.reduce(
      (combined, section) => [...combined, ...section.fields], []);
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
    return this.nextPage || `/guide/edit/${this.featureId}`;
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

  renderFields(formattedFeature, section) {
    return section.fields.map(field => {
      const featureJSONKey = ALL_FIELDS[field].name || field;
      return html`
      <chromedash-form-field
        name=${field}
        value=${formattedFeature[featureJSONKey]}
        ?forEnterprise=${formattedFeature.is_enterprise_feature}>
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
    return html`
      <form name="feature_form" method="POST"
        action="/guide/edit/${this.featureId}">
        <input type="hidden" name="token">
        <input type="hidden" name="form_fields" value=${this.getFormFields()} >
        <input type="hidden" name="nextPage" value=${this.getNextPage()} >

        <chromedash-form-table ${ref(this.registerHandlers)}>
          ${this.renderSections(formattedFeature, FLAT_METADATA_FIELDS.sections)}
        </chromedash-form-table>

        <div class="final_buttons">
          <input class="button" type="submit" value="Submit">
          <button id="cancel-button" type="reset"
            @click=${this.handleCancelClick}>Cancel</button>
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

customElements.define('chromedash-guide-metadata-page', ChromedashGuideMetadataPage);
