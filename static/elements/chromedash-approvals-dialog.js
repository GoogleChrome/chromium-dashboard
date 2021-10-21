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
const ACTIVE_STATES = [0, 3, 4];

const APPROVAL_DEFS = [
  {name: 'Intent to Prototype',
    id: 1,
    threadField: 'intent_to_implement_url',
  },
  {name: 'Intent to Experiment',
    id: 2,
    threadField: 'intent_to_experiment_url',
  },
  {name: 'Intent to Extend Experiment',
    id: 3,
    threadField: 'intent_to_extend_experiment_url',
  },
  {name: 'Intent to Ship',
    id: 4,
    threadField: 'intent_to_ship_url',
  },
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
      showAllIntents: {type: Boolean},
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
    this.subsetPending = false;
    this.showAllIntents = false;
  }

  connectedCallback() {
    super.connectedCallback();
  }

  static get styles() {
    return [
      SHARED_STYLES,
      css`
        h3 {
          margin: var(--content-padding-half);
        }

        .approval_section {
          margin-top: var(--content-padding);
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

        #show_all_checkbox {
         float: left;
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
        const numPending = this.approvals.filter((av) =>
          ACTIVE_STATES.includes(av.state)).length;
        this.subsetPending = (numPending > 0 &&
                              numPending < APPROVAL_DEFS.length);
        this.showAllIntents = numPending == 0;
      });
    const p3 = window.csClient.getComments(this.featureId).then(
      (res) => {
        this.comments = res.comments;
      });
    Promise.all([p1, p2, p3]).then(() => {
      this.shadowRoot.querySelector('chromedash-dialog').open();
    });
  }


  toggleShowAllIntents() {
    this.showAllIntents = !this.showAllIntents;
  }

  renderLoading() {
    if (this.feature === {}) {
      return html`<p>Loading...</p>`;
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

  renderApproval(approvalDef) {
    const approvalValues = this.approvals.filter((a) =>
      a.field_id == approvalDef.id);
    const isActive = approvalValues.some((av) =>
      ACTIVE_STATES.includes(av.state));

    if (!isActive && !this.showAllIntents) return nothing;

    let threadLink = nothing;
    if (this.feature[approvalDef.threadField]) {
      threadLink = html`
        <div>
          <a href="${this.feature[approvalDef.threadField]}" target="_blank"
             >blink-dev thread</a>
        </div>
      `;
    }

    return html`
      <div class="approval_section">
        <h3>${approvalDef.name}</h3>
        ${approvalValues.map((av) => this.renderApprovalValue(av))}
        ${this.renderAddApproval()}
        ${threadLink}
      </div>
    `;
  }

  renderAllApprovals() {
    return APPROVAL_DEFS.map((apprDef) =>
      this.renderApproval(apprDef));
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
    let showAllCheckbox = nothing;
    if (this.subsetPending) {
      showAllCheckbox = html`
         <label id="show_all_checkbox"><input
          type="checkbox" ?checked=${this.showAllIntents}
          @click=${this.toggleShowAllIntents}
          >Show all intents</label>
      `;
    }

    return html`
     <div style="margin-top:2em">
      <textarea rows=4 cols=80></textarea>
     </div>
     <div class="controls">
       ${showAllCheckbox}
         <label id="post_link_dev" style="margin-right:1em"><input
          type="checkbox"
          >Post to blink-dev</label>
       <button class="primary">Save</button>
       <button>Cancel</button>
     </div>
    `;
  }

  render() {
    const dialogName = this.feature && this.feature.name || '';
    return html`
      <chromedash-dialog name="${dialogName}">
        ${this.renderLoading()}
        ${this.renderAllApprovals()}
        ${this.comments.map(this.renderComment)}
        ${this.renderControls()}
      </chromedash-dialog>
    `;
  }
}

customElements.define('chromedash-approvals-dialog', ChromedashApprovalsDialog);
