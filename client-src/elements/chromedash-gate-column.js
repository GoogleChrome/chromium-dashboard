import {LitElement, css, html, nothing} from 'lit';
import './chromedash-activity-log';
import {showToastMessage, findProcessStage} from './utils.js';

import {SHARED_STYLES} from '../sass/shared-css.js';


export const STATE_NAMES = [
  [7, 'No response'],
  [1, 'N/a or Ack'],
  [2, 'Review requested'],
  [3, 'Review started'],
  [4, 'Needs work'],
  [8, 'Internal review'],
  [5, 'Approved'],
  [6, 'Denied'],
];


class ChromedashGateColumn extends LitElement {
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

       #votes-area {
         margin: var(--content-padding) 0;
       }

       #votes-area table {
         border-spacing: var(--content-padding-half) var(--content-padding);
       }

       #votes-area th {
         font-weight: bold;
       }

       #review-status-area {
         margin: var(--content-padding-half) 0;
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
      window.csClient.getComments(featureId),
    ]).then(([process, approvalRes, commentRes]) => {
      this.process = process;
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

  renderReviewStatus() {
    // TODO(jrobbins): display gate state name and requested_on or reviewed_on.
    return html`
      <div>
        Review requested on YYYY-MM-DD
      </div>
    `;
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
    for (const item of STATE_NAMES) {
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
    // hoist is needed when <sl-select> is in overflow:hidden context.
    return html`
      <sl-select name="${this.gate.id}"
                 value="${state}"
                 @sl-change=${this.handleSelectChanged}
                 hoist size="small">
        ${STATE_NAMES.map((valName) => html`
          <sl-menu-item value="${valName[0]}">${valName[1]}</sl-menu-item>`,
        )}
      </sl-select>
    `;
  }

  renderVoteRow(vote) {
    const voteCell = (vote.set_by == this.user.email) ?
      this.renderVoteMenu(vote.state) :
      this.renderVoteReadOnly(vote);
    return html`
      <tr>
       <td>${vote.set_by}</td>
       <td>${voteCell}</td>
      </tr>
    `;
  }

  renderVotes() {
    const canVote = true; // TODO(jrobbins): permission checks.
    const myVoteExists = this.votes.some((v) => v.set_by == this.user.email);
    const addVoteRow = (canVote && !myVoteExists) ?
      this.renderVoteRow({set_by: this.user.email, state: 7}) :
      nothing;

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
    return html`
      <h2>Comments &amp; Activity</h2>
      <sl-skeleton effect="sheen"></sl-skeleton>
    `;
  }

  renderComments() {
    return html`
      <h2>Comments &amp; Activity</h2>
      TODO(jrobbins): Comments go here
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
