import {LitElement, css, html, nothing} from 'lit';
import {ref, createRef} from 'lit/directives/ref.js';
import './chromedash-activity-log';
import {showToastMessage, findProcessStage} from './utils.js';

import {SHARED_STYLES} from '../sass/shared-css.js';


export const PREPARING = 0;
export const REVIEW_REQUESTED = 2;
export const STATE_NAMES = {
  NO_RESPONSE: [7, 'No response'],
  NA: [1, 'N/a or Ack'],
  REVIEW_STARTED: [3, 'Review started'],
  NEEDS_WORK: [4, 'Needs work'],
  INTERNAL_REVIEW: [8, 'Internal review'],
  APPROVED: [5, 'Approved'],
  DENIED: [6, 'Denied'],
};

export const ACTIVE_REVIEW_STATES = [
  REVIEW_REQUESTED,
  STATE_NAMES.REVIEW_STARTED[0],
  STATE_NAMES.NEEDS_WORK[0],
  STATE_NAMES.INTERNAL_REVIEW[0],
];


export class ChromedashGateColumn extends LitElement {
  voteSelectRef = createRef();
  commentAreaRef = createRef();

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
       #close-button {
         font-size: 2em;
         position: absolute;
         top: var(--content-padding-quarter);
         right: var(--content-padding-quarter);
       }

       #review-status-area {
         margin: var(--content-padding-half) 0;
       }
       .status {
         display: flex;
         gap: var(--content-padding-half);
         align-items: center;
         font-weight: 500;
       }
       sl-icon {
         font-size: 1.3rem;
       }
       .approved {
         color: var(--gate-approved-color);
       }
       .approved sl-icon {
         color: var(--gate-approved-icon-color);
       }
       .denied {
         color: var(--gate-denied-color);
       }
       .denied sl-icon {
         color: var(--gate-denied-icon-color);
       }

       #votes-area {
         margin: var(--content-padding) 0;
       }
       #votes-area table {
         border-spacing: var(--content-padding-half) var(--content-padding);
       }
       #votes-area th {
         font-weight: 500;
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

    `];
  }

  static get properties() {
    return {
      user: {type: Object},
      feature: {type: Object},
      stage: {type: Object},
      gate: {type: Object},
      process: {type: Object},
      votes: {type: Array},
      comments: {type: Array},
      loading: {type: Boolean},
      needsSave: {type: Boolean},
      showSaved: {type: Boolean},
      needsPost: {type: Boolean},
    };
  }

  constructor() {
    super();
    this.user = {};
    this.feature = {};
    this.stage = {};
    this.gate = {};
    this.process = {};
    this.votes = [];
    this.comments = [];
    this.loading = true; // Avoid errors before first usage.
    this.needsSave = false;
    this.showSaved = false;
    this.needsPost = false;
  }

  setContext(feature, stage, gate) {
    this.loading = true;
    this.feature = feature;
    this.stage = stage;
    this.gate = gate;
    const featureId = this.feature.id;
    Promise.all([
      window.csClient.getFeatureProcess(featureId),
      window.csClient.getApprovals(featureId),
      // TODO(jrobbins): Include activities for this gate
      window.csClient.getComments(featureId),
    ]).then(([process, approvalRes, commentRes]) => {
      this.process = process;
      this.votes = approvalRes.approvals.filter((v) =>
        v.gate_id == this.gate.id);
      this.comments = commentRes.comments;
      this.needsSave = false;
      this.needsPost = false;
      this.loading = false;
    }).catch(() => {
      showToastMessage('Some errors occurred. Please refresh the page or try again later.');
      this.handleCancel();
    });
  }

  reloadComments() {
    const commentArea = this.commentAreaRef.value;
    commentArea.value = '';
    this.needsPost = false;
    Promise.all([
      // TODO(jrobbins): Include activities for this gate
      window.csClient.getComments(this.feature.id),
    ]).then(([commentRes]) => {
      this.comments = commentRes.comments;
    }).catch(() => {
      showToastMessage('Some errors occurred. Please refresh the page or try again later.');
      this.handleCancel();
    });
  }

  /* Reload all data for the currently displayed items. */
  refetch() {
    const featureId = this.feature.id;
    Promise.all([
      window.csClient.getGates(featureId),
      window.csClient.getApprovals(featureId),
      // TODO(jrobbins): Include activities for this gate
      window.csClient.getComments(featureId),
    ]).then(([gatesRes, approvalRes, commentRes]) => {
      for (const g of gatesRes.gates) {
        if (g.id == this.gate.id) this.gate = g;
      }
      this.votes = approvalRes.approvals.filter((v) =>
        v.gate_id == this.gate.id);
      this.comments = commentRes.comments;
      this.needsSave = false;
      this.loading = false;
    }).catch(() => {
      showToastMessage('Some errors occurred. Please refresh the page or try again later.');
      this.handleCancel();
    });
  }

  _fireEvent(eventName, detail) {
    const event = new CustomEvent(eventName, {
      bubbles: true,
      composed: true,
      detail,
    });
    this.dispatchEvent(event);
  }

  checkNeedsPost() {
    let newNeedsPost = false;
    const commentArea = this.commentAreaRef.value;
    const newVal = commentArea && commentArea.value.trim() || '';
    if (newVal != '') newNeedsPost = true;
    this.needsPost = newNeedsPost;
  }

  handlePost() {
    const commentArea = this.commentAreaRef.value;
    const commentText = commentArea.value.trim();
    const postToApprovalFieldId = 0; // Don't post to thread.
    // TODO(jrobbins): Also post to intent thread
    if (commentText != '') {
      window.csClient.postComment(
        this.feature.id, null, null, commentText,
        Number(postToApprovalFieldId))
        .then(() => this.reloadComments());
    }
  }

  handleSelectChanged() {
    this.needsSave = true;
    this.showSaved = false;
  }

  handleSave() {
    // TODO(jrobbins): This should specify gate ID rather than gate type.
    window.csClient.setApproval(
      this.feature.id, this.gate.gate_type,
      this.voteSelectRef.value.value)
      .then(() => {
        this.needsSave = false;
        this.showSaved = true;
        this._fireEvent('refetch-needed', {});
      });
  }

  handleCancel() {
    this._fireEvent('close', {});
  }

  renderHeadingsSkeleton() {
    return html`
      <h3 class="sl-skeleton-header-container"
          style="width: 60%">
        <sl-skeleton effect="sheen"></sl-skeleton>
      </h3>
      <h2 class="sl-skeleton-header-container"
          style="margin-top: 4px; width: 75%">
        <sl-skeleton effect="sheen"></sl-skeleton>
      </h2>
    `;
  }

  renderHeadings() {
    const processStage = findProcessStage(this.stage, this.process);
    const processStageName = processStage ? processStage.name : nothing;
    return html`
      <h3>${processStageName}</h3>
      <h2>${this.gate.team_name}</h2>
    `;
  }

  renderReviewStatusSkeleton() {
    return html`
      <h3 class="sl-skeleton-header-container">
        Status: <sl-skeleton effect="sheen"></sl-skeleton>
      </h3>
    `;
  }

  handleReviewRequested() {
    // TODO(jrobbins): This should specify gate ID rather than gate type.
    window.csClient.setApproval(
      this.feature.id, this.gate.gate_type, REVIEW_REQUESTED)
      .then(() => {
        this._fireEvent('refetch-needed', {});
      });
  }

  formatDate(dateStr) {
    return dateStr.split(' ')[0]; // Ignore time of day
  }

  formatRelativeDate(dateStr) {
    // Format date to "YYYY-MM-DDTHH:mm:ss.sssZ" to represent UTC.
    dateStr = dateStr || '';
    dateStr = dateStr.replace(' ', 'T');
    const dateObj = new Date(`${dateStr}Z`);
    if (isNaN(dateObj)) {
      return nothing;
    }
    return html`
      <span class="relative_date">
        (<sl-relative-time date="${dateObj.toISOString()}">
        </sl-relative-time>)
      </span>`;
  }

  /* A user that can edit the current feature can request a review. */
  userCanRequestReview() {
    return (this.user &&
            (this.user.can_edit_all ||
             this.user.editable_features.includes(this.feature.id)));
  }

  renderReviewStatusPreparing() {
    if (this.userCanRequestReview()) {
      return html`
       <sl-button pill size=small variant=primary
         @click=${this.handleReviewRequested}
         >Request review</sl-button>
      `;
    } else {
      return html`
        Review has not been requested yet.
      `;
    }
  }

  renderReviewStatusActive() {
    return html`
      Review requested on ${this.formatDate(this.gate.requested_on)}
      ${this.formatRelativeDate(this.gate.requested_on)}
    `;
  }

  renderReviewStatusApproved() {
    // TODO(jrobbins): Show date of approval.
    return html`
      <div class="status approved">
        <sl-icon library="material" name="check_circle_filled_20px"></sl-icon>
        Approved
      </div>
    `;
  }

  renderReviewStatusDenied() {
    // TODO(jrobbins): Show date of denial.
    return html`
      <div class="status denied">
        <sl-icon library="material" name="block_20px"></sl-icon>
        Denied
      </div>
    `;
  }

  renderReviewStatus() {
    if (this.gate.state == PREPARING) {
      return this.renderReviewStatusPreparing();
    } else if (ACTIVE_REVIEW_STATES.includes(this.gate.state)) {
      return this.renderReviewStatusActive();
    } else if (this.gate.state == STATE_NAMES.APPROVED[0]) {
      return this.renderReviewStatusApproved();
    } else if (this.gate.state == STATE_NAMES.DENIED[0]) {
      return this.renderReviewStatusDenied();
    } else {
      console.log('Unexpected gate state');
      console.log(this.gate);
      return nothing;
    }
  }

  renderVotesSkeleton() {
    return html`
      <table>
        <tr><th>Reviewer</th><th>Review status</th></tr>
        <tr>
         <td><sl-skeleton effect="sheen"></sl-skeleton></td>
         <td><sl-skeleton effect="sheen"></sl-skeleton></td>
        </tr>
      </table>
    `;
  }

  findStateName(state) {
    if (state == REVIEW_REQUESTED) {
      return 'Review requested';
    }
    for (const item of Object.values(STATE_NAMES)) {
      if (item[0] == state) {
        return item[1];
      }
    }
    // This should not normally be seen by users, but it will help us
    // cope with data migration.
    return `State ${state}`;
  }

  renderVoteReadOnly(vote) {
    // TODO(jrobbins): background colors
    return this.findStateName(vote.state);
  }

  renderVoteMenu(state) {
    // hoist is needed when <sl-select> is in overflow:auto context.
    return html`
      <sl-select name="${this.gate.id}"
                 value="${state}" ${ref(this.voteSelectRef)}
                 @sl-change=${this.handleSelectChanged}
                 hoist size="small">
        ${Object.values(STATE_NAMES).map((valName) => html`
          <sl-menu-item value="${valName[0]}">${valName[1]}</sl-menu-item>`,
        )}
      </sl-select>
    `;
  }

  renderVoteRow(vote) {
    const shortVoter = vote.set_by.split('@')[0] + '@';
    let saveButton = nothing;
    let voteCell = this.renderVoteReadOnly(vote);

    if (vote.set_by == this.user?.email) {
      // If the current reviewer was the one who requested the review,
      // select "No response" in the menu because there is no
      // "Review requested" menu item now.
      const state = (vote.state == REVIEW_REQUESTED ?
        STATE_NAMES.NO_RESPONSE[0] : vote.state);
      voteCell = this.renderVoteMenu(state);
      if (this.needsSave) {
        saveButton = html`
          <sl-button
            size="small" variant="primary"
            @click=${this.handleSave}
            >Save</sl-button>
          `;
      } else if (this.showSaved) {
        saveButton = html`<b>Saved</b>`;
      }
    }

    return html`
      <tr>
       <td title=${vote.set_by}>${shortVoter}</td>
       <td>${voteCell}</td>
       <td>${saveButton}</td>
      </tr>
    `;
  }

  renderVotes() {
    const canVote = (
      this.user &&
        this.user.approvable_gate_types.includes(this.gate.gate_type));
    const myVoteExists = this.votes.some((v) => v.set_by == this.user?.email);
    const addVoteRow = (canVote && !myVoteExists) ?
      this.renderVoteRow({set_by: this.user?.email, state: 7}) :
      nothing;

    if (!canVote && this.votes.length === 0) {
      return html`
        <p>No review activity yet.</p>
      `;
    }

    return html`
      <table>
        <tr><th>Reviewer</th><th>Review status</th></tr>
        ${this.votes.map((v) => this.renderVoteRow(v))}
        ${addVoteRow}
      </table>
    `;
  }

  renderQuestionnaireSkeleton() {
    return nothing;
  }

  renderQuestionnaire() {
    // TODO(jrobbins): Implement questionnaires later.
    return nothing;
  }

  renderCommentsSkeleton() {
    // TODO(jrobbins): Include activities too.
    return html`
      <h2>Comments</h2>
      <sl-skeleton effect="sheen"></sl-skeleton>
    `;
  }

  renderControls() {
    if (!this.user || !this.user.can_comment) return nothing;
    // TODO(jrobbins): checkbox to also post to intent thread.

    return html`
      <sl-textarea id="comment_area" rows=2 cols=40 ${ref(this.commentAreaRef)}
        @sl-change=${this.checkNeedsPost}
        @keypress=${this.checkNeedsPost}
        placeholder="Add a comment"
        ></sl-textarea>
       <div id="controls">
         <sl-button variant="primary"
           @click=${this.handlePost}
           ?disabled=${!this.needsPost}
           size="small"
           >Post</sl-button>
       </div>
    `;
  }


  renderComments() {
    // TODO(jrobbins): Include relevant activities too.
    return html`
      <h2>Comments</h2>
      ${this.renderControls()}
      <chromedash-activity-log
        .user=${this.user}
        .feature=${this.feature}
        .narrow=${true}
        .reverse=${true}
        .comments=${this.comments}>
      </chromedash-activity-log>
    `;
  }

  render() {
    return html`
      <sl-icon-button title="Close" name="x" id="close-button"
        @click=${() => this.handleCancel()}
        ></sl-icon-button>

        ${this.loading ?
          this.renderHeadingsSkeleton() :
          this.renderHeadings()}

        <div id="review-status-area">
          ${this.loading ?
            this.renderReviewStatusSkeleton() :
            this.renderReviewStatus()}
        </div>

        <div id="votes-area">
          ${this.loading ?
            this.renderVotesSkeleton() :
            this.renderVotes()}
        </div>

        ${this.loading ?
          this.renderQuestionnaireSkeleton() :
          this.renderQuestionnaire()}

        ${this.loading ?
          this.renderCommentsSkeleton() :
          this.renderComments()}
    `;
  }
}

customElements.define('chromedash-gate-column', ChromedashGateColumn);
