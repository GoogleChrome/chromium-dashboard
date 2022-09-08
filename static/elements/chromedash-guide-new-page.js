import {LitElement, css, html} from 'lit';
import {ref} from 'lit/directives/ref.js';
import './chromedash-form-table';
import './chromedash-form-field';
import {NEW_FEATURE_FORM_FIELDS} from './form-definition';
import {SHARED_STYLES} from '../sass/shared-css.js';
import {FORM_STYLES} from '../sass/forms-css.js';


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
    };
  }

  constructor() {
    super();
    this.userEmail = '';
  }

  connectedCallback() {
    super.connectedCallback();

    // TODO(kevinshen56714): Remove this once SPA index page is set up.
    // Has to include this for now to remove the spinner at _base.html.
    document.body.classList.remove('loading');
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

    return html`
      <section id="stage_form">
        <form name="overview_form" method="POST" action='/guide/new'>
          <input type="hidden" name="token">
          <chromedash-form-table ${ref(this.registerFormSubmitHandler)}>

            <span>
              Please see the
              <a href="https://www.chromium.org/blink/launching-features"
                target="_blank" rel="noopener">Launching features</a>
              page for process instructions.
            </span>

            ${NEW_FEATURE_FORM_FIELDS.map((field) => html`
              <chromedash-form-field
                name=${field}
                value=${newFeatureInitialValues[field]}>
              </chromedash-form-field>
            `)}

            <chromedash-form-field
              name="feature_type_radio_group"
              class="choices">
            </chromedash-form-field>
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
