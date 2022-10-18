import {LitElement, css, html, nothing} from 'lit';
import {ref} from 'lit/directives/ref.js';
import {showToastMessage} from './utils.js';
import './chromedash-form-table';
import './chromedash-form-field';
import {formatFeatureForEdit, STAGE_FORMS, IMPL_STATUS_FORMS} from './form-definition';
import {IMPLEMENTATION_STATUS} from './form-field-enums';
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
      featureFormFields: {type: Array},
      implStatusFormFields: {type: Array},
      implStatusOffered: {type: String},
      loading: {type: Boolean},
      appTitle: {type: String},
    };
  }

  constructor() {
    super();
    this.stageId = 0;
    this.stageName = '';
    this.featureId = 0;
    this.feature = {};
    this.featureFormFields = [];
    this.implStatusFormFields = [];
    this.implStatusOffered = '';
    this.loading = true;
    this.appTitle = '';
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
      if (this.feature.name) {
        document.title = `${this.feature.name} - ${this.appTitle}`;
      }
      process.stages.map(stage => {
        if (stage.outgoing_stage === this.stageId) {
          this.stageName = stage.name;
        }
      });
      this.featureFormFields = STAGE_FORMS[this.feature.feature_type_int][this.stageId];
      [this.implStatusOffered, this.implStatusFormFields] =
        IMPL_STATUS_FORMS[this.stageId] || [null, null];

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
    this.scrollToPosition();
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
      }
    }
  }

  handleCancelClick() {
    window.location.href = `/guide/edit/${this.featureId}`;
  }

  // get a comma-spearated list of field names
  getFormFields() {
    const fields = this.implStatusFormFields ?
      [...this.featureFormFields, ...this.implStatusFormFields] : this.featureFormFields;
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

  renderFeatureFormSection(formattedFeature) {
    const alreadyOnThisStage = this.stageId === this.feature.intent_stage_int;
    return html`
      <section class="stage_form">
        ${this.featureFormFields.map((field) => html`
          <chromedash-form-field
            name=${field}
            value=${formattedFeature[field]}>
          </chromedash-form-field>
        `)}
        <chromedash-form-field
          name="set_stage"
          value=${alreadyOnThisStage}
          ?disabled=${alreadyOnThisStage}>
        </chromedash-form-field>
      </section>
    `;
  }

  renderImplStatusFormSection(formattedFeature) {
    const alreadyOnThisImplStatus = (
      this.implStatusOffered == this.feature.browsers.chrome.status.val);
    const implStatusKey = Object.keys(IMPLEMENTATION_STATUS).find(
      key => IMPLEMENTATION_STATUS[key][0] === this.implStatusOffered);
    const implStatusName = implStatusKey ? IMPLEMENTATION_STATUS[implStatusKey][1]: null;

    if (!implStatusName && !this.implStatusFormFields) return nothing;

    return html`
      <h3>Implementation in Chromium</h3>
      <section class="stage_form">
        ${implStatusName ? html`
          <tr>
            <td colspan="2"><b>Implementation status:</b></span></td>
          </tr>
          <tr>
            ${alreadyOnThisImplStatus ?
              html`
                <td style="padding: 6px 10px;">
                    This feature already has implementation status:
                    <b>${implStatusName}</b>.
                </td>
              ` :
              // TODO(jrobbins): When checked, make some milestone fields required.
              html`
                <td style="padding: 6px 10px;">
                  <input type="hidden" name="impl_status_offered"
                          value=${this.implStatusOffered}>
                  <sl-checkbox name="set_impl_status"
                          id="set_impl_status"
                          size="small">
                    Set implementation status to: <b>${implStatusName}</b>
                  </sl-checkbox>
                </td>
                <td style="padding: 6px 10px;">
                  <span class="helptext"
                        style="display: block; font-size: small; margin-top: 2px;">
                    Check this box to update the implementation
                    status of this feature in Chromium.
                  </span>
                </td>
              `}
          </tr>
        `: nothing}

        ${this.implStatusFormFields.map((field) => html`
          <chromedash-form-field
            name=${field}
            value=${formattedFeature[field]}>
          </chromedash-form-field>
        `)}
      </section>
    `;
  }

  renderForm() {
    const formattedFeature = formatFeatureForEdit(this.feature);
    return html`
      <form name="feature_form" method="POST"
        action="/guide/stage/${this.featureId}/${this.stageId}">
        <input type="hidden" name="token">
        <input type="hidden" name="form_fields" value=${this.getFormFields()} >

        <chromedash-form-table ${ref(this.registerHandlers)}>
          ${this.renderFeatureFormSection(formattedFeature)}
          ${this.renderImplStatusFormSection(formattedFeature)}
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

customElements.define('chromedash-guide-stage-page', ChromedashGuideStagePage);
