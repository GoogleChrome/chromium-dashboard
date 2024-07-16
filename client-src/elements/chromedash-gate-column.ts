import {LitElement, TemplateResult, css, html, nothing} from 'lit';
import {createRef, ref} from 'lit/directives/ref.js';
import './chromedash-activity-log';
import {openNaRationaleDialog} from './chromedash-na-rationale-dialog';
import {
  openPreflightDialog,
  somePendingGates,
  somePendingPrereqs,
} from './chromedash-preflight-dialog';
import {maybeOpenPrevoteDialog} from './chromedash-prevote-dialog';
import {GATE_QUESTIONNAIRES} from './form-definition.js';
import {
  GATE_NA_REQUESTED,
  GATE_PREPARING,
  GATE_REVIEW_REQUESTED,
  VOTE_OPTIONS,
} from './form-field-enums';
import {
  autolink,
  findProcessStage,
  renderAbsoluteDate,
  renderRelativeDate,
  showToastMessage,
} from './utils.js';

import {customElement, property, state} from 'lit/decorators.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {Feature, StageDict, User} from '../js-src/cs-client';
import {GateDict} from './chromedash-gate-chip';

interface Vote {
  feature_id: number;
  gate_id: number;
  gate_type?: number;
  state: number;
  set_on: Date;
  set_by: string;
}

export interface ProgressItem {
  name: string;
  field?: string;
  stage: ProcessStage;
}

export interface Action {
  name: string;
  url: string;
  prerequisites: string[];
}

interface ApprovalFieldDef {
  name: string;
  description: string;
  field_id: number;
  rule: string;
  approvers: string | string[];
  team_name: string;
  escalation_email?: string;
  slo_initial_response?: number;
}

export interface ProcessStage {
  name: string;
  description: string;
  progress_items: ProgressItem[];
  actions: Action[];
  approvals: ApprovalFieldDef[]; // Assuming ApprovalFieldDef is defined somewhere
  incoming_stage: number;
  outgoing_stage: number;
  stage_type?: number;
}

export interface Process {
  name: string;
  description: string;
  applicability: string;
  stages: ProcessStage[];
}

@customElement('chromedash-gate-column')
export class ChromedashGateColumn extends LitElement {
  voteSelectRef = createRef<HTMLSelectElement>();
  commentAreaRef = createRef<HTMLTextAreaElement>();
  postToThreadRef = createRef<HTMLInputElement>();
  assigneeSelectRef = createRef<HTMLSelectElement>();

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
        #slo-area sl-icon {
          font-size: 16px;
          vertical-align: text-bottom;
          color: var(--unimportant-text-color);
        }
        .overdue,
        #slo-area .overdue sl-icon {
          color: var(--slo-overdue-color);
        }

        .process-notice {
          margin: var(--content-padding-half) 0;
          padding: var(--content-padding-half);
          background: var(--light-accent-color);
          border-radius: 8px;
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
        table .your-vote {
          font-style: italic;
          white-space: nowrap;
        }

        #questionnaire {
          padding: var(--content-padding-half);
          border-radius: var(--border-radius);
          background: var(--table-alternate-background);
        }
        #questionnaire * + * {
          padding-top: var(--content-padding);
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

        details {
          padding: 10px;
        }
        details summary {
          cursor: pointer;
          transition: margin 250ms ease-out;
          color: var(--link-color);
        }
        details summary::hover {
          color: var(--link-hover-color);
        }
        details[open] summary {
          margin-bottom: 10px;
        }
      `,
    ];
  }

  @property({type: Object})
  user!: User;
  @state()
  feature!: Feature;
  @state()
  featureGates!: GateDict[];
  @state()
  stage!: StageDict;
  @state()
  gate!: GateDict;
  @state()
  progress!: ProgressItem;
  @state()
  process!: Process;
  @state()
  votes: Vote[] = [];
  @state()
  comments: string[] = [];
  @state()
  needsSave = false;
  @state()
  showSaved = false;
  @state()
  submittingComment = false;
  @state()
  submittingVote = false;
  @state()
  needsPost = false;
  @state()
  loading = true;

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
      window.csClient.getComments(featureId, gate.id),
    ])
      .then(([progress, process, stage, votesRes, commentRes]) => {
        this.progress = progress;
        this.process = process;
        this.stage = stage;
        this.votes = votesRes.votes.filter(v => v.gate_id == this.gate.id);
        this.comments = commentRes.comments;
        this.needsSave = false;
        this.showSaved = false;
        this.submittingComment = false;
        this.submittingVote = false;
        this.needsPost = false;
        this.loading = false;
      })
      .catch(() => {
        showToastMessage(
          'Some errors occurred. Please refresh the page or try again later.'
        );
        this.handleCancel();
      });
  }

  reloadComments() {
    const commentArea = this.commentAreaRef.value;
    if (commentArea) {
      commentArea.value = '';
    }
    this.needsPost = false;
    Promise.all([
      // TODO(jrobbins): Include activities for this gate
      window.csClient.getComments(this.feature.id, this.gate.id),
    ])
      .then(([commentRes]) => {
        this.comments = commentRes.comments;
      })
      .catch(() => {
        showToastMessage(
          'Some errors occurred. Please refresh the page or try again later.'
        );
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
    ])
      .then(([gatesRes, votesRes, commentRes]) => {
        for (const g of gatesRes.gates) {
          if (g.id == this.gate.id) this.gate = g;
        }
        this.votes = votesRes.votes.filter(v => v.gate_id == this.gate.id);
        this.comments = commentRes.comments;
        this.needsSave = false;
        this.loading = false;
      })
      .catch(() => {
        showToastMessage(
          'Some errors occurred. Please refresh the page or try again later.'
        );
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
    const newVal = (commentArea && commentArea.value.trim()) || '';
    if (newVal != '') newNeedsPost = true;
    this.needsPost = newNeedsPost;
  }

  handlePost() {
    const commentArea = this.commentAreaRef.value;
    const commentText = commentArea?.value.trim();
    const postToThreadType = this.postToThreadRef.value?.checked
      ? this.gate.gate_type
      : 0;
    this.postComment(commentText, postToThreadType);
  }

  async postComment(commentText, postToThreadType = 0) {
    this.submittingVote = true;
    if (commentText != '') {
      await window.csClient
        .postComment(
          this.feature.id,
          this.gate.id,
          commentText,
          Number(postToThreadType)
        )
        .then(() => {
          this.reloadComments();
          this.submittingVote = false;
        })
        .catch(() => {
          showToastMessage(
            'Some errors occurred. Please refresh the page or try again later.'
          );
          this.submittingVote = false;
        });
    }
  }

  handleSelectChanged() {
    this.needsSave = true;
    this.showSaved = false;
  }

  saveVote() {
    this.submittingComment = true;
    window.csClient
      .setVote(this.feature.id, this.gate.id, this.voteSelectRef.value?.value)
      .then(() => {
        this.needsSave = false;
        this.showSaved = true;
        this.submittingComment = false;
        this._fireEvent('refetch-needed', {});
      })
      .catch(() => {
        showToastMessage(
          'Some errors occurred. Please refresh the page or try again later.'
        );
        this.submittingComment = false;
      });
  }

  handleSave() {
    Promise.all([window.csClient.getGates(this.feature.id)])
      .then(([gatesRes]) => {
        this.featureGates = gatesRes.gates;
        const vote = this.voteSelectRef.value?.value;
        maybeOpenPrevoteDialog(
          this.featureGates,
          this.stage,
          this.gate,
          vote
        ).then(() => {
          this.saveVote();
        });
      })
      .catch(() => {
        showToastMessage(
          'Some errors occurred. Please refresh the page or try again later.'
        );
      });
  }

  handleCancel() {
    this._fireEvent('close', {});
  }

  renderHeadingsSkeleton() {
    return html`
      <h3 class="sl-skeleton-header-container" style="width: 60%">
        <sl-skeleton effect="sheen"></sl-skeleton>
      </h3>
      <h2
        class="sl-skeleton-header-container"
        style="margin-top: 4px; width: 75%"
      >
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

  async handleReviewRequested() {
    await window.csClient.setVote(
      this.feature.id,
      this.gate.id,
      GATE_REVIEW_REQUESTED
    );
    this._fireEvent('refetch-needed', {});
  }

  handleNARequested() {
    openNaRationaleDialog(this.gate).then(rationale => {
      this.handleNARequestSubmitted(rationale);
    });
  }

  async handleNARequestSubmitted(rationale) {
    await window.csClient.setVote(
      this.feature.id,
      this.gate.id,
      GATE_NA_REQUESTED
    );
    // Post the comment after the review request so that it will go
    // to the assigned reviewer rather than all reviewers.
    const commentText = 'An "N/A" response is requested because: ' + rationale;
    await this.postComment(commentText);
    this._fireEvent('refetch-needed', {});
  }

  /* A user that can edit the current feature can request a review. */
  userCanRequestReview() {
    return (
      this.user &&
      (this.user.can_edit_all ||
        this.user.editable_features.includes(this.feature.id))
    );
  }

  userCanVote() {
    return (
      this.user && this.user.approvable_gate_types.includes(this.gate.gate_type)
    );
  }

  renderAction(processStage, action) {
    const label = action.name;
    const url = action.url
      .replace('{feature_id}', this.feature.id)
      .replace('{intent_stage}', processStage.outgoing_stage)
      .replace('{gate_id}', this.gate.id);

    const checkCompletion = () => {
      if (
        somePendingPrereqs(action, this.progress) ||
        somePendingGates(this.featureGates, this.stage)
      ) {
        // Open the dialog.
        openPreflightDialog(
          this.feature,
          this.progress,
          this.process,
          action,
          processStage,
          this.stage,
          this.featureGates,
          url
        );
        return;
      } else {
        // Act like user clicked left button to go to the draft email window.
        // Use setTimeout() to prevent safari from blocking the new tab.
        setTimeout(() => {
          const draftWindow = window.open(url, '_blank');
          draftWindow!.focus();
        });
      }
    };

    const loadThenCheckCompletion = () => {
      Promise.all([window.csClient.getGates(this.feature.id)])
        .then(([gatesRes]) => {
          this.featureGates = gatesRes.gates;
          checkCompletion();
        })
        .catch(() => {
          showToastMessage(
            'Some errors occurred. Please refresh the page or try again later.'
          );
        });
    };

    return html`
      <sl-button
        @click=${loadThenCheckCompletion}
        size="small"
        variant="primary"
        >${label}</sl-button
      >
    `;
  }

  renderReviewStatusPreparing() {
    if (!this.userCanRequestReview()) {
      return html` Review has not been requested yet. `;
    }

    const processStage = findProcessStage(this.stage, this.process);
    if (
      processStage?.actions?.length > 0 &&
      this.gate.team_name == 'API Owners'
    ) {
      return processStage.actions.map(act =>
        this.renderAction(processStage, act)
      );
    }

    return html`
      <sl-button
        size="small"
        variant="primary"
        @click=${this.handleReviewRequested}
        >Request review</sl-button
      >
      <sl-button size="small" @click=${this.handleNARequested}
        >Request N/A</sl-button
      >
    `;
  }

  renderReviewRequest() {
    for (const v of this.votes) {
      if (v.state === GATE_REVIEW_REQUESTED || v.state === GATE_NA_REQUESTED) {
        const shortVoter = v.set_by.split('@')[0] + '@';
        return html`
          ${shortVoter} requested on
          ${renderAbsoluteDate(this.gate.requested_on)}
          ${renderRelativeDate(this.gate.requested_on)}
        `;
      }
    }
    return nothing;
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
    if (this.gate.state == GATE_PREPARING) {
      return this.renderReviewStatusPreparing();
    } else if (this.gate.state == VOTE_OPTIONS.APPROVED[0]) {
      return this.renderReviewStatusApproved();
    } else if (this.gate.state == VOTE_OPTIONS.DENIED[0]) {
      return this.renderReviewStatusDenied();
    } else {
      return nothing;
    }
  }

  renderSLOStatusSkeleton() {
    return html` <p>Reviewer SLO status:</p>`;
  }

  renderInfoIcon() {
    return html`
      <sl-tooltip
        hoist
        style="--max-width: 14em;"
        content="Reviewers are encouraged to provide an initial
          review status update
          or a comment within this number of days.
          The full review may take longer."
      >
        <sl-icon name="info-circle" id="info-button"></sl-icon>
      </sl-tooltip>
    `;
  }

  dayPhrase(count) {
    return String(count) + (count == 1 ? ' day' : ' days');
  }

  renderSLOStatus() {
    const limit = this.gate?.slo_initial_response;
    const took = this.gate?.slo_initial_response_took;
    const remaining = this.gate?.slo_initial_response_remaining;
    let msg: typeof nothing | TemplateResult = nothing;
    let iconName = '';
    let className = '';

    if (typeof took === 'number') {
      msg = html`took ${this.dayPhrase(took)} for initial response`;
    } else if (typeof remaining === 'number') {
      iconName = 'clock_loader_60_20px';
      if (remaining > 0) {
        msg = html`${this.dayPhrase(remaining)} remaining`;
      } else if (remaining < 0) {
        className = 'overdue';
        msg = html`${this.dayPhrase(-remaining)} overdue`;
      } else {
        msg = html`initial response is due today`;
      }
    } else if (typeof limit === 'number') {
      return html`
        <p>
          Reviewer SLO: ${this.dayPhrase(limit)} for initial response
          ${this.renderInfoIcon()}
        </p>
      `;
    }

    if (msg === nothing) {
      return nothing;
    } else {
      const icon = iconName
        ? html`<sl-icon library="material" name="${iconName}"></sl-icon>`
        : nothing;
      return html` <p id="slo-area">
        Reviewer SLO status: <span class="${className}">${icon} ${msg}</span>
      </p>`;
    }
  }

  renderWarnings() {
    if (this.gate && this.gate.team_name == 'Privacy') {
      return html`
        <div class="process-notice">
          Googlers: Please follow the instructions at
          <a
            href="https://goto.corp.google.com/wp-launch-guidelines"
            target="_blank"
            rel="noopener"
            >go/wp-launch-guidelines</a
          >
          (internal document) to determine whether you also require an internal
          review.
        </div>
      `;
    }
    return nothing;
  }

  renderVotesSkeleton() {
    return html`
      <table>
        <tr>
          <th>Reviewer</th>
          <th>Review status</th>
        </tr>
        <tr>
          <td><sl-skeleton effect="sheen"></sl-skeleton></td>
          <td><sl-skeleton effect="sheen"></sl-skeleton></td>
        </tr>
      </table>
    `;
  }

  findStateName(state) {
    if (state == GATE_REVIEW_REQUESTED) {
      return 'Review requested';
    }
    for (const item of Object.values(VOTE_OPTIONS)) {
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
      <sl-select
        name="${this.gate.id}"
        value="${state}"
        ${ref(this.voteSelectRef)}
        @sl-change=${this.handleSelectChanged}
        hoist
        size="small"
      >
        ${Object.values(VOTE_OPTIONS).map(
          valName =>
            html` <sl-option value="${valName[0]}">${valName[1]}</sl-option>`
        )}
      </sl-select>
    `;
  }

  renderSaveButton() {
    return html`
      <sl-button
        size="small"
        variant="primary"
        @click=${this.handleSave}
        ?disabled=${this.submittingComment}
        >Save</sl-button
      >
    `;
  }

  renderVoteRow(vote, canVote) {
    const shortVoter = vote.set_by.split('@')[0] + '@';
    let saveButton: typeof nothing | TemplateResult = nothing;
    let voteCell: TemplateResult | string = this.renderVoteReadOnly(vote);

    if (canVote && vote.set_by == this.user?.email) {
      voteCell = this.renderVoteMenu(vote.state);
      if (this.needsSave) {
        saveButton = this.renderSaveButton();
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

  renderAddVoteRow() {
    const assignedToMe = this.gate.assignee_emails.includes(this.user.email);
    const shortVoter = this.user.email.split('@')[0] + '@';
    const yourLabel = assignedToMe
      ? html`<td title=${this.user.email}>${shortVoter}</td>`
      : html`<td class="your-vote">Awaiting review</td>`;
    const voteCell = this.renderVoteMenu(VOTE_OPTIONS.NO_RESPONSE[0]);
    const saveButton = this.needsSave ? this.renderSaveButton() : nothing;
    return html`
      <tr>
        ${yourLabel}
        <td>${voteCell}</td>
        <td>${saveButton}</td>
      </tr>
    `;
  }

  renderPendingVote(assigneeEmail) {
    const shortVoter = assigneeEmail.split('@')[0] + '@';
    return html`
      <tr>
        <td title=${assigneeEmail}>${shortVoter}</td>
        <td>No response yet</td>
        <td></td>
      </tr>
    `;
  }

  saveAssignedReviewer() {
    const assignee = this.assigneeSelectRef.value?.value;
    const assigneeList = assignee === '' ? [] : [assignee];
    window.csClient
      .updateGate(this.feature.id, this.gate.id, assigneeList)
      .then(() => this._fireEvent('refetch-needed', {}));
  }

  renderAssignReviewerControls() {
    if (!this.userCanRequestReview() && !this.userCanVote()) {
      return nothing;
    }
    if (this.gate.state === VOTE_OPTIONS.APPROVED[0]) {
      return nothing;
    }
    const currentAssignee =
      this.gate.assignee_emails?.length > 0 ? this.gate.assignee_emails[0] : '';
    return html`
      <details>
        <summary>Assign a reviewer</summary>
        <sl-select
          hoist
          size="small"
          ${ref(this.assigneeSelectRef)}
          value=${currentAssignee}
        >
          <sl-option value="">None</sl-option>
          ${this.gate.possible_assignee_emails.map(
            email => html` <sl-option value="${email}">${email}</sl-option>`
          )}
        </sl-select>
        <sl-button
          size="small"
          variant="primary"
          @click=${() => this.saveAssignedReviewer()}
          >Assign</sl-button
        >
      </details>
    `;
  }

  isReviewRequest(vote) {
    return (
      vote.state === GATE_REVIEW_REQUESTED || vote.state === GATE_NA_REQUESTED
    );
  }

  renderVotes() {
    const canVote = this.userCanVote();
    const responses = this.votes.filter(v => !this.isReviewRequest(v));
    const responseEmails = responses.map(v => v.set_by);
    const othersPending = this.gate.assignee_emails.filter(
      ae => !responseEmails.includes(ae) && ae != this.user?.email
    );
    const myResponseExists = responses.some(v => v.set_by == this.user?.email);
    const addVoteRow =
      canVote && !myResponseExists ? this.renderAddVoteRow() : nothing;
    const assignControls = this.renderAssignReviewerControls();

    if (!canVote && responses.length === 0 && othersPending.length === 0) {
      return html`
        <p>No review activity yet.</p>
        ${assignControls}
      `;
    }

    return html`
      <table>
        <tr>
          <th>Reviewer</th>
          <th>Review status</th>
        </tr>
        ${responses.map(v => this.renderVoteRow(v, canVote))}
        ${othersPending.map(ae => this.renderPendingVote(ae))} ${addVoteRow}
      </table>
      ${assignControls}
    `;
  }

  renderQuestionnaireSkeleton() {
    return html`
      <h2>Survey questions</h2>
      <!-- prettier-ignore -->
      <div id="questionnaire">Loading...</div>
      <p class="instructions">&nbsp;</p>
    `;
  }

  renderQuestionnaire() {
    const questionnaireText = GATE_QUESTIONNAIRES[this.gate.gate_type];
    if (!questionnaireText) return nothing;
    const markup =
      typeof questionnaireText == 'string'
        ? autolink(questionnaireText)
        : questionnaireText;
    return html`
      <h2>Survey questions</h2>
      <!-- prettier-ignore -->
      <div id="questionnaire">${markup}</div>
      <p class="instructions">Please post responses in the comments below.</p>
    `;
  }

  renderCommentsSkeleton() {
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
        'https://groups.google.com/a/chromium.org/d/msgid/blink-dev/'
      ) ||
        threadArchiveUrl.startsWith(
          'https://groups.google.com/d/msgid/jrobbins-test'
        ))
    );
  }

  renderControls() {
    const canComment = this.user?.can_comment || this.userCanRequestReview();
    if (!canComment) return nothing;

    const postButton = html`
      <sl-button
        variant="primary"
        @click=${this.handlePost}
        ?disabled=${!this.needsPost || this.submittingVote}
        size="small"
        >Post</sl-button
      >
    `;
    const checkboxLabel = this.stage.intent_thread_url
      ? html`
          Also post to
          <a href=${this.stage.intent_thread_url} target="_blank"
            >intent thread</a
          >
        `
      : 'Also post to intent thread';
    const postToThreadCheckbox = this.gateHasIntentThread()
      ? html`
          <sl-checkbox
            ${ref(this.postToThreadRef)}
            ?disabled=${!this.canPostTo(this.stage.intent_thread_url)}
            size="small"
            >${checkboxLabel}</sl-checkbox
          >
        `
      : nothing;
    const escalation = this.gate.escalation_email
      ? html`If needed, you can
          <a href="mailto:${this.gate.escalation_email}" target="_blank"
            >email the team directly</a
          >.`
      : nothing;

    return html`
      <sl-textarea
        id="comment_area"
        rows="2"
        cols="40"
        ${ref(this.commentAreaRef)}
        @sl-change=${this.checkNeedsPost}
        @keypress=${this.checkNeedsPost}
        placeholder="Add a comment"
      ></sl-textarea>
      <div id="controls">${postButton} ${postToThreadCheckbox}</div>
      <div class="instructions">
        Comments will be visible publicly. Only reviewers will be notified when
        a comment is posted. ${escalation}
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
        .featureId=${this.feature.id}
        .narrow=${true}
        .reverse=${true}
        .comments=${this.comments}
      >
      </chromedash-activity-log>
    `;
  }

  render() {
    return html`
      <sl-icon-button
        title="Close"
        name="x"
        id="close-button"
        @click=${() => this.handleCancel()}
      ></sl-icon-button>

      ${this.loading ? this.renderHeadingsSkeleton() : this.renderHeadings()}

      <div id="review-status-area">
        ${this.loading
          ? this.renderReviewStatusSkeleton()
          : this.renderReviewStatus()}
        ${this.renderReviewRequest()}
      </div>
      <div id="slo-area">
        ${this.loading
          ? this.renderSLOStatusSkeleton()
          : this.renderSLOStatus()}
      </div>

      ${this.renderWarnings()}

      <div id="votes-area">
        ${this.loading ? this.renderVotesSkeleton() : this.renderVotes()}
      </div>

      ${this.loading
        ? this.renderQuestionnaireSkeleton()
        : this.renderQuestionnaire()}
      ${this.loading ? this.renderCommentsSkeleton() : this.renderComments()}
    `;
  }
}
