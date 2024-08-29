/**
 * Copyright 2024 Google LLC
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

import {LitElement, type TemplateResult, CSSResultGroup, css, html} from 'lit';
import {customElement, property} from 'lit/decorators.js';
import {formatURLParams} from './utils.js';
import {ifDefined} from 'lit/directives/if-defined.js';
import {range} from 'lit/directives/range.js';
import {map} from 'lit/directives/map.js';
import {SHARED_STYLES} from '../css/shared-css.js';

@customElement('chromedash-feature-pagination')
export class ChromedashFeaturePagination extends LitElement {
  @property({type: Number})
  totalCount = 0; // The total number of items

  @property({type: Number})
  start = 0; // Index of first result among total results.

  @property({type: Number})
  pageSize = 100; // Number of items to display per page

  static get styles(): CSSResultGroup {
    return [
      SHARED_STYLES,
      css`
        .active {
          background: var(--light-grey);
        }
        .stepper {
          width: 7em;
        }
        .pagination {
          padding: var(--content-padding-half) 0;
          min-height: 50px;
        }
        .pagination span {
          color: var(--unimportant-text-color);
          margin-right: var(--content-padding);
        }
        sl-button::part(base):hover {
          background: var(--sl-color-blue-100);
        }
        .pagination sl-icon-button {
          font-size: 1.6rem;
        }
        .pagination sl-icon-button::part(base) {
          padding: 0;
        }
      `,
    ];
  }

  formatUrlForRelativeOffset(delta: number): string | undefined {
    const offset = this.start + delta;
    if (
      this.totalCount === undefined ||
      offset <= -this.pageSize ||
      offset >= this.totalCount
    ) {
      return undefined;
    }
    return this.formatUrlForOffset(Math.max(0, offset));
  }

  formatUrlForOffset(offset: number): string {
    return formatURLParams('start', offset).toString();
  }

  renderPageButtons(): TemplateResult {
    if (this.totalCount === undefined || this.totalCount === 0) {
      return html``;
    }
    const currentPage = Math.floor(this.start / this.pageSize);
    const numPages = Math.ceil(this.totalCount / this.pageSize);

    return html`
      ${map(
        range(numPages),
        i => html`
          <sl-button
            variant="text"
            id="jump_${i + 1}"
            class="page-button ${i === currentPage ? 'active' : ''}"
            href=${this.formatUrlForOffset(i * this.pageSize)}
          >
            ${i + 1}
          </sl-button>
        `
      )}
    `;
  }

  render(): TemplateResult {
    if (this.totalCount === undefined || this.totalCount === 0) {
      return html``;
    }

    const prevUrl = this.formatUrlForRelativeOffset(-this.pageSize);
    const nextUrl = this.formatUrlForRelativeOffset(this.pageSize);

    return html`
      <div id="main" class="pagination hbox halign-items-space-between">
        <div class="spacer"></div>
        <sl-button
          variant="text"
          id="previous"
          class="stepper"
          href=${ifDefined(prevUrl)}
          ?disabled=${prevUrl === undefined}
          >Previous</sl-button
        >

        ${this.renderPageButtons()}

        <sl-button
          variant="text"
          id="next"
          class="stepper"
          href=${ifDefined(nextUrl)}
          ?disabled=${nextUrl === undefined}
          >Next</sl-button
        >

        <div class="spacer"></div>
      </div>
    `;
  }
}
