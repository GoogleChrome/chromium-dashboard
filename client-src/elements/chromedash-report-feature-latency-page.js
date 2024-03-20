// @ts-check
import {Task} from '@lit/task';
import '@shoelace-style/shoelace';
import {LitElement, css, html} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';

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
      td, th {
        padding: var(--content-padding);
        border-bottom: var(--table-divider);
      }
      th {
        background: var(--table-header-background);
      }
      tr {
        background: var(--table-row-background);
      }
      `];
  }

  static get properties() {
    return {
      latencyList: {type: Array},
      startDate: {state: true},
      endDate: {state: true},
    };
  }

  /** @type {import('chromestatus-openapi').DefaultApiInterface} */
  _client;

  constructor() {
    super();
    // Default to entire year 2023.
    this.startDate = new Date('January 1, 2023');
    this.endDate = new Date('January 1, 2024');
    // @ts-ignore
    this._client = window.csOpenApiClient;
    this._latencyTask = new Task(this, {
      task: async ([startDate, endDate], {signal}) => {
        this.latencyList = await this._client.listFeatureLatency(
          {startDate, endDate}, {signal});
        return this.latencyList;
      },
      args: () => [this.startDate, this.endDate],
    });
  }

  renderCount() {
    return html`
     <p>
     Launched ${this.latencyList.length} features between
     ${this.startDate.toLocaleDateString()} and
     ${this.endDate.toLocaleDateString()}.
     </p>
   `;
  }


  renderLatencyRow(featureLatency) {
    const latencyMs = featureLatency.shipped_date - featureLatency.entry_created_date;
    const latencyDays = Math.ceil(latencyMs / (1000 * 3600 * 24));
    return html`
     <tr>
       <td>
         <a href="/feature/${featureLatency.feature.id}">
           ${featureLatency.feature.name}
         </a>
       </td>
       <td>${featureLatency.owner_email}</td>
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
         <th>Latency days</th>
       </tr>
       ${this.latencyList.map((fl) => this.renderLatencyRow(fl))}
     </table>
   `;
  }

  renderWhenComplete() {
    return html`
     ${this.renderCount()}
     ${this.renderTable()}
   `;
  }

  render() {
    return this._latencyTask.render({
      initial: () => html`<p>Loading...</p>`,
      pending: () => html`<p>Loading...</p>`,
      complete: () => {
        return this.renderWhenComplete();
      },
      error: (e) => {
        console.error(e);
        return html`<p>Some errors occurred. Please refresh the page or try again later.</p>`;
      },
    });
  }
}

customElements.define('chromedash-report-feature-latency-page', ChromedashReportFeatureLatencyPage);
