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
import '@shoelace-style/shoelace/dist/components/button/button.js';
import '@shoelace-style/shoelace/dist/components/badge/badge.js';
import '@shoelace-style/shoelace/dist/components/icon/icon.js';
import '@shoelace-style/shoelace/dist/components/tooltip/tooltip.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {autolink} from './utils.js';
import {FEATURE_CATEGORIES} from './form-field-enums.js';
import {
  SummarySuggestion,
  SummarySuggestionStatusEnum,
} from 'chromestatus-openapi';

export type FeatureCardItem = {
  id: number;
  name: string;
  summary: string;
  category?: string | number;
  category_name?: string;
  feature_type?: string | number;
  summary_source?: string;
  doc_links?: string[];
  spec_link?: string;
  explainer_links?: string[];
  markdown_fields?: string[];
  [key: string]: unknown;
};

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

  disconnectedCallback() {
    super.disconnectedCallback();
    if (this._copiedTimeout) {
      clearTimeout(this._copiedTimeout);
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
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
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
          font-size: var(--h3-font-size, 1.25rem);
          font-weight: 600;
          margin: 0;
          line-height: 1.3;
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

        .heading-anchor-link:hover,
        .heading-anchor-link:focus-visible {
          background-color: var(--light-accent-color);
          color: var(--default-color);
          outline: 2px solid var(--primary-button-background);
          outline-offset: 2px;
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

        .feature-links-section {
          display: flex;
          flex-direction: column;
          gap: var(--content-padding-quarter);
          border-top: var(--default-border);
          padding-top: var(--content-padding-half);
        }

        .feature-link-item {
          display: inline-flex;
          align-items: center;
          gap: var(--content-padding-quarter);
          max-width: 100%;
          text-decoration: underline;
          text-underline-offset: 2px;
          font-size: var(--button-small-font-size, 0.875rem);
        }

        .link-text {
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
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

  async handleAnchorCopy(e: Event) {
    e.preventDefault();
    if (!this.feature) return;

    const anchor = `#feature-${this.feature.id}`;
    const fullUrl = new URL(anchor, window.location.href).href;

    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(fullUrl);
        if (this._copiedTimeout) {
          clearTimeout(this._copiedTimeout);
        }
        this.isCopied = true;
        this._copiedTimeout = setTimeout(() => {
          this.isCopied = false;
        }, 2000);
      }
    } catch (err) {
      console.warn('Could not copy anchor link to clipboard:', err);
    }
  }

  handleReviewClick() {
    this.dispatchEvent(
      new CustomEvent('review-click', {
        detail: {
          feature: this.feature,
          suggestion: this.suggestion,
          featureId: this.feature?.id,
        },
        bubbles: true,
        composed: true,
      })
    );
  }

  handleGenerateClick() {
    this.dispatchEvent(
      new CustomEvent('generate-click', {
        detail: {
          feature: this.feature,
          featureId: this.feature?.id,
        },
        bubbles: true,
        composed: true,
      })
    );
  }

  renderCategoryBadge(): TemplateResult | typeof nothing {
    if (!this.feature) return nothing;
    let categoryName = this.feature.category_name;
    if (!categoryName && typeof this.feature.category === 'string') {
      categoryName = this.feature.category;
    } else if (!categoryName && typeof this.feature.category === 'number') {
      const entry = Object.values(FEATURE_CATEGORIES).find(
        ([val]) => val === this.feature!.category
      );
      categoryName = entry ? entry[1] : '';
    }
    if (!categoryName) return nothing;

    return html`<sl-badge variant="neutral" pill>${categoryName}</sl-badge>`;
  }

  renderProvenanceBadge(): TemplateResult | typeof nothing {
    if (!this.feature) return nothing;

    if (
      this.suggestion &&
      this.suggestion.status === SummarySuggestionStatusEnum.PENDING
    ) {
      return html`<sl-badge variant="warning" pill
        >AI Review Pending</sl-badge
      >`;
    }

    if (this.feature.summary_source === 'AI_APPLIED') {
      return html`<sl-badge variant="success" pill>AI Applied</sl-badge>`;
    }

    return html`<sl-badge variant="neutral" pill>Human Authored</sl-badge>`;
  }

  renderDocLinks(): TemplateResult | typeof nothing {
    if (!this.feature) return nothing;

    const links: string[] = [];

    if (Array.isArray(this.feature.doc_links)) {
      links.push(...this.feature.doc_links);
    }
    if (this.feature.spec_link && !links.includes(this.feature.spec_link)) {
      links.push(this.feature.spec_link);
    }
    if (Array.isArray(this.feature.explainer_links)) {
      for (const link of this.feature.explainer_links) {
        if (!links.includes(link)) {
          links.push(link);
        }
      }
    }
    if (
      this.suggestion?.suggested_doc_links &&
      Array.isArray(this.suggestion.suggested_doc_links)
    ) {
      for (const link of this.suggestion.suggested_doc_links) {
        if (!links.includes(link)) {
          links.push(link);
        }
      }
    }

    if (links.length === 0) return nothing;

    return html`
      <div class="feature-links-section" aria-label="Documentation links">
        ${links.map(
          link => html`
            <a
              class="feature-link-item"
              href=${link}
              target="_blank"
              rel="noopener noreferrer"
              title=${link}
            >
              <span class="link-text">${link}</span>
              <sl-icon name="box-arrow-up-right"></sl-icon>
            </a>
          `
        )}
      </div>
    `;
  }

  renderReviewActions(): TemplateResult | typeof nothing {
    if (!this.reviewMode || !this.feature) return nothing;

    const hasPendingSuggestion =
      this.suggestion &&
      this.suggestion.status === SummarySuggestionStatusEnum.PENDING;

    return html`
      <div class="card-actions">
        <div class="action-buttons">
          ${
            hasPendingSuggestion
              ? html`
                  <sl-button
                    size="small"
                    variant="primary"
                    class="review-button"
                    @click=${this.handleReviewClick}
                  >
                    <sl-icon slot="prefix" name="pencil"></sl-icon>
                    Review Suggestion
                  </sl-button>
                `
              : html`
                  <sl-button
                    size="small"
                    variant="default"
                    class="review-button"
                    @click=${this.handleReviewClick}
                  >
                    <sl-icon slot="prefix" name="eye"></sl-icon>
                    Inspect / Edit
                  </sl-button>
                `
          }
          <sl-button
            size="small"
            variant="default"
            class="generate-button"
            @click=${this.handleGenerateClick}
          >
            <sl-icon slot="prefix" name="arrow-clockwise"></sl-icon>
            ${hasPendingSuggestion ? 'Regenerate' : 'Generate AI Summary'}
          </sl-button>
        </div>

        ${
          this.suggestion?.reasoning
            ? html`
                <div class="suggestion-meta">
                  <sl-tooltip content=${this.suggestion.reasoning}>
                    <sl-icon
                      tabindex="0"
                      name="info-circle"
                      aria-label="Summary reasoning details"
                    ></sl-icon>
                  </sl-tooltip>
                  <span>Grounding available</span>
                </div>
              `
            : nothing
        }
      </div>
    `;
  }

  render() {
    if (!this.feature) {
      return nothing;
    }

    const isMarkdown = Boolean(
      this.feature.markdown_fields?.includes('summary')
    );
    const formattedSummary = autolink(this.feature.summary, [], isMarkdown);

    return html`
      <article
        class="feature-card"
        id="feature-${this.feature.id}"
        aria-labelledby="feature-title-${this.feature.id}"
      >
        <header class="card-header">
          <div class="title-wrapper">
            <h3 class="feature-title" id="feature-title-${this.feature.id}">
              <a class="feature-name" href="/feature/${this.feature.id}">
                ${this.feature.name}
              </a>
            </h3>
            <a
              class="heading-anchor-link ${this.isCopied ? 'copied' : ''}"
              href="#feature-${this.feature.id}"
              aria-label="Copy link to ${this.feature.name}"
              title="Copy link to feature"
              data-anchor="#feature-${this.feature.id}"
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
          </div>
        </header>

        <div class="feature-summary">${formattedSummary}</div>

        ${this.renderDocLinks()} ${this.renderReviewActions()}
      </article>
    `;
  }
}
