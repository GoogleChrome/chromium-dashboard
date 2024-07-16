import {LitElement, TemplateResult, css, html, nothing} from 'lit';
import {openAddStageDialog} from './chromedash-add-stage-dialog';
import {
  dialogTypes,
  openFinalizeExtensionDialog,
  openPrereqsDialog,
} from './chromedash-ot-prereqs-dialog';
import {
  openPreflightDialog,
  somePendingGates,
  somePendingPrereqs,
} from './chromedash-preflight-dialog';
import {
  FLAT_ENTERPRISE_METADATA_FIELDS,
  FLAT_METADATA_FIELDS,
  FLAT_TRIAL_EXTENSION_FIELDS,
  FORMS_BY_STAGE_TYPE,
} from './form-definition';
import {
  OT_EXTENSION_STAGE_MAPPING,
  STAGE_SHORT_NAMES,
  STAGE_TYPES_ORIGIN_TRIAL,
  VOTE_OPTIONS,
} from './form-field-enums';
import {makeDisplaySpecs} from './form-field-specs';
import {getFieldValueFromFeature, hasFieldValue, isDefinedValue} from './utils';

import '@polymer/iron-icon';
import {property, state} from 'lit/decorators.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {Feature, FeatureLink, StageDict, User} from '../js-src/cs-client';
import './chromedash-activity-log';
import './chromedash-callout';
import './chromedash-gate-chip';
import {GateDict} from './chromedash-gate-chip';
import {Process, ProgressItem} from './chromedash-gate-column';
import {
  DEPRECATED_FIELDS,
  GATE_TEAM_ORDER,
  GATE_TYPES,
  STAGE_PSA_SHIPPING,
} from './form-field-enums';
import {
  autolink,
  findProcessStage,
  flattenSections,
  parseRawQuery,
} from './utils.js';

export const DETAILS_STYLES = [
  css`
    sl-details {
      border: var(--card-border);
      box-shadow: var(--card-box-shadow);
      margin: var(--content-padding-half);
      border-radius: 4px;
      background: var(--card-background);
    }
    sl-details::part(base),
    sl-details::part(header) {
      background: transparent;
    }
    sl-details::part(header) {
      padding-bottom: 8px;
    }

    .card {
      background: var(--card-background);
      max-width: var(--max-content-width);
      padding: 16px;
    }
  `,
];

const LONG_TEXT = 60;

class ChromedashFeatureDetail extends LitElement {
  @property({type: String})
  appTitle = '';
  @property({attribute: false})
  featureLinks!: FeatureLink[];
  @property({attribute: false})
  user!: User;
  @property({type: Boolean})
  canEdit = false;
  @property({attribute: false})
  feature!: Feature;
  @property({type: Array, attribute: false})
  gates!: GateDict[];
  @property({attribute: false})
  process!: Process;
  @property({attribute: false})
  progress!: ProgressItem;
  @property({type: Number})
  selectedGateId = 0;

  @state()
  anyCollapsed = true;
  @state()
  openStage = 0;
  @state()
  previousStageTypeRendered = 0;
  @state()
  sameTypeRendered = 0;

  static get styles() {
    const ICON_WIDTH = 18;
    const GAP = 10;
    const CONTENT_PADDING = 16;

    return [
      ...SHARED_STYLES,
      ...DETAILS_STYLES,
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
          margin-top: var(--content-padding);
          display: flex;
        }
        h2 span {
          flex: 1;
        }

        .description,
        .gates {
          padding: 8px 16px;
        }

        sl-details sl-button,
        sl-details sl-dropdown {
          float: right;
          margin-right: 4px;
        }
        sl-details sl-dropdown sl-icon-button {
          font-size: 1.4rem;
        }

        sl-details sl-button[variant='default']::part(base) {
          color: var(--sl-color-primary-600);
          border: 1px solid var(--sl-color-primary-600);
        }

        ol {
          list-style: none;
          padding: 0;
        }

        ol li {
          margin-top: 0.5em;
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

        #new-stage {
          margin-left: 8px;
          margin-bottom: 4px;
        }

        #footnote {
          margin-left: 8px;
          margin-bottom: 4px;
          margin-top: 4px;
        }
      `,
    ];
  }

  _fireEvent(eventName, detail) {
    const event = new CustomEvent(eventName, {
      bubbles: true,
      composed: true,
      detail,
    });
    this.dispatchEvent(event);
  }

  connectedCallback() {
    super.connectedCallback();
    this.intializeGateColumn();
  }

  initializeExtensionDialog(rawQuery) {
    if (!('initiateExtension' in rawQuery)) {
      return;
    }
    const gateId = parseInt(rawQuery.gate);
    const extensionGate = this.gates.find(g => g.id === gateId);
    // Don't try to display dialog if we can't find the associated gate or the gate isn't approved.
    if (
      !extensionGate ||
      (extensionGate.state !== VOTE_OPTIONS.APPROVED[0] &&
        extensionGate.state !== VOTE_OPTIONS.NA[0])
    ) {
      return;
    }
    let extensionStage;
    for (const stage of this.feature.stages) {
      const foundStage = stage.extensions.find(
        s => s.id === extensionGate.stage_id
      );
      if (foundStage) {
        extensionStage = foundStage;
        break;
      }
    }
    // Don't try to display dialog if we can't find the associated stage or no action is requested.
    if (!extensionStage || !extensionStage.ot_action_requested) {
      return;
    }
    openFinalizeExtensionDialog(
      this.feature.id,
      extensionStage,
      extensionStage.desktop_last,
      dialogTypes.FINALIZE_EXTENSION
    );
  }

  intializeGateColumn() {
    const rawQuery = parseRawQuery(window.location.search);
    if (!rawQuery.hasOwnProperty('gate')) {
      return;
    }
    const gateVal = rawQuery['gate'];
    const foundGates = this.gates.filter(g => g.id == gateVal);
    if (!foundGates.length) {
      return;
    }
    const gate = foundGates[0];

    const foundStages = this.feature.stages.filter(s => {
      return (
        s.id === gate.stage_id || s.extensions.some(e => e.id === gate.stage_id)
      );
    });

    if (!foundStages.length) {
      return;
    }
    let stage = foundStages[0];
    this.openStage = stage.id;

    // Make sure to use the extension stage if an extension gate is being referenced.
    if (gate.gate_type === GATE_TYPES.API_EXTEND_ORIGIN_TRIAL) {
      stage = stage.extensions.find(e => e.id === gate.stage_id)!;
    }

    this._fireEvent('show-gate-column', {
      feature: this.feature,
      stage: stage,
      gate: gate,
    });
    this.initializeExtensionDialog(rawQuery);
  }

  isAnyCollapsed() {
    const sections = this.renderRoot.querySelectorAll('.stage');
    const open = this.renderRoot.querySelectorAll('.stage[open]');
    return open.length < sections.length;
  }

  updateCollapsed() {
    this.anyCollapsed = this.isAnyCollapsed();
  }

  toggleAll() {
    const shouldOpen = this.anyCollapsed;
    this.renderRoot.querySelectorAll('.stage').forEach(el => {
      (el as HTMLDetailsElement).open = shouldOpen;
    });
  }

  handleAddXfnGates(feStage) {
    const prompt =
      'Would you like to add gates for Privacy, Security, etc.? \n\n' +
      'This is needed if the API Owners ask you to add them, ' +
      'or if you send an "Intent to Ship" rather than a PSA.';
    if (confirm(prompt)) {
      window.csClient.addXfnGates(feStage.feature_id, feStage.id).then(() => {
        this._fireEvent('refetch-needed', {});
      });
    }
  }

  renderControls() {
    const editAllButton = html`
      <sl-button variant="text" href="/guide/editall/${this.feature.id}">
        Edit all fields
      </sl-button>
    `;
    const toggleLabel = this.anyCollapsed ? 'Expand all' : 'Collapse all';
    return html`
      ${this.canEdit ? editAllButton : nothing}

      <sl-button
        variant="text"
        title="Expand or collapse all sections"
        @click=${this.toggleAll}
      >
        ${toggleLabel}
      </sl-button>
    `;
  }

  renderText(value) {
    value = String(value);
    const markup = autolink(value, this.featureLinks);
    if (value.length > LONG_TEXT || value.includes('\n')) {
      return html`<span class="longtext">${markup}</span>`;
    }
    return html`<span class="text">${markup}</span>`;
  }

  renderUrl(value) {
    if (value.startsWith('http')) {
      return html`<chromedash-link
        href=${value}
        class="url ${value.length > LONG_TEXT ? 'longurl' : ''}"
        .featureLinks=${this.featureLinks}
      ></chromedash-link>`;
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
        <ul class="inline-list">
          ${value.map(url => html`<li>${this.renderUrl(url)}</li>`)}
        </ul>
      `;
    }
    return this.renderText(value);
  }

  renderField(fieldDef, feStage) {
    const [fieldId, fieldDisplayName, fieldType] = fieldDef;
    const value = getFieldValueFromFeature(fieldId, feStage, this.feature);
    const isDefined = isDefinedValue(value);
    const isDeprecatedField = DEPRECATED_FIELDS.has(fieldId);
    if (!isDefined && isDeprecatedField) {
      return nothing;
    }

    const icon = isDefined
      ? html`<sl-icon library="material" name="check_circle_20px"></sl-icon>`
      : html`<sl-icon library="material" name="blank_20px"></sl-icon>`;

    return html`
      <dt id=${fieldId}>${icon} ${fieldDisplayName}</dt>
      <dd>
        ${isDefined
          ? this.renderValue(fieldType, value)
          : html`<i>No information provided yet</i>`}
      </dd>
    `;
  }

  stageHasAnyFilledFields(fields, feStage) {
    return fields.some(fieldDef =>
      hasFieldValue(fieldDef[0], feStage, this.feature)
    );
  }

  // Renders all fields for trial extension stages as a subsection of the
  // origin trial stage that the extension is associated with.
  renderExtensionFields(extensionStages) {
    const extensionFields: TemplateResult[] = [];
    const fieldNames = flattenSections(FLAT_TRIAL_EXTENSION_FIELDS);
    const fields = makeDisplaySpecs(fieldNames);
    extensionStages.forEach((extensionStage, i) => {
      if (this.stageHasAnyFilledFields(fields, extensionStage)) {
        extensionFields.push(html`
          <div>
            <h3>Trial extension ${i !== 0 ? i + 1 : nothing}</h3>
            <br />
            ${fields.map(fieldDef =>
              this.renderField(fieldDef, extensionStage)
            )}
          </div>
        `);
      }
    });
    return extensionFields;
  }

  renderSectionFields(fields, feStage) {
    if (this.stageHasAnyFilledFields(fields, feStage)) {
      // Add the subsection of trial extension information if it is relevant.
      const extensionFields = feStage.extensions
        ? this.renderExtensionFields(feStage.extensions)
        : [];

      return html` <dl>
        ${fields.map(fieldDef => this.renderField(fieldDef, feStage))}
        ${extensionFields}
      </dl>`;
    } else {
      return html`<p>No relevant fields have been filled in.</p>`;
    }
  }

  renderSection(
    summary,
    content,
    isActive = false,
    defaultOpen = false,
    isStage = true
  ) {
    if (isActive) {
      summary += ' - Active';
    }
    return html`
      <sl-details
        summary=${summary}
        @sl-after-show=${this.updateCollapsed}
        @sl-after-hide=${this.updateCollapsed}
        ?open=${isActive || defaultOpen}
        class="${isActive ? 'active' : ''} ${isStage ? 'stage' : ''}"
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
    const fieldNames = flattenSections(
      this.feature.is_enterprise_feature
        ? FLAT_ENTERPRISE_METADATA_FIELDS
        : FLAT_METADATA_FIELDS
    );
    if (fieldNames === undefined || fieldNames.length === 0) {
      return nothing;
    }
    const fields = makeDisplaySpecs(fieldNames);
    const editButton = html`
      <sl-button
        size="small"
        style="float:right"
        href="/guide/stage/${this.feature.id}/metadata"
        >Edit fields</sl-button
      >
    `;

    const content = html`
      <p class="description">${this.canEdit ? editButton : nothing}</p>
      <section class="card">${this.renderSectionFields(fields, {})}</section>
    `;
    return this.renderSection(
      'Metadata',
      content,
      /* isActive=*/ false,
      /* defaultOpen=*/ this.feature.is_enterprise_feature,
      /* isStage=*/ false
    );
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
    gatesForStage.sort(
      (g1, g2) =>
        GATE_TEAM_ORDER.indexOf(g1.team_name) -
        GATE_TEAM_ORDER.indexOf(g2.team_name)
    );
    return gatesForStage.map(g => this.renderGateChip(feStage, g));
  }

  hasStageActions(stage, feStage) {
    // See if there is an API owners gate where actions are displayed.
    const hasOwnersGate = this.gates.some(
      g => g.team_name === 'API Owners' && g.stage_id === feStage.id
    );
    // If there are actions to be displayed for this stage, and
    // these actions are not displayed at the gate-level, return true.
    if (stage?.actions?.length > 0 && !hasOwnersGate) {
      return true;
    }
    return false;
  }

  renderStageAction(action, stage, feStage) {
    const label = action.name;
    const url = action.url
      .replace('{feature_id}', this.feature.id)
      .replace('{intent_stage}', stage.outgoing_stage)
      // No gate_id for this URL.
      .replace('/{gate_id}', '');

    const gatesForStage = this.gates.filter(g => g.stage_id == feStage.id);
    const checkCompletion = () => {
      if (
        somePendingPrereqs(action, this.progress) ||
        somePendingGates(gatesForStage, feStage)
      ) {
        // Open the dialog.
        openPreflightDialog(
          this.feature,
          this.progress,
          this.process,
          action,
          stage,
          feStage,
          gatesForStage,
          url
        );
        return;
      } else {
        // Act like user clicked left button to go to the draft email window.
        const draftWindow = window.open(url, '_blank');
        draftWindow?.focus();
      }
    };
    return html`
      <sl-button size="small" @click=${checkCompletion}>${label}</sl-button>
    `;
  }

  renderStageActions(stage, feStage) {
    if (!this.canEdit) {
      return nothing;
    }
    return html`
      ${stage.actions.map(act => this.renderStageAction(act, stage, feStage))}
    `;
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
      numberDifferentiation = ` ${this.sameTypeRendered}`;
    } else {
      this.previousStageTypeRendered = feStage.stage_type;
      this.sameTypeRendered = 1;
    }

    let name = `${processStage.name}${numberDifferentiation}`;
    if (feStage.display_name) {
      name = `${processStage.name}: ${feStage.display_name}`;
    }
    const isActive = this.feature.active_stage_id === feStage.id;

    // Show any buttons that should be displayed at the top of the detail card.
    const stageMenu = this.renderStageMenu(feStage);
    const addExtensionButton = this.renderExtensionButton(feStage);
    const editButton = this.renderEditButton(feStage, processStage);
    const trialButton = this.renderOriginTrialButton(feStage);
    const extensionGateChips = feStage.extensions?.map(extension => {
      return html` <div class="gates">
        ${STAGE_SHORT_NAMES[extension.stage_type]}:
        ${this.renderGateChips(extension)}
      </div>`;
    });
    // Gates should only be prefixed with stage name if gates from multiple stages are displayed.
    let gatesPrefix = '';
    if (extensionGateChips.length > 0) {
      gatesPrefix = `${STAGE_SHORT_NAMES[feStage.stage_type]}: `;
    }
    const content = html`
      <p class="description">
        ${stageMenu} ${trialButton}
        ${this.hasStageActions(processStage, feStage)
          ? this.renderStageActions(processStage, feStage)
          : nothing}
        ${editButton} ${addExtensionButton} ${processStage.description}
      </p>
      <div class="gates">${gatesPrefix}${this.renderGateChips(feStage)}</div>
      ${extensionGateChips}
      <section class="card">
        ${this.renderSectionFields(fields, feStage)}
      </section>
    `;
    const defaultOpen =
      this.feature.is_enterprise_feature || feStage.id == this.openStage;
    return this.renderSection(name, content, isActive, defaultOpen);
  }

  renderEditButton(feStage, processStage) {
    if (!this.canEdit) {
      return nothing;
    }
    return html` <sl-button
      size="small"
      href="/guide/stage/${this.feature
        .id}/${processStage.outgoing_stage}/${feStage.id}"
      >Edit fields</sl-button
    >`;
  }

  renderFinalizeExtensionButton(extensionStage) {
    return html` <sl-button
      size="small"
      variant="primary"
      @click=${() =>
        openFinalizeExtensionDialog(
          this.feature.id,
          extensionStage,
          extensionStage.desktop_last,
          dialogTypes.FINALIZE_EXTENSION
        )}
      >Finalize Extension</sl-button
    >`;
  }

  renderDisabledExtensionButton() {
    const tooltipText =
      'A pending extension request exists. Follow the process for ' +
      'obtaining extension approval, or contact origin-trials-support@google.com for help.';
    return html` <sl-tooltip content=${tooltipText}>
      <sl-button size="small" disabled>Trial Extension Pending</sl-button>
    </sl-tooltip>`;
  }

  renderExtensionButton(feStage) {
    // Don't render an extension request button if this is not an OT stage,
    // or the user does not have access to submit an extension request,
    // or the OT stage has not been created in the OT Console yet.
    const userCannotViewOTControls =
      !this.user ||
      (!this.user.email.endsWith('@chromium.org') &&
        !this.user.email.endsWith('@google.com'));
    const isNotOriginTrialStage = !STAGE_TYPES_ORIGIN_TRIAL.has(
      feStage.stage_type
    );
    const originTrialNotCreatedYet = !feStage.origin_trial_id;
    if (
      userCannotViewOTControls ||
      isNotOriginTrialStage ||
      originTrialNotCreatedYet
    ) {
      return nothing;
    }

    // Add button to finalize an extension if the extension has been approved.
    const extensionReadyForFinalize = feStage.extensions.find(e => {
      const extensionGate: GateDict | undefined = this.gates.find(
        g => g.stage_id === e.id
      );
      return (
        e.ot_action_requested &&
        extensionGate &&
        (extensionGate.state === VOTE_OPTIONS.APPROVED[0] ||
          extensionGate.state === VOTE_OPTIONS.NA[0])
      );
    });
    if (extensionReadyForFinalize) {
      return this.renderFinalizeExtensionButton(extensionReadyForFinalize);
    }

    const extensionInProgress =
      feStage.extensions && feStage.extensions.some(e => e.ot_action_requested);
    // Show a disabled button if an extension request has already been submitted.
    if (extensionInProgress) {
      return this.renderDisabledExtensionButton();
    }

    // Button text changes based on whether or not an extension stage already exists.
    let extensionButtonText = 'Request a trial extension';
    if (feStage.extensions && feStage.extensions.length > 0) {
      extensionButtonText = 'Request another trial extension';
    }

    const stageId = feStage.id;
    return html` <sl-button
      size="small"
      @click=${() =>
        location.assign(`/ot_extension_request/${this.feature.id}/${stageId}`)}
      >${extensionButtonText}</sl-button
    >`;
  }

  renderOriginTrialButton(feStage) {
    // Don't render an origin trial button if this is not an OT stage.
    if (!STAGE_TYPES_ORIGIN_TRIAL.has(feStage.stage_type)) {
      return nothing;
    }

    // If we have an origin trial ID associated with the stage, add a link to the trial.
    if (feStage.origin_trial_id) {
      let originTrialsURL = `https://origintrials-staging.corp.google.com/origintrials/#/view_trial/${feStage.origin_trial_id}`;
      // If this is the production host, link to the production OT site.
      if (this.appTitle === 'Chrome Platform Status') {
        originTrialsURL = `https://developer.chrome.com/origintrials/#/view_trial/${feStage.origin_trial_id}`;
      }
      return html` <sl-button
        size="small"
        variant="primary"
        href=${originTrialsURL}
        target="_blank"
        >View Origin Trial</sl-button
      >`;
    }
    const canSeeOTControls =
      this.user &&
      (this.user.email.endsWith('@chromium.org') ||
        this.user.email.endsWith('@google.com'));
    if (!canSeeOTControls) {
      return nothing;
    }

    const trialIsApproved = this.gates.every(g => {
      return (
        g.stage_id !== feStage.id ||
        g.state === VOTE_OPTIONS.APPROVED[0] ||
        g.state === VOTE_OPTIONS.NA[0]
      );
    });
    if (feStage.ot_action_requested) {
      // Display the button as disabled with tooltip text if a request
      // has already been submitted.
      return html` <sl-tooltip
        content="Action already requested. For further inquiries, contact origin-trials-support@google.com."
      >
        <sl-button size="small" variant="primary" disabled
          >Request Trial Creation</sl-button
        >
      </sl-tooltip>`;
    } else if (!trialIsApproved) {
      // Display the button as disabled with tooltip text if the trial has not
      // yet received approvals.
      return html` <sl-tooltip
        content="Approvals must be obtained before submission. For questions, contact origin-trials-support@google.com."
      >
        <sl-button size="small" variant="primary" disabled
          >Request Trial Creation</sl-button
        >
      </sl-tooltip>`;
    }
    // Display the creation request button if user has edit access.
    return html` <sl-button
      size="small"
      variant="primary"
      @click="${() =>
        openPrereqsDialog(this.feature.id, feStage, dialogTypes.CREATION)}"
      >Request Trial Creation</sl-button
    >`;
  }

  offerAddXfnGates(feStage) {
    const stageGates = this.gates.filter(g => g.stage_id == feStage.id);
    return feStage.stage_type == STAGE_PSA_SHIPPING && stageGates.length < 6;
  }

  renderFootnote() {
    return html`
      <section id="footnote">
        Please see the
        <a
          href="https://www.chromium.org/blink/launching-features"
          target="_blank"
          rel="noopener"
        >
          Launching features
        </a>
        page for process instructions.
      </section>
    `;
  }

  renderStageMenu(feStage) {
    const items: TemplateResult[] = [];
    if (this.offerAddXfnGates(feStage)) {
      items.push(html`
        <sl-menu-item @click=${() => this.handleAddXfnGates(feStage)}>
          Add cross-functional gates
        </sl-menu-item>
      `);
    }

    if (items.length === 0) return nothing;

    return html`
      <sl-dropdown>
        <sl-icon-button
          library="material"
          name="more_vert_24px"
          label="Stage menu"
          slot="trigger"
        ></sl-icon-button>
        <sl-menu>${items}</sl-menu>
      </sl-dropdown>
    `;
  }

  renderAddStageButton() {
    if (!this.canEdit) {
      return nothing;
    }
    const text = this.feature.is_enterprise_feature ? 'Add Step' : 'Add Stage';

    return html` <sl-button
      id="new-stage"
      size="small"
      @click="${() =>
        openAddStageDialog(this.feature.id, this.feature.feature_type_int)}"
    >
      ${text}
    </sl-button>`;
  }

  renderSectionHeader() {
    const text = this.feature.is_enterprise_feature
      ? 'Rollout steps'
      : 'Development stages';
    return html` <span
      >${text}
      <sl-icon-button
        name="info-circle"
        href="https://www.chromium.org/blink/launching-features"
        style="font-size: 0.8rem;"
        target="_blank"
        label="Launching feature guide"
      >
      </sl-icon-button>
    </span>`;
  }

  render() {
    return html`
      ${this.renderMetadataSection()}
      <h2>${this.renderSectionHeader()} ${this.renderControls()}</h2>
      ${this.feature.stages.map(feStage => this.renderProcessStage(feStage))}
      ${this.renderAddStageButton()} ${this.renderFootnote()}
    `;
  }
}

customElements.define('chromedash-feature-detail', ChromedashFeatureDetail);
