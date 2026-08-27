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

import {LitElement, css, html, nothing, TemplateResult} from 'lit';
import {customElement, property, state} from 'lit/decorators.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {autolink} from './utils.js';
import {FEATURE_CATEGORIES} from './form-field-enums.js';
import {
  ReleaseNoteFeature,
  ReleaseNoteLink,
  ReleaseNoteLinkTypeEnum,
  ReleaseNoteFeatureSummarySourceEnum,
  SummarySuggestion,
  SummarySuggestionStatusEnum,
} from 'chromestatus-openapi';

export const LINK_TYPE_TITLES: Record<ReleaseNoteLinkTypeEnum, string> = {
  [ReleaseNoteLinkTypeEnum.BUG]: 'Tracking bug',
  [ReleaseNoteLinkTypeEnum.CHROMESTATUS]: 'ChromeStatus',
  [ReleaseNoteLinkTypeEnum.SPEC]: 'Spec',
  [ReleaseNoteLinkTypeEnum.ORIGIN_TRIAL]: 'Origin trial',
  [ReleaseNoteLinkTypeEnum.DOC]: 'Docs',
  [ReleaseNoteLinkTypeEnum.EXPLAINER]: 'Explainer',
  [ReleaseNoteLinkTypeEnum.DEMO]: 'Demo',
  [ReleaseNoteLinkTypeEnum.OTHER]: 'Resource',
};

export type FeatureCardItem = Partial<ReleaseNoteFeature> & {
  id: number;
  name: string;
  summary: string;
  doc_links?: string[];
  spec_link?: string;
  explainer_links?: string[];
  markdown_fields?: string[];
};

/**
 * Aggregates and deduplicates resource and documentation links for a feature.
 */
export function aggregateFeatureLinks(
  feature: FeatureCardItem,
  suggestion?: SummarySuggestion | null
): ReleaseNoteLink[] {
  const normalizedLinks: ReleaseNoteLink[] = [];
  const seenUrls = new Set<string>();

  function addLink(
    url?: string,
    type: ReleaseNoteLinkTypeEnum = ReleaseNoteLinkTypeEnum.DOC,
    title?: string
  ): void {
    const trimmed = url?.trim();
    if (!trimmed || seenUrls.has(trimmed)) return;
    seenUrls.add(trimmed);
    normalizedLinks.push({url: trimmed, type, title: title?.trim()});
  }

  if (Array.isArray(feature.links) && feature.links.length > 0) {
    for (const link of feature.links) {
      addLink(link.url, link.type, link.title);
    }
  } else {
    if (Array.isArray(feature.doc_links)) {
      for (const url of feature.doc_links) {
        addLink(url, ReleaseNoteLinkTypeEnum.DOC);
      }
    }
    if (feature.spec_link) {
      addLink(feature.spec_link, ReleaseNoteLinkTypeEnum.SPEC);
    }
    if (Array.isArray(feature.explainer_links)) {
      for (const url of feature.explainer_links) {
        addLink(url, ReleaseNoteLinkTypeEnum.EXPLAINER);
      }
    }
  }

  if (Array.isArray(suggestion?.suggested_doc_links)) {
    for (const url of suggestion.suggested_doc_links) {
      addLink(url, ReleaseNoteLinkTypeEnum.DOC);
    }
  }

  return normalizedLinks;
}

@customElement('chromedash-release-feature-card')
export class ChromedashReleaseFeatureCard extends LitElement {
  @property({attribute: false})
  feature: FeatureCardItem | null = null;

  @property({attribute: false})
  suggestion: SummarySuggestion | null = null;

  @property({type: Boolean})
  reviewMode = false;

  @property({type: Number})
  milestone?: number;

  @state()
  isCopied = false;

  private _copiedTimeout?: ReturnType<typeof setTimeout>;

  disconnectedCallback(): void {
    super.disconnectedCallback();
    if (this._copiedTimeout) {
      clearTimeout(this._copiedTimeout);
      this._copiedTimeout = undefined;
    }
  }

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        :host {
          display: block;
        }

        .feature-card {
          border: var(--card-border);
          border-radius: var(--border-radius);
          box-shadow: var(--card-box-shadow);
          padding: var(--content-padding);
          background-color: var(--card-background);
          display: flex;
          flex-direction: column;
          gap: var(--content-padding-half);
          scroll-margin-top: 5rem;
          transition:
            box-shadow 0.15s ease,
            border-color 0.15s ease;
        }

        .feature-card:hover {
          box-shadow: var(--sl-shadow-medium, 0 4px 12px rgba(0, 0, 0, 0.08));
        }

        .card-header {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          flex-wrap: wrap;
          gap: var(--content-padding-half);
        }

        .title-wrapper {
          display: flex;
          align-items: center;
          gap: var(--content-padding-quarter);
          flex-wrap: wrap;
        }

        .feature-title {
          font-size: var(--sl-font-size-large, 1.25rem);
          font-weight: 600;
          margin: 0;
          line-height: 1.3;
          overflow-wrap: break-word;
        }

        .feature-name {
          color: var(--link-color, #1a73e8);
          text-decoration: none;
        }

        .feature-name:hover {
          text-decoration: underline;
        }

        .heading-anchor-link {
          opacity: 0;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          min-width: 1.5rem;
          min-height: 1.5rem;
          padding: 2px;
          border-radius: var(--border-radius);
          color: var(--unimportant-text-color);
          text-decoration: none;
          position: relative;
          transition:
            opacity 0.15s ease,
            background-color 0.15s ease;
        }

        .feature-card:hover .heading-anchor-link,
        .heading-anchor-link:focus-visible {
          opacity: 1;
        }

        .heading-anchor-link:hover {
          background-color: var(--light-accent-color);
          color: var(--default-color);
        }

        .heading-anchor-link:focus-visible {
          background-color: var(--light-accent-color);
          color: var(--default-color);
          outline: 2px solid var(--primary-button-background);
          outline-offset: 2px;
        }

        @media (hover: none) {
          .heading-anchor-link {
            opacity: 0.6;
            min-width: 2rem;
            min-height: 2rem;
          }
        }

        .anchor-tooltip {
          position: absolute;
          bottom: calc(100% + var(--content-padding-quarter));
          left: 50%;
          transform: translateX(-50%);
          background-color: var(--toast-background, #323232);
          color: var(--toast-color, #fff);
          font-size: var(--button-small-font-size, 0.75rem);
          padding: 4px 8px;
          border-radius: var(--border-radius);
          white-space: nowrap;
          pointer-events: none;
          opacity: 0;
          transition:
            opacity 0.2s ease,
            transform 0.2s ease;
          z-index: 10;
        }

        .heading-anchor-link.copied .anchor-tooltip {
          opacity: 1;
          transform: translateX(-50%) translateY(-2px);
        }

        .badges-wrapper {
          display: flex;
          align-items: center;
          gap: var(--sl-spacing-2x-small);
          flex-wrap: wrap;
        }

        .feature-summary {
          line-height: 1.5;
          color: var(--default-color);
          overflow-wrap: break-word;
        }

        .feature-summary p {
          margin: 0 0 var(--content-padding-half) 0;
        }

        .feature-summary p:last-child {
          margin-bottom: 0;
        }

        .feature-summary code {
          font-family: monospace;
          background-color: var(--light-accent-color);
          padding: 2px 4px;
          border-radius: var(--border-radius);
          border: var(--default-border);
        }

        .feature-summary a {
          text-decoration: underline;
          text-underline-offset: 2px;
        }

        .feature-links-bar {
          display: flex;
          flex-wrap: wrap;
          align-items: center;
          gap: var(--content-padding-quarter) var(--content-padding-half);
          border-top: var(--default-border);
          padding-top: var(--content-padding-half);
          margin-top: auto;
          font-size: var(--button-font-size, 0.875rem);
        }

        .feature-links-bar a {
          text-decoration: underline;
          text-underline-offset: 2px;
        }

        .link-separator {
          color: var(--sl-color-neutral-400);
          user-select: none;
        }

        .feature-link-item {
          display: inline-flex;
          align-items: center;
          gap: var(--content-padding-quarter);
          max-width: 100%;
          text-decoration: underline;
          text-underline-offset: 2px;
          min-width: 0;
        }

        .doc-link-text {
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          min-width: 0;
        }

        .sr-only {
          position: absolute;
          width: 1px;
          height: 1px;
          padding: 0;
          margin: -1px;
          overflow: hidden;
          clip: rect(0, 0, 0, 0);
          white-space: nowrap;
          border: 0;
        }

        .external-icon {
          font-size: var(--button-font-size, 0.875rem);
          line-height: 1;
        }

        .card-actions {
          display: flex;
          align-items: center;
          justify-content: space-between;
          flex-wrap: wrap;
          gap: var(--sl-spacing-small);
          border-top: var(--default-border);
          padding-top: var(--content-padding-half);
        }

        .action-buttons {
          display: flex;
          align-items: center;
          gap: var(--sl-spacing-small);
        }

        .suggestion-meta {
          display: flex;
          align-items: center;
          gap: var(--sl-spacing-x-small);
          font-size: var(--button-small-font-size, 0.875rem);
          color: var(--unimportant-text-color);
        }
      `,
    ];
  }

  async handleAnchorCopy(e: Event): Promise<void> {
    const feature = this.feature;
    if (!feature) return;

    const anchor = `#feature-${feature.id}`;
    const fullUrl = new URL(anchor, window.location.href).href;

    if (navigator.clipboard && navigator.clipboard.writeText) {
      e.preventDefault();
      try {
        await navigator.clipboard.writeText(fullUrl);
        if (this._copiedTimeout) {
          clearTimeout(this._copiedTimeout);
        }
        this.isCopied = true;
        this._copiedTimeout = setTimeout(() => {
          this.isCopied = false;
          this._copiedTimeout = undefined;
        }, 2000);
      } catch (err) {
        console.warn('Could not copy anchor link to clipboard:', err);
        window.location.hash = anchor;
      }
    }
  }

  /**
   * Dispatched when the user clicks the "Review Suggestion" or "Inspect / Edit" button.
   * Event name: `review-click`
   * Detail payload: { feature: FeatureCardItem | null, featureId: number | undefined, suggestion: SummarySuggestion | null }
   */
  handleReviewClick(): void {
    this.dispatchEvent(
      new CustomEvent('review-click', {
        detail: {
          feature: this.feature,
          featureId: this.feature?.id,
          suggestion: this.suggestion ?? null,
        },
        bubbles: true,
        composed: true,
      })
    );
  }

  /**
   * Dispatched when the user clicks the "Generate AI Summary" or "Regenerate" button.
   * Event name: `generate-click`
   * Detail payload: { feature: FeatureCardItem | null, featureId: number | undefined, suggestion: SummarySuggestion | null }
   */
  handleGenerateClick(): void {
    this.dispatchEvent(
      new CustomEvent('generate-click', {
        detail: {
          feature: this.feature,
          featureId: this.feature?.id,
          suggestion: this.suggestion ?? null,
        },
        bubbles: true,
        composed: true,
      })
    );
  }

  renderCategoryBadge(): TemplateResult | typeof nothing {
    const feature = this.feature;
    if (!feature) return nothing;

    let categoryName = feature.category_name?.trim();
    if (!categoryName && typeof feature.category === 'number') {
      const targetCat = feature.category;
      const entry = Object.values(FEATURE_CATEGORIES).find(
        tuple => tuple[0] === targetCat
      );
      categoryName = entry ? entry[1] : undefined;
    }
    if (!categoryName) return nothing;

    return html`<sl-badge variant="neutral" pill>${categoryName}</sl-badge>`;
  }

  renderProvenanceBadge(): TemplateResult | typeof nothing {
    const feature = this.feature;
    if (!feature) return nothing;

    if (
      feature.summary_source === ReleaseNoteFeatureSummarySourceEnum.AI_APPLIED
    ) {
      return html`<sl-badge variant="success" pill>AI Applied</sl-badge>`;
    }

    return html`<sl-badge variant="neutral" pill>Human Authored</sl-badge>`;
  }

  renderReviewBadge(): TemplateResult | typeof nothing {
    if (
      this.suggestion &&
      this.suggestion.status === SummarySuggestionStatusEnum.PENDING
    ) {
      return html`<sl-badge variant="warning" pill
        >AI Review Pending</sl-badge
      >`;
    }
    return nothing;
  }

  renderDocLinks(): TemplateResult | typeof nothing {
    const feature = this.feature;
    if (!feature) return nothing;

    const normalizedLinks = aggregateFeatureLinks(feature, this.suggestion);
    if (normalizedLinks.length === 0) return nothing;

    return html`
      <div
        class="feature-links-bar"
        aria-label="Feature metadata and resources"
      >
        ${normalizedLinks.map((link, idx) => {
          const isInternal =
            (link.url.startsWith('/') && !link.url.startsWith('//')) ||
            link.url.startsWith('#');
          const isExternal = !isInternal;
          const title = link.title?.trim();
          const displayLabel = title || LINK_TYPE_TITLES[link.type] || link.url;
          return html`
            ${
              idx > 0
                ? html`<span class="link-separator" aria-hidden="true">|</span>`
                : nothing
            }
            <a
              class="feature-link-item"
              href=${link.url}
              target=${isExternal ? '_blank' : '_self'}
              rel=${isExternal ? 'noopener noreferrer' : ''}
              title=${link.url}
            >
              <span class="doc-link-text">${displayLabel}</span>
              ${
                isExternal
                  ? html`<span aria-hidden="true" class="external-icon">↗</span
                      ><span class="sr-only">(opens in new window)</span>`
                  : nothing
              }
            </a>
          `;
        })}
      </div>
    `;
  }

  renderPrimaryReviewButton(hasPendingSuggestion: boolean): TemplateResult {
    if (hasPendingSuggestion) {
      return html`
        <sl-button
          size="small"
          variant="primary"
          class="review-button"
          @click=${this.handleReviewClick}
        >
          <sl-icon slot="prefix" name="pencil"></sl-icon>
          Review Suggestion
        </sl-button>
      `;
    }

    return html`
      <sl-button
        size="small"
        variant="default"
        class="review-button"
        @click=${this.handleReviewClick}
      >
        <sl-icon slot="prefix" name="eye"></sl-icon>
        Inspect / Edit
      </sl-button>
    `;
  }

  renderGenerateButton(hasPendingSuggestion: boolean): TemplateResult {
    const label = hasPendingSuggestion ? 'Regenerate' : 'Generate AI Summary';
    return html`
      <sl-button
        size="small"
        variant="default"
        class="generate-button"
        @click=${this.handleGenerateClick}
      >
        <sl-icon slot="prefix" name="arrow-clockwise"></sl-icon>
        ${label}
      </sl-button>
    `;
  }

  renderReasoningMeta(): TemplateResult | typeof nothing {
    const reasoning = this.suggestion?.reasoning?.trim();
    if (!reasoning) return nothing;

    return html`
      <div class="suggestion-meta">
        <sl-tooltip content=${reasoning}>
          <sl-icon
            tabindex="0"
            name="info-circle"
            aria-label="Summary reasoning details"
          ></sl-icon>
        </sl-tooltip>
        <span>Grounding available</span>
      </div>
    `;
  }

  renderReviewActions(): TemplateResult | typeof nothing {
    if (!this.reviewMode || !this.feature) return nothing;

    const hasPendingSuggestion =
      this.suggestion?.status === SummarySuggestionStatusEnum.PENDING;

    return html`
      <div class="card-actions">
        <div class="action-buttons">
          ${this.renderPrimaryReviewButton(hasPendingSuggestion)}
          ${this.renderGenerateButton(hasPendingSuggestion)}
        </div>
        ${this.renderReasoningMeta()}
      </div>
    `;
  }

  renderFeatureSummary(): TemplateResult | typeof nothing {
    const feature = this.feature;
    if (!feature || !feature.summary?.trim()) return nothing;

    const isMarkdown = Boolean(feature.markdown_fields?.includes('summary'));
    const formattedSummary = autolink(feature.summary, [], isMarkdown);

    return html`
      <div class="feature-summary ${isMarkdown ? '' : 'preformatted'}">
        ${formattedSummary}
      </div>
    `;
  }

  render(): TemplateResult | typeof nothing {
    const feature = this.feature;
    if (!feature) {
      return nothing;
    }

    return html`
      <article
        class="feature-card"
        id="feature-${feature.id}"
        aria-labelledby="feature-title-${feature.id}"
      >
        <header class="card-header">
          <div class="title-wrapper">
            <h3 class="feature-title" id="feature-title-${feature.id}">
              <a class="feature-name" href="/feature/${feature.id}">
                ${feature.name}
              </a>
            </h3>
            <a
              class="heading-anchor-link ${this.isCopied ? 'copied' : ''}"
              href="#feature-${feature.id}"
              aria-label=${
                this.isCopied
                  ? `Link to ${feature.name} copied to clipboard`
                  : `Copy link to ${feature.name}`
              }
              title="Copy link to feature"
              data-anchor="#feature-${feature.id}"
              @click=${this.handleAnchorCopy}
            >
              <span aria-hidden="true">#</span>
              <span class="anchor-tooltip" role="status" aria-live="polite">
                ${this.isCopied ? 'Link copied!' : 'Copy link'}
              </span>
            </a>
          </div>

          <div class="badges-wrapper">
            ${this.renderCategoryBadge()} ${this.renderProvenanceBadge()}
            ${this.renderReviewBadge()}
          </div>
        </header>

        ${this.renderFeatureSummary()} ${this.renderDocLinks()}
        ${this.renderReviewActions()}
      </article>
    `;
  }
}
