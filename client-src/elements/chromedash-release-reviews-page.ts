import {LitElement, css, html, nothing} from 'lit';
import {customElement, property, state, query} from 'lit/decorators.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {User, Feature, SuggestionData} from '../js-src/cs-client.js';
import {showToastMessage} from './utils.js';
import './chromedash-summary-review-dialog.js';
import {ChromedashSummaryReviewDialog} from './chromedash-summary-review-dialog.js';
import './chromedash-release-feature-card.js';
import '@shoelace-style/shoelace/dist/components/spinner/spinner.js';
import '@shoelace-style/shoelace/dist/components/button/button.js';
import '@shoelace-style/shoelace/dist/components/tag/tag.js';
import '@shoelace-style/shoelace/dist/components/skeleton/skeleton.js';
import '@shoelace-style/shoelace/dist/components/alert/alert.js';
import '@shoelace-style/shoelace/dist/components/icon/icon.js';

@customElement('chromedash-release-reviews-page')
export class ChromedashReleaseReviewsPage extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        .reviews-container {
          padding: var(--content-padding);
          max-width: 1000px;
          margin: 0 auto;
        }

        .dashboard-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: var(--content-padding);
          border-bottom: var(--card-border);
          padding-bottom: var(--content-padding-half);
        }

        .dashboard-header h2 {
          margin: 0;
          font-size: 1.8rem;
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .gemini-icon {
          width: 1.2em;
          height: 1.2em;
          transform-origin: center center;
          transition: transform 0.7s ease-in-out;
        }

        h2:hover .gemini-icon {
          transform: rotate(360deg);
        }

        .reviews-count-badge {
          background: var(--sl-color-neutral-100);
          color: var(--sl-color-neutral-700);
          font-size: 1rem;
          padding: 4px 10px;
          border-radius: 20px;
          font-weight: 600;
        }

        .category-group {
          margin-bottom: 2rem;
        }

        .category-title {
          font-size: 1.2rem;
          font-weight: 600;
          margin-bottom: 1rem;
          border-bottom: 1px solid var(--sl-color-neutral-200);
          padding-bottom: 4px;
          color: var(--sl-color-neutral-800);
        }

        .features-list {
          display: flex;
          flex-direction: column;
          gap: var(--content-padding-half);
        }

        .feature-card {
          background: var(--card-background);
          border: var(--card-border);
          border-radius: 8px;
          padding: var(--content-padding);
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          transition: box-shadow 0.2s ease;
        }

        .feature-card:hover {
          box-shadow: var(--card-box-shadow);
        }

        .feature-info {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .feature-title-row {
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .feature-title {
          font-size: 1.1rem;
          font-weight: 600;
          color: var(--sl-color-primary-600);
          text-decoration: none;
        }

        .feature-title:hover {
          text-decoration: underline;
        }

        .feature-summary {
          color: var(--sl-color-neutral-600);
          font-size: 0.95rem;
          line-height: 1.4;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }

        .empty-dashboard-state {
          text-align: center;
          padding: 3rem 1rem;
          color: var(--sl-color-neutral-500);
        }

        .empty-dashboard-state sl-icon {
          font-size: 3rem;
          margin-bottom: 1rem;
        }

        .skeleton-category {
          margin-bottom: 2rem;
        }

        .skeleton-card {
          background: var(--card-background);
          border: var(--card-border);
          border-radius: 8px;
          padding: var(--content-padding);
          display: flex;
          flex-direction: column;
          gap: 10px;
          margin-bottom: var(--content-padding-half);
        }

        .pagination-controls {
          display: flex;
          justify-content: center;
          align-items: center;
          gap: var(--content-padding);
          margin-top: 2rem;
          padding-top: 1rem;
          border-top: 1px solid var(--sl-color-neutral-100);
        }

        .pagination-info {
          font-weight: 500;
          color: var(--sl-color-neutral-600);
        }
      `,
    ];
  }

  @property({attribute: false})
  user!: User;

  @state()
  pendingFeatures: Feature[] = [];

  @state()
  currentPage = 1;

  @state()
  loading = true;

  @state()
  activeReviewSuggestion: SuggestionData | null = null;

  @state()
  activeReviewFeature: Feature | null = null;

  @query('#review-dialog')
  reviewDialogEl!: ChromedashSummaryReviewDialog;

  connectedCallback() {
    super.connectedCallback();
    void this.fetchPendingReviewsData();
  }

  async fetchPendingReviewsData() {
    this.loading = true;
    try {
      const resp = await window.csClient.getPendingReviews();
      this.pendingFeatures = resp.features;
      this.currentPage = 1;
    } catch {
      showToastMessage('Failed to load pending release reviews.');
    } finally {
      this.loading = false;
    }
  }

  canUserEditFeature(feature: Feature) {
    if (!this.user?.email) return false;
    const email = this.user.email;
    return (
      (feature.owner_emails || []).includes(email) ||
      (feature.editor_emails || []).includes(email) ||
      feature.creator_email === email
    );
  }

  handleReviewSuggestion(
    e: CustomEvent<{feature: Feature; suggestion: SuggestionData}>
  ) {
    const {feature, suggestion} = e.detail;
    this.activeReviewFeature = feature;
    this.activeReviewSuggestion = suggestion;
    void this.updateComplete.then(() => {
      if (this.reviewDialogEl) {
        this.reviewDialogEl.show();
      }
    });
  }

  handleApplied() {
    void this.fetchPendingReviewsData();
    showToastMessage('AI summary suggestion successfully applied!');
  }

  handleDiscarded() {
    void this.fetchPendingReviewsData();
    showToastMessage('AI summary suggestion discarded.');
  }

  renderSkeletons() {
    return html`
      <div class="skeleton-category">
        <sl-skeleton
          effect="sheen"
          style="width: 150px; height: 24px; margin-bottom: 1rem;"
        ></sl-skeleton>
        <div class="skeleton-card">
          <sl-skeleton
            effect="sheen"
            style="width: 40%; height: 20px;"
          ></sl-skeleton>
          <sl-skeleton
            effect="sheen"
            style="width: 85%; height: 14px;"
          ></sl-skeleton>
          <sl-skeleton
            effect="sheen"
            style="width: 60%; height: 14px;"
          ></sl-skeleton>
        </div>
        <div class="skeleton-card">
          <sl-skeleton
            effect="sheen"
            style="width: 30%; height: 20px;"
          ></sl-skeleton>
          <sl-skeleton
            effect="sheen"
            style="width: 90%; height: 14px;"
          ></sl-skeleton>
          <sl-skeleton
            effect="sheen"
            style="width: 45%; height: 14px;"
          ></sl-skeleton>
        </div>
      </div>
    `;
  }

  renderFeatureCard(feature: Feature) {
    return html`
      <chromedash-release-feature-card
        .feature=${feature}
        .user=${this.user}
        @review-suggestion=${this.handleReviewSuggestion}
      ></chromedash-release-feature-card>
    `;
  }

  render() {
    const totalReviews = this.pendingFeatures.length;
    const ITEMS_PER_PAGE = 10;
    const totalPages = Math.ceil(totalReviews / ITEMS_PER_PAGE) || 1;

    // Slice features for current page
    const startIndex = (this.currentPage - 1) * ITEMS_PER_PAGE;
    const endIndex = startIndex + ITEMS_PER_PAGE;
    const paginatedFeatures = this.pendingFeatures.slice(startIndex, endIndex);

    return html`
      <div class="reviews-container">
        <div class="dashboard-header">
          <h2>
            <img
              class="gemini-icon"
              src="https://www.gstatic.com/images/branding/productlogos/gemini_2025/v1/192px.svg"
              alt="Gemini AI Logo"
            />
            AI-Assisted Release Reviews Pending
            ${totalReviews > 0
              ? html`<span
                  class="reviews-count-badge"
                  data-testid="reviews-count"
                  >${totalReviews} pending</span
                >`
              : nothing}
          </h2>
        </div>

        ${this.loading
          ? this.renderSkeletons()
          : totalReviews === 0
            ? html`
                <div
                  class="empty-dashboard-state"
                  data-testid="empty-dashboard"
                >
                  <sl-icon name="check-circle" class="text-success"></sl-icon>
                  <p>
                    All clear! There are no release reviews pending your
                    attention.
                  </p>
                </div>
              `
            : html`
                <div class="features-list">
                  ${paginatedFeatures.map(f => this.renderFeatureCard(f))}
                </div>

                <!-- Pagination Controls -->
                ${totalPages > 1
                  ? html`
                      <div class="pagination-controls" data-testid="pagination">
                        <sl-button
                          size="small"
                          ?disabled=${this.currentPage === 1 || this.loading}
                          @click=${() => {
                            this.currentPage--;
                          }}
                        >
                          <sl-icon name="chevron-left" slot="prefix"></sl-icon>
                          Previous
                        </sl-button>
                        <span
                          class="pagination-info"
                          data-testid="pagination-info"
                        >
                          Page ${this.currentPage} of ${totalPages}
                        </span>
                        <sl-button
                          size="small"
                          ?disabled=${this.currentPage === totalPages ||
                          this.loading}
                          @click=${() => {
                            this.currentPage++;
                          }}
                        >
                          Next
                          <sl-icon name="chevron-right" slot="suffix"></sl-icon>
                        </sl-button>
                      </div>
                    `
                  : nothing}
              `}
      </div>

      <chromedash-summary-review-dialog
        id="review-dialog"
        .feature=${this.activeReviewFeature}
        .suggestion=${this.activeReviewSuggestion}
        .user=${this.user}
        @applied=${this.handleApplied}
        @discarded=${this.handleDiscarded}
      ></chromedash-summary-review-dialog>
    `;
  }
}
