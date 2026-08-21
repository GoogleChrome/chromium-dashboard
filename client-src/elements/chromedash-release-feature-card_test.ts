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

import {html, fixture, assert, oneEvent} from '@open-wc/testing';
import './chromedash-release-feature-card.js';
import {
  ChromedashReleaseFeatureCard,
  FeatureCardItem,
} from './chromedash-release-feature-card.js';
import {
  ReleaseNoteFeatureSummarySourceEnum,
  SummarySuggestion,
  SummarySuggestionStatusEnum,
} from 'chromestatus-openapi';
import sinon from 'sinon';

describe('chromedash-release-feature-card', () => {
  const mockFeature: FeatureCardItem = {
    id: 12345,
    name: 'CSS Subgrid',
    summary:
      'Enables grid items to inherit and share the **grid definition** of their parent.',
    category: 'CSS',
    category_name: 'CSS',
    feature_type: 1,
    summary_source: ReleaseNoteFeatureSummarySourceEnum.HUMAN,
    doc_links: [
      'https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_grid_layout/Subgrid',
    ],
    spec_link: 'https://www.w3.org/TR/css-grid-2/',
    explainer_links: ['https://github.com/w3c/csswg-drafts/issues/1234'],
  };

  const mockSuggestion: SummarySuggestion = {
    feature_id: 12345,
    suggested_summary: 'AI-generated summary for CSS Subgrid.',
    original_summary: 'Enables grid items to inherit grid definition.',
    status: SummarySuggestionStatusEnum.PENDING,
    reasoning: 'Extracted from W3C spec and MDN documentation.',
    suggested_doc_links: [
      'https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_grid_layout/Subgrid',
    ],
    version_token: 1,
    created: new Date('2026-08-20T10:00:00Z'),
    updated: new Date('2026-08-20T10:00:00Z'),
  };

  it('renders standard feature card with name, summary, category, and links', async () => {
    const el = await fixture<ChromedashReleaseFeatureCard>(
      html`<chromedash-release-feature-card
        .feature=${mockFeature}
      ></chromedash-release-feature-card>`
    );

    const titleEl = el.shadowRoot!.querySelector('.feature-title a');
    assert.isNotNull(titleEl);
    assert.equal(titleEl?.textContent?.trim(), 'CSS Subgrid');
    assert.equal(titleEl?.getAttribute('href'), '/feature/12345');

    const summaryEl = el.shadowRoot!.querySelector('.feature-summary');
    assert.isNotNull(summaryEl);
    assert.include(
      summaryEl?.textContent || '',
      'Enables grid items to inherit'
    );

    const categoryBadge = el.shadowRoot!.querySelector(
      '.badges-wrapper sl-badge'
    );
    assert.isNotNull(categoryBadge);
    assert.equal(categoryBadge?.textContent?.trim(), 'CSS');

    const links = el.shadowRoot!.querySelectorAll(
      '.feature-links-section .feature-link-item'
    );
    assert.equal(links.length, 3);
  });

  it('renders plain-text summary with preformatted class', async () => {
    const plainFeature: FeatureCardItem = {
      ...mockFeature,
      summary: 'Line 1\nLine 2',
      markdown_fields: [],
    };

    const el = await fixture<ChromedashReleaseFeatureCard>(
      html`<chromedash-release-feature-card
        .feature=${plainFeature}
      ></chromedash-release-feature-card>`
    );

    const summaryEl = el.shadowRoot!.querySelector('.feature-summary');
    assert.isNotNull(summaryEl);
    assert.isTrue(summaryEl?.classList.contains('preformatted'));
    assert.include(summaryEl?.textContent || '', 'Line 1\nLine 2');
  });

  it('renders markdown summary without preformatted class', async () => {
    const mdFeature: FeatureCardItem = {
      ...mockFeature,
      summary: '**Bold summary** with [link](https://example.com)',
      markdown_fields: ['summary'],
    };

    const el = await fixture<ChromedashReleaseFeatureCard>(
      html`<chromedash-release-feature-card
        .feature=${mdFeature}
      ></chromedash-release-feature-card>`
    );

    const summaryEl = el.shadowRoot!.querySelector('.feature-summary');
    assert.isNotNull(summaryEl);
    assert.isFalse(summaryEl?.classList.contains('preformatted'));
    assert.isNotNull(summaryEl?.querySelector('strong'));
    assert.equal(
      summaryEl?.querySelector('strong')?.textContent,
      'Bold summary'
    );
  });

  it('renders AI Applied badge when summary_source is AI_APPLIED', async () => {
    const aiFeature: FeatureCardItem = {
      ...mockFeature,
      summary_source: ReleaseNoteFeatureSummarySourceEnum.AI_APPLIED,
    };

    const el = await fixture<ChromedashReleaseFeatureCard>(
      html`<chromedash-release-feature-card
        .feature=${aiFeature}
      ></chromedash-release-feature-card>`
    );

    const badges = el.shadowRoot!.querySelectorAll('.badges-wrapper sl-badge');
    const badgeTexts = Array.from(badges).map(b => b.textContent?.trim());
    assert.include(badgeTexts, 'AI Applied');
  });

  it('renders AI Review Pending badge when pending suggestion exists', async () => {
    const el = await fixture<ChromedashReleaseFeatureCard>(
      html`<chromedash-release-feature-card
        .feature=${mockFeature}
        .suggestion=${mockSuggestion}
      ></chromedash-release-feature-card>`
    );

    const badges = el.shadowRoot!.querySelectorAll('.badges-wrapper sl-badge');
    const badgeTexts = Array.from(badges).map(b => b.textContent?.trim());
    assert.include(badgeTexts, 'AI Review Pending');
  });

  it('renders review actions when reviewMode is true', async () => {
    const el = await fixture<ChromedashReleaseFeatureCard>(
      html`<chromedash-release-feature-card
        .feature=${mockFeature}
        .suggestion=${mockSuggestion}
        ?reviewMode=${true}
      ></chromedash-release-feature-card>`
    );

    const actions = el.shadowRoot!.querySelector('.card-actions');
    assert.isNotNull(actions);

    const reviewBtn = el.shadowRoot!.querySelector('.review-button');
    assert.isNotNull(reviewBtn);
    assert.include(reviewBtn?.textContent || '', 'Review Suggestion');

    const generateBtn = el.shadowRoot!.querySelector('.generate-button');
    assert.isNotNull(generateBtn);
    assert.include(generateBtn?.textContent || '', 'Regenerate');

    const groundingMeta = el.shadowRoot!.querySelector('.suggestion-meta');
    assert.isNotNull(groundingMeta);
    assert.include(groundingMeta?.textContent || '', 'Grounding available');
  });

  it('dispatches review-click event when review button is clicked', async () => {
    const el = await fixture<ChromedashReleaseFeatureCard>(
      html`<chromedash-release-feature-card
        .feature=${mockFeature}
        .suggestion=${mockSuggestion}
        ?reviewMode=${true}
      ></chromedash-release-feature-card>`
    );

    const reviewBtn =
      el.shadowRoot!.querySelector<HTMLElement>('.review-button');
    const eventPromise = oneEvent(el, 'review-click');
    reviewBtn?.click();

    const event = (await eventPromise) as CustomEvent;
    assert.isNotNull(event);
    assert.equal(event.detail.featureId, 12345);
    assert.deepEqual(event.detail.suggestion, mockSuggestion);
  });

  it('dispatches generate-click event when generate button is clicked', async () => {
    const el = await fixture<ChromedashReleaseFeatureCard>(
      html`<chromedash-release-feature-card
        .feature=${mockFeature}
        ?reviewMode=${true}
      ></chromedash-release-feature-card>`
    );

    const generateBtn =
      el.shadowRoot!.querySelector<HTMLElement>('.generate-button');
    const eventPromise = oneEvent(el, 'generate-click');
    generateBtn?.click();

    const event = (await eventPromise) as CustomEvent;
    assert.isNotNull(event);
    assert.equal(event.detail.featureId, 12345);
  });

  it('copies anchor link when heading anchor link is clicked', async () => {
    const clipboardStub = sinon
      .stub(navigator.clipboard, 'writeText')
      .resolves();

    const el = await fixture<ChromedashReleaseFeatureCard>(
      html`<chromedash-release-feature-card
        .feature=${mockFeature}
      ></chromedash-release-feature-card>`
    );

    const anchorLink = el.shadowRoot!.querySelector<HTMLElement>(
      '.heading-anchor-link'
    );
    assert.isNotNull(anchorLink);
    anchorLink?.click();

    assert.isTrue(clipboardStub.calledOnce);
    assert.include(clipboardStub.firstCall.args[0], '#feature-12345');

    clipboardStub.restore();
  });

  it('renders nothing when feature is null', async () => {
    const el = await fixture<ChromedashReleaseFeatureCard>(
      html`<chromedash-release-feature-card></chromedash-release-feature-card>`
    );
    assert.isNull(el.shadowRoot!.querySelector('.feature-card'));
  });

  it('does not render card actions when reviewMode is false', async () => {
    const el = await fixture<ChromedashReleaseFeatureCard>(
      html`<chromedash-release-feature-card
        .feature=${mockFeature}
        .reviewMode=${false}
      ></chromedash-release-feature-card>`
    );
    assert.isNull(el.shadowRoot!.querySelector('.card-actions'));
  });

  it('renders inspect button when reviewMode is true without pending suggestion', async () => {
    const el = await fixture<ChromedashReleaseFeatureCard>(
      html`<chromedash-release-feature-card
        .feature=${mockFeature}
        ?reviewMode=${true}
      ></chromedash-release-feature-card>`
    );
    const reviewBtn = el.shadowRoot!.querySelector('.review-button');
    assert.include(reviewBtn?.textContent || '', 'Inspect / Edit');
    const generateBtn = el.shadowRoot!.querySelector('.generate-button');
    assert.include(generateBtn?.textContent || '', 'Generate AI Summary');
  });

  it('renders category badge from numeric category ID', async () => {
    const featureWithNumCategory: FeatureCardItem = {
      ...mockFeature,
      category: 15,
      category_name: undefined,
    };
    const el = await fixture<ChromedashReleaseFeatureCard>(
      html`<chromedash-release-feature-card
        .feature=${featureWithNumCategory}
      ></chromedash-release-feature-card>`
    );
    const badges = el.shadowRoot!.querySelectorAll('sl-badge');
    const categoryBadge = Array.from(badges).find(
      b => b.textContent?.trim() === 'CSS'
    );
    assert.isDefined(categoryBadge);
  });

  it('renders no doc links section when no links are present', async () => {
    const featureNoLinks: FeatureCardItem = {
      ...mockFeature,
      doc_links: [],
      spec_link: undefined,
      explainer_links: [],
    };
    const el = await fixture<ChromedashReleaseFeatureCard>(
      html`<chromedash-release-feature-card
        .feature=${featureNoLinks}
      ></chromedash-release-feature-card>`
    );
    assert.isNull(el.shadowRoot!.querySelector('.feature-links-section'));
  });

  it('deduplicates links across doc_links, spec_link, explainer_links, and suggested_doc_links', async () => {
    const duplicateFeature: FeatureCardItem = {
      ...mockFeature,
      doc_links: ['https://example.com/same-link'],
      spec_link: 'https://example.com/same-link',
      explainer_links: ['https://example.com/same-link'],
    };
    const suggestionWithSameLink: SummarySuggestion = {
      ...mockSuggestion,
      suggested_doc_links: ['https://example.com/same-link'],
    };
    const el = await fixture<ChromedashReleaseFeatureCard>(
      html`<chromedash-release-feature-card
        .feature=${duplicateFeature}
        .suggestion=${suggestionWithSameLink}
      ></chromedash-release-feature-card>`
    );
    const links = el.shadowRoot!.querySelectorAll(
      '.feature-links-section .feature-link-item'
    );
    assert.equal(links.length, 1);
    assert.equal(
      links[0].getAttribute('href'),
      'https://example.com/same-link'
    );
  });

  it('handles clipboard failure gracefully without throwing', async () => {
    const clipboardStub = sinon
      .stub(navigator.clipboard, 'writeText')
      .rejects(new Error('Clipboard permission denied'));

    const el = await fixture<ChromedashReleaseFeatureCard>(
      html`<chromedash-release-feature-card
        .feature=${mockFeature}
      ></chromedash-release-feature-card>`
    );

    const anchorLink = el.shadowRoot!.querySelector<HTMLElement>(
      '.heading-anchor-link'
    );
    anchorLink?.click();

    // Should not throw or mark isCopied
    assert.isFalse(el.isCopied);

    clipboardStub.restore();
  });

  it('clears copied timeout on disconnectedCallback', async () => {
    const clearTimeoutSpy = sinon.spy(window, 'clearTimeout');
    const clipboardStub = sinon
      .stub(navigator.clipboard, 'writeText')
      .resolves();

    const el = await fixture<ChromedashReleaseFeatureCard>(
      html`<chromedash-release-feature-card
        .feature=${mockFeature}
      ></chromedash-release-feature-card>`
    );

    const clickEvent = new MouseEvent('click', {
      bubbles: true,
      cancelable: true,
    });
    await el.handleAnchorCopy(clickEvent);
    assert.isTrue(el.isCopied);

    // Trigger disconnectedCallback
    el.disconnectedCallback();
    assert.isTrue(clearTimeoutSpy.called);

    clipboardStub.restore();
    clearTimeoutSpy.restore();
  });
});
