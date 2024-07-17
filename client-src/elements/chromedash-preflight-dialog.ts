import {LitElement, css, html, nothing} from 'lit';
import './chromedash-callout';
import {GATE_TEAM_ORDER, GATE_FINISHED_REVIEW_STATES} from './form-field-enums';
import {findFirstFeatureStage} from './utils';
import {SHARED_STYLES} from '../css/shared-css.js';
import {customElement, state} from 'lit/decorators.js';
import {Feature, StageDict} from '../js-src/cs-client';
import {GateDict} from './chromedash-gate-chip';
import {
  Action,
  Process,
  ProcessStage,
  ProgressItem,
} from './chromedash-gate-column';
import {Stage} from './chromedash-report-external-reviews-page';

let preflightDialogEl;

export async function openPreflightDialog(
  feature: Feature,
  progress: ProgressItem,
  process: Process,
  action: Action,
  stage: StageDict,
  feStage: StageDict,
  featureGates: GateDict[],
  url: string
) {
  if (!preflightDialogEl) {
    preflightDialogEl = document.createElement('chromedash-preflight-dialog');
    document.body.appendChild(preflightDialogEl);
    await preflightDialogEl.updateComplete;
  }
  preflightDialogEl.openWithContext(
    feature,
    progress,
    process,
    action,
    stage,
    feStage,
    featureGates,
    url
  );
}

export function somePendingPrereqs(action: Action, progress: ProgressItem) {
  return action.prerequisites.some(
    itemName => !progress.hasOwnProperty(itemName)
  );
}

export function somePendingGates(featureGates: GateDict[], feStage: StageDict) {
  return findPendingGates(featureGates, feStage).length > 0;
}

export function findPendingGates(featureGates: GateDict[], feStage: StageDict) {
  const gatesForStage = featureGates.filter(g => g.stage_id == feStage.id);
  const otherGates = gatesForStage.filter(g => g.team_name != 'API Owners');
  const pendingGates = otherGates.filter(
    g => !GATE_FINISHED_REVIEW_STATES.includes(g.state)
  );
  pendingGates.sort(
    (g1, g2) =>
      GATE_TEAM_ORDER.indexOf(g1.team_name) -
      GATE_TEAM_ORDER.indexOf(g2.team_name)
  );
  return pendingGates;
}

@customElement('chromedash-preflight-dialog')
export class ChromedashPreflightDialog extends LitElement {
  @state()
  private _feature!: Feature;
  @state()
  private _featureGates!: GateDict[];
  @state()
  private _progress!: ProgressItem;
  @state()
  private _process!: Process;
  @state()
  private _action!: Action;
  @state()
  private _stage!: StageDict;
  @state()
  private _feStage!: StageDict;
  @state()
  private _url!: string;

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        ol {
          list-style: none;
          padding: 0;
        }

        ol li {
          margin-top: 0.5em;
        }

        .missing-prereqs-list {
          padding-bottom: 1em;
        }

        .missing-prereqs-list li {
          list-style: circle;
          margin-left: 2em;
        }

        .edit-progress-item {
          visibility: hidden;
          margin-left: var(--content-padding-half);
        }

        .active .edit-progress-item,
        .missing-prereqs .edit-progress-item,
        .pending:hover .edit-progress-item,
        .done:hover .edit-progress-item {
          visibility: visible;
        }

        sl-button {
          float: right;
          margin: var(--content-padding-half);
        }
      `,
    ];
  }

  openWithContext(
    feature: Feature,
    progress: ProgressItem,
    process: Process,
    action: Action,
    stage: StageDict,
    feStage: StageDict,
    featureGates: GateDict[],
    url: string
  ) {
    this._feature = feature;
    this._progress = progress;
    this._process = process;
    this._action = action;
    this._stage = stage;
    this._feStage = feStage;
    this._featureGates = featureGates;
    this._url = url;
    this.renderRoot.querySelector('sl-dialog')?.show();
  }

  hide() {
    this.renderRoot.querySelector('sl-dialog')?.hide();
  }

  handleCancel() {
    this.hide();
  }

  handleProceed() {
    // The button opens a new tab due to the href and target attrs.
    // Also, close this dialog, so it is gone when the user returns.
    this.hide();
  }

  renderEditLink(stage: ProcessStage, feStage: StageDict, pi: ProgressItem) {
    if (pi.field && stage && feStage) {
      return html`
        <a
          class="edit-progress-item"
          href="/guide/stage/${this._feature
            .id}/${stage.outgoing_stage}/${feStage.id}#id_${pi.field}"
          @click=${this.hide}
        >
          Edit
        </a>
      `;
    }
    return nothing;
  }

  makePrereqItem(itemName) {
    for (const s of this._process.stages || []) {
      for (const pi of s.progress_items) {
        if (itemName == pi.name) {
          return {...pi, stage: s};
        }
      }
    }
    throw new Error('prerequiste is not a defined progress item');
  }

  renderDialogContent() {
    if (this._feature == null) {
      return nothing;
    }
    const prereqItems: ProgressItem[] = [];
    for (const itemName of this._action.prerequisites || []) {
      if (!this._progress.hasOwnProperty(itemName)) {
        prereqItems.push(this.makePrereqItem(itemName));
      }
    }
    const pendingGates = findPendingGates(this._featureGates, this._feStage);

    return html`
      Before you ${this._action.name}, it is strongly recommended that you do
      the following:
      <ol class="missing-prereqs-list">
        ${prereqItems.map(
          item =>
            html` <li class="pending">
              ${item.stage.name}: ${item.name}
              ${this.renderEditLink(
                item.stage,
                findFirstFeatureStage(
                  item.stage.outgoing_stage,
                  this._stage,
                  this._feature
                ),
                item
              )}
            </li>`
        )}
        ${pendingGates.map(
          g => html`
            <li class="pending">
              Get approval or NA from the
              <a
                href="/feature/${this._feature.id}?gate=${g.id}"
                @click=${this.hide}
                >${g.team_name}</a
              >
              team
            </li>
          `
        )}
      </ol>

      <sl-button
        href="${this._url}"
        target="_blank"
        size="small"
        @click=${this.handleProceed}
        >Proceed anyway
      </sl-button>
      <sl-button size="small" variant="warning" @click=${this.handleCancel}
        >Don't draft email yet</sl-button
      >
    `;
  }

  render() {
    return html`
      <sl-dialog
        class="missing-prereqs"
        label="Missing Prerequisites"
        style="--width:fit-content"
      >
        ${this.renderDialogContent()}
      </sl-dialog>
    `;
  }
}
