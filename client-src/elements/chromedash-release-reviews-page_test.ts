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

import {assert, fixture} from '@open-wc/testing';
import {html} from 'lit';
import sinon from 'sinon';
import {ChromedashReleaseReviewsPage} from './chromedash-release-reviews-page.js';
import './chromedash-release-reviews-page.js';
import {ChromedashSummaryReviewDialog} from './chromedash-summary-review-dialog.js';
import './chromedash-summary-review-dialog.js';
import {ChromeStatusHttpError} from '../js-src/cs-client.js';

describe('chromedash-release-reviews-page', () => {
  let getPendingQueueStub: sinon.SinonStub;

  const mockSuggestions = [
    {
      feature_id: 101,
      feature_name: 'CSS Grid Subgrid',
      suggested_summary:
        'Enables nested grids to participate in parent sizing.',
      original_summary: 'Subgrid for CSS grid layout.',
      version_token: 1,
    },
    {
      feature_id: 102,
      feature_name: 'Popover API',
      suggested_summary: 'Provides standard top-layer popover capabilities.',
      original_summary: 'HTML Popover attribute.',
      version_token: 2,
    },
  ];

  beforeEach(() => {
    window.csClient = {} as any;
    getPendingQueueStub = sinon.stub();
    window.csClient.getPendingSuggestionsQueue = getPendingQueueStub;
  });

  afterEach(() => {
    sinon.restore();
  });

  it('renders loading state while fetching', async () => {
    getPendingQueueStub.returns(new Promise(() => {})); // Never resolves
    const component = await fixture<ChromedashReleaseReviewsPage>(
      html`<chromedash-release-reviews-page></chromedash-release-reviews-page>`
    );

    assert.isTrue(component.loading);
    const spinner = component.shadowRoot?.querySelector('sl-spinner');
    assert.exists(spinner);
  });

  it('renders empty state when no pending reviews exist', async () => {
    getPendingQueueStub.resolves({
      suggestions: [],
      total_count: 0,
      next_cursor: null,
    });

    const component = await fixture<ChromedashReleaseReviewsPage>(
      html`<chromedash-release-reviews-page></chromedash-release-reviews-page>`
    );
    await component.fetchPendingQueue();
    await component.updateComplete;

    assert.isFalse(component.loading);
    assert.equal(component.suggestions.length, 0);
    const emptyState = component.shadowRoot?.querySelector('.empty-state');
    assert.exists(emptyState);
    assert.include(emptyState?.textContent, 'All caught up!');
  });

  it('renders queue item cards when suggestions exist', async () => {
    getPendingQueueStub.resolves({
      suggestions: mockSuggestions,
      total_count: 2,
      next_cursor: null,
    });

    const component = await fixture<ChromedashReleaseReviewsPage>(
      html`<chromedash-release-reviews-page></chromedash-release-reviews-page>`
    );
    await component.fetchPendingQueue();
    await component.updateComplete;

    assert.isFalse(component.loading);
    assert.equal(component.suggestions.length, 2);

    const cards = component.shadowRoot?.querySelectorAll('.queue-item-card');
    assert.equal(cards?.length, 2);
    assert.include(cards?.[0].textContent, 'CSS Grid Subgrid');
    assert.include(cards?.[1].textContent, 'Popover API');
  });

  it('opens review dialog with selected suggestion', async () => {
    getPendingQueueStub.resolves({
      suggestions: mockSuggestions,
      total_count: 2,
      next_cursor: null,
    });

    const component = await fixture<ChromedashReleaseReviewsPage>(
      html`<chromedash-release-reviews-page></chromedash-release-reviews-page>`
    );
    await component.fetchPendingQueue();
    await component.updateComplete;

    const reviewBtn = component.shadowRoot?.querySelector(
      '[data-testid="review-button-101"]'
    ) as HTMLElement;
    assert.exists(reviewBtn);

    const dialog =
      component.shadowRoot?.querySelector<ChromedashSummaryReviewDialog>(
        'chromedash-summary-review-dialog'
      );
    assert.exists(dialog);
    const showSpy = sinon.spy(dialog!, 'show');

    reviewBtn.click();
    await component.updateComplete;

    assert.equal(component.activeReviewSuggestion?.feature_id, 101);
    assert.isTrue(showSpy.calledOnce);
  });

  it('removes suggestion from list when applied', async () => {
    getPendingQueueStub.resolves({
      suggestions: [...mockSuggestions],
      total_count: 2,
      next_cursor: null,
    });

    const component = await fixture<ChromedashReleaseReviewsPage>(
      html`<chromedash-release-reviews-page></chromedash-release-reviews-page>`
    );
    await component.fetchPendingQueue();
    await component.updateComplete;

    assert.equal(component.suggestions.length, 2);

    component.handleSuggestionApplied(
      new CustomEvent('summary-suggestion-applied', {
        detail: {
          featureId: 101,
          summary: 'New summary',
        },
      })
    );
    await component.updateComplete;

    assert.equal(component.suggestions.length, 1);
    assert.equal(component.suggestions[0].feature_id, 102);
    assert.equal(component.totalCount, 1);
  });

  it('removes suggestion from list when rejected/discarded', async () => {
    getPendingQueueStub.resolves({
      suggestions: [...mockSuggestions],
      total_count: 2,
      next_cursor: null,
    });

    const component = await fixture<ChromedashReleaseReviewsPage>(
      html`<chromedash-release-reviews-page></chromedash-release-reviews-page>`
    );
    await component.fetchPendingQueue();
    await component.updateComplete;

    component.handleSuggestionRejected(
      new CustomEvent('summary-suggestion-rejected', {
        detail: {
          featureId: 102,
        },
      })
    );
    await component.updateComplete;

    assert.equal(component.suggestions.length, 1);
    assert.equal(component.suggestions[0].feature_id, 101);
  });

  it('renders error alert when fetching fails with 403', async () => {
    getPendingQueueStub.rejects(
      new ChromeStatusHttpError(
        'Forbidden',
        '/summary-suggestions/pending',
        'GET',
        403,
        'No permission'
      )
    );

    const component = await fixture<ChromedashReleaseReviewsPage>(
      html`<chromedash-release-reviews-page></chromedash-release-reviews-page>`
    );
    await component.fetchPendingQueue();
    await component.updateComplete;

    assert.isFalse(component.loading);
    assert.exists(component.error);
    assert.include(component.error!, 'permission');
    const alert = component.shadowRoot?.querySelector('sl-alert');
    assert.exists(alert);
  });
});
