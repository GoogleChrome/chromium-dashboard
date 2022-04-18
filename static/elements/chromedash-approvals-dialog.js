import {LitElement, css, html, nothing} from 'lit';
import '@polymer/iron-icon';
import {SHARED_STYLES} from '../sass/shared-css.js';

export const STATE_NAMES = [
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
      configs: {type: Array},
      possibleOwners: {type: Object},
      showConfigs: {type: Object},
      showAllIntents: {type: Boolean},
      changedApprovalsByField: {attribute: false},
      changedConfigsByField: {attribute: false},
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
    this.configs = [];
    this.subsetPending = false;
    this.possibleOwners = {};
    this.showConfigs = new Set();
    this.showAllIntents = false;
    this.changedApprovalsByField = new Map();
    this.changedConfigsByField = new Map();
    this.needsSave = false;
    this.loading = true;
  }

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        :host .loading {
          width: 650px;
          height: 400px;
        }

        :host h3 {
          margin: var(--content-padding-half);
        }

        :host .approval_section {
          margin-top: var(--content-padding);
        }

        :host .comment_section {
          max-height: 250px;
          overflow-y: scroll;
        }

        :host .approval_section div,
        :host .comment {
          margin-left: var(--content-padding);
        }

        :host .approval_row {
          width: 650px;
          margin-bottom: var(--content-padding-half);
        }

        :host .set_by,
        :host .set_on,
        :host .appr_val {
          display: inline-block;
          width: 200px;
          margin-right: var(--content-padding-half);
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        :host select {
          margin: 0;
        }

        :host .comment_body {
          background: var(--table-alternate-background);
          padding: var(--content-padding-half);
          white-space: pre-wrap;
          width: 46em;
          margin-bottom: var(--content-padding);
        }

        :host .config-area {
          margin-left: var(--content-padding);
          background: var(--table-alternate-background);
        }

        :host .controls {
          padding: var(--content-padding);
          text-align: right;
        }

        :host #show_all_checkbox {
         float: left;
        }

        :host textarea {
          padding: 4px;
          resize: both;
        }
      `];
  }

  openWithFeature(featureId) {
    this.featureId = featureId;
    this.loading = true;
    this.shadowRoot.querySelector('sl-dialog').show();
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
    const p4 = window.csClient.getApprovalConfigs(this.featureId).then(
      (res) => {
        this.configs = res.configs;
        this.showConfigs = new Set(this.configs.map(c => c.field_id));
        this.changedConfigsByField = new Map();
        this.possibleOwners = res.possible_owners;
      });
    Promise.all([p1, p2, p3, p4]).then(() => {
      this.loading = false;
    }).catch(() => {
      const toastEl = document.querySelector('chromedash-toast');
      toastEl.showMessage('Some errors occurred. Please refresh the page or try again later.');
      this.handleCancel();
    });
  }

  toggleShowAllIntents() {
    this.showAllIntents = !this.showAllIntents;
  }

  formatDate(dateStr) {
    return dateStr.split('.')[0]; // Ignore microseconds.
  }

  findStateName(state) {
    for (const item of STATE_NAMES) {
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
                 >${valName[1]}</option>`,
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

  renderConfigWidgets(approvalDef) {
    const fieldId = approvalDef.id;
    const isOpen = this.showConfigs.has(fieldId);
    if (!isOpen) {
      return nothing;
    }

    const config = this.configs.find(c => c.field_id == fieldId);
    const owners = (config ? config.owners : []).join(', ');
    const nextAction = config ? config.next_action : '';
    const additionalReview = config && config.additional_review;
    const offerAdditionalReview = fieldId == 2 || fieldId == 3;

    const ownerWidget = html`
      <input id="owners-${fieldId}" data-field="${fieldId}"
             @change=${this.handleConfigChanged}
             size=30 type="email" multiple placeholder="emails"
             list="possible-owners-${fieldId}"
             value="${owners}">
      <datalist id="possible-owners-${fieldId}">
         ${(this.possibleOwners[fieldId] || []).map(po => html`
            <option value="${po}"></option>
         `)}
      </datalist>
    `;
    const nextActionWidget = html`
      <input id="next-action-${fieldId}" data-field="${fieldId}"
             @change=${this.handleConfigChanged}
             type=date name="next_action_${fieldId}"
             value="${nextAction}">
    `;
    const additionalReviewWidget = html`
      <input id="additional-review-${fieldId}" data-field="${fieldId}"
             @change=${this.handleConfigChanged}
             type=checkbox ?checked=${additionalReview}>
    `;

    return html`
     <table class="config-area">
       <tr>
         <td>Owners:</td>
         <td>${ownerWidget}</td>
       </tr>
       <tr>
        <td>Next action:</td>
        <td>${nextActionWidget}</td>
       </tr>
       ${offerAdditionalReview ? html`
         <tr>
          <td>Additional review:</td>
          <td>${additionalReviewWidget}</td>
         </tr>
        `: nothing }
     </table>
    `;
  }

  renderApproval(approvalDef) {
    const approvalValues = this.approvals.filter((a) =>
      a.field_id == approvalDef.id);
    const isActive = approvalValues.some((av) =>
      PENDING_STATES.includes(av.state));

    if (!isActive && !this.showAllIntents) return nothing;


    const isOpen = this.showConfigs.has(approvalDef.id);
    const configExpandIcon = html`
      <iron-icon
         style="margin-left:4px"
         @click="${() => {
      this.toggleConfig(approvalDef);
    }}"
         icon="chromestatus:${isOpen ? 'expand-less' : 'expand-more'}">
      </iron-icon>
    `;

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
        <h3>
          ${approvalDef.name}
          ${configExpandIcon}
        </h3>
        ${this.renderConfigWidgets(approvalDef)}
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
    const postToSelect = html`
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
      <sl-dialog label="${heading}" style="--width:fit-content">
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
      </sl-dialog>
    `;
  }

  checkNeedsSave() {
    let newNeedsSave = false;
    const commentArea = this.shadowRoot.querySelector('#comment_area');
    const newVal = commentArea && commentArea.value.trim() || '';
    if (newVal != '') newNeedsSave = true;
    for (const fieldId of this.changedApprovalsByField.keys()) {
      if (this.changedApprovalsByField.get(fieldId) != -1) {
        newNeedsSave = true;
      }
    }
    if (this.changedConfigsByField.size > 0) {
      newNeedsSave = true;
    }
    this.needsSave = newNeedsSave;
  }

  handleSelectChanged(e) {
    const fieldId = e.target.dataset['field'];
    const newVal = e.target.value;
    this.changedApprovalsByField.set(fieldId, newVal);
    this.checkNeedsSave();
  }

  handleConfigChanged(e) {
    const fieldId = e.target.dataset['field'];
    const owners = this.shadowRoot.querySelector('#owners-' + fieldId).value;
    const nextAction = this.shadowRoot.querySelector(
      '#next-action-' + fieldId).value;
    const additionalReviewEl = this.shadowRoot.querySelector(
      '#additional-review-' + fieldId);
    const additionalReview = additionalReviewEl && additionalReviewEl.checked;

    this.changedConfigsByField.set(
      fieldId, {owners, nextAction, additionalReview});
    this.checkNeedsSave();
  }

  handleSave() {
    const promises = [];
    for (const fieldId of this.changedApprovalsByField.keys()) {
      if (this.changedApprovalsByField.get(fieldId) != -1) {
        promises.push(
          window.csClient.setApproval(
            this.feature.id, fieldId,
            this.changedApprovalsByField.get(fieldId)));
      }
    }
    for (const fieldId of this.changedConfigsByField.keys()) {
      const config = this.changedConfigsByField.get(fieldId);
      promises.push(
        window.csClient.setApprovalConfig(
          this.feature.id, fieldId, config['owners'],
          config['nextAction'], config['additionalReview']));
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
      this.shadowRoot.querySelector('sl-dialog').hide();
    });
  }

  handleCancel() {
    this.shadowRoot.querySelector('sl-dialog').hide();
  }

  toggleConfig(approvalDef) {
    const newConfigs = new Set([...this.showConfigs]); // Make a copy.
    if (newConfigs.has(approvalDef.id)) {
      newConfigs.delete(approvalDef.id);
    } else {
      newConfigs.add(approvalDef.id);
    }
    this.showConfigs = newConfigs;
  }
}

customElements.define('chromedash-approvals-dialog', ChromedashApprovalsDialog);
