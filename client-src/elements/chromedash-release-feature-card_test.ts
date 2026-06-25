import {html, fixture, assert} from '@open-wc/testing';
import {ChromedashReleaseFeatureCard} from './chromedash-release-feature-card.js';
import './chromedash-release-feature-card.js';
import {
  ChromeStatusClient,
  Feature,
  SuggestionData,
} from '../js-src/cs-client.js';
import sinon from 'sinon';

describe('chromedash-release-feature-card', () => {
  let originalCsClient: ChromeStatusClient;
  const mockFeature = {
    id: 12345,
    name: 'Mock Feature One',
    summary: 'This is a mock feature summary.',
    blink_components: ['Blink>DOM', 'Blink>Layout'],
    resources: {
      docs: ['https://example.com/doc1', 'https://example.com/doc2'],
    },
    owner_emails: ['owner@google.com'],
    editor_emails: ['editor@google.com'],
    creator_email: 'creator@google.com',
  } as unknown as Feature;

  const mockUserNormal = {
    can_create_feature: false,
    can_edit: false,
    is_admin: false,
    can_review_release_notes: false,
    email: 'user@example.com',
  };

  const mockUserReviewer = {
    can_create_feature: false,
    can_edit: false,
    is_admin: false,
    can_review_release_notes: true,
    email: 'reviewer@google.com',
  };

  beforeEach(async () => {
    originalCsClient = window.csClient;
    window.csClient = new ChromeStatusClient('fake_token', 1);
    // Stub the suggestion call to resolve cleanly by default
    sinon.stub(window.csClient, 'getSummarySuggestion').resolves({
      status: 'none',
      suggested_summary: null,
      suggested_doc_links: [],
      version_token: 1,
    });
  });

  afterEach(() => {
    window.csClient = originalCsClient;
  });

  it('renders feature details correctly', async () => {
    const component = (await fixture(
      html`<chromedash-release-feature-card
        .feature=${mockFeature}
        .user=${mockUserNormal}
      ></chromedash-release-feature-card>`
    )) as ChromedashReleaseFeatureCard;

    await component.updateComplete;

    // Verify title and link
    const titleLink = component.renderRoot.querySelector('.feature-title a');
    assert.exists(titleLink);
    assert.equal(titleLink.textContent?.trim(), 'Mock Feature One');
    assert.equal(titleLink.getAttribute('href'), '/feature/12345');

    // Verify Blink components
    const infoText = (component.renderRoot as HTMLElement).innerHTML;
    assert.include(infoText, 'Blink Components:');
    assert.include(infoText, 'Blink&gt;DOM, Blink&gt;Layout');

    // Verify summary
    const summary = component.renderRoot.querySelector('.feature-summary');
    assert.exists(summary);
    assert.equal(
      summary.textContent?.trim(),
      'This is a mock feature summary.'
    );

    // Verify doc links
    const docLinks = Array.from(
      component.renderRoot.querySelectorAll('.doc-links-list a')
    );
    assert.equal(docLinks.length, 2);
    assert.equal(docLinks[0].getAttribute('href'), 'https://example.com/doc1');
    assert.equal(docLinks[1].getAttribute('href'), 'https://example.com/doc2');
  });

  it('handles missing details gracefully', async () => {
    const sparseFeature = {
      id: 99999,
      name: 'Sparse Feature',
      summary: '',
      blink_components: [],
      resources: {docs: []},
    } as unknown as Feature;

    const component = (await fixture(
      html`<chromedash-release-feature-card
        .feature=${sparseFeature}
        .user=${mockUserNormal}
      ></chromedash-release-feature-card>`
    )) as ChromedashReleaseFeatureCard;

    await component.updateComplete;

    // Renders placeholder summary
    const summary = component.renderRoot.querySelector('.feature-summary em');
    assert.exists(summary);
    assert.equal(summary.textContent?.trim(), 'No summary provided.');

    // Renders "None" for blink components
    assert.include((component.renderRoot as HTMLElement).innerHTML, 'None');

    // Does not render documentation links section
    const docLinksSection =
      component.renderRoot.querySelector('.doc-links-list');
    assert.isNull(docLinksSection);
  });

  it('renders Baseline badges based on suggestion status and user permissions', async () => {
    // Case 1: Editor/Reviewer does NOT see draft suggestion (complete) pre-emptively on the card!
    const editorComponent = (await fixture(
      html`<chromedash-release-feature-card
        .feature=${mockFeature}
        .user=${mockUserReviewer}
      ></chromedash-release-feature-card>`
    )) as ChromedashReleaseFeatureCard;

    editorComponent.suggestion = {
      status: 'complete',
      suggested_summary: 'AI summary',
      suggested_doc_links: [],
      version_token: 1,
      baseline_status: 'widely',
    } as unknown as SuggestionData;
    await editorComponent.updateComplete;

    let badge = editorComponent.renderRoot.querySelector('.baseline-badge');
    assert.isNull(badge); // Draft suggestions should not show pre-emptive badges on the card!

    // Case 2: Normal user does NOT see draft suggestion (complete) baseline badge!
    const normalComponent = (await fixture(
      html`<chromedash-release-feature-card
        .feature=${mockFeature}
        .user=${mockUserNormal}
      ></chromedash-release-feature-card>`
    )) as ChromedashReleaseFeatureCard;

    normalComponent.suggestion = {
      status: 'complete',
      suggested_summary: 'AI summary',
      suggested_doc_links: [],
      version_token: 1,
      baseline_status: 'widely',
    } as unknown as SuggestionData;
    await normalComponent.updateComplete;

    badge = normalComponent.renderRoot.querySelector('.baseline-badge');
    assert.isNull(badge); // Draft suggestion hidden from public users!

    // Case 3: Normal user DOES see approved suggestion (applied) baseline badge without "Suggested:" label!
    normalComponent.suggestion = {
      status: 'applied',
      suggested_summary: 'AI summary',
      suggested_doc_links: [],
      version_token: 1,
      baseline_status: 'widely',
    } as unknown as SuggestionData;
    await normalComponent.updateComplete;

    badge = normalComponent.renderRoot.querySelector('.baseline-badge');
    assert.exists(badge);
    assert.equal(badge.getAttribute('variant'), 'success');
    assert.notInclude(badge.textContent?.trim(), 'Suggested:');
    assert.include(badge.textContent?.trim(), 'Baseline Widely Available');
  });

  describe('editor permissions logic', () => {
    it('allows review if user has can_review_release_notes permission', async () => {
      const component = (await fixture(
        html`<chromedash-release-feature-card
          .feature=${mockFeature}
          .user=${mockUserReviewer}
        ></chromedash-release-feature-card>`
      )) as ChromedashReleaseFeatureCard;

      await component.updateComplete;
      const statusEl = component.renderRoot.querySelector(
        'chromedash-feature-suggestion-status'
      ) as HTMLElement & {canReview: boolean};
      assert.exists(statusEl);
      assert.isTrue(statusEl.canReview);
    });

    it('allows review if user is the feature owner', async () => {
      const ownerUser = {
        ...mockUserNormal,
        email: 'owner@google.com',
      };
      const component = (await fixture(
        html`<chromedash-release-feature-card
          .feature=${mockFeature}
          .user=${ownerUser}
        ></chromedash-release-feature-card>`
      )) as ChromedashReleaseFeatureCard;

      await component.updateComplete;
      const statusEl = component.renderRoot.querySelector(
        'chromedash-feature-suggestion-status'
      ) as HTMLElement & {canReview: boolean};
      assert.exists(statusEl);
      assert.isTrue(statusEl.canReview);
    });

    it('allows review if user is a feature editor', async () => {
      const editorUser = {
        ...mockUserNormal,
        email: 'editor@google.com',
      };
      const component = (await fixture(
        html`<chromedash-release-feature-card
          .feature=${mockFeature}
          .user=${editorUser}
        ></chromedash-release-feature-card>`
      )) as ChromedashReleaseFeatureCard;

      await component.updateComplete;
      const statusEl = component.renderRoot.querySelector(
        'chromedash-feature-suggestion-status'
      ) as HTMLElement & {canReview: boolean};
      assert.exists(statusEl);
      assert.isTrue(statusEl.canReview);
    });

    it('denies review if user is a normal unrelated user', async () => {
      const component = (await fixture(
        html`<chromedash-release-feature-card
          .feature=${mockFeature}
          .user=${mockUserNormal}
        ></chromedash-release-feature-card>`
      )) as ChromedashReleaseFeatureCard;

      await component.updateComplete;
      const statusEl = component.renderRoot.querySelector(
        'chromedash-feature-suggestion-status'
      ) as HTMLElement & {canReview: boolean};
      assert.exists(statusEl);
      assert.isFalse(statusEl.canReview);
    });
  });

  it('intercepts review-suggestion event, stops propagation, and dispatches enriched event', async () => {
    const component = (await fixture(
      html`<chromedash-release-feature-card
        .feature=${mockFeature}
        .user=${mockUserReviewer}
      ></chromedash-release-feature-card>`
    )) as ChromedashReleaseFeatureCard;

    // Set a dummy suggestion state on the card
    const mockSuggestion = {
      status: 'complete',
      suggested_summary: 'Suggested AI text',
      suggested_doc_links: [],
    } as unknown as SuggestionData;
    component.suggestion = mockSuggestion;
    await component.updateComplete;

    const statusEl = component.renderRoot.querySelector(
      'chromedash-feature-suggestion-status'
    ) as HTMLElement & {canReview: boolean};
    assert.exists(statusEl);

    // Setup event listeners
    let enrichedEventDispatched = false;
    let enrichedEventDetail: {
      feature: Feature;
      suggestion: SuggestionData;
    } | null = null;

    // Listen on the component itself to capture the card's dispatched enriched event
    component.addEventListener('review-suggestion', (e: Event) => {
      const detail = (e as CustomEvent).detail;
      if (detail && detail.feature && detail.suggestion) {
        enrichedEventDispatched = true;
        enrichedEventDetail = detail;
      }
    });

    // Dispatch the original raw event from the child status component
    const rawEvent = new CustomEvent('review-suggestion', {
      bubbles: true,
      composed: true,
    });
    statusEl.dispatchEvent(rawEvent);

    // Wait a brief microtask for event loop cycles to complete
    await new Promise(resolve => setTimeout(resolve, 0));

    // Verify:
    // 1. The card successfully dispatched the enriched event
    assert.isTrue(enrichedEventDispatched);
    assert.deepEqual(enrichedEventDetail!.feature, mockFeature);
    assert.deepEqual(enrichedEventDetail!.suggestion, mockSuggestion);
  });
});
