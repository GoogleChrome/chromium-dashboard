/**
 * Copyright 2026 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

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
