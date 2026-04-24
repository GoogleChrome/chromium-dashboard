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
import {ref, createRef} from 'lit/directives/ref.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {customElement, property} from 'lit/decorators.js';
import {GateDict} from './chromedash-gate-chip.js';
import {SlDialog, SlTextarea} from '@shoelace-style/shoelace';

let naRationalDialogEl;

export async function openNaRationaleDialog(gate: GateDict) {
  if (!naRationalDialogEl) {
    naRationalDialogEl = document.createElement(
      'chromedash-na-rationale-dialog'
    );
    document.body.appendChild(naRationalDialogEl);
    await naRationalDialogEl.updateComplete;
  }
  return new Promise(resolve => {
    naRationalDialogEl.openOn(gate, resolve);
  });
}

@customElement('chromedash-na-rationale-dialog')
export class ChromedashNaRationaleDialog extends LitElement {
  rationaleDialogRef = createRef<SlDialog>();
  rationaleRef = createRef<SlTextarea>();

  static get styles() {
    return [...SHARED_STYLES, css``];
  }

  @property({type: Object, attribute: false})
  gate?: GateDict = undefined;
  @property({attribute: false})
  resolve: (value?: string) => void = () => {
    console.log('Missing resolve action');
  };

  openOn(gate, resolve) {
    this.gate = gate;
    this.resolve = resolve;
    this.rationaleDialogRef.value?.show();
  }

  handlePost() {
    this.resolve(this.rationaleRef.value?.value);
    this.rationaleDialogRef.value?.hide();
  }

  renderDialogContent() {
    if (this.gate === undefined) {
      return nothing;
    }
    return html`
      <p style="padding: var(--content-padding)">
        Please briefly explain why your feature does not require a review. Your
        response will be posted as a comment on this review gate and it will
        generate a notification to the reviewers. The ${this.gate.team_name}
        reviewers will still evaluate whether to give an "N/A" response or do a
        review.
      </p>
      <sl-textarea ${ref(this.rationaleRef)}></sl-textarea>
      <sl-button
        slot="footer"
        variant="primary"
        size="small"
        @click=${this.handlePost}
        >Post</sl-button
      >
    `;
  }

  render() {
    return html`
      <sl-dialog ${ref(this.rationaleDialogRef)} label="Request an N/A">
        ${this.renderDialogContent()}
      </sl-dialog>
    `;
  }
}
