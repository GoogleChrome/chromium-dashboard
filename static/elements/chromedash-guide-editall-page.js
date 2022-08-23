import {LitElement, css, html} from 'lit';
import {unsafeHTML} from 'lit/directives/unsafe-html.js';
import {showToastMessage} from './utils.js';
import './chromedash-form-table';
import './chromedash-form-field';
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
      flatForms: {type: String},
      loading: {type: Boolean},
    };
  }

  constructor() {
    super();
    this.featureId = 0;
    this.feature = {};
    this.flatForms = '';
    this.loading = true;
  }

  connectedCallback() {
    super.connectedCallback();
    this.fetchData();
  }

  fetchData() {
    this.loading = true;
    window.csClient.getFeature(this.featureId).then((feature) => {
      this.feature = feature;
      this.loading = false;

      // TODO(kevinshen56714): Remove this once SPA index page is set up.
      // Has to include this for now to remove the spinner at _base.html.
      document.body.classList.remove('loading');
    }).catch(() => {
      showToastMessage('Some errors occurred. Please refresh the page or try again later.');
    });
  }

  /* Add the form's event listener after Shoelace event listeners are attached
   * see more at https://github.com/GoogleChrome/chromium-dashboard/issues/2014 */
  firstUpdated() {
    /* TODO(kevinshen56714): remove the timeout once the form fields are all
     * migrated to frontend, we need it now because the unsafeHTML(this.overviewForm)
     * delays the Shoelace event listener attachment */
    setTimeout(() => {
      const hiddenTokenField = this.shadowRoot.querySelector('input[name=token]');
      hiddenTokenField.form.addEventListener('submit', (event) => {
        this.handleFormSubmission(event, hiddenTokenField);
      });
    }, 1000);
  }

  handleFormSubmission(event, hiddenTokenField) {
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
    JSON.parse(this.flatForms).map((form) => {
      fields = [...fields, ...form[2]];
    });
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
        </p>
      </section>
      <h3><sl-skeleton effect="sheen"></sl-skeleton></h3>
      <section id="metadata">
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
    return html`
      <form name="feature_form" method="POST" action="/guide/editall/${this.featureId}">
        <input type="hidden" name="token">
        <input type="hidden" name="form_fields" value=${this.getFormFields()}>
        ${JSON.parse(this.flatForms).map(([sectionName, flatForm]) => html`
          <h3>${sectionName}</h3>
          <section class="flat_form">
            <chromedash-form-table>
              ${unsafeHTML(flatForm)}
            </chromedash-form-table>
          </section>
        `)}

        <section class="final_buttons">
          <chromedash-form-table>
            <chromedash-form-field>
              <span slot="field">
                <input class="button" type="submit" value="Submit">
                <button id="cancel-button" type="reset"
                  @click=${this.handleCancelClick}>Cancel</button>
              </span>
            </chromedash-form-field>
          </chromedash-form-table>
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
