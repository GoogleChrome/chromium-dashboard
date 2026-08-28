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

import {html, fixture, assert} from '@open-wc/testing';
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
    assert.equal(columns.length, 2);

    assert.equal(columns[0].getAttribute('role'), 'region');
    assert.equal(
      columns[0].getAttribute('aria-labelledby'),
      'current-summary-header'
    );
    assert.include(columns[0].textContent, 'Current Feature Summary');
    assert.include(columns[0].textContent, 'Manual author summary');

    assert.equal(columns[1].getAttribute('role'), 'region');
    assert.equal(
      columns[1].getAttribute('aria-labelledby'),
      'suggested-summary-header'
    );
    assert.include(columns[1].textContent, 'AI Suggested Summary');
    assert.include(
      columns[1].textContent,
      'AI generated summary for feature 101.'
    );

    const badges = el.shadowRoot!.querySelectorAll('.sources-list sl-badge');
    assert.equal(badges.length, 1);
    assert.include(badges[0].textContent, 'developer.mozilla.org');
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
    assert.include(leftContent!.textContent, '(No existing summary)');
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
      assert.isTrue(e.detail.isEditing);
    }) as EventListener);

    const editBtn = el.shadowRoot!.querySelector(
      '.column-header sl-button'
    ) as HTMLElement;
    assert.include(editBtn.textContent, 'Edit');

    await el.toggleEdit();
    await el.updateComplete;

    assert.isTrue(toggleFired);
    assert.include(editBtn.textContent, 'Preview');
    const textarea = el.shadowRoot!.querySelector('sl-textarea');
    assert.exists(textarea);
    assert.equal(textarea!.value, 'AI suggested summary');
    assert.equal(el.textareaEl, textarea);
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
    assert.exists(textarea);

    textarea!.value = 'Updated custom summary text';
    textarea!.dispatchEvent(new Event('input'));
    await el.updateComplete;

    assert.equal(changedValue, 'Updated custom summary text');
    assert.equal(el.editBuffer, 'Updated custom summary text');
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

    assert.equal(el.editBuffer, 'User active in-progress edits');
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
    assert.notInclude(contentHtml, '<script>');
    assert.notInclude(contentHtml, 'onerror');
    assert.notInclude(contentHtml, 'href="javascript:');
  });

  it('renders grounding reasoning callout when reasoning is provided', async () => {
    const el = await fixture<ChromedashSummaryDiffView>(
      html`<chromedash-summary-diff-view
        .currentSummary=${'Current summary'}
        .suggestedSummary=${'Suggested summary'}
        .reasoning=${'Summary streamlined to highlight CSS Grid masonry placement algorithm.'}
      ></chromedash-summary-diff-view>`
    );

    const reasoningSection = el.shadowRoot!.querySelector(
      '[data-testid="diff-reasoning-section"]'
    );
    assert.isNotNull(reasoningSection);
    assert.include(
      reasoningSection!.textContent,
      'Summary streamlined to highlight CSS Grid masonry placement algorithm.'
    );
    assert.include(reasoningSection!.textContent, 'Grounding Rationale');
  });

  it('renders baseline status badge when baselineStatus is non-empty and not none', async () => {
    const el = await fixture<ChromedashSummaryDiffView>(
      html`<chromedash-summary-diff-view
        .currentSummary=${'Current summary'}
        .suggestedSummary=${'Suggested summary'}
        .baselineStatus=${'newly'}
      ></chromedash-summary-diff-view>`
    );

    const badge = el.shadowRoot!.querySelector(
      '#suggested-summary-header sl-badge'
    );
    assert.isNotNull(badge);
    assert.include(badge!.textContent, 'Baseline: Newly available');
  });
});
