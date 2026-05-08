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
import {customElement} from 'lit/decorators.js';
import {SHARED_STYLES} from '../css/shared-css.js';

let roadmapHelpDialogEl;

export async function openRoadmapHelpDialog() {
  if (!roadmapHelpDialogEl) {
    roadmapHelpDialogEl = document.createElement(
      'chromedash-roadmap-help-dialog'
    );
    document.body.appendChild(roadmapHelpDialogEl);
    await roadmapHelpDialogEl.updateComplete;
  }
  roadmapHelpDialogEl.show();
}

@customElement('chromedash-roadmap-help-dialog')
export class ChromedashRoadmapHelpDialog extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        #dialog-content {
          max-width: 60rem;
        }
        #legend li {
          padding: var(--content-padding-quarter);
          white-space: nowrap;
        }
        #legend span {
          display: inline-block;
          width: 8em;
        }

        #legend sl-icon {
          width: 26px;
          height: 18px;
        }
        sl-icon.not-started {
          color: var(--gate-preparing-icon-color);
        }
        sl-icon.in-progress {
          color: var(--gate-pending-icon-color);
        }
        sl-icon.needs-work {
          color: var(--gate-needs-work-icon-color);
        }
        sl-icon.approved {
          color: var(--gate-approved-icon-color);
        }
        sl-icon.denied {
          color: var(--gate-denied-icon-color);
        }
      `,
    ];
  }

  show() {
    this.renderRoot.querySelector('sl-dialog')?.show();
  }

  hide() {
    this.renderRoot.querySelector('sl-dialog')?.hide();
  }

  renderDialogContent() {
    return html`
      <div id="dialog-content">
        <ul id="legend">
          <li>
            <sl-icon
              library="material"
              class="approved"
              name="check_circle_filled_20px"
            ></sl-icon>
            <span>Approved</span>
            <span>Reviewers approved feature at this stage</span>
          </li>
          <li>
            <sl-icon
              library="material"
              class="not-started"
              name="arrow_circle_right_20px"
            ></sl-icon>
            <span>Not started</span>
            <span>Feature owners have not requested reviews yet</span>
          </li>
          <li>
            <sl-icon
              library="material"
              class="in-progress"
              name="pending_20px"
            ></sl-icon>
            <span>In-progress</span>
            <span>Not all reviews have finished</span>
          </li>
          <li>
            <sl-icon
              library="material"
              class="needs-work"
              name="autorenew_20px"
            ></sl-icon>
            <span>Needs work</span>
            <span>Reviewers have asked for changes</span>
          </li>
          <li>
            <sl-icon
              library="material"
              class="denied"
              name="block_20px"
            ></sl-icon>
            <span>Denied</span>
            <span>Reviewers suggested directional changes</span>
          </li>
        </ul>
      </div>
    `;
  }

  render() {
    return html`
      <sl-dialog label="Roadmap legend" style="--width:fit-content">
        ${this.renderDialogContent()}
      </sl-dialog>
    `;
  }
}
