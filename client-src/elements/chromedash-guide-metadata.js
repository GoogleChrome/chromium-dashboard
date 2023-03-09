import {LitElement, css, html, nothing} from 'lit';
import {ref} from 'lit/directives/ref.js';
import {autolink, flattenSections, renderHTMLIf} from './utils.js';
import './chromedash-form-table';
import './chromedash-form-field';
import {ENTERPRISE_FEATURE_CATEGORIES_DISPLAYNAME} from './form-field-enums';
import {
  formatFeatureForEdit,
  FLAT_ENTERPRISE_METADATA_FIELDS,
  FLAT_METADATA_FIELDS} from './form-definition';
import {SHARED_STYLES} from '../sass/shared-css.js';
import {FORM_STYLES} from '../sass/forms-css.js';


export class ChromedashGuideMetadata extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      ...FORM_STYLES,
      css`
        #metadata-buttons {
          float: right;
          margin-left: var(--content-padding);
        }

        #metadata-buttons div {
          margin-top: var(--content-padding);
        }

        .flex-cols {
          display: flex;
          flex-flow: row wrap;
          align-items: flex-start;
          align-content: space-between;
        }

        table.property-sheet {
          margin-right: var(--content-padding);
          margin-bottom: var(--content-padding);
        }

        table.property-sheet tr:nth-of-type(odd) {
          background: var(--table-alternate-background);
        }

        table.property-sheet th, #metadata-readonly td {
          padding: var(--content-padding-half) 30px var(--content-padding-half) var(--content-padding-half);
        }

        table.property-sheet th {
          white-space: nowrap;
        }
    `];
  }

  static get properties() {
    return {
      feature: {type: Object},
      isAdmin: {type: Boolean},
      editing: {type: Boolean},
    };
  }

  constructor() {
    super();
    this.feature = {};
    this.isAdmin = false;
    this.editing = false;
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

  handleDeleteFeature() {
    if (!confirm('Delete feature?')) return;

    window.csClient.doDelete(`/features/${this.feature.id}`).then((resp) => {
      if (resp.message === 'Done') {
        location.href = '/features';
      }
    });
  }

  renderReadOnlyTable() {
    return html`
      <div id="metadata-readonly">
        <div style="margin-bottom: 1em">
          <div id="metadata-buttons">
            <a id="open-metadata" @click=${() => this.editing = true}>Edit</a>
            ${this.isAdmin ? html`
              <div>
                <a id="delete-feature" class="delete-button"
                  @click=${this.handleDeleteFeature}>Delete</a>
              </div>
            `: nothing}
          </div>
          <div>${autolink(this.feature.summary)}</div>
        </div>

        ${this.feature.unlisted ? html`
          <div style="padding: 8px">
            This feature is only shown in the feature list
            to users with access to edit this feature.
          </div>
        `: nothing}

        <div class="flex-cols">
          <table class="property-sheet">
            <tr>
              <th>Owners</th>
              <td>
                ${this.feature.browsers.chrome.owners.map((owner) => html`
                  <a href="mailto:${owner}">${owner}</a>
                `)}
              </td>
            </tr>

            ${!this.feature.is_enterprise_feature ? html`
              <tr>
                <th>CC</th>
                <td>
                  ${this.feature.cc_recipients ?
                    this.feature.cc_recipients.map((ccRecipient)=> html`
                    <a href="mailto:${ccRecipient}">${ccRecipient}</a>
                    `): html`
                    None
                  `}
                </td>
              </tr>` :
            nothing}

            ${!this.feature.is_enterprise_feature ? html`
              <tr>
                <th>DevRel</th>
                <td>
                  ${this.feature.browsers.chrome.devrel ?
                    this.feature.browsers.chrome.devrel.map((dev) => html`
                    <a href="mailto:${dev}">${dev}</a>
                  `): html`
                  None
                `}
                </td>
              </tr>` :
            nothing}

            ${this.feature.is_enterprise_feature ? html`
              <tr>
                <th>Editors</th>
                <td>
                  ${this.feature.editors ?
                    this.feature.editors.map((editor)=> html`
                    <a href="mailto:${editor}">${editor}</a>
                    `): html`
                    None
                  `}
                </td>
              </tr>` :
            nothing}

            ${!this.feature.is_enterprise_feature ? html`
              <tr>
                <th>Category</th>
                <td>${this.feature.category}</td>
              </tr>` :
            nothing}
            ${this.feature.is_enterprise_feature ? html`
              <tr>
                <th>Categories</th>
                <td>${this.feature.enterprise_feature_categories.map(id =>
              ENTERPRISE_FEATURE_CATEGORIES_DISPLAYNAME[id]) || 'None'}</td>
              </tr>` :
            nothing}

            <tr>
              <th>Feature type</th>
              <td>${this.feature.feature_type}</td>
            </tr>

            ${renderHTMLIf(!this.feature.is_enterprise_feature, html`
              <tr>
                <th>Process stage</th>
                <td>${this.feature.intent_stage}</td>
              </tr>`,
            )}

            ${this.feature.tags && !this.feature.is_enterprise_feature ? html`
              <tr>
                <th>Search tags</th>
                <td>
                  ${this.feature.tags.map((tag) => html`
                    <a href="/features#tags:${tag}">${tag}</a><span
                      class="conditional-comma">, </span>
                  `)}
                </td>
              </tr>
            `: nothing}
          </table>


          <table class="property-sheet">
          ${!this.feature.is_enterprise_feature ? html`
              <tr>
                <th>Implementation status</th>
                <td>${this.feature.browsers.chrome.status.text}</td>
              </tr>` :
            nothing}

            <tr>
              <th>Blink components</th>
              <td>${this.feature.browsers.chrome.blink_components.join(', ')}</td>
            </tr>

            ${!this.feature.is_enterprise_feature ? html`
              <tr>
                <th>Tracking bug</th>
                <td>
                  ${this.feature.browsers.chrome.bug ? html`
                    <a href="${this.feature.browsers.chrome.bug}">${this.feature.browsers.chrome.bug}</a>
                  `: html`
                    None
                  `}
                </td>
              </tr>` :
              nothing}

            <tr>
              <th>Launch bug</th>
              <td>
                ${this.feature.launch_bug_url ? html`
                  <a href="${this.feature.launch_bug_url}">${this.feature.launch_bug_url}</a>
                `: html`
                  None
                `}
              </td>
            </tr>

            <tr>
              <th>Breaking change</th>
              <td>${this.feature.breaking_change}</td>
            </tr>
          </table>
        </div>
      </div>
    `;
  }

  renderEditForm() {
    const formattedFeature = formatFeatureForEdit(this.feature);
    const metadataFields = flattenSections(this.feature.is_enterprise_feature ?
      FLAT_ENTERPRISE_METADATA_FIELDS :
      FLAT_METADATA_FIELDS);
    return html`
      <div id="metadata-editing">
        <form name="overview_form" method="POST" action="/guide/stage/${this.feature.id}/0">
          <input type="hidden" name="token">
          <input type="hidden" name="form_fields"
             value="${metadataFields.join(',')}">

          <chromedash-form-table ${ref(this.registerFormSubmitHandler)}>
            ${metadataFields.map((field) => html`
              <chromedash-form-field
                name=${field}
                value=${formattedFeature[field]}>
              </chromedash-form-field>
            `)}
          </chromedash-form-table>

          <section class="final_buttons">
            <input class="button" type="submit" value="Submit">
            <button id="close-metadata" type="reset"
              @click=${() => this.editing = false}>Cancel</button>
          </section>
        </form>
      </div>
    `;
  }

  render() {
    return html`
      <section id="metadata">
        ${this.editing ? this.renderEditForm() : this.renderReadOnlyTable()}
      </section>
    `;
  }
}

customElements.define('chromedash-guide-metadata', ChromedashGuideMetadata);
