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

import {LitElement, css, html, nothing} from 'lit';
import {customElement, property, state, query} from 'lit/decorators.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {User, Feature, SuggestionData} from '../js-src/cs-client.js';
import {showToastMessage, updateURLParams, parseRawQuery} from './utils.js';
import './chromedash-summary-review-dialog.js';
import {ChromedashSummaryReviewDialog} from './chromedash-summary-review-dialog.js';
import './chromedash-release-feature-card.js';
import '@shoelace-style/shoelace/dist/components/spinner/spinner.js';
import '@shoelace-style/shoelace/dist/components/button/button.js';
import '@shoelace-style/shoelace/dist/components/tag/tag.js';
import '@shoelace-style/shoelace/dist/components/skeleton/skeleton.js';
import '@shoelace-style/shoelace/dist/components/select/select.js';
import '@shoelace-style/shoelace/dist/components/option/option.js';
import '@shoelace-style/shoelace/dist/components/alert/alert.js';
import '@shoelace-style/shoelace/dist/components/icon/icon.js';

interface MilestoneChannel {
  version: number;
}

interface MilestoneChannels {
  stable: MilestoneChannel;
  beta: MilestoneChannel;
  dev: MilestoneChannel;
}

@customElement('chromedash-releases-page')
export class ChromedashReleasesPage extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        .releases-container {
          padding: 1.5rem;
          max-width: 1000px;
          margin: 0 auto;
        }
        .header-nav {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 2rem;
          gap: 1rem;
        }
        @media (max-width: 768px) {
          .header-nav {
            flex-direction: column;
            gap: 1.5rem;
          }
        }
        .category-header {
          font-size: 1.5rem;
          font-weight: 500;
          color: var(--sl-color-neutral-800);
          margin: 2rem 0 1rem;
          border-bottom: 2px solid var(--sl-color-neutral-200);
          padding-bottom: 0.5rem;
        }
        .feature-card {
          background: var(--card-background);
          border: var(--card-border);
          border-radius: var(--default-border-radius);
          padding: 1.5rem;
          margin-bottom: 1.5rem;
          box-shadow: var(--card-box-shadow);
        }
        .feature-header {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          margin-bottom: 1rem;
        }
        .feature-title {
          font-size: 1.4rem;
          margin: 0;
          font-weight: 500;
          display: flex;
          align-items: center;
        }
        .doc-links-list {
          margin: 0.5rem 0 0;
          padding-left: 1.2rem;
        }
        .baseline-badge {
          margin-left: 10px;
          display: inline-flex;
          align-items: center;
          gap: 4px;
        }
        .baseline-badge-icon {
          width: 12px;
          height: 12px;
          display: inline-block;
        }
        .suggestion-control-panel {
          margin-top: 1rem;
          padding-top: 1rem;
          border-top: 1px dashed var(--sl-color-neutral-200);
          display: flex;
          align-items: center;
          gap: 1rem;
        }
        .reviews-header-container {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 2rem;
          gap: 1rem;
        }
        @media (max-width: 768px) {
          .reviews-header-container {
            flex-direction: column;
            align-items: flex-start;
            gap: 1.5rem;
          }
        }
        .reviews-title {
          margin: 0;
          font-size: 1.6rem;
          font-weight: 500;
        }
        .reviews-subtitle {
          margin: 0.5rem 0 0;
          color: var(--sl-color-neutral-600);
          font-size: 0.95rem;
        }
        .milestone-selector-container {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }
        .milestone-select-elem {
          width: 130px;
        }
        .pending-reviews-btn {
          margin-left: 1rem;
        }
      `,
    ];
  }

  @property({attribute: false})
  user!: User;
  @state()
  selectedMilestone!: number;
  @state()
  featuresByType: {[key: string]: Feature[]} = {};
  @state()
  loading = true;
  @state()
  activeReviewSuggestion: SuggestionData | null = null;
  @state()
  milestonesList: number[] = [];
  @state()
  channels: MilestoneChannels | null = null;

  @state()
  activeReviewFeature: Feature | null = null;

  @query('#review-dialog')
  reviewDialogEl!: ChromedashSummaryReviewDialog;

  connectedCallback() {
    super.connectedCallback();
    void this.initMilestone();
  }

  disconnectedCallback() {
    super.disconnectedCallback();
  }

  async initMilestone() {
    this.loading = true;
    try {
      const channels = await window.csClient.getChannels();
      this.channels = channels;
      const stableVersion = channels.stable.version;

      // Generate milestones list for the dropdown navigation (stable - 5 to stable + 5)
      this.milestonesList = Array.from(
        {length: 11},
        (_, i) => stableVersion - 5 + i
      );

      const queryParams = parseRawQuery(window.location.search);
      if (queryParams.milestone) {
        this.selectedMilestone = parseInt(queryParams.milestone, 10);
      } else {
        this.selectedMilestone = stableVersion;
        updateURLParams('milestone', this.selectedMilestone.toString());
      }
      await this.fetchMilestoneData();
    } catch {
      showToastMessage('Failed to initialize releases page.');
    } finally {
      this.loading = false;
    }
  }

  canUserEditFeature(feature: Feature) {
    if (!this.user?.email) return false;
    const email = this.user.email;
    return (
      feature.owner_emails?.includes(email) ||
      feature.editor_emails?.includes(email) ||
      feature.creator_email === email
    );
  }

  async fetchMilestoneData() {
    const rawFeatures = await window.csClient.getFeaturesInMilestone(
      this.selectedMilestone
    );

    // Normalize basic features to include verbose role keys for self-contained consistency
    for (const category of Object.keys(rawFeatures)) {
      rawFeatures[category] = rawFeatures[category].map(f => ({
        ...f,
        owner_emails: f.owner_emails || f.owners || [],
        editor_emails: f.editor_emails || f.editors || [],
        creator_email: f.creator_email || f.creator,
      }));
    }
    this.featuresByType = rawFeatures;

    // Stop page loading block immediately
    this.loading = false;
  }

  async navigateMilestone(direction: number) {
    this.selectedMilestone += direction;
    updateURLParams('milestone', this.selectedMilestone.toString());
    this.loading = true;
    try {
      await this.fetchMilestoneData();
    } catch {
      showToastMessage('Failed to fetch milestone features.');
    } finally {
      this.loading = false;
    }
  }

  handleMilestoneSelectChange(e: Event) {
    const target = e.target;
    if (target && 'value' in target) {
      this.selectedMilestone = parseInt(String(target.value), 10);
      updateURLParams('milestone', this.selectedMilestone.toString());
      this.loading = true;
      this.fetchMilestoneData()
        .catch(() => showToastMessage('Failed to fetch milestone features.'))
        .finally(() => (this.loading = false));
    }
  }

  handleReviewSuggestion(
    e: CustomEvent<{feature: Feature; suggestion: SuggestionData}>
  ) {
    const {feature, suggestion} = e.detail;
    this.activeReviewFeature = feature;
    this.activeReviewSuggestion = suggestion;
    void this.openReviewDialog();
  }

  async openReviewDialog() {
    await this.updateComplete;
    this.reviewDialogEl.show();
  }

  handleSuggestionApplied(e: CustomEvent<{summary: string; links: string[]}>) {
    if (!this.activeReviewFeature) return;
    const {summary, links} = e.detail;

    this.activeReviewFeature.summary = summary;
    if (!this.activeReviewFeature.resources) {
      this.activeReviewFeature.resources = {docs: [], samples: []};
    }
    this.activeReviewFeature.resources.docs = links;

    // Trigger card component refresh for live sync!
    const card = this.renderRoot.querySelector(
      `[data-testid="feature-card-${this.activeReviewFeature.id}"]`
    ) as any;
    if (card) {
      card.refreshSuggestion();
    }

    this.dispatchEvent(
      new CustomEvent('refetch-needed', {
        bubbles: true,
        composed: true,
      })
    );
  }

  handleSuggestionDiscarded() {
    if (!this.activeReviewFeature) return;
    const card = this.renderRoot.querySelector(
      `[data-testid="feature-card-${this.activeReviewFeature.id}"]`
    ) as any;
    if (card) {
      card.refreshSuggestion();
    }

    this.dispatchEvent(
      new CustomEvent('refetch-needed', {
        bubbles: true,
        composed: true,
      })
    );
  }

  renderFeature(feature: Feature) {
    return html`
      <chromedash-release-feature-card
        .feature=${feature}
        .user=${this.user}
        @review-suggestion=${this.handleReviewSuggestion}
      ></chromedash-release-feature-card>
    `;
  }

  renderCategoryGroup(category: string, features: Feature[]) {
    if (features.length === 0) return nothing;
    return html`
      <h3 class="category-header">${category}</h3>
      ${features.map(f => this.renderFeature(f))}
    `;
  }

  renderMilestoneChannelBanner() {
    if (!this.channels) return nothing;

    let bannerText = '';
    let variant = 'primary';
    let iconName = 'info-circle';

    if (this.selectedMilestone === this.channels.stable.version) {
      bannerText = `Chrome ${this.selectedMilestone} is now available on the Stable channel.`;
      variant = 'success';
      iconName = 'check-circle';
    } else if (this.selectedMilestone === this.channels.beta.version) {
      bannerText = `Chrome ${this.selectedMilestone} is currently in Beta. Feature owners should review and apply summary suggestions.`;
      variant = 'warning';
      iconName = 'exclamation-triangle';
    } else if (this.selectedMilestone === this.channels.dev.version) {
      bannerText = `Chrome ${this.selectedMilestone} is currently on the Dev channel under active development.`;
      variant = 'primary';
      iconName = 'info-circle';
    }

    if (!bannerText) return nothing;

    return html`
      <sl-alert variant=${variant} open style="margin-bottom: 1.5rem;">
        <sl-icon slot="icon" name=${iconName}></sl-icon>
        <strong>${bannerText}</strong>
      </sl-alert>
    `;
  }

  render() {
    if (this.loading) {
      return html`
        <div
          class="releases-container"
          style="text-align: center; margin-top: 5rem;"
        >
          <sl-spinner style="font-size: 3rem;"></sl-spinner>
          <p>Loading features for Chrome ${this.selectedMilestone}...</p>
        </div>
      `;
    }

    const hasAnyFeatures = Object.values(this.featuresByType).some(
      list => list.length > 0
    );

    return html`
      <div class="releases-container">
        ${this.renderMilestoneChannelBanner()}
        <div class="header-nav">
          <sl-button @click=${() => this.navigateMilestone(-1)}>
            &larr; Chrome ${this.selectedMilestone - 1}
          </sl-button>

          <div class="milestone-selector-container">
            <h2>Chrome</h2>
            <sl-select
              .value=${this.selectedMilestone.toString()}
              @sl-change=${this.handleMilestoneSelectChange}
              class="milestone-select-elem"
            >
              ${this.milestonesList.map(
                m => html` <sl-option value=${m.toString()}>${m}</sl-option> `
              )}
            </sl-select>
            <h2>Releases</h2>
          </div>

          <sl-button @click=${() => this.navigateMilestone(1)}>
            Chrome ${this.selectedMilestone + 1} &rarr;
          </sl-button>
        </div>
        ${!hasAnyFeatures
          ? html`<p>No features found in this milestone.</p>`
          : Object.keys(this.featuresByType).map(category =>
              this.renderCategoryGroup(category, this.featuresByType[category])
            )}
      </div>

      <!-- Refactored Modular Dialog component -->
      <chromedash-summary-review-dialog
        id="review-dialog"
        .user=${this.user}
        .feature=${this.activeReviewFeature}
        .suggestion=${this.activeReviewSuggestion}
        @applied=${this.handleSuggestionApplied}
        @discarded=${this.handleSuggestionDiscarded}
      ></chromedash-summary-review-dialog>
    `;
  }
}
