import {LitElement, css, html} from 'lit';
import {showToastMessage} from './utils.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {FORM_STYLES} from '../css/forms-css.js';
import {customElement, state} from 'lit/decorators.js';

interface StaleFeatureInfo {
  id: number;
  name: string;
  owner_emails: string[];
  milestone: number;
  milestone_field: string;
  outstanding_notifications: number;
  accurate_as_of: string;
}

type SortableColumns =
  | 'name'
  | 'milestone'
  | 'milestone_field'
  | 'outstanding_notifications'
  | 'accurate_as_of';

@customElement('chromedash-stale-features-page')
export class ChromedashStaleFeaturesPage extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      ...FORM_STYLES,
      css`
        :host {
          display: block;
          padding: 1em 2em;
          max-width: 1400px;
          margin: auto;
        }

        #subheader {
          padding: 0.5em 0;
          margin-bottom: 1.5em;
          border-bottom: 1px solid #e0e0e0;
        }

        #breadcrumbs {
          color: #333;
          font-size: 1.75em;
          font-weight: 600;
          margin: 0;
        }

        table {
          width: 100%;
          border-collapse: collapse;
        }

        th,
        td {
          padding: 14px 18px;
          text-align: left;
          border-bottom: 1px solid #ddd;
        }

        thead tr {
          background-color: #f9f9f9;
        }

        th {
          font-weight: 600;
          color: #555;
          text-transform: uppercase;
          font-size: 0.85em;
          letter-spacing: 0.05em;
        }

        th.sortable {
          cursor: pointer;
          user-select: none;
          position: relative;
          padding-right: 36px;
        }

        th.sortable:hover {
          background-color: #f0f0f0;
        }

        .sort-indicator {
          position: absolute;
          top: 50%;
          right: 18px;
          transform: translateY(-50%);
          opacity: 0.6;
          transition: opacity 0.2s ease-in-out;
        }

        tbody tr:nth-child(even) {
          background-color: #fdfdfd;
        }

        tbody tr:hover {
          background-color: #f1f1f1;
          transition: background-color 0.2s ease-in-out;
        }

        td a {
          color: var(--link-color);
          text-decoration: none;
          font-weight: 500;
        }

        td a:hover {
          text-decoration: underline;
        }

        .no-features {
          padding: 2em;
          text-align: center;
          font-style: italic;
          color: #777;
          background-color: #fafafa;
          border: 1px solid #ddd;
          border-radius: 8px;
        }
      `,
    ];
  }
  @state()
  private staleFeatures: StaleFeatureInfo[] = [];
  @state()
  private loading = true;
  @state()
  private _sortColumn: SortableColumns = 'name';
  @state()
  private _sortDirection: 'asc' | 'desc' = 'asc';

  connectedCallback() {
    super.connectedCallback();
    this.fetchData();
  }

  async fetchData() {
    this.loading = true;
    try {
      const staleFeaturesResp = await window.csClient.getStaleFeatures();
      this.staleFeatures = staleFeaturesResp.stale_features;
    } catch (error) {
      console.error(error);
      showToastMessage(
        'Some errors occurred. Please refresh the page or try again later.'
      );
    } finally {
      this.loading = false;
    }
  }

  private _handleSort(column: SortableColumns) {
    if (this._sortColumn === column) {
      this._sortDirection = this._sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      this._sortColumn = column;
      this._sortDirection = 'asc';
    }
  }

  private _renderSortIndicator(column: SortableColumns) {
    if (this._sortColumn !== column) {
      return '';
    }
    return this._sortDirection === 'asc' ? '▲' : '▼';
  }

  renderSkeletons() {
    return html`
      <h3><sl-skeleton effect="sheen"></sl-skeleton></h3>
      <section id="metadata">
        <h3><sl-skeleton effect="sheen"></sl-skeleton></h3>
        <p>
          <sl-skeleton effect="sheen"></sl-skeleton>
          <sl-skeleton effect="sheen"></sl-skeleton>
          <sl-skeleton effect="sheen"></sl-skeleton>
          <sl-skeleton effect="sheen"></sl-skeleton>
          <sl-skeleton effect="sheen"></sl-skeleton>
          <sl-skeleton effect="sheen"></sl-skeleton>
          <sl-skeleton effect="sheen"></sl-skeleton>
          <sl-skeleton effect="sheen"></sl-skeleton>
        </p>
      </section>
    `;
  }

  renderSubheader() {
    return html`
      <div id="subheader">
        <h2 id="breadcrumbs">Stale Features</h2>
      </div>
    `;
  }

  renderStaleFeatures() {
    if (this.staleFeatures.length === 0) {
      return html`
        <div class="no-features">
          <p>No stale features found. Great job!</p>
        </div>
      `;
    }

    const sortedFeatures = [...this.staleFeatures].sort((a, b) => {
      const valA = a[this._sortColumn];
      const valB = b[this._sortColumn];

      let comparison = 0;
      if (typeof valA === 'string' && typeof valB === 'string') {
        comparison = valA.localeCompare(valB);
      } else if (typeof valA === 'number' && typeof valB === 'number') {
        comparison = valA - valB;
      } else if (this._sortColumn === 'accurate_as_of') {
        comparison = new Date(valA).getTime() - new Date(valB).getTime();
      }

      return this._sortDirection === 'asc' ? comparison : -comparison;
    });

    return html`
      <div class="stale-features-table-container">
        <table>
          <thead>
            <tr>
              <th class="sortable" @click=${() => this._handleSort('name')}>
                Name
                <span class="sort-indicator"
                  >${this._renderSortIndicator('name')}</span
                >
              </th>
              <th>Owner Emails</th>
              <th
                class="sortable"
                @click=${() => this._handleSort('milestone_field')}
              >
                Milestone Field
                <span class="sort-indicator"
                  >${this._renderSortIndicator('milestone_field')}</span
                >
              </th>
              <th
                class="sortable"
                @click=${() => this._handleSort('milestone')}
              >
                Milestone
                <span class="sort-indicator"
                  >${this._renderSortIndicator('milestone')}</span
                >
              </th>
              <th
                class="sortable"
                @click=${() => this._handleSort('outstanding_notifications')}
              >
                Notifications
                <span class="sort-indicator"
                  >${this._renderSortIndicator(
                    'outstanding_notifications'
                  )}</span
                >
              </th>
              <th
                class="sortable"
                @click=${() => this._handleSort('accurate_as_of')}
              >
                Last Updated
                <span class="sort-indicator"
                  >${this._renderSortIndicator('accurate_as_of')}</span
                >
              </th>
            </tr>
          </thead>
          <tbody>
            ${sortedFeatures.map(
              feature => html`
                <tr>
                  <td><a href="/feature/${feature.id}">${feature.name}</a></td>
                  <td>${feature.owner_emails.join(', ')}</td>
                  <td>${feature.milestone_field}</td>
                  <td>${feature.milestone}</td>
                  <td>${feature.outstanding_notifications}</td>
                  <td>
                    ${new Date(feature.accurate_as_of).toLocaleDateString()}
                  </td>
                </tr>
              `
            )}
          </tbody>
        </table>
      </div>
    `;
  }

  render() {
    return html`
      ${this.renderSubheader()}
      ${this.loading ? this.renderSkeletons() : this.renderStaleFeatures()}
    `;
  }
}
