import {LitElement, css, html, nothing} from 'lit';
import {ref} from 'lit/directives/ref.js';
import './chromedash-form-table';
import './chromedash-form-field';
import {
  NEW_FEATURE_FORM_FIELDS,
  ENTERPRISE_NEW_FEATURE_FORM_FIELDS,
} from './form-definition';
import {SHARED_STYLES} from '../sass/shared-css.js';
import {FORM_STYLES} from '../sass/forms-css.js';
import {setupScrollToHash} from './utils';


export class ChromedashGuideNewPage extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      ...FORM_STYLES,
      // The following style is a workaround to better support radio buttons
      // without sl-radio which does not yet do validation.
      // We do depend on sl-focus-ring being defined.
      css`
        table td label input[type=radio]:focus {
          box-shadow: 0 0 0 var(--sl-focus-ring-width) var(--sl-input-focus-ring-color);
        }

        .choices label {
          font-weight: bold;
        }
        .choices div {
          margin-top: 1em;
        }
        .choices p {
          margin: .5em 1.5em 1em;
        }
      `];
  }

  static get properties() {
    return {
      userEmail: {type: String},
      isEnterpriseFeature: {type: Boolean},
    };
  }

  constructor() {
    super();
    this.userEmail = '';
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

  renderSubHeader() {
    return html`
      <div id="subheader" style="display:block">
        <span style="float:right; margin-right: 2em">
        <a href="https://github.com/GoogleChrome/chromium-dashboard/issues/new?labels=Feedback&amp;template=process-and-guide-ux-feedback.md"
          target="_blank" rel="noopener">Process and UI feedback</a></span>
        <h2>Add a feature</h2>
      </div>
    `;
  }

  renderForm() {
    const newFeatureInitialValues = {owner: this.userEmail};
    const formFields = this.isEnterpriseFeature ?
      ENTERPRISE_NEW_FEATURE_FORM_FIELDS :
      NEW_FEATURE_FORM_FIELDS;
    const postAction = this.isEnterpriseFeature ? '/guide/enterprise/new' : '/guide/new';

    return html`
      <section id="stage_form">
        <form name="overview_form" method="POST" action=${postAction}>
          <input type="hidden" name="token">
          <chromedash-form-table ${ref(this.registerHandlers)}>

            <span>
              Please see the
              <a href="https://www.chromium.org/blink/launching-features"
                target="_blank" rel="noopener">Launching features</a>
              page for process instructions.
            </span>

            ${formFields.map((field) => html`
              <chromedash-form-field
                name=${field}
                value=${newFeatureInitialValues[field]}>
              </chromedash-form-field>
            `)}

            ${!this.isEnterpriseFeature ? html`
              <chromedash-form-field
                name="feature_type_radio_group"
                class="choices">
              </chromedash-form-field>` :
            nothing}
          </chromedash-form-table>
          <input type="submit" class="primary" value="Submit">
        </form>
      </section>
    `;
  }

  render() {
    return html`
      ${this.renderSubHeader()}
      ${this.renderForm()}
    `;
  }
}

customElements.define('chromedash-guide-new-page', ChromedashGuideNewPage);
