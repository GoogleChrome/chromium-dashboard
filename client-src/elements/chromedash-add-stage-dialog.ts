import {LitElement, TemplateResult, css, html} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';
import {CREATEABLE_STAGES, FORMS_BY_STAGE_TYPE} from './form-definition.js';
import {customElement, property, query} from 'lit/decorators.js';

let addStageDialogEl;
let currentFeatureId;

export async function openAddStageDialog(
  featureId,
  featureType,
  onSubmitCustomHandler?
) {
  if (
    !addStageDialogEl ||
    currentFeatureId !== featureId ||
    onSubmitCustomHandler !== addStageDialogEl.onSubmitCustomHandler
  ) {
    addStageDialogEl = document.createElement('chromedash-add-stage-dialog');
    addStageDialogEl.featureId = featureId;
    addStageDialogEl.featureType = featureType;
    addStageDialogEl.onSubmitCustomHandler = onSubmitCustomHandler;
    document.body.appendChild(addStageDialogEl);
    await addStageDialogEl.updateComplete;
  }
  currentFeatureId = featureId;
  addStageDialogEl.show();
}

@customElement('chromedash-add-stage-dialog')
class ChromedashAddStageDialog extends LitElement {
  @property({type: Number})
  featureId = 0;
  @property({type: Number})
  featureType = 0;
  @property({type: Boolean})
  canSubmit = false;
  @property({attribute: false})
  onSubmitCustomHandler: ((stage: {stage_type: number}) => void) | null = null;

  @query('#stage_create_select')
  stageCreateSelect;
  @query('sl-dialog')
  dialog;

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
    this.dialog.show();
  }

  renderSelectMenuItems() {
    const menuItems: TemplateResult[] = [];
    for (const stageType of CREATEABLE_STAGES[this.featureType]) {
      // Get the name of the stage from the form definition based on the stage type.
      const stageInfo = FORMS_BY_STAGE_TYPE[stageType];
      menuItems.push(html`
        <sl-option value="${stageType}"> ${stageInfo.name} </sl-option>
      `);
    }
    return menuItems;
  }

  getStageSelectValue() {
    return this.stageCreateSelect.value;
  }

  handleStageCreate() {
    if (this.onSubmitCustomHandler) {
      this.onSubmitCustomHandler({
        stage_type: Number(this.getStageSelectValue()),
      });
      this.onSubmitCustomHandler = null;
      this.dialog.hide();
      return;
    }
    window.csClient
      .createStage(this.featureId, {
        stage_type: {
          form_field_name: 'stage_type',
          value: this.getStageSelectValue(),
        },
      })
      .then(() => {
        this.dialog.hide();
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
          placement="top"
          hoist
          value="0"
          id="stage_create_select"
          size="small"
          @sl-change=${this.checkCanSubmit}
          style="width:16rem"
        >
          <sl-option value="0" disabled>Select a stage to create</sl-option>
          ${this.renderSelectMenuItems()}
        </sl-select>
        <sl-button
          variant="primary"
          @click=${this.handleStageCreate}
          ?disabled=${!this.canSubmit}
          size="small"
          >Create stage</sl-button
        >
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
