import {LitElement, css, html} from 'lit';
import {ref, createRef} from 'lit/directives/ref.js';
import {SHARED_STYLES} from '../css/shared-css.js';

let naRationalDialogEl;

export async function openNaRationaleDialog(gate) {
  if (!naRationalDialogEl) {
    naRationalDialogEl = document.createElement(
      'chromedash-na-rationale-dialog'
    );
    document.body.appendChild(naRationalDialogEl);
    await naRationalDialogEl.updateComplete;
  }
  return new Promise(resolve => {
    naRationalDialogEl.openOn(gate, resolve);
  });
}

export class ChromedashNaRationaleDialog extends LitElement {
  rationaleDialogRef = createRef();
  rationaleRef = createRef();

  static get properties() {
    return {
      gate: {attribute: false},
      resolve: {attribute: false},
    };
  }

  static get styles() {
    return [...SHARED_STYLES, css``];
  }

  constructor() {
    super();
    this.gate = {};
    this.resolve = function () {
      console.log('Missing resolve action');
    };
  }

  openOn(gate, resolve) {
    this.gate = gate;
    this.resolve = resolve;
    this.rationaleDialogRef.value.show();
  }

  handlePost() {
    this.resolve(this.rationaleRef.value.value);
    this.rationaleDialogRef.value.hide();
  }

  renderDialogContent() {
    return html`
      <p style="padding: var(--content-padding)">
        Please briefly explain why your feature does not require a review. Your
        response will be posted as a comment on this review gate and it will
        generate a notification to the reviewers. The ${this.gate.team_name}
        reviewers will still evaluate whether to give an "N/A" response or do a
        review.
      </p>
      <sl-textarea ${ref(this.rationaleRef)}></sl-textarea>
      <sl-button
        slot="footer"
        variant="primary"
        size="small"
        @click=${this.handlePost}
        >Post</sl-button
      >
    `;
  }

  render() {
    return html`
      <sl-dialog ${ref(this.rationaleDialogRef)} label="Request an N/A">
        ${this.renderDialogContent()}
      </sl-dialog>
    `;
  }
}

customElements.define(
  'chromedash-na-rationale-dialog',
  ChromedashNaRationaleDialog
);
