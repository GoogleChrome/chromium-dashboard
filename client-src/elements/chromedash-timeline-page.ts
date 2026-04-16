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

import {LitElement, css, html} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';
import './chromedash-timeline.js';
import {showToastMessage, METRICS_TYPE_AND_VIEW_TO_SUBTITLE} from './utils.js';
import {property} from 'lit/decorators.js';
import {Property} from './chromedash-timeline.js';

export class ChromedashTimelinePage extends LitElement {
  @property({type: String})
  type = '';

  @property({type: String})
  view = '';

  @property({attribute: false})
  props: Property[] = [];

  @property({attribute: false})
  selectedBucketId = '1';

  static get styles() {
    return [...SHARED_STYLES, css``];
  }

  connectedCallback() {
    super.connectedCallback();

    let endpoint = `/data/blink/${this.type}props`;

    // [DEV] Change to true to use the staging server endpoint for development
    const devMode = false;
    if (devMode) endpoint = 'https://cr-status-staging.appspot.com' + endpoint;
    const options: RequestInit = {credentials: 'omit'};

    fetch(endpoint, options)
      .then(res => res.json())
      .then(props => {
        this.props = props;
      })
      .catch(() => {
        showToastMessage(
          'Some errors occurred. Please refresh the page or try again later.'
        );
      });
  }

  renderSubheader() {
    const subTitleText =
      METRICS_TYPE_AND_VIEW_TO_SUBTITLE[this.type + this.view];
    return html`
      <div id="subheader">
        <h2 id="breadcrumbs">
          <a href="/metrics/${this.type}/${this.view}">
            <sl-icon name="arrow-left"></sl-icon> </a
          >${subTitleText} > timeline
        </h2>
      </div>
    `;
  }

  renderDataPanel() {
    return html`
      <chromedash-timeline
        .type=${this.type}
        .view=${this.view}
        .props=${this.props}
        .selectedBucketId=${this.selectedBucketId}
      >
      </chromedash-timeline>
    `;
  }

  render() {
    return html` ${this.renderSubheader()} ${this.renderDataPanel()} `;
  }
}

customElements.define('chromedash-timeline-page', ChromedashTimelinePage);
