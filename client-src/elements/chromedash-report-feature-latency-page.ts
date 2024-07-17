// @ts-check
import {Task} from '@lit/task';
import '@shoelace-style/shoelace';
import {DefaultApiInterface, FeatureLatency} from 'chromestatus-openapi';
import {LitElement, css, html} from 'lit';
import {customElement, property, state} from 'lit/decorators.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {RawQuery} from './utils.js';

@customElement('chromedash-report-feature-latency-page')
export class ChromedashReportFeatureLatencyPage extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        p {
          margin: var(--content-padding) 0;
        }

        table {
          border: var(--table-divider);
        }
        td,
        th {
          padding: var(--content-padding);
          border-bottom: var(--table-divider);
          vertical-align: baseline;
        }
        th {
          background: var(--table-header-background);
        }
        tr {
          background: var(--table-row-background);
        }
      `,
    ];
  }

  static get properties() {
    return {
      latencyList: {type: Array},
      startAtDate: {state: true},
      endAtDate: {state: true},
    };
  }

  @property({type: Object})
  rawQuery: RawQuery = {};
  @property({attribute: false})
  private _client: DefaultApiInterface = window.csOpenApiClient;
  @property({attribute: false})
  latencyList: FeatureLatency[] = [];
  @property({attribute: false})
  private _latencyTask = new Task(this, {
    task: async ([startAt, endAt], {signal}) => {
      this.latencyList = await this._client.listFeatureLatency(
        {startAt, endAt},
        {signal}
      );
      return this.latencyList;
    },
    args: () => [this.startAtDate, this.endAtDate],
  });
  @state() // Default to entire year 2023.
  startAtDate = new Date('January 1, 2023');
  @state()
  endAtDate = new Date('January 1, 2024');

  connectedCallback() {
    super.connectedCallback();
    this.initializeParams();
  }

  initializeParams() {
    if (!this.rawQuery) {
      return;
    }

    if (this.rawQuery['startAt']) {
      const parsed = Date.parse(this.rawQuery['startAt']);
      if (!isNaN(parsed)) {
        this.startAtDate = new Date(parsed);
      }
    }
    if (this.rawQuery['endAt']) {
      const parsed = Date.parse(this.rawQuery['endAt']);
      if (!isNaN(parsed)) {
        this.endAtDate = new Date(parsed);
      }
    }
  }

  renderCount() {
    return html`
      <p>
        Launched ${this.latencyList.length} features between
        ${this.startAtDate.toLocaleDateString()} and
        ${this.endAtDate.toLocaleDateString()}.
      </p>
      <p>Latency is measured in calendar days.</p>
    `;
  }

  renderLatencyRow(featureLatency) {
    const latencyMs =
      featureLatency.shipped_date - featureLatency.entry_created_date;
    const latencyDays = Math.ceil(latencyMs / (1000 * 3600 * 24));
    return html`
      <tr>
        <td>
          <a href="/feature/${featureLatency.feature.id}">
            ${featureLatency.feature.name}
          </a>
        </td>
        <td>
          ${featureLatency.owner_emails.map(addr => html`<div>${addr}</div>`)}
        </td>
        <td>${featureLatency.entry_created_date.toLocaleDateString()}</td>
        <td>${featureLatency.shipped_date.toLocaleDateString()}</td>
        <td>${latencyDays}</td>
      </tr>
    `;
  }

  renderTable() {
    return html`
      <table>
        <tr>
          <th>Feature</th>
          <th>Owners</th>
          <th>Created</th>
          <th>Shipped</th>
          <th>Latency</th>
        </tr>
        ${this.latencyList.map(fl => this.renderLatencyRow(fl))}
      </table>
    `;
  }

  renderWhenComplete() {
    return html` ${this.renderCount()} ${this.renderTable()} `;
  }

  render() {
    return this._latencyTask.render({
      initial: () => html`<p>Loading...</p>`,
      pending: () => html`<p>Loading...</p>`,
      complete: () => {
        return this.renderWhenComplete();
      },
      error: e => {
        console.error(e);
        return html`<p>
          Some errors occurred. Please refresh the page or try again later.
        </p>`;
      },
    });
  }
}
