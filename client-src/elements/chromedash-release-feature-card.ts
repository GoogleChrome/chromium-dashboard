import {LitElement, css, html, nothing} from 'lit';
import {customElement, property, state} from 'lit/decorators.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {User, Feature, SuggestionData} from '../js-src/cs-client.js';
import './chromedash-feature-suggestion-status.js';
import '@shoelace-style/shoelace/dist/components/tag/tag.js';

@customElement('chromedash-release-feature-card')
export class ChromedashReleaseFeatureCard extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        .feature-card {
          background: var(--card-background);
          border: var(--card-border);
          border-radius: 8px;
          padding: var(--content-padding);
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          transition: box-shadow 0.2s ease;
          margin-bottom: var(--content-padding-half);
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

        .feature-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 0.5rem;
        }

        .feature-title {
          font-size: 1.1rem;
          font-weight: 600;
          color: var(--sl-color-primary-600);
          text-decoration: none;
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .feature-title:hover {
          text-decoration: underline;
        }

        .feature-summary {
          color: var(--sl-color-neutral-600);
          font-size: 0.95rem;
          line-height: 1.4;
          margin-bottom: 0.5rem;
        }

        .baseline-badge {
          font-size: 0.8rem;
          padding: 2px 6px;
          display: inline-flex;
          align-items: center;
          gap: 4px;
        }

        .baseline-badge-icon {
          width: 12px;
          height: 12px;
        }

        .doc-links-list {
          margin: 0.25rem 0 0 1.25rem;
          padding: 0;
          color: var(--sl-color-neutral-600);
          font-size: 0.9rem;
        }

        .doc-links-list a {
          color: var(--sl-color-primary-600);
          text-decoration: none;
        }

        .doc-links-list a:hover {
          text-decoration: underline;
        }
      `,
    ];
  }

  @property({type: Object})
  feature!: Feature;

  @property({attribute: false})
  user!: User;

  @state()
  suggestion: SuggestionData | null = null;

  canUserEditFeature(feature: Feature) {
    if (!this.user?.email) return false;
    const email = this.user.email;
    return (
      (feature.owner_emails || []).includes(email) ||
      (feature.editor_emails || []).includes(email) ||
      feature.creator_email === email
    );
  }

  handleSuggestionLoaded(e: CustomEvent<{suggestion: SuggestionData}>) {
    this.suggestion = e.detail.suggestion;
  }

  handleReviewSuggestion(e: CustomEvent) {
    e.stopPropagation();
    // Intercept and enrich the event with our loaded suggestion before bubbling it up!
    this.dispatchEvent(
      new CustomEvent('review-suggestion', {
        detail: {feature: this.feature, suggestion: this.suggestion},
        bubbles: true,
        composed: true,
      })
    );
  }

  renderBaselineBadge() {
    if (
      !this.suggestion ||
      !this.suggestion.baseline_status ||
      this.suggestion.baseline_status === 'none'
    ) {
      return nothing;
    }

    const isApplied = this.suggestion.status === 'applied';
    const canReview = !!(
      this.user?.can_review_release_notes ||
      this.canUserEditFeature(this.feature)
    );

    // Public users should ONLY see approved/applied baseline badges!
    if (!isApplied && !canReview) {
      return nothing;
    }

    let label = '';
    let variant = '';
    let iconSrc = '';

    switch (this.suggestion.baseline_status) {
      case 'widely':
        label = 'Baseline Widely Available';
        variant = 'success';
        iconSrc = '/static/img/baseline-widely-icon.svg';
        break;
      case 'newly':
        label = 'Baseline Newly Available';
        variant = 'primary';
        iconSrc = '/static/img/baseline-newly-icon.svg';
        break;
      case 'limited':
        label = 'Baseline Limited';
        variant = 'warning';
        iconSrc = '/static/img/baseline-limited-icon.svg';
        break;
      default:
        return nothing;
    }

    // If it is a draft suggestion and the user is an editor, render with dashed styling!
    if (!isApplied && canReview) {
      return html`
        <sl-tag
          variant=${variant}
          size="small"
          class="baseline-badge baseline-badge-suggested"
          pill
          style="border-style: dashed; border-width: 1.5px; background: transparent;"
        >
          <img src="${iconSrc}" class="baseline-badge-icon" alt="" />
          <strong>Suggested:</strong> ${label}
        </sl-tag>
      `;
    }

    return html`
      <sl-tag variant=${variant} size="small" class="baseline-badge" pill>
        <img src="${iconSrc}" class="baseline-badge-icon" alt="" />
        ${label}
      </sl-tag>
    `;
  }

  render() {
    const docs = this.feature.resources?.docs || [];
    const featureUrl = `/feature/${this.feature.id}`;

    return html`
      <div class="feature-card" data-testid="feature-card-${this.feature.id}">
        <div class="feature-info">
          <div class="feature-header">
            <div>
              <h4 class="feature-title">
                <a href=${featureUrl}>${this.feature.name}</a>
                ${this.renderBaselineBadge()}
              </h4>
              <div style="margin-top: 0.5rem;">
                <strong>Blink Components:</strong>
                ${this.feature.blink_components?.join(', ') || 'None'}
              </div>
            </div>
          </div>
          <p class="feature-summary">
            ${this.feature.summary || html`<em>No summary provided.</em>`}
          </p>
          ${docs.length > 0
            ? html`
                <strong>Documentation links:</strong>
                <ul class="doc-links-list">
                  ${docs.map(
                    link =>
                      html`<li>
                        <a href=${link} target="_blank">${link}</a>
                      </li>`
                  )}
                </ul>
              `
            : nothing}
        </div>
        <chromedash-feature-suggestion-status
          .feature=${this.feature}
          .canReview=${this.user?.can_review_release_notes ||
          this.canUserEditFeature(this.feature)}
          @suggestion-loaded=${this.handleSuggestionLoaded}
          @review-suggestion=${this.handleReviewSuggestion}
        ></chromedash-feature-suggestion-status>
      </div>
    `;
  }

  refreshSuggestion() {
    const statusComponent = this.shadowRoot?.querySelector(
      'chromedash-feature-suggestion-status'
    ) as any;
    if (statusComponent) {
      statusComponent.refresh();
    }
  }
}
