import {LitElement, css, html, nothing} from 'lit';
import {ref} from 'lit/directives/ref.js';
import {
  getStageValue,
  showToastMessage,
  setupScrollToHash,
  shouldShowDisplayNameField} from './utils.js';
import './chromedash-form-table';
import './chromedash-form-field';
import {
  FLAT_TRIAL_EXTENSION_FIELDS,
  formatFeatureForEdit,
  FORMS_BY_STAGE_TYPE} from './form-definition';
import {IMPLEMENTATION_STATUS, STAGE_SPECIFIC_FIELDS} from './form-field-enums';
import {ALL_FIELDS} from './form-field-specs';
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
      intentStage: {type: Number},
      stageName: {type: String},
      featureId: {type: Number},
      feature: {type: Object},
      isActiveStage: {type: Boolean},
      featureFormFields: {type: Array},
      implStatusFormFields: {type: Array},
      implStatusOffered: {type: String},
      loading: {type: Boolean},
      appTitle: {type: String},
      nextPage: {type: String},
    };
  }

  constructor() {
    super();
    this.stageId = 0;
    this.intentStage = 0;
    this.stageName = '';
    this.featureId = 0;
    this.feature = {};
    this.isActiveStage = false;
    this.featureFormFields = [];
    this.implStatusFormFields = [];
    this.implStatusOffered = '';
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
    Promise.all([
      window.csClient.getFeature(this.featureId),
      window.csClient.getStage(this.featureId, this.stageId),
    ]).then(([feature, stage]) => {
      this.feature = feature;
      this.stage = stage;

      if (this.feature.name) {
        document.title = `${this.feature.name} - ${this.appTitle}`;
      }
      if (this.feature.active_stage_id === this.stage.id) {
        this.isActiveStage = true;
      }
      this.featureFormFields = FORMS_BY_STAGE_TYPE[stage.stage_type] || {
        name: '',
        sections: [],
      };
      this.stageName = this.featureFormFields.name;
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

  handleCancelClick() {
    window.location.href = `/guide/edit/${this.featureId}`;
  }

  // get a comma-spearated list of field names
  getFormFields() {
    const fields = this.featureFormFields.sections.reduce(
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

  renderFields(formattedFeature, section, feStage, useStageId=false) {
    if (!feStage) {
      feStage = this.stage;
    }
    return section.fields.map(field => {
      // Only show "display name" field if there is more than one stage of the same type.
      if (field === 'display_name' &&
          !shouldShowDisplayNameField(this.feature.stages, feStage.stage_type)) {
        return nothing;
      }
      const featureJSONKey = ALL_FIELDS[field].name || field;
      let value = formattedFeature[featureJSONKey];
      if (STAGE_SPECIFIC_FIELDS.has(featureJSONKey)) {
        value = getStageValue(feStage, featureJSONKey);
      }
      // stageId is only used here for trial extension stages to be used after submission.
      return html`
      <chromedash-form-field
        name=${field}
        value=${value}
        stageId=${useStageId ? feStage.id : undefined}
        ?forEnterprise=${formattedFeature.is_enterprise_feature}>
      </chromedash-form-field>
    `;
    });
  }

  renderSections(formattedFeature, stageSections) {
    const formSections = [];
    if (!formattedFeature.is_enterprise_feature) {
      formSections.push(
        html`
        <section class="stage_form">
          <chromedash-form-field
            name="set_stage"
            value=${this.isActiveStage}
            ?disabled=${this.isActiveStage}
            ?forEnterprise=${formattedFeature.is_enterprise_feature}>
          </chromedash-form-field>
        </section>`);
    }

    stageSections.forEach(section => {
      if (section.isImplementationSection) {
        formSections.push(this.renderImplStatusFormSection(formattedFeature, section));
      } else {
        formSections.push(html`
          <h3>${section.name}</h3>
          <section class="stage_form">
            ${this.renderFields(formattedFeature, section)}
          </section>
        `);
      }
    });

    if (this.stage.extensions) {
      let i = 1;
      for (const extensionStage of this.stage.extensions) {
        for (const section of FLAT_TRIAL_EXTENSION_FIELDS.sections) {
          formSections.push(html`
            <h3>${section.name} ${i}</h3>
            <section class="stage_form">
              ${this.renderFields(formattedFeature, section, extensionStage, true)}
            </section>
          `);
        }
        i++;
      }
    }

    return formSections;
  }

  renderImplStatusFormSection(formattedFeature, section) {
    const alreadyOnThisImplStatus = (
      section.implStatusValue === this.feature.browsers.chrome.status.val);

    const implStatusKey = Object.keys(IMPLEMENTATION_STATUS).find(
      key => IMPLEMENTATION_STATUS[key][0] === section.implStatusValue);
    const implStatusName = implStatusKey ? IMPLEMENTATION_STATUS[implStatusKey][1]: null;

    if (!implStatusName && !this.implStatusFormFields) return nothing;

    return html`
      <h3>${section.name}</h3>
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
                          value=${section.implStatusValue}>
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

        ${this.renderFields(formattedFeature, section)}
      </section>
    `;
  }

  renderForm() {
    let extensionStageIds = null;
    // If any trial extensions are associated with this stage,
    // their IDs are kept to retrieve during submission to save their values separately.
    if (this.stage.extensions) {
      extensionStageIds = this.stage.extensions.map(feStage => feStage.id);
    }
    const formattedFeature = formatFeatureForEdit(this.feature);
    return html`
      <form name="feature_form" method="POST"
        action="/guide/stage/${this.featureId}/${this.intentStage}/${this.stageId}">
        <input type="hidden" name="token">
        ${extensionStageIds ? html`
        <input type="hidden" name="extension_stage_ids" value="${extensionStageIds}">` : nothing}
        <input type="hidden" name="form_fields" value=${this.getFormFields()} >
        <input type="hidden" name="nextPage" value=${this.getNextPage()} >

        <chromedash-form-table ${ref(this.registerHandlers)}>
          ${this.renderSections(formattedFeature, this.featureFormFields.sections)}
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
