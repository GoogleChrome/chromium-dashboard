import {LitElement, css, html, nothing} from 'lit';
import {openAddStageDialog} from './chromedash-add-stage-dialog';
import {makeDisplaySpecs} from './form-field-specs';
import {
  FLAT_ENTERPRISE_METADATA_FIELDS,
  FLAT_METADATA_FIELDS,
  FLAT_TRIAL_EXTENSION_FIELDS,
  FORMS_BY_STAGE_TYPE,
  OT_EXTENSION_STAGE_MAPPING,
} from './form-definition';

import {
  DEPRECATED_FIELDS,
  GATE_TEAM_ORDER,
  PLATFORMS_DISPLAYNAME,
  STAGE_SPECIFIC_FIELDS,
  OT_MILESTONE_END_FIELDS,
  ENTERPRISE_FEATURE_CATEGORIES_DISPLAYNAME} from './form-field-enums';
import '@polymer/iron-icon';
import './chromedash-activity-log';
import './chromedash-callout';
import './chromedash-gate-chip';
import {autolink, findProcessStage, flattenSections} from './utils.js';
import {SHARED_STYLES} from '../sass/shared-css.js';

const LONG_TEXT = 60;

class ChromedashFeatureDetail extends LitElement {
  static get properties() {
    return {
      user: {type: Object},
      canEdit: {type: Boolean},
      feature: {type: Object},
      gates: {type: Array},
      process: {type: Object},
      dismissedCues: {type: Array},
      anyCollapsed: {type: Boolean},
      selectedGateId: {type: Number},
      rawQuery: {type: Object},
      openStage: {type: Number},
    };
  }

  constructor() {
    super();
    this.user = {};
    this.canEdit = false;
    this.feature = {};
    this.gates = [];
    this.process = {};
    this.dismissedCues = [];
    this.anyCollapsed = true;
    this.previousStageTypeRendered = 0;
    this.sameTypeRendered = 0;
    this.selectedGateId = 0;
    this.rawQuery = {};
    this.openStage = 0;
  }

  static get styles() {
    const ICON_WIDTH = 18;
    const GAP = 10;
    const CONTENT_PADDING = 16;

    return [
      ...SHARED_STYLES,
      css`
      :host {
        display: block;
        position: relative;
        box-sizing: border-box;
        contain: content;
        overflow: hidden;
        background: inherit;
      }

      h2 {
        display: flex;
      }
      h2 span {
        flex: 1;
      }

      sl-details {
        border: var(--card-border);
        box-shadow: var(--card-box-shadow);
        margin: var(--content-padding-half);
        border-radius: 4px;
      }

      sl-details {
        background: var(--card-background);
      }

      sl-details::part(base),
      sl-details::part(header) {
        background: transparent;
      }
      sl-details::part(header) {
        padding-bottom: 8px;
      }

      .description,
      .gates {
        padding: 8px 16px;
      }

      sl-details sl-button::part(base) {
        color: var(--sl-color-primary-600);
        border: 1px solid var(--sl-color-primary-600);
      }

      .card {
        background: var(--card-background);
        max-width: var(--max-content-width);
        padding: 16px;
      }

      ol {
        list-style: none;
        padding: 0;
      }

      ol li {
        margin-top: .5em;
      }

      dl {
        padding: 0 var(--content-padding-half);
      }

      dt {
        font-weight: 500;
        display: flex;
        gap: ${GAP}px;
        align-items: center;
      }
      dt sl-icon {
        color: var(--gate-approved-color);
        font-size: 1.3em;
      }

      dd {
        padding: var(--content-padding-half);
        padding-left: ${ICON_WIDTH + GAP + CONTENT_PADDING}px;
        padding-bottom: var(--content-padding-large);
      }

      .inline-list {
        display: inline-block;
        padding: 0;
        margin: 0;
      }

      .longtext {
        display: block;
        white-space: pre-wrap;
        padding: var(--content-padding-half);
      }

      .longurl {
        display: block;
        padding: var(--content-padding-half);
      }

      .active .card {
        border: var(--spot-card-border);
        box-shadow: var(--spot-card-box-shadow);
      }

    `];
  }

  connectedCallback() {
    super.connectedCallback();
    this.intializeGateColumn();
  }

  intializeGateColumn() {
    if (!this.rawQuery) {
      return;
    }

    if (!this.rawQuery.hasOwnProperty('gate')) {
      return;
    }
    const gateVal = this.rawQuery['gate'];
    const foundGates = this.gates.filter(g => g.id == gateVal);
    if (!foundGates.length) {
      return;
    }
    const gate = foundGates[0];

    const foundStages = this.feature.stages.filter(s => s.id == gate.stage_id);
    if (!foundStages.length) {
      return;
    }
    const stage = foundStages[0];
    this.openStage = stage.id;

    this._fireEvent('show-gate-column', {
      feature: this.feature,
      stage: stage,
      gate: gate,
    });
  }

  _fireEvent(eventName, detail) {
    const event = new CustomEvent(eventName, {
      bubbles: true,
      composed: true,
      detail,
    });
    this.dispatchEvent(event);
  }

  isAnyCollapsed() {
    const sections = this.shadowRoot.querySelectorAll('sl-details');
    const open = this.shadowRoot.querySelectorAll('sl-details[open]');
    return open.length < sections.length;
  }

  updateCollapsed() {
    this.anyCollapsed = this.isAnyCollapsed();
  }

  toggleAll() {
    const shouldOpen = this.anyCollapsed;
    this.shadowRoot.querySelectorAll('sl-details').forEach((el) => {
      el.open = shouldOpen;
    });
  }

  renderControls() {
    const editAllButton = html`
      <sl-button variant="text"
           href="/guide/editall/${this.feature.id}">
         Edit all fields
      </sl-button>
    `;
    const toggleLabel = this.anyCollapsed ? 'Expand all' : 'Collapse all';
    return html`
      ${this.canEdit ? editAllButton : nothing}

      <sl-button variant="text"
        title="Expand or collapse all sections"
        @click=${this.toggleAll}>
        ${toggleLabel}
      </sl-button>
    `;
  }

  isDefinedValue(value) {
    return !(value === undefined || value === null || value.length == 0);
  }

  // Look at all extension milestones and calculate the highest milestone that an origin trial
  // is available. This is used to display the highest milestone available, but to preserve the
  // milestone that the trial was originally available for without extensions.
  calcMaxMilestone(fieldName, feStage) {
    // If the max milestone has already been calculated, or no trial extensions exist, do nothing.
    if (feStage[`max_${fieldName}`] || !feStage.extensions) {
      return;
    }
    let maxMilestone = feStage[fieldName];
    for (const extension of feStage.extensions) {
      if (extension[fieldName]) {
        maxMilestone = Math.max(maxMilestone, extension[fieldName]);
      }
    }
    // Save the findings with the "max_" prefix as a prop of the stage for reference.
    feStage[`max_${fieldName}`] = maxMilestone;
  }

  // Get the milestone value that is displayed to the user regarding the origin trial end date.
  getMilestoneExtensionValue(fieldName, feStage) {
    const milestoneFieldName = OT_MILESTONE_END_FIELDS[fieldName];
    this.calcMaxMilestone(milestoneFieldName, feStage);

    const maxMilestoneFieldName = `max_${milestoneFieldName}`;
    // Display only extension milestone if the original milestone has not been added.
    if (feStage[maxMilestoneFieldName] && !feStage[fieldName]) {
      return `Extended to ${feStage[maxMilestoneFieldName]}`;
    }
    // If the trial has been extended past the original milestone, display the extension
    // milestone with additional text reminding of the original milestone end date.
    if (feStage[maxMilestoneFieldName] && feStage[maxMilestoneFieldName] > feStage[fieldName]) {
      return `${feStage[maxMilestoneFieldName]} (extended from ${feStage[milestoneFieldName]})`;
    }
    return feStage[fieldName];
  }

  getFieldValue(fieldName, feStage) {
    if (STAGE_SPECIFIC_FIELDS.has(fieldName)) {
      const value = feStage[fieldName];
      if (fieldName === 'rollout_platforms' && value) {
        return value.map(platformId => PLATFORMS_DISPLAYNAME[platformId]);
      } else if (fieldName in OT_MILESTONE_END_FIELDS) {
        // If an origin trial end date is being displayed, handle extension milestones as well.
        return this.getMilestoneExtensionValue(fieldName, feStage);
      }
      return feStage[fieldName];
    }

    let value = this.feature[fieldName];
    const fieldNameMapping = {
      owner: 'browsers.chrome.owners',
      editors: 'browsers.chrome.editors',
      search_tags: 'tags',
      spec_link: 'standards.spec',
      standard_maturity: 'standards.maturity.text',
      sample_links: 'resources.samples',
      docs_links: 'resources.docs',
      bug_url: 'browsers.chrome.bug',
      blink_components: 'browsers.chrome.blink_components',
      devrel: 'browsers.chrome.devrel',
      prefixed: 'browsers.chrome.prefixed',
      impl_status_chrome: 'browsers.chrome.status.text',
      shipped_milestone: 'browsers.chrome.desktop',
      shipped_android_milestone: 'browsers.chrome.android',
      shipped_webview_milestone: 'browsers.chrome.webview',
      shipped_ios_milestone: 'browsers.chrome.ios',
      ff_views: 'browsers.ff.view.text',
      ff_views_link: 'browsers.ff.view.url',
      ff_views_notes: 'browsers.ff.view.notes',
      safari_views: 'browsers.safari.view.text',
      safari_views_link: 'browsers.safari.view.url',
      safari_views_notes: 'browsers.safari.view.notes',
      web_dev_views: 'browsers.webdev.view.text',
      web_dev_views_link: 'browsers.webdev.view.url',
      web_dev_views_notes: 'browsers.webdev.view.notes',
      other_views_notes: 'browsers.other.view.notes',
    };
    if (!value && fieldNameMapping[fieldName]) {
      value = this.feature;
      for (const step of fieldNameMapping[fieldName].split('.')) {
        if (value) {
          value = value[step];
        }
      }
    }
    if (fieldName === 'enterprise_feature_categories' && value) {
      return value.map(categoryId =>
        ENTERPRISE_FEATURE_CATEGORIES_DISPLAYNAME[categoryId]);
    }
    return value;
  }

  hasFieldValue(fieldName, feStage) {
    const value = this.getFieldValue(fieldName, feStage);
    return this.isDefinedValue(value);
  }

  renderText(value) {
    value = String(value);
    const markup = autolink(value);
    if (value.length > LONG_TEXT || value.includes('\n')) {
      return html`<span class="longtext">${markup}</span>`;
    }
    return html`<span class="text">${markup}</span>`;
  }

  renderUrl(value) {
    if (value.startsWith('http')) {
      return html`
        <a href=${value} target="_blank"
           class="url ${value.length > LONG_TEXT ? 'longurl' : ''}"
           >${value}</a>
      `;
    }
    return this.renderText(value);
  }

  renderValue(fieldType, value) {
    if (fieldType == 'checkbox') {
      return this.renderText(value ? 'True' : 'False');
    } else if (fieldType == 'url') {
      return this.renderUrl(value);
    } else if (fieldType == 'multi-url') {
      return html`
        <ul class='inline-list'>
          ${value.map(url => html`<li>${this.renderUrl(url)}</li>`)}
        </ul>
      `;
    }
    return this.renderText(value);
  }

  renderField(fieldDef, feStage) {
    const [fieldId, fieldDisplayName, fieldType] = fieldDef;
    const value = this.getFieldValue(fieldId, feStage);
    const isDefinedValue = this.isDefinedValue(value);
    const isDeprecatedField = DEPRECATED_FIELDS.has(fieldId);
    if (!isDefinedValue && isDeprecatedField) {
      return nothing;
    }

    const icon = isDefinedValue ?
      html`<sl-icon library="material" name="check_circle_20px"></sl-icon>` :
      html`<sl-icon library="material" name="blank_20px"></sl-icon>`;

    return html`
      <dt id=${fieldId}>${icon} ${fieldDisplayName}</dt>
      <dd>
       ${isDefinedValue ?
          this.renderValue(fieldType, value) :
          html`<i>No information provided yet</i>`}
      </dd>
    `;
  }

  stageHasAnyFilledFields(fields, feStage) {
    return fields.some(fieldDef => this.hasFieldValue(fieldDef[0], feStage));
  }

  // Renders all fields for trial extension stages as a subsection of the
  // origin trial stage that the extension is associated with.
  renderExtensionFields(extensionStages) {
    const extensionFields = [];
    const fieldNames = flattenSections(FLAT_TRIAL_EXTENSION_FIELDS);
    const fields = makeDisplaySpecs(fieldNames);
    extensionStages.forEach((extensionStage, i) => {
      if (this.stageHasAnyFilledFields(fields, extensionStage)) {
        extensionFields.push(html`
        <div>
          <h3>Trial extension ${(i !== 0) ? i + 1 : nothing}</h3>
          <br>
          ${fields.map(fieldDef => this.renderField(fieldDef, extensionStage))}
        </div>
        `);
      }
    });
    return extensionFields;
  }

  renderSectionFields(fields, feStage) {
    if (this.stageHasAnyFilledFields(fields, feStage)) {
      // Add the subsection of trial extension information if it is relevant.
      const extensionFields = (
        (feStage.extensions) ? this.renderExtensionFields(feStage.extensions) : []);

      return html`
        <dl>
          ${fields.map(fieldDef => this.renderField(fieldDef, feStage))}
          ${extensionFields}
        </dl>`;
    } else {
      return html`<p>No relevant fields have been filled in.</p>`;
    }
  }

  renderSection(summary, content, isActive=false, defaultOpen=false) {
    if (isActive) {
      summary += ' - Active';
    }
    return html`
      <sl-details summary=${summary}
        @sl-after-show=${this.updateCollapsed}
        @sl-after-hide=${this.updateCollapsed}
        ?open=${isActive || defaultOpen}
        class=${isActive ? 'active' : ''}
      >
        ${content}
      </sl-details>
    `;
  }

  getStageForm(stageType) {
    return FORMS_BY_STAGE_TYPE[stageType] || null;
  }

  renderMetadataSection() {
    // modify for enterprise
    const fieldNames = flattenSections(this.feature.is_enterprise_feature ?
      FLAT_ENTERPRISE_METADATA_FIELDS :
      FLAT_METADATA_FIELDS);
    if (fieldNames === undefined || fieldNames.length === 0) {
      return nothing;
    }
    const fields = makeDisplaySpecs(fieldNames);
    const editButton = html`
      <sl-button size="small" style="float:right"
          href="/guide/stage/${this.feature.id}/metadata"
          >Edit fields</sl-button>
    `;

    const content = html`
      <p class="description">
        ${this.canEdit ? editButton : nothing}
      </p>
      <section class="card">
        ${this.renderSectionFields(fields, {})}
      </section>
    `;
    return this.renderSection(
      'Metadata',
      content,
      /* isActive=*/false,
      /* defaultOpen=*/this.feature.is_enterprise_feature);
  }

  renderGateChip(feStage, gate) {
    return html`
      <chromedash-gate-chip
        .feature=${this.feature}
        .stage=${feStage}
        .gate=${gate}
        selectedGateId=${this.selectedGateId}
      >
      </chromedash-gate-chip>
    `;
  }

  renderGateChips(feStage) {
    const gatesForStage = this.gates.filter(g => g.stage_id == feStage.id);
    gatesForStage.sort((g1, g2) =>
      GATE_TEAM_ORDER.indexOf(g1.team_name) -
      GATE_TEAM_ORDER.indexOf(g2.team_name));
    return html`
      <div class="gates">
        ${gatesForStage.map(g => this.renderGateChip(feStage, g))}
      </div>
    `;
  }

  // Create an extension stage for an origin trial stage on button click.
  createExtensionStage(feStage, extensionAlreadyExists) {
    if (!feStage.stage_type in OT_EXTENSION_STAGE_MAPPING) {
      return;
    }
    const confirmText = ('Trial extension fields are already available for this trial. ' +
      'Do you want to add more fields for another, separate trial extension?');
    if (!extensionAlreadyExists || window.confirm(confirmText)) {
      const body = {
        stage_type: OT_EXTENSION_STAGE_MAPPING[feStage.stage_type],
        ot_stage_id: feStage.id,
      };

      window.csClient.createStage(this.feature.id, body)
        .then(() => {
          // Redirect to origin trial stage after creation.
          location.assign(
            `/guide/stage/${this.feature.id}/${feStage.intent_stage}/${feStage.id}`);
        });
    }
  }

  renderProcessStage(feStage) {
    const stageForm = this.getStageForm(feStage.stage_type);
    const fieldNames = stageForm === null ? [] : flattenSections(stageForm);
    if (fieldNames === undefined || fieldNames.length == 0) return nothing;
    const fields = makeDisplaySpecs(fieldNames);

    const processStage = findProcessStage(feStage, this.process);
    if (!processStage) return nothing;


    // Add a number differentiation if this stage type is the same as another stage.
    let numberDifferentiation = '';
    if (this.previousStageTypeRendered === feStage.stage_type) {
      this.sameTypeRendered += 1;
      numberDifferentiation = ` (${this.sameTypeRendered})`;
    } else {
      this.previousStageTypeRendered = feStage.stage_type;
      this.sameTypeRendered = 1;
    }

    const name = `${processStage.name}${numberDifferentiation}`;
    const isActive = this.feature.active_stage_id === feStage.id;

    // Show a button to add a trial extension stage for origin trial stages.
    let addExtensionButton = nothing;
    if (this.canEdit && 'extensions' in feStage) {
      // Button text changes based on whether or not an extension stage already exists.
      const extensionAlreadyExists = (feStage.extensions && feStage.extensions.length > 0);
      const extensionButtonText = extensionAlreadyExists ?
        'Add another trial extension' : 'Add a trial extension';
      addExtensionButton = html`
      <sl-button size="small" style="float:right"
          @click=${() => this.createExtensionStage(feStage, extensionAlreadyExists)}
          >${extensionButtonText}</sl-button>`;
    }

    const editButton = html`
      <sl-button size="small" style="float:right"
          href="/guide/stage/${this.feature.id}/${processStage.outgoing_stage}/${feStage.id}"
          >Edit fields</sl-button>
`;
    const content = html`
      <p class="description">
        ${this.canEdit ? editButton : nothing}
        ${addExtensionButton}
        ${processStage.description}
      </p>
      ${this.renderGateChips(feStage)}
      <section class="card">
        ${this.renderSectionFields(fields, feStage)}
      </section>
    `;
    const defaultOpen = this.feature.is_enterprise_feature || (feStage.id == this.openStage);
    return this.renderSection(name, content, isActive, defaultOpen);
  }

  renderActivitySection() {
    const summary = 'Comments & Activity';
    const content = html`
        <div style="padding-top: var(--content-padding)">
          <chromedash-activity-log
            .user=${this.user}
            .feature=${this.feature}
            .comments=${this.comments}
          ></chromedash-activity-log>
        </div>
    `;
    return this.renderSection(summary, content);
  }

  renderAddStageButton() {
    if (!this.canEdit) {
      return nothing;
    }

    return html`
    <sl-button size="small" @click="${
        () => openAddStageDialog(this.feature.id, this.feature.feature_type_int)}">
      Add stage
    </sl-button>`;
  }

  render() {
    return html`
      <h2>
        <span>Development stages</span>
        ${this.renderControls()}
      </h2>
      ${this.renderMetadataSection()}
      ${this.feature.stages.map(feStage => this.renderProcessStage(feStage))}
      ${this.renderActivitySection()}
      ${this.renderAddStageButton()}
    `;
  }
}

customElements.define('chromedash-feature-detail', ChromedashFeatureDetail);
