import {LitElement, css, html, nothing} from 'lit';
import {unsafeHTML} from 'lit/directives/unsafe-html.js';
import {showToastMessage} from './utils.js';
import './chromedash-form-table';
import './chromedash-form-field';
import {SHARED_STYLES} from '../sass/shared-css.js';
import {FORM_STYLES} from '../sass/forms-css.js';


export class ChromedashGuideStagePage extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      ...FORM_STYLES,
      css`
      `];
  }

  static get properties() {
    return {
      stageId: {type: Number},
      stageName: {type: String},
      featureId: {type: Number},
      feature: {type: Object},
      featureForm: {type: String},
      implStatusForm: {type: String},
      implStatusName: {type: String},
      implStatusOffered: {type: String},
      loading: {type: Boolean},
    };
  }

  constructor() {
    super();
    this.stageId = 0;
    this.stageName = '';
    this.featureId = 0;
    this.feature = {};
    this.featureForm = '';
    this.implStatusForm = '';
    this.implStatusName = '';
    this.implStatusOffered = '';
    this.loading = true;
  }

  connectedCallback() {
    super.connectedCallback();
    this.fetchData();
  }

  fetchData() {
    this.loading = true;
    Promise.all([
      window.csClient.getFeature(this.featureId),
      window.csClient.getFeatureProcess(this.featureId),
    ]).then(([feature, process]) => {
      this.feature = feature;
      process.stages.map(stage => {
        if (stage.outgoing_stage === this.stageId) {
          this.stageName = stage.name;
        }
      });
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
      this.addMiscEventListeners();
      this.scrollToPosition();
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

  addMiscEventListeners() {
    const fields = this.shadowRoot.querySelectorAll('input, textarea');
    for (let i = 0; i < fields.length; ++i) {
      fields[i].addEventListener('input', (e) => {
        e.target.classList.add('interacted');
      });
    }

    // Allow editing if there was already a value specified in this
    // deprecated field.
    const timelineField = this.shadowRoot.querySelector('#id_experiment_timeline');
    if (timelineField && timelineField.value) {
      timelineField.disabled = '';
    }

    // Copy field SRC to DST if SRC is edited and DST was empty and
    // has not been edited.
    const COPY_ON_EDIT = [
      ['dt_milestone_desktop_start', 'dt_milestone_android_start'],
      ['dt_milestone_desktop_start', 'dt_milestone_webview_start'],
      // Don't autofill dt_milestone_ios_start because it is rare.
      ['ot_milestone_desktop_start', 'ot_milestone_android_start'],
      ['ot_milestone_desktop_end', 'ot_milestone_android_end'],
      ['ot_milestone_desktop_start', 'ot_milestone_webview_start'],
      ['ot_milestone_desktop_end', 'ot_milestone_webview_end'],
    ];

    for (const [srcId, dstId] of COPY_ON_EDIT) {
      const srcEl = this.shadowRoot.querySelector('#id_' + srcId);
      const dstEl = this.shadowRoot.querySelector('#id_' + dstId);
      if (srcEl && dstEl && srcEl.value == dstEl.value) {
        srcEl.addEventListener('input', () => {
          if (!dstEl.classList.contains('interacted')) {
            dstEl.value = srcEl.value;
            dstEl.classList.add('copied');
          }
        });
      }
    }
  }

  scrollToPosition() {
    if (location.hash) {
      const hash = decodeURIComponent(location.hash);
      if (hash) {
        const el = this.shadowRoot.querySelector(hash);
        el.scrollIntoView(true, {behavior: 'smooth'});
        el.focus();
      }
    }
  }

  handleCancelClick() {
    window.location.href = `/guide/edit/${this.featureId}`;
  }

  // get a comma-spearated list of field names
  getFormFields() {
    let fields = JSON.parse(this.featureForm)[1];

    // if there is a implStatusForm. add its field names to the list
    if (this.implStatusForm) {
      fields = [...fields, ...JSON.parse(this.implStatusForm)[1]];
    }
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

  renderSubheader() {
    return html`
      <div id="subheader">
        <h2 id="breadcrumbs">
          <a href="/guide/edit/${this.featureId}">
            <iron-icon icon="chromestatus:arrow-back"></iron-icon>
            Edit feature: ${this.feature.name}
          </a>
        </h2>
      </div>
      <h3>${this.stageName}</h3>
    `;
  }

  renderFeatureFormSection() {
    const alreadyOnThisStage = this.stageId === this.feature.intent_stage_int;
    return html`
      <section class="stage_form">
        <chromedash-form-table>
          ${unsafeHTML(JSON.parse(this.featureForm)[0])}

          <chromedash-form-field
            name="set_stage"
            stage=${this.stageName}
            value=${alreadyOnThisStage}
            ?disabled=${alreadyOnThisStage}>
          </chromedash-form-field>

        </chromedash-form-table>
      </section>
    `;
  }

  renderImplStatusFormSection() {
    const alreadyOnThisImplStatus = this.implStatusOffered === this.feature.impl_status_chrome;
    return html`
      <h3>Implementation in Chromium</h3>
      <section class="stage_form">
        <chromedash-form-table>
          ${this.implStatusName ? html`
            <chromedash-form-field>
              <span slot="label">Implementation status:</span>

              ${alreadyOnThisImplStatus ?
                html`
                  <span slot="help">
                      This feature already has implementation status:
                      <b>${this.implStatusName}</b>.
                    </td>
                  </span>
                ` :
                // TODO(jrobbins): When checked, make some milestone fields required.
                html`
                  <span slot="field">
                    <input type="hidden" name="impl_status_offered"
                            value=${this.implStatusOffered}>
                    <input type="checkbox" name="set_impl_status"
                            id="set_impl_status">
                    <label for="set_impl_status">
                      Set implementation status to: <b>${this.implStatusName}</b>
                    </label>
                  </span>
                  <span slot="help">
                      Check this box to update the implementation
                      status of this feature in Chromium.
                  </span>
                `}
            </chromedash-form-field>
          `: nothing}

          ${unsafeHTML(JSON.parse(this.implStatusForm)[0])}

        </chromedash-form-table>
      </section>
    `;
  }

  renderForm() {
    return html`
      <form name="feature_form" method="POST"
        action="/guide/stage/${this.featureId}/${this.stageId}">
        <input type="hidden" name="token">
        <input type="hidden" name="form_fields" value=${this.getFormFields()} >

        ${this.renderFeatureFormSection()}

        ${this.implStatusName || this.implStatusForm ?
          this.renderImplStatusFormSection() : nothing}

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

customElements.define('chromedash-guide-stage-page', ChromedashGuideStagePage);
