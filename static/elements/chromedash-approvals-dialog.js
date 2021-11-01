import {LitElement, css, html} from 'lit-element';
import {nothing} from 'lit-html';
import './chromedash-dialog';
import SHARED_STYLES from '../css/shared.css';

const STATE_NAMES = [
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
      changedApprovalsByField: {type: Map},
      needsSave: {type: Boolean},
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
    this.changedApprovalsByField = new Map();
    this.needsSave = false;
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

        .comment_section {
          max-height: 250px;
          overflow: scroll;
        }

        .approval_section div,
        .comment {
          margin-left: var(--content-padding);
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

        .comment_body {
          background: var(--table-alternate-background);
          padding: var(--content-padding-half);
          white-space: pre-wrap;
          width: 46em;
          margin-bottom: var(--content-padding);
        }

        .controls {
          padding: var(--content-padding);
          text-align: right;
        }

        #show_all_checkbox {
         float: left;
        }

        textarea {
          padding: 4px;
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
        this.changedApprovalsByField = new Map();
        this.needsSave = false;
      });
    const p3 = window.csClient.getComments(this.featureId).then(
      (res) => {
        this.comments = res.comments;
      });
    Promise.all([p1, p2, p3]).then(() => {
      // Clear out any previously typed comment.
      this.shadowRoot.querySelector('#comment_area').value = '';
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
    const selectedValue = (
      this.changedApprovalsByField.get(approvalValue.field_id) ||
          approvalValue.state);
    let placeholderOption = nothing;
    if (approvalValue.state == -1) {
      placeholderOption = html`
        <option value="-1" selected>No value</option>
      `;
    }

    return html`
      <div class="approval_row">
        <span class="set_by">${approvalValue.set_by}</span>
        ${approvalValue.set_by == this.signedInUser ? html`
        <select
          selected=${selectedValue}
          data-field="${approvalValue.field_id}"
          @change=${this.handleSelectChanged}
        >
            ${placeholderOption}
            ${STATE_NAMES.map((valName) => html`
              <option value="${valName[0]}"
                ?selected=${valName[0] == selectedValue}
               >${valName[1]}</option>`
              )}
          </select>` : html`
          ${STATE_NAMES[approvalValue.state][1]}
          `}
       </div>
    `;
  }

  renderAddApproval(fieldId) {
    const existingApprovalByMe = this.approvals.some((a) =>
      a.field_id == fieldId);
    if (existingApprovalByMe) {
      return nothing;
    } else {
      return this.renderApprovalValue(
        {set_by: this.signedInUser, state: -1, field_id: fieldId});
    }
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
        ${this.renderAddApproval(approvalDef.id)}
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
      <div class="comment">
        <div class="comment_header">
           <span class="author"">${comment.author}</span>
           on
           <span class="date"">${comment.created}</span>
           wrote:
        </div>
        <div class="comment_body">${comment.content}</div>
      </div>
    `;
  }

  renderAllComments() {
    return html`
        <h3>Comments</h3>
        <div class="comment_section">
          ${this.comments.map(this.renderComment)}
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
     <div>
      <textarea id="comment_area" rows=4 cols=80
        @change=${this.checkNeedsSave}
        @keypress=${this.checkNeedsSave}
        placeholder="Add a comment"
        ></textarea>
     </div>
     <div class="controls">
       ${showAllCheckbox}
       <label id="post_link_dev" style="margin-right:1em"><input
         type="checkbox"
         >Post to blink-dev</label>
       <button class="primary"
         @click=${this.handleSave}
         ?disabled=${!this.needsSave}
         >Save</button>
       <button
         @click=${this.handleCancel}
         >Cancel</button>
     </div>
    `;
  }

  render() {
    const dialogName = this.feature && this.feature.name || '';
    return html`
      <chromedash-dialog name="${dialogName}">
        ${this.renderLoading()}
        ${this.renderAllApprovals()}
        ${this.renderAllComments()}
        ${this.renderControls()}
      </chromedash-dialog>
    `;
  }

  checkNeedsSave() {
    console.log('In checkNeedsSave()');
    let newNeedsSave = false;
    const commentArea = this.shadowRoot.querySelector('#comment_area');
    const newVal = commentArea.value;
    if (newVal != '') newNeedsSave = true;
    for (let fieldId of this.changedApprovalsByField.keys()) {
      if (this.changedApprovalsByField.get(fieldId) != -1) {
        newNeedsSave = true;
      }
    }
    this.needsSave = newNeedsSave;
    console.log(this.needsSave);
  }

  handleSelectChanged(e) {
    const fieldId = e.target.dataset['field'];
    const newVal = e.target.value;
    this.changedApprovalsByField.set(fieldId, newVal);
    this.checkNeedsSave();
  }

  handleSave() {
    const promises = [];
    for (let fieldId of this.changedApprovalsByField.keys()) {
      if (this.changedApprovalsByField.get(fieldId) != -1) {
        promises.push(
          window.csClient.setApproval(
            this.feature.id, fieldId,
            this.changedApprovalsByField.get(fieldId)));
      }
    }
    const commentArea = this.shadowRoot.querySelector('#comment_area');
    const commentText = commentArea.value;
    if (commentText != '') {
      promises.push(
        window.csClient.postComment(
          this.feature.id, null, null, commentText));
    }
    Promise.all(promises).then(() => {
      this.shadowRoot.querySelector('chromedash-dialog').close();
    });
  }

  handleCancel() {
    this.shadowRoot.querySelector('chromedash-dialog').close();
  }
}

customElements.define('chromedash-approvals-dialog', ChromedashApprovalsDialog);
