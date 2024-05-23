// @ts-check
import {Task} from '@lit/task';
import {LitElement, css, html} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';

export class ChromedashReportVerificationPage extends LitElement {
  static get styles() {
    return [...SHARED_STYLES, css``];
  }

  /** @type {import('chromestatus-openapi').DefaultApiInterface} */
  _client;

  constructor() {
    super();
    // @ts-ignore
    this._client = window.csOpenApiClient;
    this._pendingVerificationsTask = new Task(this, {
      task: async (_, {signal}) => {
        const pendingVerifications =
          await this._client.listPendingVerifications({signal});
        pendingVerifications.sort(
          (a, b) =>
            (a.accurate_as_of?.getTime() ?? 0) -
            (b.accurate_as_of?.getTime() ?? 0)
        );
        return pendingVerifications;
      },
      args: () => [],
    });
  }

  render() {
    return html`
      <div id="subheader">
        <h2>Features whose accuracy needs to be verified</h2>
      </div>
      <table class="data-table">
        <thead>
          <tr>
            <th>Feature</th>
            <th>Last Verified</th>
          </tr>
        </thead>
        ${this._pendingVerificationsTask.render({
          pending: () =>
            [1, 2, 3].map(
              () =>
                html`<tr>
                  <td><sl-skeleton effect="sheen"></sl-skeleton></td>
                  <td><sl-skeleton effect="sheen"></sl-skeleton></td>
                </tr>`
            ),
          complete: pendingVerifications =>
            pendingVerifications.map(
              verification =>
                html`<tr>
                  <td>
                    <a href="/guide/verify_accuracy/${verification.feature.id}"
                      >${verification.feature.name}</a
                    >
                  </td>
                  <td>
                    ${verification.accurate_as_of?.toLocaleDateString(
                      undefined,
                      {dateStyle: 'medium'}
                    )}
                  </td>
                </tr>`
            ),
          error: e => {
            console.error(e);
            return html`<tr>
              <td colspan="2">
                Some errors occurred. Please refresh the page or try again
                later.
              </td>
            </tr>`;
          },
        })}
      </table>
    `;
  }
}

customElements.define(
  'chromedash-report-verification-page',
  ChromedashReportVerificationPage
);
