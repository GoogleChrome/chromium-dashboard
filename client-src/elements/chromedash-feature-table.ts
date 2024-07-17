import {LitElement, css, html, nothing} from 'lit';
import {customElement, property, state} from 'lit/decorators.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {Feature} from '../js-src/cs-client.js';
import './chromedash-feature-filter';
import './chromedash-feature-row';
import {clamp, showToastMessage} from './utils.js';
import {GateDict} from './chromedash-gate-chip.js';

@customElement('chromedash-feature-table')
export class ChromedashFeatureTable extends LitElement {
  @state()
  loading = true;
  @state()
  reloading = false;
  @state()
  features!: Feature[];
  @state()
  totalCount = 0;
  @property({type: Number, attribute: false})
  start = 0;
  @property({type: String, attribute: false})
  query = '';
  @property({type: Boolean, attribute: false})
  showEnterprise = false;
  @property({type: String, attribute: false})
  sortSpec = '';
  @property({type: Boolean})
  showQuery = false;
  @property({type: Object, attribute: false})
  starredFeatures = new Set<number>();
  @property({type: Number, attribute: false})
  num = 100;
  @property({type: Boolean})
  alwaysOfferPagination = false;
  @property({type: String})
  noResultsMessage = 'No results';
  @property({type: Boolean})
  canEdit = false;
  @property({type: Object})
  gates: Record<number, GateDict[]> = {};
  @property({type: Number})
  selectedGateId = 0;
  @property({type: String})
  columns!: 'normal' | 'approvals';
  @property({type: Boolean})
  signedIn!: boolean;

  connectedCallback() {
    super.connectedCallback();
    this.fetchFeatures(true);
  }

  fetchFeatures(isInitialLoad = false) {
    this.loading = isInitialLoad;
    this.reloading = !isInitialLoad;
    window.csClient
      .searchFeatures(
        this.query,
        this.showEnterprise,
        this.sortSpec,
        this.start,
        this.num
      )
      .then(resp => {
        this.features = resp.features;
        this.totalCount = resp.total_count;
        this.loading = false;
        this.reloading = false;
      })
      .catch(() => {
        showToastMessage(
          'Some errors occurred. Please refresh the page or try again later.'
        );
      });
    if (this.columns == 'approvals') {
      this.loadGateData();
    }
  }

  refetch() {
    this.fetchFeatures();
  }

  loadGateData() {
    window.csClient
      .getPendingGates()
      .then(res => {
        const gatesByFID: Record<number, GateDict[]> = {};
        for (const g of res.gates) {
          if (!gatesByFID.hasOwnProperty(g.feature_id)) {
            gatesByFID[g.feature_id] = [];
          }
          gatesByFID[g.feature_id].push(g);
        }
        this.gates = gatesByFID;
      })
      .catch(() => {
        showToastMessage(
          'Some errors occurred. Please refresh the page or try again later.'
        );
      });
  }

  // For rerendering of the "Features I starred" section when a feature is starred
  // only re-fetch if !this.loading to avoid double fetching on first update.
  updated(changedProperties) {
    if (
      this.query == 'starred-by:me' &&
      !this.loading &&
      changedProperties.has('starredFeatures')
    ) {
      this.fetchFeatures();
    }
  }

  handleSearch(event) {
    this.loading = true;
    this.query = event.detail.query;
    this.fetchFeatures();
  }

  loadNewPaginationPage(delta) {
    const proposedStart = this.start + delta;
    this.start = clamp(proposedStart, 0, this.totalCount - 1);
    this._fireEvent('pagination', {index: this.start});
    this.fetchFeatures();
  }

  _fireEvent(eventName, detail) {
    const event = new CustomEvent(eventName, {
      bubbles: true,
      composed: true,
      detail,
    });
    this.dispatchEvent(event);
  }

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        .pagination {
          padding: var(--content-padding-half) 0;
          min-height: 50px;
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
      `,
    ];
  }

  renderMessages() {
    if (this.loading) {
      return html`
        <tr class="skel">
          <td>
            <sl-skeleton effect="sheen" style="width: 50%"></sl-skeleton>
          </td>
        </tr>
        <tr class="skel">
          <td>
            <sl-skeleton effect="sheen" style="width: 65%"></sl-skeleton>
          </td>
        </tr>
        <tr class="skel">
          <td>
            <sl-skeleton effect="sheen" style="width: 40%"></sl-skeleton>
          </td>
        </tr>
        <tr class="skel">
          <td>
            <sl-skeleton effect="sheen" style="width: 50%"></sl-skeleton>
          </td>
        </tr>
      `;
    }
    if (this.features.length == 0) {
      return html`
        <tr>
          <td>${this.noResultsMessage}</td>
        </tr>
      `;
    }
    return false; // Causes features to render instead.
  }

  renderSearch() {
    if (this.showQuery) {
      return html`
        <chromedash-feature-filter
          .query=${this.query}
          @search="${this.handleSearch}"
        ></chromedash-feature-filter>
      `;
    }
    return nothing;
  }

  renderPagination() {
    // Indexes of first and last items shown in one-based counting.
    const firstShown = this.start + 1;
    const lastShown = this.start + this.features.length;

    const hasPrevPage = firstShown > 1;
    const hasNextPage = lastShown < this.totalCount;

    if (this.alwaysOfferPagination) {
      if (this.loading) {
        // reserve vertical space to use when loaded.
        return html` <div class="pagination">
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

    if (this.features.length === 0) {
      return nothing;
    }

    return html`
      <div class="pagination hbox">
        <span>${this.reloading ? 'Reloading...' : nothing}</span>
        <div class="spacer"></div>
        <span>${firstShown} - ${lastShown} of ${this.totalCount}</span>
        <sl-icon-button
          library="material"
          name="navigate_before"
          title="Previous page"
          @click=${() => this.loadNewPaginationPage(-this.num)}
          ?disabled=${!hasPrevPage}
        ></sl-icon-button>
        <sl-icon-button
          library="material"
          name="navigate_next"
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
        ?canEdit=${this.canEdit}
        .starredFeatures=${this.starredFeatures}
        .gates=${this.gates}
        selectedGateId=${this.selectedGateId}
      ></chromedash-feature-row>
    `;
  }

  render() {
    return html`
      ${this.renderSearch()} ${this.renderPagination()}
      <table>
        ${this.renderMessages() ||
        this.features.map(feature => this.renderFeature(feature))}
      </table>
    `;
  }
}
