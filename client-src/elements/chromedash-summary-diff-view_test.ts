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

import {html, fixture, expect} from '@open-wc/testing';
import './chromedash-summary-diff-view.js';
import {ChromedashSummaryDiffView} from './chromedash-summary-diff-view.js';

describe('chromedash-summary-diff-view', () => {
  it('renders side-by-side comparison with current and suggested summary', async () => {
    const el = await fixture<ChromedashSummaryDiffView>(
      html`<chromedash-summary-diff-view
        .currentSummary=${'Manual author summary'}
        .suggestedSummary=${'AI generated summary for feature **101**.'}
        .suggestedDocLinks=${[
          'https://developer.mozilla.org/en-US/docs/Web/API/Test',
        ]}
      ></chromedash-summary-diff-view>`
    );

    const columns = el.shadowRoot!.querySelectorAll('.column-card');
    expect(columns.length).to.equal(2);

    expect(columns[0].getAttribute('role')).to.equal('region');
    expect(columns[0].getAttribute('aria-labelledby')).to.equal(
      'current-summary-header'
    );
    expect(columns[0].textContent).to.contain('Current Feature Summary');
    expect(columns[0].textContent).to.contain('Manual author summary');

    expect(columns[1].getAttribute('role')).to.equal('region');
    expect(columns[1].getAttribute('aria-labelledby')).to.equal(
      'suggested-summary-header'
    );
    expect(columns[1].textContent).to.contain('AI Suggested Summary');
    expect(columns[1].textContent).to.contain(
      'AI generated summary for feature 101.'
    );

    const badges = el.shadowRoot!.querySelectorAll('.sources-list sl-badge');
    expect(badges.length).to.equal(1);
    expect(badges[0].textContent).to.contain('developer.mozilla.org');
  });

  it('handles empty current summary gracefully', async () => {
    const el = await fixture<ChromedashSummaryDiffView>(
      html`<chromedash-summary-diff-view
        .currentSummary=${''}
        .suggestedSummary=${'AI summary'}
      ></chromedash-summary-diff-view>`
    );

    const leftContent = el.shadowRoot!.querySelector(
      '.column-card:first-child .column-content'
    );
    expect(leftContent!.textContent).to.contain('(No existing summary)');
  });

  it('toggles edit mode, emits summary-edit-toggle event, and focuses textarea', async () => {
    const el = await fixture<ChromedashSummaryDiffView>(
      html`<chromedash-summary-diff-view
        .currentSummary=${'Old summary'}
        .suggestedSummary=${'AI suggested summary'}
      ></chromedash-summary-diff-view>`
    );

    let toggleFired = false;
    el.addEventListener('summary-edit-toggle', ((
      e: CustomEvent<{isEditing: boolean; value: string}>
    ) => {
      toggleFired = true;
      expect(e.detail.isEditing).to.be.true;
    }) as EventListener);

    const editBtn = el.shadowRoot!.querySelector(
      '.column-header sl-button'
    ) as HTMLElement;
    expect(editBtn.textContent).to.contain('Edit');

    await el.toggleEdit();
    await el.updateComplete;

    expect(toggleFired).to.be.true;
    expect(editBtn.textContent).to.contain('Preview');
    const textarea = el.shadowRoot!.querySelector('sl-textarea');
    expect(textarea).to.exist;
    expect(textarea!.value).to.equal('AI suggested summary');
    expect(el.textareaEl).to.equal(textarea);
  });

  it('dispatches summary-value-change when textarea input changes', async () => {
    const el = await fixture<ChromedashSummaryDiffView>(
      html`<chromedash-summary-diff-view
        .isEditing=${true}
        .suggestedSummary=${'Initial summary'}
      ></chromedash-summary-diff-view>`
    );

    let changedValue = '';
    el.addEventListener('summary-value-change', ((
      e: CustomEvent<{value: string}>
    ) => {
      changedValue = e.detail.value;
    }) as EventListener);

    const textarea = el.shadowRoot!.querySelector('sl-textarea');
    expect(textarea).to.exist;

    textarea!.value = 'Updated custom summary text';
    textarea!.dispatchEvent(new Event('input'));
    await el.updateComplete;

    expect(changedValue).to.equal('Updated custom summary text');
    expect(el.editBuffer).to.equal('Updated custom summary text');
  });

  it('preserves active in-progress editBuffer when suggestedSummary updates during edit mode', async () => {
    const el = await fixture<ChromedashSummaryDiffView>(
      html`<chromedash-summary-diff-view
        .isEditing=${true}
        .suggestedSummary=${'Initial summary'}
      ></chromedash-summary-diff-view>`
    );

    el.editBuffer = 'User active in-progress edits';
    el.suggestedSummary = 'New background summary from server';
    await el.updateComplete;

    expect(el.editBuffer).to.equal('User active in-progress edits');
  });

  it('sanitizes malicious markup in markdown summaries to prevent XSS', async () => {
    const maliciousSummary =
      'Feature description <script>alert("xss")</script><img src="x" onerror="alert(1)"> with [malicious link](javascript:alert(1))';
    const el = await fixture<ChromedashSummaryDiffView>(
      html`<chromedash-summary-diff-view
        .currentSummary=${maliciousSummary}
        .suggestedSummary=${maliciousSummary}
      ></chromedash-summary-diff-view>`
    );

    const contentHtml = el.shadowRoot!.innerHTML;
    expect(contentHtml).to.not.contain('<script>');
    expect(contentHtml).to.not.contain('onerror');
    expect(contentHtml).to.not.contain('href="javascript:');
  });
});
