import {LitElement, css, html, nothing} from 'lit';
import '@polymer/iron-icon';
import './chromedash-activity-log';
import {showToastMessage} from './utils.js';

import {SHARED_STYLES} from '../sass/shared-css.js';

export const STATE_NAMES = [
  // Not used: [0, 'Preparing'],
  [7, 'No response'],
  [1, 'N/a or Ack'],
  [2, 'Review requested'],
  [3, 'Review started'],
  [4, 'Needs work'],
  [8, 'Internal review'],
  [5, 'Approved'],
  [6, 'Denied'],
];
const PENDING_STATES = [2, 3, 4, 8];

let approvalDialogEl;

export async function openApprovalsDialog(user, feature) {
  if (!approvalDialogEl) {
    approvalDialogEl = document.createElement('chromedash-approvals-dialog');
    approvalDialogEl.user = user;
    document.body.appendChild(approvalDialogEl);
    await approvalDialogEl.updateComplete;
  }
  approvalDialogEl.openWithFeature(feature);
}


class ChromedashApprovalsDialog extends LitElement {
  static get properties() {
    return {
      user: {type: Object},
      feature: {type: Object},
      votes: {type: Array},
      comments: {type: Array},
      configs: {type: Array},
      gates: {type: Array},
      possibleOwners: {type: Object},
      showConfigs: {type: Object},
      showAllIntents: {type: Boolean},
      submittingChanges: {type: Boolean},
      changedApprovalsByGate: {attribute: false},
      changedConfigsByField: {attribute: false},
      needsSave: {type: Boolean},
      loading: {attribute: false},
    };
  }

  constructor() {
    super();
    this.user = {};
    this.feature = {};
    this.votes = [];
    this.comments = [];
    this.configs = [];
    this.gates = [];
    this.subsetPending = false;
    this.possibleOwners = {};
    this.showConfigs = new Set();
    this.showAllIntents = false;
    this.submittingChanges = false;
    this.changedApprovalsByGate = new Map();
    this.changedConfigsByField = new Map();
    this.needsSave = false;
    this.loading = true;
  }

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        .loading {
          width: 650px;
          height: 400px;
        }

        h3 {
          margin: var(--content-padding-half);
          margin-top: var(--content-padding);
        }

        .approval_section {
          margin-top: var(--content-padding);
        }

        .approval_section div {
          margin-left: var(--content-padding);
        }

        .approval_row {
          width: 650px;
          margin-bottom: var(--content-padding-half);
          display: flex;
          align-items: center;
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

        .config-area {
          margin-left: var(--content-padding);
          background: var(--table-alternate-background);
        }

        #comment_area {
          margin: 0 var(--content-padding);
        }

        #controls {
          padding: var(--content-padding);
          text-align: right;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        #controls * + * {
          padding-left: var(--content-padding);
        }

        #post_to_approval_field {
          flex: 1;
        }

        textarea {
          padding: 4px;
          resize: both;
        }

        .comment_section {
          max-height: 250px;
          overflow-y: scroll;
        }
      `];
  }

  openWithFeature(feature) {
    this.loading = true;
    this.submittingChanges = false;
    this.feature = feature;
    this.shadowRoot.querySelector('sl-dialog').show();
    const featureId = this.feature.id;
    Promise.all([
      window.csClient.getVotes(featureId, null),
      window.csClient.getComments(featureId),
      window.csClient.getApprovalConfigs(featureId),
      window.csClient.getGates(featureId),
    ]).then(([votesRes, commentRes, configRes, gatesRes]) => {
      this.votes = votesRes.votes;
      this.gates = gatesRes.gates;

      // Associate stages with their respective gates.
      for (const gate of this.gates) {
        gate.stage = this.feature.stages.find(s => s.id === gate.stage_id);
      }

      // Sort gates for display. Gates are sorted by the stage type they are
      // associated, then by gate type. This ensures all ship gates are
      // listed near each other, as well as origin trial gates, etc.
      this.gates.sort((a, b) => {
        if (a.stage && b.stage && a.stage.stage_type !== b.stage.stage_type) {
          return a.stage.stage_type - b.stage.stage_type;
        }
        return a.gate_type - b.gate_type;
      });

      const numPending = this.votes.filter((av) =>
        PENDING_STATES.includes(av.state)).length;
      this.subsetPending = (
        numPending > 0 && numPending < this.gates.length);
      this.showAllIntents = numPending == 0;
      this.changedApprovalsByGate = new Map();
      this.needsSave = false;

      this.comments = commentRes.comments;

      this.configs = configRes.configs;
      this.showConfigs = new Set(this.configs.map(c => c.field_id));
      this.changedConfigsByField = new Map();
      this.possibleOwners = configRes.possible_owners;

      this.loading = false;
    }).catch(() => {
      showToastMessage('Some errors occurred. Please refresh the page or try again later.');
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

  renderApprovalValue(voteValue) {
    const selectedValue = (
      this.changedApprovalsByGate.get(voteValue.gate_id) ||
      voteValue.state);
    const canVote = (this.user?.can_approve &&
                     voteValue.set_by == this.user?.email);
    // hoist is needed when <sl-select> is in overflow:hidden context.
    return html`
      <div class="approval_row">
        <span class="set_by">${voteValue.set_by}</span>
        <span class="set_on">${this.formatDate(voteValue.set_on)}</span>
        <span class="appr_val">
          ${canVote ? html`
        <sl-select name="${voteValue.gate_id}"
            value="${selectedValue}"
            data-field="${voteValue.gate_id}"
            @sl-change=${this.handleSelectChanged}
            hoist size="small"
          >
              ${STATE_NAMES.map((valName) => html`
                <sl-option value="${valName[0]}"
                 >${valName[1]}</sl-option>`,
                )}
        </sl-select>` : html`
           ${this.findStateName(voteValue.state)}
            `}
        </span>
      </div>
    `;
  }

  renderMyPendingApproval(gateInfo) {
    if (!this.user || !this.user.can_approve) return nothing;
    const existingApprovalByMe = this.votes.some((a) =>
      a.gate_id === gateInfo.id && a.set_by == this.user.email);
    // There shoud be only one approval entry for now, until we have
    // multiple stage entities for the same type of stage, e.g.
    // multiple shipping gates.
    if (existingApprovalByMe) {
      return nothing;
    } else {
      return this.renderApprovalValue(
        {set_by: this.user.email,
          set_on: '',
          state: 7,
          gate_id: gateInfo.id,
          gate_type: gateInfo.gate_type});
    }
  }

  renderConfigWidgets(gateInfo) {
    const gateType = gateInfo.gate_type;
    const isOpen = this.showConfigs.has(gateType);
    if (!isOpen) {
      return nothing;
    }

    const config = this.configs.find(c => c.field_id == gateType);
    const owners = (config ? config.owners : []).join(', ');
    const nextAction = config ? config.next_action : '';
    const additionalReview = config && config.additional_review;
    const offerAdditionalReview = gateType == 2 || gateType == 3;

    const ownerWidget = html`
      <input id="owners-${gateType}" data-field="${gateType}"
             @change=${this.handleConfigChanged}
             size=30 type="email" multiple placeholder="emails"
             list="possible-owners-${gateType}"
             value="${owners}">
      <datalist id="possible-owners-${gateType}">
         ${(this.possibleOwners[gateType] || []).map(po => html`
            <option value="${po}"></option>
         `)}
      </datalist>
    `;
    const nextActionWidget = html`
      <input id="next-action-${gateType}" data-field="${gateType}"
             @change=${this.handleConfigChanged}
             type=date name="next_action_${gateType}"
             value="${nextAction}">
    `;
    const additionalReviewWidget = html`
      <input id="additional-review-${gateType}" data-field="${gateType}"
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

  renderApproval(gateInfo) {
    const voteValues = this.votes.filter((a) =>
      a.gate_id == gateInfo.id);
    const isActive = voteValues.some(v =>
      PENDING_STATES.includes(v.state));

    if (!isActive && !this.showAllIntents) return nothing;

    const isOpen = this.showConfigs.has(gateInfo.gate_type);
    const configExpandIcon = html`
      <iron-icon
         style="margin-left:4px"
         @click="${() => {
      this.toggleConfig(gateInfo);
    }}"
         icon="chromestatus:${isOpen ? 'expand-less' : 'expand-more'}">
      </iron-icon>
    `;

    let threadLink = nothing;
    if (gateInfo.stage?.intent_thread_url) {
      threadLink = html`
        <div>
          <a href="${gateInfo.stage.intent_thread_url}" target="_blank"
             >blink-dev thread</a>
        </div>
      `;
    }

    return html`
      <div class="approval_section">
        <h3>
          ${gateInfo.gate_name}
          ${configExpandIcon}
        </h3>
        ${this.renderConfigWidgets(gateInfo)}
        ${voteValues.map(v => this.renderApprovalValue(v))}
        ${this.renderMyPendingApproval(gateInfo)}
        ${threadLink}
      </div>
    `;
  }

  renderAllApprovals() {
    // Render an approval for each gate associated with the feature.
    return this.gates.map(gateInfo => this.renderApproval(gateInfo));
  }

  renderAllComments() {
    return html`
      <h3>Comments</h3>
      <div class="comment_section">
        <chromedash-activity-log
          .user=${this.user}
          .feature=${this.feature}
          .comments=${this.comments}>
        </chromedash-activity-log>
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
    if (!this.user || !this.user.can_comment) return nothing;
    let showAllCheckbox = nothing;
    if (this.subsetPending) {
      showAllCheckbox = html`
         <sl-checkbox
           id="show_all_checkbox"
           ?checked=${this.showAllIntents}
           @sl-change=${this.toggleShowAllIntents}
           size="small"
           >Show all intents</sl-checkbox>
      `;
    }
    const postToSelect = html`
      <sl-select placement="top" value=0 id="post_to_approval_field" size="small">
        <sl-option value="0">Don't post to mailing list</sl-option>
        ${this.gates.map(gate => html`
          <sl-option value="${gate.id}"
                  ?disabled=${!this.canPostTo(gate.stage?.intent_thread_url || '')}
          >Post to ${gate.gate_name} thread</sl-option>
        `)}
      </sl-select>
      `;

    return html`
    <sl-textarea id="comment_area" rows=4 cols=80
      @sl-change=${this.checkNeedsSave}
      @keypress=${this.checkNeedsSave}
      placeholder="Add a comment"
      ></sl-textarea>
     <div id="controls">
       ${showAllCheckbox}
       ${postToSelect}
       <sl-button variant="primary"
         @click=${this.handleSave}
         ?disabled=${!this.needsSave || this.submittingChanges}
         size="small"
         >Save</sl-button>
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

  // Check if any information is new and can be saved
  // after each user interaction with the dialog box.
  checkNeedsSave() {
    let newNeedsSave = false;
    const commentArea = this.shadowRoot.querySelector('#comment_area');
    const newVal = commentArea && commentArea.value.trim() || '';
    if (newVal != '') newNeedsSave = true;
    for (const voteValue of this.changedApprovalsByGate.values()) {
      if (voteValue != -1) {
        newNeedsSave = true;
      }
    }
    if (this.changedConfigsByField.size > 0) {
      newNeedsSave = true;
    }
    this.needsSave = newNeedsSave;
  }

  // Handle a vote value being changed by the user.
  handleSelectChanged(e) {
    const gateId = e.target.dataset['field'];
    const newVal = e.target.value;
    this.changedApprovalsByGate.set(gateId, newVal);
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
    this.submittingChanges = true;
    // Check if any votes were changed by the user, and change them if so.
    for (const [gateId, voteValue] of this.changedApprovalsByGate) {
      if (voteValue !== -1) {
        const changedGate = this.gates.find(g => g.id === Number(gateId));
        if (!changedGate) {
          continue;
        }
        promises.push(
          window.csClient.setVote(
            this.feature.id, changedGate.id,
            voteValue));
      }
    }

    // TODO(danielrsmith): ApprovalConfig entities are deprecated and
    // this request should instead affect Gate entities.
    for (const fieldId of this.changedConfigsByField.keys()) {
      const config = this.changedConfigsByField.get(fieldId);
      promises.push(
        window.csClient.setApprovalConfig(
          this.feature.id, fieldId, config['owners'],
          config['nextAction'], config['additionalReview']));
    }

    // Handle saving comment and posting to thread if a comment was provided.
    const commentArea = this.shadowRoot.querySelector('#comment_area');
    const commentText = commentArea.value.trim();
    const postToSelect = this.shadowRoot.querySelector(
      '#post_to_approval_field');
    const gateId = (postToSelect) ? Number(postToSelect.value) : 0;
    const gate = this.gates.find(g => g.id === gateId);
    const gateType = (gate) ? gate.gate_type : 0;
    if (commentText != '') {
      promises.push(
        window.csClient.postComment(
          this.feature.id, gateId, commentText,
          Number(gateType)));
    }
    Promise.all(promises).then(() => {
      this.handleCancel();
    }).catch(() => {
      showToastMessage('Some errors occurred. Please refresh the page or try again later.');
      this.handleCancel();
    });
  }

  handleCancel() {
    this.shadowRoot.querySelector('sl-dialog').hide();
  }

  toggleConfig(gateInfo) {
    const newConfigs = new Set([...this.showConfigs]); // Make a copy.
    if (newConfigs.has(gateInfo.gate_type)) {
      newConfigs.delete(gateInfo.gate_type);
    } else {
      newConfigs.add(gateInfo.gate_type);
    }
    this.showConfigs = newConfigs;
  }
}

customElements.define('chromedash-approvals-dialog', ChromedashApprovalsDialog);
