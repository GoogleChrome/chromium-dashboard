// @ts-check
import {Task} from '@lit/task';
import '@shoelace-style/shoelace';
import {LitElement, css, html} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';
import './chromedash-report-spec-mentor.js';
import {isoDateString} from './utils.js';

export class ChromedashReportSpecMentorsPage extends LitElement {
  static get styles() {
    return [...SHARED_STYLES, css``];
  }

  static get properties() {
    return {
      rawQuery: {type: Object},
      _updatedAfter: {state: true},
    };
  }

  /** @type {Record<string, string>} */
  rawQuery = {};

  /** @type {import('chromestatus-openapi').DefaultApiInterface} */
  _client;

  constructor() {
    super();
    // Default to a year ago.
    this._updatedAfter = new Date(Date.now() - 365 * 24 * 60 * 60 * 1000);
    // @ts-ignore
    this._client = window.csOpenApiClient;
    this._mentorsTask = new Task(this, {
      task: async ([updatedAfter], {signal}) => {
        const mentors = await this._client.listSpecMentors(
          {after: updatedAfter},
          {signal}
        );
        mentors.sort((a, b) => a.email.localeCompare(b.email));
        return mentors;
      },
      args: () => [this._updatedAfter],
    });
  }

  connectedCallback() {
    super.connectedCallback();
    this.initializeParams();
  }

  initializeParams() {
    if (!this.rawQuery) {
      return;
    }

    if (this.rawQuery.hasOwnProperty('after')) {
      const parsed = Date.parse(this.rawQuery['after']);
      if (!isNaN(parsed)) {
        this._updatedAfter = new Date(parsed);
      }
    }
  }

  /**
   * @param {import('@shoelace-style/shoelace').SlChangeEvent & {target: import('@shoelace-style/shoelace').SlInput}} e
   * @return {void}
   */
  afterChanged(e) {
    e.stopPropagation();
    const newDate = e.target.valueAsDate;
    if (newDate) {
      this._updatedAfter = newDate;
      this.dispatchEvent(
        new CustomEvent('afterchanged', {
          detail: {after: this._updatedAfter},
          bubbles: true,
          composed: true,
        })
      );
    }
  }

  render() {
    return html`
      <div id="subheader">
        <sl-input
          type="date"
          name="after"
          value=${isoDateString(this._updatedAfter)}
          label="List spec mentors who've worked on features that were updated after this date"
          @sl-change=${this.afterChanged}
        ></sl-input>
      </div>
      ${this._mentorsTask.render({
        pending: () =>
          html` <details open>
            <summary><sl-skeleton effect="sheen"></sl-skeleton></summary>
            <sl-skeleton effect="sheen"></sl-skeleton>
          </details>`,
        complete: specMentors =>
          specMentors.map(
            mentor =>
              html`<chromedash-report-spec-mentor
                .mentor=${mentor}
              ></chromedash-report-spec-mentor>`
          ),
        error: e => {
          console.error(e);
          return html`<p>
            Some errors occurred. Please refresh the page or try again later.
          </p>`;
        },
      })}
    `;
  }
}

customElements.define(
  'chromedash-report-spec-mentors-page',
  ChromedashReportSpecMentorsPage
);
