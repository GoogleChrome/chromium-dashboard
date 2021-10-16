import {LitElement, css, html} from 'lit-element';
import {nothing} from 'lit-html';
import './chromedash-dialog';
import SHARED_STYLES from '../css/shared.css';

const STATE_NAMES = [
  [-1, 'No value'],
  [0, 'Needs review'],
  [1, 'N/a or Ack'],
  [3, 'Review started'],
  [4, 'Need info'],
  [5, 'Approved'],
  [6, 'Not approved'],
];


class ChromedashApprovalsDialog extends LitElement {
  static get properties() {
    return {
      signedInUser: {type: String},
      featureId: {type: Number},
      feature: {type: Object},
      approvals: {type: Array},
      comments: {type: Array},
      canApprove: {type: Boolean},
    };
  }

  constructor() {
    super();
    this.signedInUser = ''; // email address
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
        h3 {
          margin-bottom: var(--content-padding-half);
        }

        .approval_section div {
          margin-left: var(--content-padding-half);
        }

        .approval_row {
          width: 30em;
          margin-bottom: var(--content-padding-half);
        }

        .set_by {
          width: 16em;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          display: inline-block;
        }

        .controls {
          padding: var(--content-padding);
          text-align: right;
        }

      `];
  }

  openWithFeature(featureId) {
    this.featureId = featureId;
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
    Promise.all([p1, p2, p3]).then(() => {
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

  renderApprovalValue(approvalValue) {
    return html`
      <div class="approval_row">
        <span class="set_by">${approvalValue.set_by}</span>
        ${approvalValue.set_by == this.signedInUser ? html`
          <select value=${approvalValue.state}>
            ${STATE_NAMES.map((valName) => html`
              <option value="${valName[0]}">${valName[1]}</option>`
              )}
          </select>` : html`
          ${STATE_NAMES[approvalValue.state + 1][1]}
          `}
       </div>
    `;
  }

  renderAddApproval() {
    // conditional
    return this.renderApprovalValue(
      {set_by: this.signedInUser, value: -1});
  }

  renderApproval(approvalName, approvalValues, threadField) {
    let threadLink = nothing;
    if (this.feature[threadField]) {
      threadLink = html`
        <div>
          <a href="${this.feature[threadField]}" target="_blank"
             >blink-dev thread</a>
        </div>
      `;
    }

    return html`
      <div class="approval_section">
        <h3>${approvalName}</h3>
        ${approvalValues.map(this.renderApprovalValue.bind(this))}
        ${this.renderAddApproval()}
        ${threadLink}
      </div>
    `;
  }

  renderAllApprovals() {
    const prototype = this.renderApproval(
      'Intent to Prototype',
      this.approvals.filter((a) => a.field_id == 1),
      'intent_to_implement_url');
    const experiment = this.renderApproval(
      'Intent to Experiment',
      this.approvals.filter((a) => a.field_id == 2),
      'intent_to_experiment_url');
    const extend = this.renderApproval(
      'Intent to Extend Experiment',
      this.approvals.filter((a) => a.field_id == 3),
      'intent_to_extend_experiment_url');
    const ship = this.renderApproval(
      'Intent to Ship',
      this.approvals.filter((a) => a.field_id == 4),
      'intent_to_ship_url');
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
       <button class="primary">Save</button>
       <button>Cancel</button>
     </div>
    `;
  }

  render() {
    const title = this.feature && this.feature.name || '';
    return html`
      <chromedash-dialog title="${title}">
        ${this.renderLoading()}
        ${this.renderAllApprovals()}
        ${this.comments.map(this.renderComment)}
        ${this.renderControls()}
      </chromedash-dialog>
    `;
  }
}

customElements.define('chromedash-approvals-dialog', ChromedashApprovalsDialog);
