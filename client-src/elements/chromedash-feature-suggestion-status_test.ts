import {assert, fixture} from '@open-wc/testing';
import {html} from 'lit';
import sinon from 'sinon';
import {ChromeStatusClient} from '../js-src/cs-client.js';
import {ChromedashFeatureSuggestionStatus} from './chromedash-feature-suggestion-status.js';
import './chromedash-feature-suggestion-status.js';

describe('chromedash-feature-suggestion-status', () => {
  const feature = {
    id: 12345,
    name: 'Mock Feature',
    owner_emails: ['owner@example.com'],
  };

  const suggestionPromise = Promise.resolve({
    status: 'complete',
    suggested_summary: 'Suggested summary text.',
    suggested_doc_links: ['https://example.com/doc'],
    version_token: 1,
  });

  beforeEach(async () => {
    window.csClient = new ChromeStatusClient('fake_token', 1);
    sinon
      .stub(window.csClient, 'getSummarySuggestion')
      .returns(suggestionPromise);
    sinon.stub(window.csClient, 'triggerSummaryGeneration').resolves({});
  });

  afterEach(() => {
    window.csClient.getSummarySuggestion.restore();
    window.csClient.triggerSummaryGeneration.restore();
  });

  it('renders nothing if canReview is false', async () => {
    const el = (await fixture(
      html`<chromedash-feature-suggestion-status
        .feature=${feature}
        .canReview=${false}
      ></chromedash-feature-suggestion-status>`
    )) as ChromedashFeatureSuggestionStatus;

    await el.updateComplete;
    const controlPanel = el.shadowRoot!.querySelector(
      '.suggestion-control-panel'
    );
    assert.isNull(controlPanel);
  });

  it('renders skeleton loader when suggestion is pending', async () => {
    // Delay resolution to catch pending state
    let resolveSuggestion: (value: unknown) => void = () => {};
    const pendingPromise = new Promise(resolve => {
      resolveSuggestion = resolve;
    });
    window.csClient.getSummarySuggestion.restore();
    sinon.stub(window.csClient, 'getSummarySuggestion').returns(pendingPromise);

    const el = (await fixture(
      html`<chromedash-feature-suggestion-status
        .feature=${feature}
        .canReview=${true}
      ></chromedash-feature-suggestion-status>`
    )) as ChromedashFeatureSuggestionStatus;

    // Renders skeleton in shadow DOM
    const skeleton = el.shadowRoot!.querySelector('sl-skeleton');
    assert.exists(skeleton);

    // Resolve and update
    resolveSuggestion({
      status: 'complete',
      suggested_summary: 'Doc',
      suggested_doc_links: [],
    });
    await new Promise(resolve => setTimeout(resolve, 0));
    await el.updateComplete;

    const controlPanel = el.shadowRoot!.querySelector(
      '.suggestion-control-panel'
    );
    assert.exists(controlPanel);
    assert.include(controlPanel.innerHTML, 'Draft Available');
  });

  it('renders suggestion status complete and reviews suggestions', async () => {
    const el = (await fixture(
      html`<chromedash-feature-suggestion-status
        .feature=${feature}
        .canReview=${true}
      ></chromedash-feature-suggestion-status>`
    )) as ChromedashFeatureSuggestionStatus;

    await el.updateComplete;
    const controlPanel = el.shadowRoot!.querySelector(
      '.suggestion-control-panel'
    );
    assert.exists(controlPanel);
    assert.include(controlPanel.innerHTML, 'Draft Available');

    const reviewBtn = el.shadowRoot!.querySelector(
      'sl-button[variant="primary"]'
    ) as HTMLElement;
    assert.exists(reviewBtn);

    // Click triggers review event to parent
    const eventPromise = new Promise<CustomEvent>(resolve => {
      el.addEventListener('review-suggestion', e => resolve(e as CustomEvent));
    });
    reviewBtn.click();
    const event = await eventPromise;
    assert.equal(event.detail.feature.id, 12345);
  });

  it('renders chromedash-ai-summary-progress when status is in_progress', async () => {
    window.csClient.getSummarySuggestion.restore();
    sinon.stub(window.csClient, 'getSummarySuggestion').resolves({
      status: 'in_progress',
      progress_steps: [],
    });

    const el = (await fixture(
      html`<chromedash-feature-suggestion-status
        .feature=${feature}
        .canReview=${true}
      ></chromedash-feature-suggestion-status>`
    )) as ChromedashFeatureSuggestionStatus;

    await el.updateComplete;

    // Verify child component is rendered
    const progressEl = el.shadowRoot!.querySelector(
      'chromedash-ai-summary-progress'
    );
    assert.exists(progressEl);
  });

  it('renders Server Busy badge and allows regeneration when status is overloaded', async () => {
    window.csClient.getSummarySuggestion.restore();
    sinon.stub(window.csClient, 'getSummarySuggestion').resolves({
      status: 'overloaded',
      suggested_summary: null,
      suggested_doc_links: [],
      version_token: 1,
    });

    const el = (await fixture(
      html`<chromedash-feature-suggestion-status
        .feature=${feature}
        .canReview=${true}
      ></chromedash-feature-suggestion-status>`
    )) as ChromedashFeatureSuggestionStatus;

    await el.updateComplete;

    // Verify badge
    const badge = el.shadowRoot!.querySelector('sl-tag');
    assert.exists(badge);
    assert.include(badge.textContent, 'Server Busy');

    // Verify Generate button is visible and active
    const generateBtn = el.shadowRoot!.querySelector(
      'sl-button'
    ) as HTMLElement;
    assert.exists(generateBtn);
    assert.include(generateBtn.textContent, 'Generate Summary');
    assert.isFalse(generateBtn.hasAttribute('disabled'));

    // Click triggers generation
    generateBtn.click();
    assert.isTrue(
      (
        window.csClient.triggerSummaryGeneration as sinon.SinonStub
      ).calledOnceWith(12345)
    );
  });
});
