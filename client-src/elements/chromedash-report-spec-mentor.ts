// @ts-check
import {SpecMentor} from 'chromestatus-openapi';
import {LitElement, css, html} from 'lit';
import {customElement, property} from 'lit/decorators.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import './chromedash-feature-row.js';

@customElement('chromedash-report-spec-mentor')
export class ChromedashReportSpecMentor extends LitElement {
  static get styles() {
    return [...SHARED_STYLES, css``];
  }

  @property({attribute: false})
  mentor!: SpecMentor;

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
