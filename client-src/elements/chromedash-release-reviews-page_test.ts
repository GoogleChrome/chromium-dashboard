import {html, fixture, assert} from '@open-wc/testing';
import {LitElement} from 'lit';
import sinon from 'sinon';
import {ChromedashReleaseReviewsPage} from './chromedash-release-reviews-page.js';
import './chromedash-release-reviews-page.js';
import {User, ChromeStatusClient, Feature} from '../js-src/cs-client.js';

describe('chromedash-release-reviews-page', () => {
  const user = {
    can_create_feature: true,
    can_edit: true,
    is_admin: true,
    can_review_release_notes: true,
    email: 'editor@google.com',
  } as unknown as User;

  const mockPendingReviews = {
    features: [
      {
        id: 111,
        name: 'CSS Subgrid Hack',
        summary: 'Pending CSS subgrid improvements.',
        blink_components: ['Blink>CSS'],
        category: 5, // CSS
        resources: {docs: []},
      },
      {
        id: 222,
        name: 'V8 Super Array',
        summary: 'Pending V8 optimization.',
        blink_components: ['Blink>JavaScript'],
        category: 6, // JavaScript/V8
        resources: {docs: []},
      },
    ],
    total_count: 2,
  };

  beforeEach(() => {
    window.csClient = new ChromeStatusClient('fake_token', 1);
    sinon.stub(window.csClient, 'getSummarySuggestion').resolves({
      status: 'complete',
      suggested_summary: 'AI summary',
      suggested_doc_links: [],
      version_token: 1,
    });
  });

  afterEach(() => {
    sinon.restore();
  });

  async function waitForLoading(component: ChromedashReleaseReviewsPage) {
    while (component.loading) {
      await new Promise(resolve => setTimeout(resolve, 50));
    }
    await component.updateComplete;
    const cards = Array.from(
      component.renderRoot.querySelectorAll('chromedash-release-feature-card')
    ) as LitElement[];
    await Promise.all(cards.map(card => card.updateComplete));
  }

  it('renders the pending reviews dashboard grouped by category', async () => {
    const getPendingReviewsStub = sinon
      .stub(window.csClient, 'getPendingReviews')
      .resolves(mockPendingReviews);

    const component = (await fixture(
      html`<chromedash-release-reviews-page
        .user=${user}
      ></chromedash-release-reviews-page>`
    )) as ChromedashReleaseReviewsPage;

    await waitForLoading(component);

    assert.isTrue(getPendingReviewsStub.calledOnce);

    // Verify header and badge
    const headerTitle = component.renderRoot.querySelector(
      '.dashboard-header h2'
    );
    assert.exists(headerTitle);
    assert.include(
      headerTitle.textContent,
      'AI-Assisted Release Reviews Pending'
    );

    const badge = component.renderRoot.querySelector(
      '[data-testid="reviews-count"]'
    );
    assert.exists(badge);
    assert.include(badge.textContent, '2 pending');

    // Verify category groups are NOT present (flat list layout)
    const cssGroup = component.renderRoot.querySelector(
      '[data-testid="category-group-CSS"]'
    );
    assert.isNull(cssGroup);

    const jsGroup = component.renderRoot.querySelector(
      '[data-testid="category-group-JavaScript/V8"]'
    );
    assert.isNull(jsGroup);

    // Verify flat features list container is present
    const featuresList = component.renderRoot.querySelector('.features-list');
    assert.exists(featuresList);

    // Verify feature card rendering
    const cards = Array.from(
      component.renderRoot.querySelectorAll('chromedash-release-feature-card')
    ) as (LitElement & {feature: Feature})[];

    const card1 = cards.find(c => c.feature.id === 111);
    assert.exists(card1);
    await card1.updateComplete;
    assert.include(card1.shadowRoot!.textContent, 'CSS Subgrid Hack');
    assert.include(
      card1.shadowRoot!.textContent,
      'Pending CSS subgrid improvements.'
    );

    const card2 = cards.find(c => c.feature.id === 222);
    assert.exists(card2);
    await card2.updateComplete;
    assert.include(card2.shadowRoot!.textContent, 'V8 Super Array');
    assert.include(card2.shadowRoot!.textContent, 'Pending V8 optimization.');
  });

  it('renders empty dashboard state when there are no reviews pending', async () => {
    const getPendingReviewsStub = sinon
      .stub(window.csClient, 'getPendingReviews')
      .resolves({features: [], total_count: 0});

    const component = (await fixture(
      html`<chromedash-release-reviews-page
        .user=${user}
      ></chromedash-release-reviews-page>`
    )) as ChromedashReleaseReviewsPage;

    await waitForLoading(component);

    assert.isTrue(getPendingReviewsStub.calledOnce);

    const emptyState = component.renderRoot.querySelector(
      '[data-testid="empty-dashboard"]'
    );
    assert.exists(emptyState);
    assert.include(
      emptyState.textContent,
      'All clear! There are no release reviews pending'
    );

    const badge = component.renderRoot.querySelector(
      '[data-testid="reviews-count"]'
    );
    assert.isNull(badge);
  });

  it('handles flat list pagination correctly when count exceeds page limit', async () => {
    // Create 12 mock features (limit is 10)
    const manyFeatures = Array.from({length: 12}, (_, i) => ({
      id: i + 1,
      name: `Feature ${i + 1}`,
      summary: `Summary ${i + 1}`,
      blink_components: ['Blink'],
      category: 1,
      resources: {docs: []},
    }));
    const mockManyReviews = {
      features: manyFeatures,
      total_count: 12,
    };

    const getPendingReviewsStub = sinon
      .stub(window.csClient, 'getPendingReviews')
      .resolves(mockManyReviews);

    const component = (await fixture(
      html`<chromedash-release-reviews-page
        .user=${user}
      ></chromedash-release-reviews-page>`
    )) as ChromedashReleaseReviewsPage;

    await waitForLoading(component);

    assert.isTrue(getPendingReviewsStub.calledOnce);

    // Verify page 1: renders exactly 10 cards
    let cards = Array.from(
      component.renderRoot.querySelectorAll('chromedash-release-feature-card')
    );
    assert.equal(cards.length, 10);

    // Verify pagination controls are visible
    const pagination = component.renderRoot.querySelector(
      '[data-testid="pagination"]'
    );
    assert.exists(pagination);

    const info = component.renderRoot.querySelector(
      '[data-testid="pagination-info"]'
    );
    assert.include(info?.textContent, 'Page 1 of 2');

    // Click Next button
    const nextButton = component.renderRoot.querySelectorAll(
      '[data-testid="pagination"] sl-button'
    )[1] as HTMLElement; // Next button is the second button
    assert.exists(nextButton);
    assert.isFalse(nextButton.hasAttribute('disabled'));
    nextButton.click();

    await component.updateComplete;
    // Wait for cards to render
    cards = Array.from(
      component.renderRoot.querySelectorAll('chromedash-release-feature-card')
    );
    await Promise.all(cards.map(c => (c as LitElement).updateComplete));

    // Verify page 2: renders remaining 2 cards
    cards = Array.from(
      component.renderRoot.querySelectorAll('chromedash-release-feature-card')
    );
    assert.equal(cards.length, 2);
    assert.include(info?.textContent, 'Page 2 of 2');

    // Click Previous button
    const prevButton = component.renderRoot.querySelectorAll(
      '[data-testid="pagination"] sl-button'
    )[0] as HTMLElement; // Prev button is the first button
    assert.exists(prevButton);
    assert.isFalse(prevButton.hasAttribute('disabled'));
    prevButton.click();

    await component.updateComplete;
    cards = Array.from(
      component.renderRoot.querySelectorAll('chromedash-release-feature-card')
    );
    await Promise.all(cards.map(c => (c as LitElement).updateComplete));

    // Verify back to page 1
    cards = Array.from(
      component.renderRoot.querySelectorAll('chromedash-release-feature-card')
    );
    assert.equal(cards.length, 10);
    assert.include(info?.textContent, 'Page 1 of 2');
  });
});
