import {LitElement, css, html, nothing} from 'lit';
import {SHARED_STYLES} from '../sass/shared-css.js';


class ChromedashGateColumn extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
       #votes-area {
         margin: var(--content-padding) 0;
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
      loading: {type: Boolean},
    };
  }

  constructor() {
    super();
    this.user = {};
    this.loading = false;
  }

  connectedCallback() {
    super.connectedCallback();
    this.loading = true;
    // TODO(jrobbins): Just simulate loading data for now.
    window.setTimeout(() => {
      this.loading = false;
    }, 2000);
  }

  renderHeadingsSkeleton() {
    return html`
      <h3 class="sl-skeleton-header-container">
        <sl-skeleton effect="sheen"></sl-skeleton>
      </h3>
      <h2 class="sl-skeleton-header-container">
        <sl-skeleton effect="sheen"></sl-skeleton>
      </h2>
    `;
  }

  renderHeadings() {
    return html`
      <h3>Stage</h3>
      <h2>Gate</h2>
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
    return html`
      <h3>
        Status: Review requested
      </h3>
    `;
  }

  renderVotesSkeleton() {
    return html`
      <table cellspacing=4>
        <tr><th>Reviewer</th><th>Vote</th></tr>
        <tr>
         <td><sl-skeleton effect="sheen"></sl-skeleton></td>
         <td><sl-skeleton effect="sheen"></sl-skeleton></td>
        </tr>
      </table>
    `;
  }

  renderVotes() {
    return html`
      <table cellspacing=4>
        <tr><th>Reviewer</th><th>Vote</th></tr>
        <tr>
         <td>user1@example.com</td>
         <td>Needs work</td>
        </tr>
        <tr>
         <td>user2@example.com</td>
         <td>Review started</td>
        </tr>
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
