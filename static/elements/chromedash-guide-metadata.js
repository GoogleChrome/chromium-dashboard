import {LitElement, css, html, nothing} from 'lit';
import {unsafeHTML} from 'lit/directives/unsafe-html.js';
import {autolink, showToastMessage} from './utils.js';
import './chromedash-form-table';
import './chromedash-form-field';
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

        #breadcrumbs a {
          text-decoration: none;
          color: inherit;
        }

        sl-skeleton {
          margin-bottom: 1em;
          width: 60%;
        }

        sl-skeleton:nth-of-type(even) {
          width: 50%;
        }

        h3 sl-skeleton {
          width: 30%;
          height: 1.5em;
        }
    `];
  }

  static get properties() {
    return {
      user: {type: Object},
      featureId: {type: Number},
      feature: {type: Object},
      xsrfToken: {type: String},
      overviewForm: {type: String},
      editing: {type: Boolean},
      loading: {type: Boolean},
    };
  }

  constructor() {
    super();
    this.user = {};
    this.featureId = 0;
    this.feature = {};
    this.xsrfToken = '';
    this.overviewForm = '';
    this.editing = false;
    this.loading = true;
  }

  connectedCallback() {
    super.connectedCallback();
    this.fetchData();
  }

  fetchData() {
    this.loading = true;
    Promise.all([
      window.csClient.getPermissions(),
      window.csClient.getFeature(this.featureId),
    ]).then(([user, feature]) => {
      this.user = user;
      this.feature = feature;
      this.loading = false;

      // TODO(kevinshen56714): Remove this once SPA index page is set up.
      // Has to include this for now to remove the spinner at _base.html.
      document.body.classList.remove('loading');
    }).catch(() => {
      showToastMessage('Some errors occurred. Please refresh the page or try again later.');
    });
  }

  handleDeleteFeature() {
    if (!confirm('Delete feature?')) return;

    window.csClient.doDelete(`/features/${this.featureId}`).then((resp) => {
      if (resp.message === 'Done') {
        location.href = '/features';
      }
    });
  }

  renderSkeletons() {
    return html`
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

  renderReadOnlyTable() {
    return html`
      <div id="metadata-readonly">
        <div style="margin-bottom: 1em">
          <div id="metadata-buttons">
            <a id="open-metadata" @click=${() => this.editing = true}>Edit</a>
            ${this.user.is_admin ? html`
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

            <tr>
              <th>Category</th>
              <td>${this.feature.category}</td>
            </tr>

            <tr>
              <th>Feature type</th>
              <td>${this.feature.feature_type}</td>
            </tr>

            <tr>
              <th>Process stage</th>
              <td>${this.feature.intent_stage}</td>
            </tr>

            ${this.feature.tags ? html`
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
            <tr>
              <th>Implementation status</th>
              <td>${this.feature.browsers.chrome.status.text}</td>
            </tr>

            <tr>
              <th>Blink components</th>
              <td>${this.feature.browsers.chrome.blink_components.join(', ')}</td>
            </tr>

            <tr>
              <th>Tracking bug</th>
              <td>
                ${this.feature.browsers.chrome.bug ? html`
                  <a href="${this.feature.browsers.chrome.bug}">${this.feature.browsers.chrome.bug}</a>
                `: html`
                  None
                `}
              </td>
            </tr>

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
          </table>
        </div>
      </div>
    `;
  }

  renderEditForm() {
    return html`
      <div id="metadata-editing">
        <form name="overview_form" method="POST" action="/guide/stage/${this.featureId}/0">
          <input type="hidden" name="token" value=${this.xsrfToken}>

          <chromedash-form-table>
            ${unsafeHTML(this.overviewForm)}

            <chromedash-form-field>
              <span slot="field">
                <input class="button" type="submit" value="Submit">
                <button id="close-metadata" @click=${() => this.editing = false} type="reset">Cancel</button>
              </span>
            </chromedash-form-field>
          </chromedash-form-table>
        </form>
      </div>
    `;
  }

  render() {
    return html`
      ${this.loading ?
        this.renderSkeletons() :
        html`
          <section id="metadata">
            ${this.editing ? this.renderEditForm() : this.renderReadOnlyTable()}
          </section>
        `}
    `;
  }
}

customElements.define('chromedash-guide-metadata', ChromedashGuideMetadata);
