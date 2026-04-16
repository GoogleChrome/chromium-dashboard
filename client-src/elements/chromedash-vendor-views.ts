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
import {customElement, property} from 'lit/decorators.js';
import {FeatureLink} from '../js-src/cs-client.js';

/**
 * Use like `<chromedash-vendor-views href="https://evidence/for/the/view"
 * .featureLinks=${this.featureLinks}>Text description of the view</chromedash-vendor-views>`
 */
@customElement('chromedash-vendor-views')
export class ChromedashVendorViews extends LitElement {
  /** URL of the evidence for this view.*/
  @property({type: String})
  href;
  @property({attribute: false})
  featureLinks: FeatureLink[] = [];

  urlIsStandardsPosition(url: string): boolean {
    return /github.com\/(mozilla|WebKit)\/standards-positions\/issues/.test(
      url
    );
  }

  render() {
    if (this.href) {
      return html`<chromedash-link
        href=${this.href}
        ?showContentAsLabel=${!this.urlIsStandardsPosition(this.href)}
        .featureLinks=${this.featureLinks}
        ><slot></slot
      ></chromedash-link>`;
    } else {
      return html`<slot></slot>`;
    }
  }
}
