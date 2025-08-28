import {LitElement, css, html, nothing} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';
import {findPendingGates} from './chromedash-preflight-dialog';
import {VOTE_OPTIONS} from './form-field-enums';
import {customElement, property} from 'lit/decorators.js';
import {GateDict} from './chromedash-gate-chip.js';
import {Feature, StageDict} from '../js-src/cs-client';

let prevoteDialogEl;

export interface MissingFieldItem {
  name: string;
  field: string;
}

export function findMissingFields(feature: Feature): MissingFieldItem[] {
  const missingFields: MissingFieldItem[] = [];
  if (!feature.web_feature || feature.web_feature === 'Missing feature') {
    missingFields.push({name: 'Web feature', field: 'web_feature'});
  }
  return missingFields;
}

export function shouldShowPrevoteDialog(
  feature: Feature,
  pendingGates: GateDict[],
  gate: GateDict,
  vote: number
) {
  return (
    (pendingGates.length > 0 || findMissingFields(feature).length > 0) &&
    gate.team_name == 'API Owners' &&
    vote == VOTE_OPTIONS.APPROVED[0]
  );
}

export async function maybeOpenPrevoteDialog(
  feature: Feature,
  featureGates: GateDict[],
  stage: StageDict,
  gate: GateDict,
  vote: number
) {
  const pendingGates = findPendingGates(featureGates, stage);
  if (shouldShowPrevoteDialog(feature, pendingGates, gate, vote)) {
    return new Promise(resolve => {
      openPrevoteDialog(feature, pendingGates, resolve);
    });
  } else {
    return Promise.resolve();
  }
}

async function openPrevoteDialog(feature, pendingGates, resolve) {
  if (!prevoteDialogEl) {
    prevoteDialogEl = document.createElement('chromedash-prevote-dialog');
    document.body.appendChild(prevoteDialogEl);
  }
  prevoteDialogEl.feature = feature;
  prevoteDialogEl.pendingGates = pendingGates;
  prevoteDialogEl.resolve = resolve;
  await prevoteDialogEl.updateComplete;
  prevoteDialogEl.show();
}

@customElement('chromedash-prevote-dialog')
class ChromedashPrevoteDialog extends LitElement {
  @property({type: Object})
  feature!: Feature;
  @property({type: Array})
  pendingGates!: GateDict[];
  @property({attribute: false})
  resolve: (value?: string) => void = () => {
    console.log('Missing resolve action');
  };

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        #prereqs-list li {
          margin-left: 8px;
          margin-bottom: 8px;
          list-style: circle;
        }
        #prereqs-header {
          margin-bottom: 8px;
        }
        sl-button {
          float: right;
          margin: var(--content-padding-half);
        }
      `,
    ];
  }

  show() {
    this.renderRoot.querySelector('sl-dialog')?.show();
  }

  hide() {
    this.renderRoot.querySelector('sl-dialog')?.hide();
  }

  handleCancel() {
    // Note: promise is never resolved.
    this.hide();
  }

  handleProceed() {
    this.resolve();
    this.hide();
  }

  renderGateItem(gate) {
    return html`
      <li>
        <a
          href="/feature/${gate.feature_id}?gate=${gate.id}"
          @click=${this.hide}
          >${gate.team_name}</a
        >
      </li>
    `;
  }

  renderGatesSection() {
    if (this.pendingGates === undefined) {
      return html`Loading gates...`;
    }

    return html`
      <div id="gates-header">The following gates are missing approvals:</div>
      <br />
      <ul id="gates-list">
        ${this.pendingGates.map(gate => this.renderGateItem(gate))}
      </ul>
    `;
  }

  renderEditLink(item: MissingFieldItem) {
    return html`
      <a
        class="edit-progress-item"
        href="/guide/stage/${this.feature.id}/metadata#id_${item.field}"
        @click=${this.hide}
      >
        Edit
      </a>
    `;
  }

  renderFieldItem(item: MissingFieldItem) {
    return html` <li class="pending">
      'Metadata:' ${item.name} ${this.renderEditLink(item)}
    </li>`;
  }

  renderFieldsSection() {
    const missingFields: MissingFieldItem[] = findMissingFields(this.feature);
    if (missingFields.length == 0) {
      return nothing;
    }
    return html`
      <div id="fields-header">
        The following prerequisite fields are missing:
      </div>
      <br />
      <ul id="fields-list">
        ${missingFields.map(mf => this.renderFieldItem(mf))}
      </ul>
    `;
  }

  render() {
    return html` <sl-dialog label="Prerequsites for API Owner approval">
      ${this.renderFieldsSection()} ${this.renderGatesSection()}
      <br />
      <sl-button size="small" @click=${this.handleProceed}
        >Approve anyway</sl-button
      >
      <sl-button size="small" variant="warning" @click=${this.handleCancel}
        >Don't approve yet</sl-button
      >
    </sl-dialog>`;
  }
}
