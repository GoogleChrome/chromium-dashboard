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

import {
  LitElement,
  type TemplateResult,
  CSSResultGroup,
  css,
  html,
  nothing,
} from 'lit';
import {customElement, property} from 'lit/decorators.js';
import {
  formatURLParams,
  formatUrlForRelativeOffset,
  formatUrlForOffset,
} from './utils.js';
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
        cw-button::part(base):hover {
          background: var(--cw-color-blue-100);
        }
        .pagination cw-icon-button {
          font-size: 1.6rem;
        }
        .pagination cw-icon-button::part(base) {
          padding: 0;
        }
        #items-per-page {
          align-self: center;
          color: var(--unimportant-text-color);
          font-size: var(--cw-input-font-size-small);
        }
        cw-select {
          align-self: center;
          display: inline-block;
          margin: 0 var(--content-padding-quarter) 0 var(--content-padding);
          width: 7em;
        }
      `,
    ];
  }

  renderPageButtons(): TemplateResult {
    if (this.totalCount === undefined || this.totalCount === 0) {
      return html``;
    }
    const currentPage = Math.floor(this.start / this.pageSize);
    const numPages = Math.ceil(this.totalCount / this.pageSize);

    let missingFront = false;
    let missingBack = false;
    let hasLastPage = numPages > 1;

    let displayPages: Array<number> = [];
    const displaySet = new Set<number>();
    for (const digit of range(numPages)) {
      if (digit === 0 || digit === numPages - 1) {
        continue;
      }
      if (numPages <= 10) {
        displaySet.add(digit);
        continue;
      }
      if (digit < currentPage - 4) {
        missingFront = true;
        continue;
      }
      if (digit > currentPage + 4) {
        missingBack = true;
        continue;
      }
      displaySet.add(digit);
    }
    displayPages = Array.from(displaySet);

    return html`
      <cw-button
        variant="text"
        id="jump_1"
        class="page-button ${0 === currentPage ? 'active' : ''}"
        href=${formatUrlForOffset(0)}
      >
        ${1}
      </cw-button>
      ${missingFront ? html`<div>...</div>` : nothing}
      ${map(
        displayPages,
        i => html`
          <cw-button
            variant="text"
            id="jump_${i + 1}"
            class="page-button ${i === currentPage ? 'active' : ''}"
            href=${formatUrlForOffset(i * this.pageSize)}
          >
            ${i + 1}
          </cw-button>
        `
      )}
      ${missingBack ? html`<div>...</div>` : nothing}
      ${
        hasLastPage
          ? html`<cw-button
              variant="text"
              id="jump_${numPages}"
              class="page-button ${numPages - 1 === currentPage ? 'active' : ''}"
              href=${formatUrlForOffset((numPages - 1) * this.pageSize)}
            >
              ${numPages}
            </cw-button>`
          : nothing
      }
    `;
  }

  setItemsPerPage(event: Event): void {
    const target = event.target as HTMLInputElement;
    const newSize = parseInt(target.value);
    const newURL = formatURLParams('num', newSize).toString();
    window.location.href = newURL;
  }

  renderItemsPerPage(): TemplateResult {
    const options = [25, 50, 100];
    if (!options.includes(this.pageSize)) {
      options.push(this.pageSize);
      options.sort((a, b) => a - b);
    }
    return html`
      <cw-select
        value="${this.pageSize}"
        size="small"
        @cw-change=${this.setItemsPerPage}
      >
        ${options.map(
          opt => html`
            <cw-option id="opt_${opt}" value=${opt}>${opt}</cw-option>
          `
        )}
      </cw-select>
      <span id="items-per-page"> items per page </span>
    `;
  }

  render(): TemplateResult {
    if (this.totalCount === undefined || this.totalCount === 0) {
      return html``;
    }

    const prevUrl = formatUrlForRelativeOffset(
      this.start,
      -this.pageSize,
      this.pageSize,
      this.totalCount
    );
    const nextUrl = formatUrlForRelativeOffset(
      this.start,
      this.pageSize,
      this.pageSize,
      this.totalCount
    );

    return html`
      <div id="main" class="pagination hbox halign-items-space-between">
        <div class="spacer"></div>
        <cw-button
          variant="text"
          id="previous"
          class="stepper"
          href=${ifDefined(prevUrl)}
          ?disabled=${prevUrl === undefined}
          >Previous</cw-button
        >

        ${this.renderPageButtons()}

        <cw-button
          variant="text"
          id="next"
          class="stepper"
          href=${ifDefined(nextUrl)}
          ?disabled=${nextUrl === undefined}
          >Next</cw-button
        >

        ${this.renderItemsPerPage()}

        <div class="spacer"></div>
      </div>
    `;
  }
}
