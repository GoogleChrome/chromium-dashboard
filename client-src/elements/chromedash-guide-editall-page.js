import {LitElement, css, html} from 'lit';
import {ref} from 'lit/directives/ref.js';
import {showToastMessage} from './utils.js';
import './chromedash-form-table';
import './chromedash-form-field';
import {formatFeatureForEdit, FLAT_FORMS, FLAT_FORMS_BY_FEATURE_TYPE} from './form-definition';
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

  // get a comma-spearated list of field names
  getFormFields() {
    let fields = [];
    FLAT_FORMS.map((form) => {
      fields = [...fields, ...form[1]];
    });
    return fields.join();
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

  renderSubheader() {
    return html`
      <div id="subheader">
        <h2 id="breadcrumbs">
          <a href="/guide/edit/${this.featureId}">
            <iron-icon icon="chromestatus:arrow-back"></iron-icon>
            Edit feature: ${this.loading ? 'loading...' : this.feature.name}
          </a>
        </h2>
      </div>
    `;
  }

  renderForm() {
    const formattedFeature = formatFeatureForEdit(this.feature);
    return html`
      <form name="feature_form" method="POST" action="/guide/editall/${this.featureId}">
        <input type="hidden" name="token">
        <input type="hidden" name="form_fields" value=${this.getFormFields(formattedFeature.feature_type)}>
        <chromedash-form-table ${ref(this.registerFormSubmitHandler)}>
          ${FLAT_FORMS_BY_FEATURE_TYPE[formattedFeature.feature_type].map(([sectionName, flatFormFields]) => html`
            <h3>${sectionName}</h3>
            <section class="flat_form">
              ${flatFormFields.map((field) => html`
                <chromedash-form-field
                  name=${field}
                  value=${formattedFeature[field]}>
                </chromedash-form-field>
              `)}
            </section>
          `)}
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
