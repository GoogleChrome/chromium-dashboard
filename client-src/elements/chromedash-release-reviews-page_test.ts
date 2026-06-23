import {html, fixture, assert} from '@open-wc/testing';
import sinon from 'sinon';
import {ChromedashReleaseReviewsPage} from './chromedash-release-reviews-page.js';
import './chromedash-release-reviews-page.js';
import {User, ChromeStatusClient} from '../js-src/cs-client.js';

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
    ) as any[];
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
    assert.include(headerTitle.textContent, 'Release Reviews Dashboard');

    const badge = component.renderRoot.querySelector(
      '[data-testid="reviews-count"]'
    );
    assert.exists(badge);
    assert.include(badge.textContent, '2 pending');

    // Verify categories rendering
    const cssGroup = component.renderRoot.querySelector(
      '[data-testid="category-group-CSS"]'
    );
    assert.exists(cssGroup);
    assert.include(cssGroup.textContent, 'CSS (1)');

    const jsGroup = component.renderRoot.querySelector(
      '[data-testid="category-group-JavaScript/V8"]'
    );
    assert.exists(jsGroup);
    assert.include(jsGroup.textContent, 'JavaScript/V8 (1)');

    // Verify feature card rendering
    const cards = Array.from(
      component.renderRoot.querySelectorAll('chromedash-release-feature-card')
    ) as any[];

    const card1 = cards.find(c => c.feature.id === 111);
    assert.exists(card1);
    await card1.updateComplete;
    assert.include(card1.shadowRoot.textContent, 'CSS Subgrid Hack');
    assert.include(
      card1.shadowRoot.textContent,
      'Pending CSS subgrid improvements.'
    );

    const card2 = cards.find(c => c.feature.id === 222);
    assert.exists(card2);
    await card2.updateComplete;
    assert.include(card2.shadowRoot.textContent, 'V8 Super Array');
    assert.include(card2.shadowRoot.textContent, 'Pending V8 optimization.');
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
});
