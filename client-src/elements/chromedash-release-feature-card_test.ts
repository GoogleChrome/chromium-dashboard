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
import './chromedash-release-feature-card.js';
import {
  ChromedashReleaseFeatureCard,
  FeatureCardItem,
} from './chromedash-release-feature-card.js';
import {
  ReleaseNoteFeatureSummarySourceEnum,
  ReleaseNoteLinkTypeEnum,
} from 'chromestatus-openapi';
import sinon from 'sinon';

describe('chromedash-release-feature-card', () => {
  let sandbox: sinon.SinonSandbox;

  beforeEach(() => {
    sandbox = sinon.createSandbox();
  });

  afterEach(() => {
    sandbox.restore();
  });

  const mockFeature: FeatureCardItem = {
    id: 12345,
    name: 'CSS Subgrid',
    summary:
      'Enables grid items to inherit and share the **grid definition** of their parent.',
    category: 15,
    category_name: 'CSS',
    feature_type: 1,
    summary_source: ReleaseNoteFeatureSummarySourceEnum.HUMAN,
    links: [
      {
        url: 'https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_grid_layout/Subgrid',
        type: ReleaseNoteLinkTypeEnum.DOC,
        title: 'MDN Subgrid Guide',
      },
      {
        url: 'https://www.w3.org/TR/css-grid-2/',
        type: ReleaseNoteLinkTypeEnum.SPEC,
      },
      {
        url: 'https://github.com/w3c/csswg-drafts/issues/1234',
        type: ReleaseNoteLinkTypeEnum.EXPLAINER,
      },
    ],
  };

  it('renders standard feature card with name, summary, category, and links', async () => {
    const el = await fixture<ChromedashReleaseFeatureCard>(
      html`<chromedash-release-feature-card
        .feature=${mockFeature}
      ></chromedash-release-feature-card>`
    );

    const titleEl = el.shadowRoot!.querySelector<HTMLAnchorElement>(
      '.feature-title .feature-name'
    );
    assert.isNotNull(titleEl);
    assert.strictEqual(titleEl!.textContent?.trim(), 'CSS Subgrid');
    assert.strictEqual(titleEl!.getAttribute('href'), '/feature/12345');

    const summaryEl =
      el.shadowRoot!.querySelector<HTMLElement>('.feature-summary');
    assert.isNotNull(summaryEl);
    assert.include(summaryEl!.textContent!, 'Enables grid items to inherit');

    const categoryBadge = el.shadowRoot!.querySelector<HTMLElement>(
      '.badges-wrapper sl-badge'
    );
    assert.isNotNull(categoryBadge);
    assert.strictEqual(categoryBadge!.textContent?.trim(), 'CSS');

    const links = el.shadowRoot!.querySelectorAll<HTMLElement>(
      '.feature-links-bar .feature-link-item'
    );
    assert.strictEqual(links.length, 3);

    const docText0 = links[0].querySelector('.doc-link-text');
    assert.isNotNull(docText0);
    assert.strictEqual(docText0!.textContent?.trim(), 'MDN Subgrid Guide');

    const docText1 = links[1].querySelector('.doc-link-text');
    assert.isNotNull(docText1);
    assert.strictEqual(docText1!.textContent?.trim(), 'Spec');

    const docText2 = links[2].querySelector('.doc-link-text');
    assert.isNotNull(docText2);
    assert.strictEqual(docText2!.textContent?.trim(), 'Explainer');
  });

  it('sets target="_blank" and rel="noopener noreferrer" on external links, and target="_self" on internal links', async () => {
    const featureWithMixedLinks: FeatureCardItem = {
      ...mockFeature,
      links: [
        {
          url: 'https://external.example.com',
          type: ReleaseNoteLinkTypeEnum.DOC,
          title: 'External Doc',
        },
        {
          url: '/feature/12345',
          type: ReleaseNoteLinkTypeEnum.CHROMESTATUS,
          title: 'Internal Feature',
        },
        {
          url: '//attacker.com/test',
          type: ReleaseNoteLinkTypeEnum.OTHER,
          title: 'Protocol Relative',
        },
      ],
    };
    const el = await fixture<ChromedashReleaseFeatureCard>(
      html`<chromedash-release-feature-card
        .feature=${featureWithMixedLinks}
      ></chromedash-release-feature-card>`
    );
    const links = el.shadowRoot!.querySelectorAll<HTMLAnchorElement>(
      '.feature-links-bar a'
    );
    assert.strictEqual(links.length, 3);

    // External link
    assert.strictEqual(links[0].getAttribute('target'), '_blank');
    assert.strictEqual(links[0].getAttribute('rel'), 'noopener noreferrer');
    assert.isNotNull(links[0].querySelector('.external-icon'));
    assert.strictEqual(
      links[0].querySelector('.sr-only')?.textContent?.trim(),
      '(opens in new window)'
    );

    // Internal link
    assert.strictEqual(links[1].getAttribute('target'), '_self');
    assert.strictEqual(links[1].getAttribute('rel'), '');
    assert.isNull(links[1].querySelector('.external-icon'));

    // Protocol relative treated as external
    assert.strictEqual(links[2].getAttribute('target'), '_blank');
    assert.strictEqual(links[2].getAttribute('rel'), 'noopener noreferrer');
  });

  it('renders links from legacy flat fields when links array is missing', async () => {
    const legacyFeature: FeatureCardItem = {
      id: 67890,
      name: 'Legacy Links Feature',
      summary: 'Summary text.',
      category: 5,
      category_name: 'DOM',
      feature_type: 1,
      doc_links: ['https://example.com/doc'],
      spec_link: 'https://example.com/spec',
      explainer_links: ['https://example.com/explainer'],
    };

    const el = await fixture<ChromedashReleaseFeatureCard>(
      html`<chromedash-release-feature-card
        .feature=${legacyFeature}
      ></chromedash-release-feature-card>`
    );

    const links = el.shadowRoot!.querySelectorAll<HTMLElement>(
      '.feature-links-bar .feature-link-item'
    );
    assert.strictEqual(links.length, 3);
    assert.strictEqual(
      links[0].querySelector('.doc-link-text')?.textContent?.trim(),
      'Docs'
    );
    assert.strictEqual(
      links[1].querySelector('.doc-link-text')?.textContent?.trim(),
      'Spec'
    );
    assert.strictEqual(
      links[2].querySelector('.doc-link-text')?.textContent?.trim(),
      'Explainer'
    );
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

    const summaryEl =
      el.shadowRoot!.querySelector<HTMLElement>('.feature-summary');
    assert.isNotNull(summaryEl);
    assert.isTrue(summaryEl!.classList.contains('preformatted'));
    assert.include(summaryEl!.textContent!, 'Line 1\nLine 2');
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

    const summaryEl =
      el.shadowRoot!.querySelector<HTMLElement>('.feature-summary');
    assert.isNotNull(summaryEl);
    assert.isFalse(summaryEl!.classList.contains('preformatted'));
    const strongEl = summaryEl!.querySelector('strong');
    assert.isNotNull(strongEl);
    assert.strictEqual(strongEl!.textContent, 'Bold summary');
  });

  it('renders nothing for feature summary when summary is missing or whitespace', async () => {
    const emptySummaryFeature: FeatureCardItem = {
      ...mockFeature,
      summary: '   ',
    };
    const el = await fixture<ChromedashReleaseFeatureCard>(
      html`<chromedash-release-feature-card
        .feature=${emptySummaryFeature}
      ></chromedash-release-feature-card>`
    );
    assert.isNull(el.shadowRoot!.querySelector('.feature-summary'));
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

  it('renders Human Authored badge when summary_source is HUMAN or unset', async () => {
    const humanEl = await fixture<ChromedashReleaseFeatureCard>(
      html`<chromedash-release-feature-card
        .feature=${mockFeature}
      ></chromedash-release-feature-card>`
    );
    const humanBadges = humanEl.shadowRoot!.querySelectorAll(
      '.badges-wrapper sl-badge'
    );
    const humanTexts = Array.from(humanBadges).map(b => b.textContent?.trim());
    assert.include(humanTexts, 'Human Authored');

    const unsetFeature: FeatureCardItem = {
      ...mockFeature,
      summary_source: undefined,
    };
    const unsetEl = await fixture<ChromedashReleaseFeatureCard>(
      html`<chromedash-release-feature-card
        .feature=${unsetFeature}
      ></chromedash-release-feature-card>`
    );
    const unsetBadges = unsetEl.shadowRoot!.querySelectorAll(
      '.badges-wrapper sl-badge'
    );
    const unsetTexts = Array.from(unsetBadges).map(b => b.textContent?.trim());
    assert.include(unsetTexts, 'Human Authored');
  });

  it('copies anchor link when heading anchor link is clicked', async () => {
    const clipboardStub = sandbox
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

    assert.isTrue(clipboardStub.calledOnce);
    assert.include(clipboardStub.firstCall.args[0], '#feature-12345');
    assert.isTrue(el.isCopied);
  });

  it('renders nothing when feature is null', async () => {
    const el = await fixture<ChromedashReleaseFeatureCard>(
      html`<chromedash-release-feature-card></chromedash-release-feature-card>`
    );
    assert.isNull(el.shadowRoot!.querySelector('.feature-card'));
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

  it('renders nothing for category badge when numeric category ID is unknown', async () => {
    const featureWithUnknownCategory: FeatureCardItem = {
      ...mockFeature,
      category: 99999,
      category_name: undefined,
    };
    const el = await fixture<ChromedashReleaseFeatureCard>(
      html`<chromedash-release-feature-card
        .feature=${featureWithUnknownCategory}
      ></chromedash-release-feature-card>`
    );
    const badges = el.shadowRoot!.querySelectorAll('sl-badge');
    assert.strictEqual(badges.length, 1);
    assert.strictEqual(badges[0].textContent?.trim(), 'Human Authored');
  });

  it('renders no doc links section when no links are present', async () => {
    const featureNoLinks: FeatureCardItem = {
      ...mockFeature,
      links: [],
      doc_links: [],
      spec_link: undefined,
      explainer_links: [],
    };
    const el = await fixture<ChromedashReleaseFeatureCard>(
      html`<chromedash-release-feature-card
        .feature=${featureNoLinks}
      ></chromedash-release-feature-card>`
    );
    assert.isNull(el.shadowRoot!.querySelector('.feature-links-bar'));
  });

  it('filters out empty and whitespace URLs from links array', async () => {
    const emptyLinksFeature: FeatureCardItem = {
      ...mockFeature,
      links: [
        {url: '', type: ReleaseNoteLinkTypeEnum.DOC},
        {url: '   ', type: ReleaseNoteLinkTypeEnum.SPEC},
        {
          url: 'https://valid.example.com',
          type: ReleaseNoteLinkTypeEnum.DOC,
          title: 'Valid Link',
        },
      ],
    };
    const el = await fixture<ChromedashReleaseFeatureCard>(
      html`<chromedash-release-feature-card
        .feature=${emptyLinksFeature}
      ></chromedash-release-feature-card>`
    );
    const links = el.shadowRoot!.querySelectorAll('.feature-links-bar a');
    assert.strictEqual(links.length, 1);
    assert.strictEqual(
      links[0].getAttribute('href'),
      'https://valid.example.com'
    );
  });

  it('deduplicates links across doc_links, spec_link, and explainer_links', async () => {
    const duplicateFeature: FeatureCardItem = {
      ...mockFeature,
      links: undefined,
      doc_links: [
        'https://example.com/same-link',
        'https://example.com/same-link',
      ],
      spec_link: 'https://example.com/same-link',
      explainer_links: ['https://example.com/same-link'],
    };
    const el = await fixture<ChromedashReleaseFeatureCard>(
      html`<chromedash-release-feature-card
        .feature=${duplicateFeature}
      ></chromedash-release-feature-card>`
    );
    const links = el.shadowRoot!.querySelectorAll(
      '.feature-links-bar .feature-link-item'
    );
    assert.strictEqual(links.length, 1);
    assert.strictEqual(
      links[0].getAttribute('href'),
      'https://example.com/same-link'
    );
  });

  it('handles clipboard failure gracefully without throwing', async () => {
    sandbox
      .stub(navigator.clipboard, 'writeText')
      .rejects(new Error('Clipboard permission denied'));
    const warnStub = sandbox.stub(console, 'warn');

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

    assert.isFalse(el.isCopied);
    assert.isTrue(warnStub.calledOnce);
  });

  it('clears copied timeout on disconnectedCallback', async () => {
    const clearTimeoutSpy = sandbox.spy(window, 'clearTimeout');
    sandbox.stub(navigator.clipboard, 'writeText').resolves();

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

    el.disconnectedCallback();
    assert.isTrue(clearTimeoutSpy.called);
  });
});
