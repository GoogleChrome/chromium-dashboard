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

import {LitElement, css, html, nothing} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';
import {customElement, property} from 'lit/decorators.js';

@customElement('chromedash-banner')
class ChromedashBanner extends LitElement {
  @property({type: Number})
  timestamp: null | number = null; // Unix timestamp: seconds since 1970-01-01.
  @property({type: String})
  message: string = '';

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        div {
          display: inline-block;
          background: var(--warning-background);
          color: var(--warning-color);
          border-radius: var(--border-radius);
          padding: var(--content-padding);
          width: 100%;
        }
      `,
    ];
  }

  computeLocalDateString() {
    if (!this.timestamp) {
      return nothing;
    }
    const date = new Date(this.timestamp * 1000);
    const formatOptions: Intl.DateTimeFormatOptions = {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: 'numeric',
      minute: 'numeric',
    }; // No seconds
    return date.toLocaleString(undefined, formatOptions);
  }

  render() {
    if (!this.message) {
      return nothing;
    }

    return html` <div>${this.message} ${this.computeLocalDateString()}</div> `;
  }
}
