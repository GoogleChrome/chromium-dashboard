import {LitElement, css, html} from 'lit-element';
import {nothing} from 'lit-html';
import './chromedash-dialog';
import SHARED_STYLES from '../css/shared.css';

class ChromedashApprovalsDialog extends LitElement {
  static get properties() {
    return {
      featureId: {type: Number},
      feature: {type: Object},
      approvals: {type: Array},
      comments: {type: Array},
      canApprove: {type: Boolean},
    };
  }

  constructor() {
    super();
    this.featureId = 0;
    this.feature = {};
    this.approvals = [];
    this.comments = [];
    this.canApprove = false;
  }

  connectedCallback() {
    super.connectedCallback();
  }

  static get styles() {
    return [
      SHARED_STYLES,
      css`
        .set_by {
          width: 6em;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          display: inline-block;
        }
      `];
  }

  updated(changedProperties) {
    if (changedProperties.has('featureId')) {
      this.featureIdChanged();
    }
  }

  featureIdChanged() {
    if (!this.featureId) {
      return;
    }
    console.log(this.featureId);
    const p1 = window.csClient.getFeature(this.featureId).then(
      (feature) => {
        this.feature = feature;
      });
    const p2 = window.csClient.getApprovals(this.featureId).then(
      (res) => {
        this.approvals = res.approvals;
      });
    const p3 = window.csClient.getComments(this.featureId).then(
      (res) => {
        this.comments = res.comments;
      });
    console.log('waiting');
    Promise.all([p1, p2, p3]).then(() => {
      console.log('waited');
      this.shadowRoot.querySelector('chromedash-dialog').open();
    });
  }

  renderLoading() {
    if (this.feature === {}) {
      return html`<p>Loading...</p`;
    } else {
      return nothing;
    }
  }

  renderApproval(approvalName) { // , approvalValues
    return html`
      <div class="approval_row">
        <h3>${approvalName}</h3>
        <div>
          <span class="set_by">Set by: TODO</span>
          <select>
            <option value="-1">No value</option>
            <option value="0>Needs review</option>
            <option value="1">N/a or Ack</option>
            <option value="3">Review started</option>
            <option value="4">Need info</option>
            <option value="5">Approved</option>
            <option value="6">Not approved</option>
          </select>
         </div>
        <div><a href="#" target="_blank">blink-dev thread</a></div>
      </div>
    `;
  }

  renderAllApprovals() {
    const prototype = this.renderApproval(
      'Intent to Prototype',
      this.approvals.filter((a) => a.field_id == 1));
    const experiment = this.renderApproval(
      'Intent to Experiment',
      this.approvals.filter((a) => a.field_id == 2));
    const extend = this.renderApproval(
      'Intent to Extend Experiment',
      this.approvals.filter((a) => a.field_id == 3));
    const ship = this.renderApproval(
      'Intent to Ship',
      this.approvals.filter((a) => a.field_id == 4));
    return [prototype, experiment, extend, ship];
  }

  renderComment(comment) {
    return html`
      <div class="comment_section">
        <div class="comment_header">
           <span class="author"">author name</span>
           on
           <span class="date"">date</span>
           wrote:
        </div>
        <div class="comment_body">
          <pre>${comment.content}</pre>
        </div>
      </div>
    `;
  }


  renderControls() {
    return html`
     <div class="controls">
       <button>Save</button>
       <button>Cancel</button>
     </div>
    `;
  }

  render() {
    console.log('this.comments');
    console.log(this.comments);
    return html`
      <chromedash-dialog>
        ${this.renderLoading()}
        ${this.renderAllApprovals()}
        ${this.comments.map(this.renderComment)}
        ${this.renderControls()}
      </chromedash-dialog>
    `;
  }
}

customElements.define('chromedash-approvals-dialog', ChromedashApprovalsDialog);
