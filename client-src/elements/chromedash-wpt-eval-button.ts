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

import {LitElement, html, css} from 'lit';
import {customElement, property} from 'lit/decorators.js';
import '@shoelace-style/shoelace/dist/components/button/button.js';

@customElement('chromedash-wpt-eval-button')
export class ChromedashWPTEvalButton extends LitElement {
  @property({type: Number})
  featureId = 0;

  static styles = css`
    :host {
      display: inline-block;
    }

    .gemini-icon {
      width: 1.5em;
      height: 1.5em;
      transform-origin: center center;
      transition: transform 0.7s ease-in-out;
    }

    sl-button:hover .gemini-icon {
      transform: rotate(360deg);
    }
  `;

  render() {
    return html`
      <sl-button href="/feature/${this.featureId}/ai-coverage-analysis">
        <img
          slot="prefix"
          class="gemini-icon"
          src="https://www.gstatic.com/images/branding/productlogos/gemini_2025/v1/192px.svg"
          alt="Gemini AI Logo"
        />
        Analyze test coverage
      </sl-button>
    `;
  }
}
