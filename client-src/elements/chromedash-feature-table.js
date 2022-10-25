import {LitElement, css, html, nothing} from 'lit';
import {STATE_NAMES} from './chromedash-approvals-dialog.js';
import {showToastMessage, clamp} from './utils.js';
import './chromedash-feature-filter';
import {SHARED_STYLES} from '../sass/shared-css.js';


class ChromedashFeatureTable extends LitElement {
  static get properties() {
    return {
      query: {type: String},
      sortSpec: {type: String},
      showQuery: {type: Boolean},
      features: {type: Array},
      totalCount: {type: Number},
      loading: {type: Boolean},
      start: {type: Number},
      num: {type: Number},
      alwaysOfferPagination: {type: Boolean},
      columns: {type: String},
      signedIn: {type: Boolean},
      canEdit: {type: Boolean},
      canApprove: {type: Boolean},
      starredFeatures: {type: Object},
      noResultsMessage: {type: String},
      approvals: {type: Object},
      comments: {type: Object},
      configs: {type: Object},
    };
  }

  constructor() {
    super();
    this.query = '';
    this.sortSpec = '';
    this.showQuery = false;
    this.loading = true;
    this.starredFeatures = new Set();
    this.features = [];
    this.totalCount = 0;
    this.start = 0;
    this.num = 100;
    this.alwaysOfferPagination = false;
    this.noResultsMessage = 'No results';
    this.canEdit = false;
    this.canApprove = false;
    this.approvals = {};
    this.comments = {};
    this.configs = {};
  }

  connectedCallback() {
    super.connectedCallback();
    this.fetchFeatures();
  }

  fetchFeatures() {
    this.loading = true;
    window.csClient.searchFeatures(
      this.query, this.sortSpec, this.start, this.num).then((resp) => {
      this.features = resp.features;
      this.totalCount = resp.total_count;
      this.loading = false;
      if (this.columns == 'approvals') {
        this.loadApprovalData();
      }
    }).catch(() => {
      showToastMessage('Some errors occurred. Please refresh the page or try again later.');
    });
  }

  loadApprovalData() {
    for (const feature of this.features) {
      window.csClient.getApprovals(feature.id).then(res => {
        const newApprovals = {...this.approvals};
        newApprovals[feature.id] = res.approvals;
        this.approvals = newApprovals;
      });
      window.csClient.getComments(feature.id).then(res => {
        const newComments = {...this.comments};
        newComments[feature.id] = res.comments;
        this.comments = newComments;
      });
      window.csClient.getApprovalConfigs(feature.id).then(res => {
        const newConfigs = {...this.configs};
        newConfigs[feature.id] = res.configs;
        this.configs = newConfigs;
      });
    }
  }

  // For rerendering of the "Features I starred" section when a feature is starred
  // only re-fetch if !this.loading to avoid double fetching on first update.
  updated(changedProperties) {
    if (this.query == 'starred-by:me' && !this.loading &&
      changedProperties.has('starredFeatures')) {
      this.fetchFeatures();
    }
  }

  handleSearch(event) {
    this.loading = true;
    this.query = event.detail.query;
    this.fetchFeatures();
  }

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
      .pagination {
        padding: var(--content-padding-half) 0;
        text-align: right;
        min-height: 50px;
      }
      .pagination span {
        color: var(--unimportant-text-color);
        margin-right: var(--content-padding);
      }
      table {
        width: 100%;
      }
      tr {
        background: var(--table-row-background);
      }
      td {
        padding: var(--content-padding-half);
        border-bottom: var(--table-divider);
      }
      td.name_col {
        width: 100%;
      }
      td.icon_col {
        white-space: nowrap;
        vertical-align: top;
      }
      td.icon_col a {
        padding: 2px 4px;
      }
      td.icon_col a:hover {
        text-decoration: none;
      }
      .quick_actions {
        white-space: nowrap;
        float: right;
      }
      .highlights {
        padding-left: var(--content-padding);
      }
      .highlights div {
        color: var(--unimportant-text-color);
        padding: var(--content-padding-quarter);
      }
      sl-icon-button {
        font-size: 1.3rem;
      }
      sl-icon-button::part(base) {
        color: var(--link-color);
      }
      button {
        border: var(--default-border);
        padding: 0 6px;
        font-size: var(--button-small-font-size);
      }
    `];
  }

  _fireEvent(eventName, detail) {
    const event = new CustomEvent(eventName, {
      bubbles: true,
      composed: true,
      detail,
    });
    this.dispatchEvent(event);
  }

  toggleStar(e) {
    e.preventDefault();
    e.stopPropagation();

    const iconEl = e.target;
    const featureId = Number(iconEl.dataset.featureId);
    const newStarred = !this.starredFeatures.has(featureId);

    // handled in chromedash-myfeatures-page.js
    this._fireEvent('star-toggle-event', {
      featureId: featureId,
      doStar: newStarred,
    });
  }

  renderMessages() {
    if (this.loading) {
      return html`
        <tr><td>Loading...</td></tr>
      `;
    }
    if (this.features.length == 0) {
      return html`
        <tr><td>${this.noResultsMessage}</td></tr>
      `;
    }
    return false; // Causes features to render instead.
  }

  openApprovalsDialog(feature) {
    // handled in chromedash-myfeatures-page.js
    this._fireEvent('open-approvals-event', {
      feature: feature,
    });
  }

  doLGTM(feature) {
    // TODO(jrobbins): Make it pre-select Approved and add comment.
    this.openApprovalsDialog(feature);
  }

  doSnooze(feature) {
    // TODO(jrobbins): Make it pre-set a new next-review-date value.
    this.openApprovalsDialog(feature);
  }

  renderApprovalsIcon(feature) {
    return html`
      <sl-icon-button
        @click="${() => this.openApprovalsDialog(feature)}"
        title="Review approvals"
        library="material" name="approval"></sl-icon-button>
    `;
  }

  renderEditIcon(feature) {
    return html`
      <sl-icon-button href="/guide/edit/${feature.id}"
        title="Edit feature"
        name="pencil-fill"></sl-icon-button>
    `;
  }

  renderStarIcon(feature) {
    return html`
      <sl-icon-button
        @click=${this.toggleStar}
        title="Receive an email notification when there are updates"
        library="material"
        name="${this.starredFeatures.has(Number(feature.id)) ?
                'star' : 'star_border'}"
        data-feature-id="${feature.id}"></sl-icon-button>
    `;
  }

  renderIcons(feature) {
    if (this.signedIn) {
      return html`
        ${this.canApprove ? this.renderApprovalsIcon(feature) : nothing}
        ${this.canEdit ? this.renderEditIcon(feature) : nothing}
        ${this.renderStarIcon(feature)}
      `;
    } else {
      return nothing;
    }
  }

  renderQuickActions(feature) {
    if (this.columns == 'approvals') {
      // TODO(jrobbins): Show only thread link for active intent.
      // Blocked on merge of PR that adds fetching that info.
      // Work around unused function parameter lint error.
      const threadLinks = feature ? [] : [];

      // TODO(jrobbins): Show these buttons when they work.
      // let lgtmButton = html`
      //  <button data-feature-id="${feature.id}"
      //          @click="${() => this.doLGTM(feature)}">
      //    Add LGTM
      //  </button>
      // `;
      // let snoozeButton = html`
      //  <button data-feature-id="${feature.id}"
      //          @click="${() => this.doSnooze(feature)}">
      //    Snooze
      //  </button>
      // `;

      return html`
        <span class="quick_actions">
          ${threadLinks}
        </span>
      `;
    }
    return nothing;
  }

  getEarliestReviewDate(feature) {
    const featureConfigs = this.configs[feature.id] || [];
    const allDates = featureConfigs.map(c => c.next_action).filter(d => d);
    if (allDates.length > 0) {
      allDates.sort();
      return allDates[0];
    }
    return null;
  }

  getActiveOwners(feature) {
    const featureConfigs = this.configs[feature.id] || [];
    const allOwners = featureConfigs.map(c => c.owners).flat();
    // TODO(jrobbins): Limit to only owners of active intents
    let activeOwners = allOwners;
    activeOwners = [...new Set(activeOwners)]; // de-dup.
    activeOwners.sort();
    return activeOwners;
  }

  getActiveApprovals(feature) {
    const featureApprovals = this.approvals[feature.id];
    // TODO(jrobbins): Limit to only owners of active intents
    const activeApprovals = featureApprovals;
    return activeApprovals;
  }

  getRecentComment(feature) {
    // TODO(jrobbins): implement this.
    return feature ? null : null;
  }

  renderApprovalsSoFar(approvals) {
    const result = [];
    for (const stateItem of STATE_NAMES) {
      const state = stateItem[0];
      const stateName = stateItem[1];
      const approvalsWithThatState = approvals.filter(a => a.state == state);
      const setters = approvalsWithThatState.map(a => a.set_by.split('@')[0]);
      if (setters.length > 0) {
        result.push(html`<span>${stateName}: ${setters.join(', ')}. </span>`);
      }
    }
    return result;
  }

  renderSearch() {
    if (this.showQuery) {
      return html`
       <chromedash-feature-filter
        @search="${this.handleSearch}"
       ></chromedash-feature-filter>
      `;
    }
    return nothing;
  }

  loadNewPaginationPage(delta) {
    const proposedStart = this.start + delta;
    this.start = clamp(proposedStart, 0, this.totalCount - 1);
    this.fetchFeatures();
  }

  renderPagination() {
    // Indexes of first and last items shown in one-based counting.
    const firstShown = this.start + 1;
    const lastShown = this.start + this.features.length;

    const hasPrevPage = firstShown > 1;
    const hasNextPage = lastShown < this.totalCount;

    if (this.alwaysOfferPagination) {
      if (this.loading) { // reserve vertical space to use when loaded.
        return html`<div class="pagination"></div>`;
      }
    } else {
      // On MyFeatures page, don't always show pagination.  Omit it if
      // results fit in each box (the most common case).
      if (this.loading || (firstShown == 1 && lastShown == this.totalCount)) {
        return nothing;
      }
    }

    return html`
      <div class="pagination">
        <span>${firstShown} - ${lastShown} of ${this.totalCount}</span>
        <sl-icon-button name="chevron-left" title="Previous page"
         @click=${() => this.loadNewPaginationPage(-this.num)}
         ?disabled=${!hasPrevPage}
         ></sl-icon-button>
        <sl-icon-button name="chevron-right" title="Next page"
         @click=${() => this.loadNewPaginationPage(this.num)}
         ?disabled=${!hasNextPage}
         ></sl-icon-button>
      </div>
    `;
  }

  renderHighlights(feature) {
    if (this.columns == 'approvals') {
      const nextReviewDate = this.getEarliestReviewDate(feature);
      const owners = this.getActiveOwners(feature);
      const activeApprovals = this.getActiveApprovals(feature);
      const recentComment = this.getRecentComment(feature);
      // TODO(jrobbins): show additional_review.

      return html`
        <div class="highlights">
          ${nextReviewDate ? html`
            <div>
              Next review date: ${nextReviewDate}
            </div>
            ` : nothing}
          ${owners.length == 1 ? html`
            <div>
              Owner: ${owners[0]}
            </div>
            ` : nothing}
          ${owners.length > 1 ? html`
            <div>
              Owners: ${owners.join(', ')}
            </div>
            ` : nothing}
          ${activeApprovals && activeApprovals.length > 0 ? html`
            <div>
              ${this.renderApprovalsSoFar(activeApprovals)}
            </div>
            ` : nothing}
          ${recentComment ? html`
            <div>
              Comment: ${recentComment.content}
            </div>
            ` : nothing}
        </div>
      `;
    }
    return nothing;
  }

  renderFeature(feature) {
    return html`
      <tr>
        <td class="name_col">
          ${this.renderQuickActions(feature)}
          <a href="/feature/${feature.id}?context=myfeatures">${feature.name}</a>
          ${this.renderHighlights(feature)}
        </td>
        <td class="icon_col">
          ${this.renderIcons(feature)}
        </td>
      </tr>
    `;
  }

  render() {
    return html`
      ${this.renderSearch()}
      ${this.renderPagination()}
       <table>
        ${this.renderMessages() ||
          this.features.map((feature) => this.renderFeature(feature))}
       </table>
     `;
  }
}

customElements.define('chromedash-feature-table', ChromedashFeatureTable);
