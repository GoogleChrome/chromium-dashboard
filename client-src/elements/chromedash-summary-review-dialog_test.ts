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
import sinon from 'sinon';
import './chromedash-summary-review-dialog.js';
import {ChromedashSummaryReviewDialog} from './chromedash-summary-review-dialog.js';
import {
  ChromeStatusClient,
  ChromeStatusHttpError,
} from '../js-src/cs-client.js';
import {
  SummarySuggestion,
  SummarySuggestionStatusEnum,
} from 'chromestatus-openapi';

describe('chromedash-summary-review-dialog', () => {
  let sandbox: sinon.SinonSandbox;

  const mockSuggestion: SummarySuggestion = {
    feature_id: 101,
    status: SummarySuggestionStatusEnum.PENDING,
    suggested_summary: 'AI generated summary for feature **101**.',
    suggested_doc_links: [
      'https://developer.mozilla.org/en-US/docs/Web/API/Test',
    ],
    version_token: 42,
    created: new Date(),
    updated: new Date(),
  };

  beforeEach(() => {
    sandbox = sinon.createSandbox();
    window.csClient = {
      getSummarySuggestion: sandbox.stub().resolves({
        suggestion: mockSuggestion,
        progress_steps: [],
      }),
      updateSummarySuggestion: sandbox.stub().resolves({
        suggestion: {
          ...mockSuggestion,
          status: SummarySuggestionStatusEnum.APPLIED,
          version_token: 43,
        },
        progress_steps: [],
      }),
      triggerSummaryGeneration: sandbox.stub().resolves({
        message: 'Task enqueued',
      }),
    } as Partial<ChromeStatusClient> as ChromeStatusClient;
  });

  afterEach(() => {
    sandbox.restore();
  });

  it('renders dialog and diff view child component', async () => {
    const el = await fixture<ChromedashSummaryReviewDialog>(
      html`<chromedash-summary-review-dialog
        .featureId=${101}
        .currentSummary=${'Manual author summary'}
        .suggestion=${mockSuggestion}
      ></chromedash-summary-review-dialog>`
    );

    const diffView = el.shadowRoot!.querySelector(
      'chromedash-summary-diff-view'
    );
    assert.exists(diffView);
    assert.equal(el.editedSummary, mockSuggestion.suggested_summary);
  });

  it('calls updateSummarySuggestion with APPLIED and dispatches event on Accept', async () => {
    let appliedFired = false;
    const onApplied = (
      e: CustomEvent<{featureId: number; summary: string}>
    ) => {
      appliedFired = true;
      assert.equal(e.detail.featureId, 101);
      assert.equal(
        e.detail.summary,
        'AI generated summary for feature **101**.'
      );
    };

    const el = await fixture<ChromedashSummaryReviewDialog>(
      html`<chromedash-summary-review-dialog
        .featureId=${101}
        .currentSummary=${'Old summary'}
        .suggestion=${mockSuggestion}
        @summary-suggestion-applied=${onApplied}
      ></chromedash-summary-review-dialog>`
    );

    const hideSpy = sandbox.spy(el, 'hide');
    await el.handleAccept();
    await el.updateComplete;

    assert.isTrue(
      (
        window.csClient.updateSummarySuggestion as sinon.SinonStub
      ).calledOnceWith(101, {
        status: SummarySuggestionStatusEnum.APPLIED,
        suggested_summary: 'AI generated summary for feature **101**.',
        version_token: 42,
      })
    );

    assert.isTrue(appliedFired);
    assert.isTrue(hideSpy.calledOnce);
  });

  it('calls updateSummarySuggestion with REJECTED and dispatches event on Discard', async () => {
    let rejectedFired = false;
    const onRejected = (e: CustomEvent<{featureId: number}>) => {
      rejectedFired = true;
      assert.equal(e.detail.featureId, 101);
    };

    const el = await fixture<ChromedashSummaryReviewDialog>(
      html`<chromedash-summary-review-dialog
        .featureId=${101}
        .currentSummary=${'Old summary'}
        .suggestion=${mockSuggestion}
        @summary-suggestion-rejected=${onRejected}
      ></chromedash-summary-review-dialog>`
    );

    const hideSpy = sandbox.spy(el, 'hide');
    await el.handleReject();
    await el.updateComplete;

    assert.isTrue(
      (
        window.csClient.updateSummarySuggestion as sinon.SinonStub
      ).calledOnceWith(101, {
        status: SummarySuggestionStatusEnum.REJECTED,
        version_token: 42,
      })
    );

    assert.isTrue(rejectedFired);
    assert.isTrue(hideSpy.calledOnce);
  });

  it('calls triggerSummaryGeneration and dispatches event on Regenerate', async () => {
    let regenFired = false;
    const onRegen = (e: CustomEvent<{featureId: number; force: boolean}>) => {
      regenFired = true;
      assert.equal(e.detail.featureId, 101);
      assert.isTrue(e.detail.force);
    };

    const el = await fixture<ChromedashSummaryReviewDialog>(
      html`<chromedash-summary-review-dialog
        .featureId=${101}
        .currentSummary=${'Old summary'}
        .suggestion=${mockSuggestion}
        @summary-generation-requested=${onRegen}
      ></chromedash-summary-review-dialog>`
    );

    const hideSpy = sandbox.spy(el, 'hide');
    await el.handleRegenerate();
    await el.updateComplete;

    assert.isTrue(
      (
        window.csClient.triggerSummaryGeneration as sinon.SinonStub
      ).calledOnceWith(101, true)
    );

    assert.isTrue(regenFired);
    assert.isTrue(hideSpy.calledOnce);
  });

  it('handles OCC 409 conflict and refreshes latest data', async () => {
    (window.csClient.updateSummarySuggestion as sinon.SinonStub).rejects(
      new ChromeStatusHttpError('Conflict', '/test', 'PATCH', 409)
    );

    const el = await fixture<ChromedashSummaryReviewDialog>(
      html`<chromedash-summary-review-dialog
        .featureId=${101}
        .currentSummary=${'Old summary'}
        .suggestion=${mockSuggestion}
      ></chromedash-summary-review-dialog>`
    );

    await el.handleAccept();
    await el.updateComplete;

    assert.isTrue(el.occConflict);
    const warningAlert = el.shadowRoot!.querySelector(
      'sl-alert[variant="warning"]'
    );
    assert.exists(warningAlert);
    assert.include(
      warningAlert!.textContent || '',
      'modified in another session'
    );

    // Accept button should be disabled during OCC conflict
    const acceptBtn = el.shadowRoot!.querySelector(
      'sl-button[variant="primary"]'
    ) as HTMLElement;
    assert.isTrue(acceptBtn.hasAttribute('disabled'));

    // Refresh updated version
    const updatedSuggestion: SummarySuggestion = {
      ...mockSuggestion,
      suggested_summary: 'Newer remote summary from token 43',
      version_token: 43,
    };
    (window.csClient.getSummarySuggestion as sinon.SinonStub).resolves({
      suggestion: updatedSuggestion,
      progress_steps: [],
    });

    await el.handleRefresh();
    await el.updateComplete;

    assert.isFalse(el.occConflict);
    assert.equal(el.suggestion?.version_token, 43);
    assert.equal(el.editedSummary, 'Newer remote summary from token 43');
  });

  it('renders danger alert on general API error', async () => {
    (window.csClient.updateSummarySuggestion as sinon.SinonStub).rejects(
      new Error('Permission denied')
    );

    const el = await fixture<ChromedashSummaryReviewDialog>(
      html`<chromedash-summary-review-dialog
        .featureId=${101}
        .currentSummary=${'Old summary'}
        .suggestion=${mockSuggestion}
      ></chromedash-summary-review-dialog>`
    );

    await el.handleAccept();
    await el.updateComplete;

    assert.isFalse(el.occConflict);
    const dangerAlert = el.shadowRoot!.querySelector(
      'sl-alert[variant="danger"]'
    );
    assert.exists(dangerAlert);
    assert.include(dangerAlert!.textContent || '', 'Permission denied');
  });

  it('preserves uncommitted edits and shows notification when suggestion changes while editing', async () => {
    const el = await fixture<ChromedashSummaryReviewDialog>(
      html`<chromedash-summary-review-dialog
        .featureId=${101}
        .currentSummary=${'Old summary'}
        .suggestion=${mockSuggestion}
      ></chromedash-summary-review-dialog>`
    );

    el.isEditing = true;
    el.editedSummary = 'My customized draft that should not be lost.';
    await el.updateComplete;

    const newerSuggestion: SummarySuggestion = {
      ...mockSuggestion,
      suggested_summary: 'New incoming summary from server.',
      version_token: 45,
    };
    el.suggestion = newerSuggestion;
    await el.updateComplete;

    assert.equal(
      el.editedSummary,
      'My customized draft that should not be lost.'
    );
    assert.isTrue(el.newerSuggestionAvailable);

    const alert = el.shadowRoot!.querySelector('sl-alert[variant="primary"]');
    assert.exists(alert);
    assert.include(
      alert!.textContent || '',
      'A newer suggestion is available on the server.'
    );
  });

  it('allows user to load newest suggestion or keep edits', async () => {
    const el = await fixture<ChromedashSummaryReviewDialog>(
      html`<chromedash-summary-review-dialog
        .featureId=${101}
        .currentSummary=${'Old summary'}
        .suggestion=${mockSuggestion}
      ></chromedash-summary-review-dialog>`
    );

    el.isEditing = true;
    el.editedSummary = 'My custom edit.';
    await el.updateComplete;

    const newerSuggestion: SummarySuggestion = {
      ...mockSuggestion,
      suggested_summary: 'New remote summary.',
      version_token: 45,
    };
    el.suggestion = newerSuggestion;
    await el.updateComplete;

    assert.isTrue(el.newerSuggestionAvailable);

    // Test dismiss
    el.handleDismissNewerSuggestion();
    await el.updateComplete;
    assert.isFalse(el.newerSuggestionAvailable);
    assert.equal(el.editedSummary, 'My custom edit.');

    // Test load newest
    el.newerSuggestionAvailable = true;
    el.handleLoadNewestSuggestion();
    await el.updateComplete;
    assert.isFalse(el.newerSuggestionAvailable);
    assert.equal(el.editedSummary, 'New remote summary.');
    assert.isFalse(el.isEditing);
  });

  it('disables buttons when suggestion is null or missing version_token', async () => {
    const el = await fixture<ChromedashSummaryReviewDialog>(
      html`<chromedash-summary-review-dialog
        .featureId=${101}
        .currentSummary=${'Old summary'}
        .suggestion=${null}
      ></chromedash-summary-review-dialog>`
    );

    const acceptBtn = el.shadowRoot!.querySelector(
      'sl-button[variant="primary"]'
    ) as HTMLElement;
    const discardBtn = el.shadowRoot!.querySelector(
      'sl-button[variant="danger"]'
    ) as HTMLElement;

    assert.isTrue(acceptBtn.hasAttribute('disabled'));
    assert.isTrue(discardBtn.hasAttribute('disabled'));
  });

  it('delegates to extracted API methods which can be overridden or spyed', async () => {
    const el = await fixture<ChromedashSummaryReviewDialog>(
      html`<chromedash-summary-review-dialog
        .featureId=${101}
        .currentSummary=${'Old summary'}
        .suggestion=${mockSuggestion}
      ></chromedash-summary-review-dialog>`
    );

    const applySpy = sandbox.spy(el, 'applySuggestion');
    await el.handleAccept();
    await el.updateComplete;

    assert.isTrue(applySpy.calledOnce);
  });
});
