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

import {html} from 'lit';
import {ChromedashAllFeaturesPage} from './chromedash-all-features-page.js';
import {customElement} from 'lit/decorators.js';

@customElement('chromedash-enterprise-page')
export class ChromedashEnterprisePage extends ChromedashAllFeaturesPage {
  renderBox(query) {
    return html`
      <chromedash-feature-table
        query=${query}
        ?signedIn=${Boolean(this.user)}
        ?canEdit=${this.user && this.user.can_edit_all}
        .starredFeatures=${this.starredFeatures}
        @star-toggle-event=${this.handleStarToggle}
        num="100"
        alwaysOfferPagination
        columns="normal"
      >
      </chromedash-feature-table>
    `;
  }

  renderEnterpriseFeatures() {
    return this.renderBox(
      'feature_type="New Feature or removal affecting enterprises" ' +
        'OR enterprise_impact>1'
    );
  }

  render() {
    return html`
      <h2>Enterprise features and breaking changes</h2>
      ${this.renderEnterpriseFeatures()}
    `;
  }
}
