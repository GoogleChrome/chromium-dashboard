// @ts-check
import {LitElement, css, html} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';
import './chromedash-feature-row.js';

export class ChromedashReportSpecMentor extends LitElement {
  static get styles() {
    return [...SHARED_STYLES, css``];
  }

  static get properties() {
    return {
      mentor: {type: Object},
    };
  }

  constructor() {
    super();
    /** @type {import('chromestatus-openapi').SpecMentor} */
    this.mentor = this.mentor;
  }

  render() {
    return html`
      <sl-details summary="${this.mentor.email} has mentored:" open>
        <table>
          ${this.mentor.mentored_features.map(
            feature => html`
              <chromedash-feature-row
                .feature="${feature}"
              ></chromedash-feature-row>
            `
          )}
        </table>
      </sl-details>
    `;
  }
}

customElements.define(
  'chromedash-report-spec-mentor',
  ChromedashReportSpecMentor
);
