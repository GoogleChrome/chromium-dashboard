import {LitElement, css, html} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';
import {customElement, property} from 'lit/decorators.js';
import {GateDict} from './chromedash-gate-chip.js';

let certifyDialogEl;

function shouldShowCertifyDialog(gate: GateDict): boolean {
  return gate.self_certify_possible;
}

export async function maybeOpenCertifyDialog(gate: GateDict) {
  if (shouldShowCertifyDialog(gate)) {
    return new Promise(resolve => {
      openCertifyDialog(gate, resolve);
    });
  } else {
    return Promise.resolve();
  }
}

async function openCertifyDialog(gate, resolve) {
  if (!certifyDialogEl) {
    certifyDialogEl = document.createElement('chromedash-self-certify-dialog');
    document.body.appendChild(certifyDialogEl);
  }
  await certifyDialogEl.updateComplete;
  certifyDialogEl.gate = gate;
  certifyDialogEl.resolve = resolve;
  certifyDialogEl.show();
}


@customElement('chromedash-self-certify-dialog')
class ChromedashSelfCertifyDialog extends LitElement {
  @property({type: Object})
  gate!: GateDict;
  @property({attribute: false})
  resolve: (value?: boolean) => void = () => {
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

  handleSelfCertify() {
    this.resolve(true);
    this.hide();
  }

  handleFullReview() {
    this.resolve(false);
    this.hide();
  }

  renderContentWhenNotEligible() {
    return html`
      <div id="prereqs-header">
    This review gate allows for self-certification rather than a full
    review.  However, the answers to the survey questions do not qualify
    for self-certification.
      </div>
      <br />
      <sl-button size="small" @click=${this.handleFullReview}
        >Request full review</sl-button
      >
      <sl-button size="small" @click=${this.handleCancel}
        >Go back to survey answers</sl-button
      >
    `;
  }

  renderContentWhenEligible() {
    return html`
      <div id="prereqs-header">
    Based on your answers to the survey questions, you may self-certify
    an approval for this gate.  Alternatively, if you want to start a
    consulation with the review team, you may request a full review.
      </div>
      <br />
      <sl-button size="small" @click=${this.handleFullReview}
        >Request full review</sl-button
      >
      <sl-button size="small" variant="primary" @click=${this.handleSelfCertify}
        >Self-certify approval</sl-button
      >
    `;
  }


  render() {
    if (this.gate === undefined) {
      return html`Loading gates...`;
    }

    return html`
    <sl-dialog label="Self-certification">
    ${this.gate.self_certify_eligible ? this.renderContentWhenEligible() :
      this.renderContentWhenNotEligible()}
    </sl-dialog>`;
  }
}
