// @ts-check
import {Task} from '@lit/task';
import {LitElement, css, html} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';
import {GATE_TYPES} from './form-field-enums.js';
import './chromedash-report-spec-mentor.js';
import {customElement, property} from 'lit/decorators.js';
import {DefaultApiInterface, ReviewLatency} from 'chromestatus-openapi';

@customElement('chromedash-report-review-latency-page')
export class ChromedashReportReviewLatencyPage extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        p {
          margin: var(--content-padding) 0;
        }
        table {
          border-collapse: collapse;
          border: 1px solid #888;
        }
        td,
        th {
          padding: var(--content-padding-half);
          text-align: center;
        }
        td {
          border-top: 1px solid #888;
          border-bottom: 1px solid #888;
        }
        colgroup {
          border: 1px solid #888;
        }
        th {
          background: var(--table-header-background);
        }
        tr {
          background: var(--table-row-background);
        }
        .left {
          text-align: left;
          min-width: 18em;
        }
      `,
    ];
  }

  static get properties() {
    return {
      featureReviewList: {state: true},
    };
  }

  @property({attribute: false})
  private _client: DefaultApiInterface = window.csOpenApiClient;
  @property({attribute: false})
  reviewLatencyList: ReviewLatency[] = [];
  @property({attribute: false})
  private _reviewLatencyTask: Task<never[], void> = new Task(this, {
    task: async ([], {signal}) => {
      this.reviewLatencyList = await this._client.listReviewsWithLatency({
        signal,
      });
    },
    args: () => [],
  });

  renderCount() {
    let count = 0;
    for (const rl of this.reviewLatencyList) {
      for (const gr of rl.gate_reviews) {
        if (gr.latency_days >= 0) {
          count++;
        }
      }
    }

    return html`
      <p>
        ${count} reviews of ${this.reviewLatencyList.length} distinct features
        in the past 90 days.
      </p>
      <p>Latency is measured in weekdays from request to initial response.</p>
    `;
  }

  renderFeatureReviewsRow(reviewLatency) {
    const gateLatency = {};
    for (const gr of reviewLatency.gate_reviews) {
      let display = gr.latency_days;
      if (gr.latency_days === -1) {
        display = '';
      } else if (gr.latency_days == -2) {
        display = 'Pending';
      }
      gateLatency[gr.gate_type] = display;
    }
    return html`
      <tr>
        <td class="left">
          <a href="/feature/${reviewLatency.feature.id}">
            ${reviewLatency.feature.name}
          </a>
        </td>
        <td>${gateLatency[GATE_TYPES.PRIVACY_ORIGIN_TRIAL]}</td>
        <td>${gateLatency[GATE_TYPES.PRIVACY_SHIP]}</td>
        <td>${gateLatency[GATE_TYPES.SECURITY_ORIGIN_TRIAL]}</td>
        <td>${gateLatency[GATE_TYPES.SECURITY_SHIP]}</td>
        <td>${gateLatency[GATE_TYPES.ENTERPRISE_SHIP]}</td>
        <td>${gateLatency[GATE_TYPES.DEBUGGABILITY_ORIGIN_TRIAL]}</td>
        <td>${gateLatency[GATE_TYPES.DEBUGGABILITY_SHIP]}</td>
        <td>${gateLatency[GATE_TYPES.TESTING_SHIP]}</td>
        <td>${gateLatency[GATE_TYPES.API_ORIGIN_TRIAL]}</td>
        <td>${gateLatency[GATE_TYPES.API_SHIP]}</td>
      </tr>
    `;
  }

  renderTable() {
    return html`
      <table>
        <colgroup>
          <col />
        </colgroup>
        <colgroup>
          <col />
          <col />
        </colgroup>
        <colgroup>
          <col />
          <col />
        </colgroup>
        <colgroup>
          <col />
        </colgroup>
        <colgroup>
          <col />
          <col />
        </colgroup>
        <colgroup>
          <col />
        </colgroup>
        <colgroup>
          <col />
          <col />
        </colgroup>
        <tr>
          <th scope="col" rowspan="2" class="left">Feature</th>
          <th scope="col" colspan="2">Privacy</th>
          <th scope="col" colspan="2">Security</th>
          <th scope="col" colspan="1">Enterprise</th>
          <th scope="col" colspan="2">Debugability</th>
          <th scope="col" colspan="1">Testing</th>
          <th scope="col" colspan="2">API Owners</th>
        </tr>
        <tr>
          <th>OT</th>
          <th>Ship</th>
          <th>OT</th>
          <th>Ship</th>
          <th>Ship</th>
          <th>OT</th>
          <th>Ship</th>
          <th>Ship</th>
          <th>OT</th>
          <th>Ship</th>
        </tr>

        ${this.reviewLatencyList.map(rl => this.renderFeatureReviewsRow(rl))}
      </table>
    `;
  }

  renderWhenComplete() {
    return html` ${this.renderCount()} ${this.renderTable()} `;
  }

  render() {
    return this._reviewLatencyTask.render({
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
