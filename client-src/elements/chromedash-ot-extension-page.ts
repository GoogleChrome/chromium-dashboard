import {LitElement, css, html} from 'lit';
import {property, state} from 'lit/decorators.js';
import {ref} from 'lit/directives/ref.js';
import {FORM_STYLES} from '../css/forms-css.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {Feature, StageDict} from '../js-src/cs-client.js';
import './chromedash-form-field.js';
import './chromedash-form-table.js';
import {dialogTypes, openInfoDialog} from './chromedash-ot-prereqs-dialog';
import {ORIGIN_TRIAL_EXTENSION_FIELDS} from './form-definition.js';
import {OT_EXTENSION_STAGE_MAPPING} from './form-field-enums.js';
import {ALL_FIELDS} from './form-field-specs';
import {
  FieldInfo,
  extensionMilestoneIsValid,
  formatFeatureChanges,
  setupScrollToHash,
  showToastMessage,
} from './utils.js';

export class ChromedashOTExtensionPage extends LitElement {
  static get styles() {
    return [...SHARED_STYLES, ...FORM_STYLES, css``];
  }

  static get properties() {
    return {
      stageId: {type: Number},
      featureId: {type: Number},
      userEmail: {type: String},
      feature: {type: Object},
      loading: {type: Boolean},
      appTitle: {type: String},
      fieldValues: {type: Array},
      // The most recent Chrome milestone.
      currentMilestone: {type: Number},
      // A reference of end dates for an origin trial based on the milestone.
      // (key=milestone, value=date origin trial will end)
      endMilestoneDateValues: {type: Object},
    };
  }

  @property({type: Number})
  stageId = 0;
  @property({type: Number})
  featureId = 0;
  @property({type: String})
  userEmail!: string;
  @property({type: String})
  appTitle = '';
  @state()
  feature!: Feature;
  @state()
  loading = true;
  @state()
  fieldValues: FieldInfo[] & {feature?: Feature} = [];
  @state()
  currentMilestone = 123;
  @state()
  endMilestoneDateValues: Record<string, string> = {};
  @state()
  stage!: StageDict;

  connectedCallback() {
    super.connectedCallback();
    this.fetchData();
  }

  // Handler to update form values when a field update event is fired.
  handleFormFieldUpdate(event) {
    const value = event.detail.value;
    // Index represents which form was updated.
    const index = event.detail.index;
    if (index >= this.fieldValues.length) {
      throw new Error('Out of bounds index when updating field values.');
    }
    // The field has been updated, so it is considered touched.
    this.fieldValues[index].touched = true;
    this.fieldValues[index].value = value;

    if (
      this.fieldValues[index].name == 'ot_extension__milestone_desktop_last'
    ) {
      this.getChromeScheduleDate(event.detail.value);
    }
  }

  openMilestoneExplanationDialog() {
    openInfoDialog(dialogTypes.END_MILESTONE_EXPLANATION);
  }

  // Display the date the origin trial will end to the user after a milestone is chosen.
  updateMilestoneDate(milestone) {
    const milestoneDiv: HTMLElement | null =
      this.renderRoot.querySelector('#milestone-date');
    const milestoneTextEl: HTMLTextAreaElement | null =
      this.renderRoot.querySelector('#milestone-date-text');
    const date = new Date(this.endMilestoneDateValues[milestone]);
    if (!milestoneDiv || !milestoneTextEl) {
      return;
    }
    milestoneDiv.style.display = 'block';
    milestoneTextEl.innerHTML = `For milestone ${milestone}, this trial will end on ${date.toLocaleDateString()}.`;
  }

  // Obtain the date the origin trial will end based on the given milestone.
  async getChromeScheduleDate(milestone) {
    const milestoneDiv: HTMLElement | null =
      this.renderRoot.querySelector('#milestone-date');
    if (!milestoneDiv) {
      return;
    }
    milestoneDiv.style.display = 'none';
    // Don't try to obtain a date if the milestone is not valid.
    if (!extensionMilestoneIsValid(milestone, this.currentMilestone)) {
      return;
    }
    if (!(milestone in this.endMilestoneDateValues)) {
      // Origin trials  will end on the late stable date of (milestone + 2).
      const milestonePlusTwo = parseInt(milestone) + 2;
      const resp = await fetch(
        `https://chromiumdash.appspot.com/fetch_milestone_schedule?mstone=${milestonePlusTwo}`
      );
      const respJson = await resp.json();
      // Keep a reference of milestone dates to avoid extra requests.
      this.endMilestoneDateValues[milestone] =
        respJson.mstones[0].late_stable_date;
    }
    this.updateMilestoneDate(milestone);
  }

  fetchData() {
    this.loading = true;
    Promise.all([
      window.csClient.getFeature(this.featureId),
      window.csClient.getStage(this.featureId, this.stageId),
    ])
      .then(([feature, stage]) => {
        this.feature = feature;
        this.stage = stage;

        if (this.feature.name) {
          document.title = `${this.feature.name} - ${this.appTitle}`;
        }
        this.loading = false;
      })
      .catch(() => {
        showToastMessage(
          'Some errors occurred. Please refresh the page or try again later.'
        );
      });

    // Fetch the current milestone so that we know if a milestone in the past is given.
    fetch('https://chromiumdash.appspot.com/fetch_milestone_schedule')
      .then(resp => resp.json())
      .then(scheduleInfo => {
        this.currentMilestone = parseInt(scheduleInfo.mstones[0].mstone);
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
    const submitButton: HTMLInputElement | null = this.renderRoot.querySelector(
      'input[id=submit-button]'
    );
    submitButton?.form?.addEventListener('submit', event => {
      this.handleFormSubmit(event);
    });

    setupScrollToHash(this);
  }

  handleFormSubmit(e) {
    e.preventDefault();
    const featureSubmitBody = formatFeatureChanges(
      this.fieldValues,
      this.featureId
    );
    // We only need the single stage changes.
    const stageSubmitBody = featureSubmitBody.stages[0];

    let newStageId = null;
    window.csClient
      .createStage(this.featureId, stageSubmitBody)
      .then(resp => {
        newStageId = resp.stage_id;
        return window.csClient.getGates(this.featureId);
      })
      .then(resp => {
        const gate = resp.gates.find(gate => gate.stage_id === newStageId);
        showToastMessage('Extension request started!');
        if (!newStageId || !gate) {
          setTimeout(() => {
            window.location.href = `/feature/${this.featureId}`;
          }, 1000);
        } else {
          setTimeout(() => {
            window.location.href = `/feature/${this.featureId}?gate=${gate.id}`;
          }, 1000);
        }
      })
      .catch(() => {
        showToastMessage(
          'Some errors occurred. Please refresh the page or try again later.'
        );
      });
  }

  handleCancelClick(e) {
    e.preventDefault(); // Stops the form from being submitted.
    window.location.href = `/feature/${this.featureId}`;
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
    return `/feature/${this.featureId}`;
  }

  renderSubheader() {
    return html`
      <div id="subheader">
        <h2 id="breadcrumbs">
          <a href=${this.getNextPage()}>
            <iron-icon icon="chromestatus:arrow-back"></iron-icon>
            Request origin trial extension: ${this.feature.name}
          </a>
        </h2>
      </div>
    `;
  }

  // Add a set of field information that will be sent with a request submission.
  // These fields are always considered touched, and are not visible to the user.
  addDefaultRequestFields() {
    // Add "ot_owner_email" field to represent the requester email.
    this.fieldValues.push({
      name: 'ot_owner_email',
      touched: true,
      value: this.userEmail,
      stageId: this.stage.id,
    });

    // Add "ot_owner_email" field to represent the requester email.
    this.fieldValues.push({
      name: 'ot_action_requested',
      touched: true,
      value: true,
      stageId: this.stage.id,
    });

    // Add "stage_type" field to create extension stage properly.
    const extensionStageType =
      OT_EXTENSION_STAGE_MAPPING[this.stage.stage_type];
    this.fieldValues.push({
      name: 'stage_type',
      touched: true,
      value: extensionStageType,
      stageId: this.stage.id,
    });

    // Add "ot_stage_id" field to link extension stage to OT stage.
    this.fieldValues.push({
      name: 'ot_stage_id',
      touched: true,
      value: this.stage.id,
      stageId: this.stage.id,
    });
  }

  renderFields(section) {
    const fields = section.fields.map(field => {
      const featureJSONKey = ALL_FIELDS[field].name || field;
      // Add the field to this component's stage before creating the field component.
      const index = this.fieldValues.length;
      this.fieldValues.push({
        name: featureJSONKey,
        touched: true,
        value: null,
        stageId: this.stage.id,
      });

      // Add the extra elements to display milestone date information.
      let milestoneInfoText = html``;
      if (featureJSONKey === 'ot_extension__milestone_desktop_last') {
        milestoneInfoText = html` <div
          id="milestone-date"
          style="display:none;"
        >
          <span id="milestone-date-text" class="helptext fade-in"></span>
          <a class="helptext" @click=${this.openMilestoneExplanationDialog}>
            Learn how this date is chosen
          </a>
        </div>`;
      }

      return html`
        <chromedash-form-field
          name=${featureJSONKey}
          index=${index}
          .fieldValues=${this.fieldValues}
          @form-field-update="${this.handleFormFieldUpdate}"
        >
        </chromedash-form-field>
        ${milestoneInfoText}
      `;
    });

    // Add additional default hidden fields.
    this.addDefaultRequestFields();

    return fields;
  }

  renderForm() {
    this.fieldValues.feature = this.feature;

    // OT extension page only has one section.
    const section = ORIGIN_TRIAL_EXTENSION_FIELDS.sections[0];
    return html`
      <form name="feature_form">
        <chromedash-form-table ${ref(this.registerHandlers)}>
          <section class="stage_form">${this.renderFields(section)}</section>
        </chromedash-form-table>
        <div class="final_buttons">
          <input
            id="submit-button"
            class="button"
            type="submit"
            value="Submit"
          />
          <button
            id="cancel-button"
            type="reset"
            @click=${this.handleCancelClick}
          >
            Cancel
          </button>
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

customElements.define(
  'chromedash-ot-extension-page',
  ChromedashOTExtensionPage
);
