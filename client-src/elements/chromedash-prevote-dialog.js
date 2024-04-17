import {LitElement, css, html} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';
import {findPendingGates} from './chromedash-preflight-dialog';
import {VOTE_OPTIONS} from './form-field-enums';

let prevoteDialogEl;

function shouldShowPrevoteDialog(pendingGates, gate, vote) {
  return (
    pendingGates.length > 0 &&
    gate.team_name == 'API Owners' &&
    vote == VOTE_OPTIONS.APPROVED[0]
  );
}

export async function maybeOpenPrevoteDialog(featrureGates, stage, gate, vote) {
  const pendingGates = findPendingGates(featrureGates, stage);
  if (shouldShowPrevoteDialog(pendingGates, gate, vote)) {
    return new Promise(resolve => {
      openPrevoteDialog(pendingGates, resolve);
    });
  } else {
    return Promise.resolve();
  }
}

async function openPrevoteDialog(pendingGates, resolve) {
  if (!prevoteDialogEl) {
    prevoteDialogEl = document.createElement('chromedash-prevote-dialog');
    document.body.appendChild(prevoteDialogEl);
  }
  await prevoteDialogEl.updateComplete;
  prevoteDialogEl.pendingGates = pendingGates;
  prevoteDialogEl.resolve = resolve;
  prevoteDialogEl.show();
}

class ChromedashPrevoteDialog extends LitElement {
  static get properties() {
    return {
      pendingGates: {type: Array},
      resolve: {attribute: false},
    };
  }

  constructor() {
    super();
    this.pendingGates = [];
    this.resolve = function () {
      console.log('Missing resolve action');
    };
  }

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
    this.shadowRoot.querySelector('sl-dialog').show();
  }

  hide() {
    this.shadowRoot.querySelector('sl-dialog').hide();
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

  render() {
    return html` <sl-dialog label="Prerequsites for API Owner approval">
      <div id="prereqs-header">
        The following prerequisite gates are missing approvals:
      </div>
      <br />
      <ul id="prereqs-list">
        ${this.pendingGates.map(gate => this.renderGateItem(gate))}
      </ul>
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

customElements.define('chromedash-prevote-dialog', ChromedashPrevoteDialog);
