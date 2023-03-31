import {LitElement, css, html, nothing} from 'lit';
import {ref, createRef} from 'lit/directives/ref.js';
import './chromedash-activity-log';
import {
  openPreflightDialog,
  somePendingPrereqs,
} from './chromedash-preflight-dialog';
import {autolink, showToastMessage, findProcessStage,
  renderAbsoluteDate, renderRelativeDate,
} from './utils.js';
import {GATE_QUESTIONNAIRES} from './form-definition.js';

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
  postToThreadRef = createRef();

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

       #questionnaire {
         white-space: pre-wrap;
         padding: var(--content-padding-half);
         border-radius: var(--border-radius);
         background: var(--table-alternate-background);
       }
       #questionnaire ul {
         padding-left: 1em;
       }
       #questionnaire li {
         list-style: disc;
       }
       .instructions {
         padding: var(--content-padding-half);
         margin-bottom: var(--content-padding-large);
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
      progress: {type: Object},
      process: {type: Object},
      votes: {type: Array},
      comments: {type: Array},
      loading: {type: Boolean},
      needsSave: {type: Boolean},
      showSaved: {type: Boolean},
      submittingComment: {type: Boolean},
      submittingVote: {type: Boolean},
      needsPost: {type: Boolean},
    };
  }

  constructor() {
    super();
    this.user = {};
    this.feature = {};
    this.stage = {};
    this.gate = {};
    this.progress = {};
    this.process = {};
    this.votes = [];
    this.comments = [];
    this.loading = true; // Avoid errors before first usage.
    this.needsSave = false;
    this.showSaved = false;
    this.submittingComment = false;
    this.submittingVote = false;
    this.needsPost = false;
  }

  setContext(feature, stageId, gate) {
    this.loading = true;
    this.feature = feature;
    this.gate = gate;
    const featureId = this.feature.id;
    Promise.all([
      window.csClient.getFeatureProgress(featureId),
      window.csClient.getFeatureProcess(featureId),
      window.csClient.getStage(featureId, stageId),
      window.csClient.getVotes(featureId, null),
      // TODO(jrobbins): Include activities for this gate
      window.csClient.getComments(featureId, gate.id),
    ]).then(([progress, process, stage, votesRes, commentRes]) => {
      this.progress = progress;
      this.process = process;
      this.stage = stage;
      this.votes = votesRes.votes.filter((v) =>
        v.gate_id == this.gate.id);
      this.comments = commentRes.comments;
      this.needsSave = false;
      this.showSaved = false;
      this.submittingComment = false;
      this.submittingVote = false;
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
      window.csClient.getComments(this.feature.id, this.gate.id),
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
      window.csClient.getVotes(featureId, null),
      // TODO(jrobbins): Include activities for this gate
      window.csClient.getComments(featureId, this.gate.id),
    ]).then(([gatesRes, votesRes, commentRes]) => {
      for (const g of gatesRes.gates) {
        if (g.id == this.gate.id) this.gate = g;
      }
      this.votes = votesRes.votes.filter((v) =>
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
    this.submittingVote = true;
    const commentArea = this.commentAreaRef.value;
    const commentText = commentArea.value.trim();
    const postToThreadType = (
      this.postToThreadRef.value?.checked ? this.gate.gate_type : 0);
    if (commentText != '') {
      window.csClient.postComment(
        this.feature.id, this.gate.id, commentText,
        Number(postToThreadType))
        .then(() => {
          this.reloadComments();
          this.submittingVote = false;
        })
        .catch(() => {
          showToastMessage('Some errors occurred. Please refresh the page or try again later.');
          this.submittingVote = false;
        });
    }
  }

  handleSelectChanged() {
    this.needsSave = true;
    this.showSaved = false;
  }

  handleSave() {
    this.submittingComment = true;
    window.csClient.setVote(
      this.feature.id, this.gate.id,
      this.voteSelectRef.value.value)
      .then(() => {
        this.needsSave = false;
        this.showSaved = true;
        this.submittingComment = false;
        this._fireEvent('refetch-needed', {});
      })
      .catch(() => {
        showToastMessage('Some errors occurred. Please refresh the page or try again later.');
        this.submittingComment = false;
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
    window.csClient.setVote(
      this.feature.id, this.gate.id, REVIEW_REQUESTED)
      .then(() => {
        this._fireEvent('refetch-needed', {});
      });
  }

  /* A user that can edit the current feature can request a review. */
  userCanRequestReview() {
    return (this.user &&
            (this.user.can_edit_all ||
             this.user.editable_features.includes(this.feature.id)));
  }

  renderAction(processStage, action) {
    const label = action.name;
    const url = action.url
      .replace('{feature_id}', this.feature.id)
      .replace('{outgoing_stage}', processStage.outgoing_stage);

    const checkCompletion = () => {
      if (somePendingPrereqs(action, this.progress)) {
        // Open the dialog.
        openPreflightDialog(
          this.feature, this.progress, this.process, action,
          processStage, this.stage);
        return;
      } else {
        // Act like user clicked left button to go to the draft email window.
        const draftWindow = window.open(url, '_blank');
        draftWindow.focus();
      }
    };

    return html`
      <sl-button @click=${checkCompletion}
       pill size=small variant=primary
       >${label}</sl-button>
    `;
  }

  renderReviewStatusPreparing() {
    if (!this.userCanRequestReview()) {
      return html`
        Review has not been requested yet.
      `;
    }

    const processStage = findProcessStage(this.stage, this.process);
    if (processStage?.actions?.length > 0 &&
       this.gate.team_name == 'API Owners') {
      return processStage.actions.map(act =>
        this.renderAction(processStage, act));
    }

    return html`
     <sl-button pill size=small variant=primary
       @click=${this.handleReviewRequested}
       >Request review</sl-button>
    `;
  }

  renderReviewStatusActive() {
    return html`
      Review requested on
      ${renderAbsoluteDate(this.gate.requested_on)}
      ${renderRelativeDate(this.gate.requested_on)}
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
          <sl-option value="${valName[0]}">${valName[1]}</sl-option>`,
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
            ?disabled=${this.submittingComment}
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
    return html`
      <h2>Survey questions</h2>
      <div id="questionnaire">Loading...</div>
      <p class="instructions">&nbsp;</p>
    `;
  }

  renderQuestionnaire() {
    const questionnaireText = GATE_QUESTIONNAIRES[this.gate.gate_type];
    if (!questionnaireText) return nothing;
    const markup = (typeof questionnaireText == 'string') ?
      autolink(questionnaireText) : questionnaireText;
    return html`
      <h2>Survey questions</h2>
      <div id="questionnaire">${markup}</div>
      <p class="instructions">
        Please post responses in the comments below.
      </p>
    `;
  }

  renderCommentsSkeleton() {
    // TODO(jrobbins): Include activities too.
    return html`
      <h2>Comments</h2>
      <sl-skeleton effect="sheen"></sl-skeleton>
    `;
  }

  gateHasIntentThread() {
    return this.gate.team_name === 'API Owners';
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

    const postButton = html`
      <sl-button variant="primary"
        @click=${this.handlePost}
        ?disabled=${!this.needsPost || this.submittingVote}
        size="small"
        >Post</sl-button>
    `;
    const checkboxLabel = (
      this.stage.intent_thread_url ?
        html`
            Also post to
              <a href=${this.stage.intent_thread_url} target="_blank"
                 >intent thread</a>
          ` : 'Also post to intent thread');
    const postToThreadCheckbox = (
      this.gateHasIntentThread() ?
        html`
          <sl-checkbox
            ${ref(this.postToThreadRef)}
            ?disabled=${!this.canPostTo(this.stage.intent_thread_url)}
            size="small"
            >${checkboxLabel}</sl-checkbox>
          ` :
        nothing);

    return html`
      <sl-textarea id="comment_area" rows=2 cols=40 ${ref(this.commentAreaRef)}
        @sl-change=${this.checkNeedsPost}
        @keypress=${this.checkNeedsPost}
        placeholder="Add a comment"
        ></sl-textarea>
       <div class="instructions">
         Comments will be visible publicly.
         Only reviewers will be notified when a comment is posted.
       </div>
       <div id="controls">
         ${postButton}
         ${postToThreadCheckbox}
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
