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
import {customElement, property} from 'lit/decorators.js';
import {createRef, Ref, ref} from 'lit/directives/ref.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {openSearchHelpDialog} from './chromedash-search-help-dialog.js';
import {QUERIABLE_FIELDS} from './queriable-fields.js';
import {ChromedashTypeahead, Candidate} from './chromedash-typeahead.js';

function convertQueriableFieldToVocabularyItems(qf): Candidate[] {
  if (qf.choices === undefined) {
    return [{group: qf.name, name: qf.name + ':', doc: qf.doc}];
  }
  const result: Candidate[] = [];
  for (const ch in qf.choices) {
    const label: string = qf.choices[ch][1];
    result.push({
      group: qf.name,
      name: qf.name + ':"' + label + '"',
      doc: qf.doc,
    });
  }
  return result;
}

const VOCABULARY: Candidate[] = QUERIABLE_FIELDS.map(
  convertQueriableFieldToVocabularyItems
).flat();

@customElement('chromedash-feature-filter')
class ChromedashFeatureFilter extends LitElement {
  typeaheadRef = createRef<ChromedashTypeahead>();

  @property({type: String})
  query = '';

  _fireEvent(eventName, detail) {
    const event = new CustomEvent(eventName, {
      bubbles: true,
      composed: true,
      detail,
    });
    this.dispatchEvent(event);
  }

  connectedCallback(): void {
    super.connectedCallback();
    document.addEventListener('keyup', this.handleDocumentKeyUp);
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    document.removeEventListener('keyup', this.handleDocumentKeyUp);
  }

  handleDocumentKeyUp = (e: KeyboardEvent) => {
    const inInputContext = e
      .composedPath()
      .some(el =>
        ['INPUT', 'TEXTAREA', 'SL-POPUP', 'SL-DIALOG'].includes(
          (el as HTMLElement).tagName
        )
      );
    if (e.key === '/' && !inInputContext) {
      e.preventDefault();
      e.stopPropagation();
      (this.typeaheadRef?.value as ChromedashTypeahead).focus();
    }
  };

  handleSearchClick() {
    const typeahead = this.typeaheadRef.value;
    if (!typeahead) return;
    typeahead.hide();
    const newQuery = typeahead.value.trim();
    this._fireEvent('search', {query: newQuery});
  }

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        sl-icon-button {
          font-size: 1.6rem;
          margin: 0 !important;
        }
      `,
    ];
  }

  showHelp(event) {
    event.stopPropagation();
    const typeahead = this.typeaheadRef.value;
    if (!typeahead) return;
    typeahead.hide();
    openSearchHelpDialog();
  }

  render() {
    return html`
      <chromedash-typeahead
        ${ref(this.typeaheadRef)}
        value=${this.query}
        placeholder="Search"
        .vocabulary=${VOCABULARY}
        @sl-change=${this.handleSearchClick}
      >
        <sl-icon-button
          library="material"
          name="search"
          slot="prefix"
          @click="${this.handleSearchClick}"
        >
        </sl-icon-button>
        <sl-icon-button
          library="material"
          name="help_20px"
          slot="suffix"
          @click="${this.showHelp}"
        >
        </sl-icon-button>
      </chromedash-typeahead>
    `;
  }
}
