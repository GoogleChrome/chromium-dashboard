import {LitElement, css, html} from 'lit-element';
import './chromedash-dialog';
import SHARED_STYLES from '../css/shared.css';

class ChromedashApprovalsDialog extends LitElement {
  static get properties() {
    return {
      signedInUser: {type: String},
      featureId: {type: Number},
      canApprove: {type: Boolean},
    };
  }

  constructor() {
    super();
    this.signedInUser = ''; // email address
    this.canApprove = false;
  }

  static get styles() {
    return [
      SHARED_STYLES,
      css`
      `];
  }

  openWithFeature(featureId) {
    this.featureId = featureId;
    this.shadowRoot.querySelector('chromedash-dialog').open();
  }

  render() {
    const heading = 'TODO: Feature name';
    return html`
      <chromedash-dialog heading="${heading}">
        TODO: dialog content
      </chromedash-dialog>
    `;
  }
}

customElements.define('chromedash-approvals-dialog', ChromedashApprovalsDialog);
