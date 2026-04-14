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
import {LitElement, html} from 'lit';
import {customElement} from 'lit/decorators.js';
import {SHARED_STYLES} from '../css/shared-css.js';

@customElement('chromedash-report-external-reviews-dispatch-page')
export class ChromedashReportExternalReviewsDispatchPage extends LitElement {
  static get styles() {
    return SHARED_STYLES;
  }

  render() {
    return html`
      <div id="subheader">Which group's reviews do you want to see?</div>
      <ul>
        <li><a href="/reports/external_reviews/tag">W3C TAG</a></li>
        <li>
          <a href="/reports/external_reviews/gecko"
            >Gecko / Firefox / Mozilla</a
          >
        </li>
        <li>
          <a href="/reports/external_reviews/webkit">WebKit / Safari / Apple</a>
        </li>
      </ul>
    `;
  }
}
