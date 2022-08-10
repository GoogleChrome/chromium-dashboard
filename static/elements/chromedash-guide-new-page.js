import {LitElement, css, html} from 'lit';
import {unsafeHTML} from 'lit/directives/unsafe-html.js';
import './chromedash-form-table';
import './chromedash-form-field';
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
      currentPath: {type: String},
      xsrfToken: {type: String},
      overviewForm: {type: String},
    };
  }

  constructor() {
    super();
    this.currentPath = '';
    this.xsrfToken = '';
    this.overviewForm = '';
  }

  connectedCallback() {
    super.connectedCallback();

    // TODO(kevinshen56714): Remove this once SPA index page is set up.
    // Has to include this for now to remove the spinner at _base.html.
    document.body.classList.remove('loading');
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
    return html`
      <section id="stage_form">
        <form name="overview_form" method="POST" action=${this.currentPath}>
          <input type="hidden" name="token" value=${this.xsrfToken}>
          <chromedash-form-table>

            <chromedash-form-field>
              <span slot="help">
                Please see the
                <a href="https://www.chromium.org/blink/launching-features"
                  target="_blank" rel="noopener">Launching features</a>
                page for process instructions.
              </span>
            </chromedash-form-field>

            ${unsafeHTML(this.overviewForm)}

            <chromedash-form-field 
              name="feature_type"
              class="choices"
              field=${`
                <label for="id_feature_type_0">
                  <input id="id_feature_type_0" name="feature_type" type="radio"
                        value="0" required>
                  New feature incubation
                </label>

                <p>When building new features, we follow a
                  process that emphasizes engagement with the WICG and other
                  stakeholders early.</p>

                <label for="id_feature_type_1">
                  <input id="id_feature_type_1" name="feature_type" type="radio"
                        value="1" required>
                  Existing feature implementation
                </label>

                <p>If there is already an agreed specification, work may
                  quickly start on implementation and origin trials.</p>

                <label for="id_feature_type_2">
                  <input id="id_feature_type_2" name="feature_type" type="radio"
                        value="2" required>
                  Web developer-facing change to existing code
                </label>

                <p>Sometimes a change to a shipped feature requires an additional
                  feature entry.  This type of feature entry can be referenced
                  from a PSA immediately.</p>

                <label for="id_feature_type_3">
                  <input id="id_feature_type_3" name="feature_type" type="radio"
                        value="3" required>
                  Feature deprecation
                </label>

                <p>Deprecate and remove an old feature.</p>`}>
            </chromedash-form-field>

            <chromedash-form-field>
              <span slot="field">
                <input type="submit" class="primary" value="Submit">
              </span>
            </chromedash-form-field>

          </chromedash-form-table>
        </form>
      </section>
    `;
  }

  render() {
    // TODO: Create precomiled forms css file and import it instead of inlining it here
    return html`
      <link rel="stylesheet" href="/static/css/forms.css">
      ${this.renderSubHeader()}
      ${this.renderForm()}
    `;
  }
}

customElements.define('chromedash-guide-new-page', ChromedashGuideNewPage);
