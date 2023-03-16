import {LitElement, css, html} from 'lit';
import {SHARED_STYLES} from '../sass/shared-css.js';
import {CREATEABLE_STAGES, FORMS_BY_STAGE_TYPE} from './form-definition.js';


let addStageDialogEl;
let currentFeatureId;


export async function openAddStageDialog(featureId, featureType) {
  if (!addStageDialogEl || currentFeatureId !== featureId) {
    addStageDialogEl = document.createElement('chromedash-add-stage-dialog');
    addStageDialogEl.featureId = featureId;
    addStageDialogEl.featureType = featureType;
    document.body.appendChild(addStageDialogEl);
    await addStageDialogEl.updateComplete;
  }
  currentFeatureId = featureId;
  addStageDialogEl.show();
}


class ChromedashAddStageDialog extends LitElement {
  static get properties() {
    return {
      featureId: {type: Number},
      featureType: {type: Number},
      canSubmit: {type: Boolean},
    };
  }

  constructor() {
    super();
    this.featureId = 0;
    this.featureType = 0;
    this.canSubmit = false;
  }

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
      #controls {
        padding: var(--content-padding);
        text-align: right;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      #controls * + * {
        padding-left: var(--content-padding);
      }
      `,
    ];
  }

  show() {
    this.shadowRoot.querySelector('sl-dialog').show();
  }

  renderSelectMenuItems() {
    const menuItems = [];
    for (const stageType of CREATEABLE_STAGES[this.featureType]) {
      // Get the name of the stage from the form definition based on the stage type.
      const stageInfo = FORMS_BY_STAGE_TYPE[stageType];
      menuItems.push(html`
      <sl-option value="${stageType}">
        ${stageInfo.name}
      </sl-option>
      `);
    }
    return menuItems;
  }

  getStageSelectValue() {
    const selectEl = this.shadowRoot.querySelector('#stage_create_select');
    return selectEl.value;
  }

  handleStageCreate() {
    window.csClient.createStage(this.featureId, {stage_type: this.getStageSelectValue()})
      .then(() => {
        this.shadowRoot.querySelector('sl-dialog').hide();
        location.reload();
      });
  }

  checkCanSubmit() {
    this.canSubmit = this.getStageSelectValue() !== 0;
  }

  renderStageSelect() {
    return html`
    <div id="controls">
      <sl-select
        placement="top" hoist
        value=0
        id="stage_create_select"
        size="small"
        @sl-change=${this.checkCanSubmit}
        style="width:16rem"
      >
        <sl-option value="0" disabled>Select a stage to create</sl-option>
        ${this.renderSelectMenuItems()}
      </sl-select>
      <sl-button variant="primary"
        @click=${this.handleStageCreate}
        ?disabled=${!this.canSubmit}
        size="small"
      >Create stage</sl-button>
    </div>
    `;
  }

  render() {
    return html`
      <sl-dialog label="Create a new stage">
        <p>Here, you can add additional stages to your feature as needed.</p>
        ${this.renderStageSelect()}
      </sl-dialog>
    `;
  }
}


customElements.define('chromedash-add-stage-dialog', ChromedashAddStageDialog);
