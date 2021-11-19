import {LitElement, css, html} from 'lit-element';
import {nothing} from 'lit-html';
import './chromedash-dialog';
import SHARED_STYLES from '../css/shared.css';

const STATE_NAMES = [
  // Not used: [0, 'Needs review'],
  [1, 'N/a or Ack'],
  [2, 'Review requested'],
  [3, 'Review started'],
  [4, 'Need info'],
  [5, 'Approved'],
  [6, 'Not approved'],
];
const PENDING_STATES = [2, 3, 4];

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
      canApprove: {type: Boolean},
      feature: {type: Object},
      approvals: {type: Array},
      comments: {type: Array},
      showAllIntents: {type: Boolean},
      changedApprovalsByField: {attribute: false},
      needsSave: {type: Boolean},
      loading: {attribute: false},
    };
  }

  constructor() {
    super();
    this.signedInUser = ''; // email address
    this.canApprove = false;
    this.featureId = 0;
    this.feature = {};
    this.approvals = [];
    this.comments = [];
    this.subsetPending = false;
    this.showAllIntents = false;
    this.changedApprovalsByField = new Map();
    this.needsSave = false;
    this.loading = true;
  }

  static get styles() {
    return [
      SHARED_STYLES,
      css`
        .loading {
          width: 650px;
          height: 400px;
        }

        h3 {
          margin: var(--content-padding-half);
        }

        .approval_section {
          margin-top: var(--content-padding);
        }

        .comment_section {
          max-height: 250px;
          overflow-y: scroll;
        }

        .approval_section div,
        .comment {
          margin-left: var(--content-padding);
        }

        .approval_row {
          width: 650px;
          margin-bottom: var(--content-padding-half);
        }

        .set_by,
        .set_on,
        .appr_val {
          display: inline-block;
          width: 200px;
          margin-right: var(--content-padding-half);
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        select {
          margin: 0;
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
          resize: both;
        }
      `];
  }

  openWithFeature(featureId) {
    this.featureId = featureId;
    this.loading = true;
    this.shadowRoot.querySelector('chromedash-dialog').open();
    const p1 = window.csClient.getFeature(this.featureId).then(
      (feature) => {
        this.feature = feature;
      });
    const p2 = window.csClient.getApprovals(this.featureId).then(
      (res) => {
        this.approvals = res.approvals;
        const numPending = this.approvals.filter((av) =>
          PENDING_STATES.includes(av.state)).length;
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
      this.loading = false;
    });
  }

  toggleShowAllIntents() {
    this.showAllIntents = !this.showAllIntents;
  }

  formatDate(dateStr) {
    return dateStr.split('.')[0]; // Ignore microseconds.
  }

  findStateName(state) {
    for (let item of STATE_NAMES) {
      if (item[0] == state) {
        return item[1];
      }
    }
    // This should not normally be seen by users, but it will help us
    // cope with data migration.
    return `State ${state}`;
  }

  renderApprovalValue(approvalValue) {
    const selectedValue = (
      this.changedApprovalsByField.get(approvalValue.field_id) ||
          approvalValue.state);
    const placeholderOption = (approvalValue.state == -1) ?
      html`<option value="-1" selected>No value</option>` :
      nothing;

    return html`
      <div class="approval_row">
        <span class="set_by">${approvalValue.set_by}</span>
        <span class="set_on">${this.formatDate(approvalValue.set_on)}</span>
        <span class="appr_val">
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
           ${this.findStateName(approvalValue.state)}
            `}
        </span>
      </div>
    `;
  }

  renderAddApproval(fieldId) {
    const existingApprovalByMe = this.approvals.some((a) =>
      a.field_id == fieldId && a.set_by == this.signedInUser);
    if (existingApprovalByMe) {
      return nothing;
    } else {
      return this.renderApprovalValue(
        {set_by: this.signedInUser,
          set_on: '',
          state: -1,
          field_id: fieldId});
    }
  }

  renderApproval(approvalDef) {
    const approvalValues = this.approvals.filter((a) =>
      a.field_id == approvalDef.id);
    const isActive = approvalValues.some((av) =>
      PENDING_STATES.includes(av.state));

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
           <span class="author">${comment.author}</span>
           on
           <span class="date">${this.formatDate(comment.created)}</span>
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
          ${this.comments.map(this.renderComment.bind(this))}
        </div>
    `;
  }

  canPostTo(threadArchiveUrl) {
    return (
      threadArchiveUrl &&
        (threadArchiveUrl.startsWith(
          'https://groups.google.com/a/chromium.org/d/msgid/blink-dev/') ||
         threadArchiveUrl.startsWith(
           'https://groups.google.com/d/msgid/jrobbins-test')));
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
    let postToSelect = html`
      <select style="margin-right:1em" id="post_to_approval_field">
        <option value="0">Don't post to mailing list</option>
        ${APPROVAL_DEFS.map((apprDef) => html`
          <option value="${apprDef.id}"
                  ?disabled=${!this.canPostTo(this.feature[apprDef.threadField])}
          >Post to ${apprDef.name} thread</option>
        `)}
      </select>
      `;

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
       ${postToSelect}
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
    const heading = !this.loading && this.feature.name || '';
    return html`
      <chromedash-dialog heading="${heading}">
        ${this.loading ?
          html`
           <div class="loading">
             <div id="spinner"><img src="/static/img/ring.svg"></div>
           </div>` :
          html`
            ${this.renderAllApprovals()}
            ${this.renderAllComments()}
            ${this.renderControls()}
          `}
      </chromedash-dialog>
    `;
  }

  checkNeedsSave() {
    let newNeedsSave = false;
    const commentArea = this.shadowRoot.querySelector('#comment_area');
    const newVal = commentArea && commentArea.value.trim() || '';
    if (newVal != '') newNeedsSave = true;
    for (let fieldId of this.changedApprovalsByField.keys()) {
      if (this.changedApprovalsByField.get(fieldId) != -1) {
        newNeedsSave = true;
      }
    }
    this.needsSave = newNeedsSave;
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
    const commentText = commentArea.value.trim();
    const postToSelect = this.shadowRoot.querySelector(
      '#post_to_approval_field');
    const postToApprovalFieldId = postToSelect && postToSelect.value || 0;
    if (commentText != '') {
      promises.push(
        window.csClient.postComment(
          this.feature.id, null, null, commentText,
          Number(postToApprovalFieldId)));
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
