import {LitElement, css, html, nothing} from 'lit';
import {showToastMessage, clamp} from './utils.js';
import './chromedash-feature-filter';
import './chromedash-feature-row';
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
        min-height: 50px;
        display: flex;
        align-items: center;
        justify-content: end;
      }
      .pagination span {
        color: var(--unimportant-text-color);
        margin-right: var(--content-padding);
      }
      .pagination sl-icon-button {
        font-size: 1.6rem;
      }
      .pagination sl-icon-button::part(base) {
        padding: 0;
      }
      table {
        width: 100%;
      }
      .skel td {
        background: white;
        padding: 14px;
        border-bottom: var(--table-divider);
      }
      sl-skeleton {
        height: 24px;
      }
    `];
  }

  renderMessages() {
    if (this.loading) {
      return html`
        <tr class="skel"><td>
          <sl-skeleton effect="sheen" style="width: 50%"></sl-skeleton>
        </td></tr>
        <tr class="skel"><td>
          <sl-skeleton effect="sheen" style="width: 65%"></sl-skeleton>
        </td></tr>
        <tr class="skel"><td>
          <sl-skeleton effect="sheen" style="width: 40%"></sl-skeleton>
        </td></tr>
        <tr class="skel"><td>
          <sl-skeleton effect="sheen" style="width: 50%"></sl-skeleton>
        </td></tr>
      `;
    }
    if (this.features.length == 0) {
      return html`
        <tr><td>${this.noResultsMessage}</td></tr>
      `;
    }
    return false; // Causes features to render instead.
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
        return html`
          <div class="pagination">
            <sl-skeleton effect="sheen" style="float: right; width: 12em">
            </sl-skeleton>
          </div>`;
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
        <sl-icon-button
          library="material" name="navigate_before"
          title="Previous page"
          @click=${() => this.loadNewPaginationPage(-this.num)}
          ?disabled=${!hasPrevPage}
          ></sl-icon-button>
        <sl-icon-button
          library="material" name="navigate_next"
          title="Next page"
          @click=${() => this.loadNewPaginationPage(this.num)}
          ?disabled=${!hasNextPage}
          ></sl-icon-button>
      </div>
    `;
  }

  renderFeature(feature) {
    return html`
      <chromedash-feature-row
         .feature=${feature}
         columns=${this.columns}
         ?signedIn=${this.signedIn}
         ?canEdit=${this.canApprove}
         ?canApprove=${this.canApprove}
         .starredFeatures=${this.starredFeatures}
         .approvals=${this.approvals}
         .configs=${this.configs}
         ></chromedash-feature-row>
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
