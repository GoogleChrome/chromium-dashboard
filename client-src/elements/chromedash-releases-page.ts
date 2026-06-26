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
import {live} from 'lit/directives/live.js';
import {Task} from '@lit/task';
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

@customElement('chromedash-release-notes-page')
export class ChromedashReleaseNotesPage extends LitElement {
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
          position: relative;
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }
        .combobox-wrapper {
          position: relative;
          display: inline-block;
        }
        .milestone-search-input {
          width: 100px;
          text-align: center;
          font-size: 1.2rem;
          font-weight: bold;
          padding: 0.25rem;
          border: 1px solid var(--sl-color-neutral-300);
          border-radius: 4px;
        }
        .milestone-options-dropdown {
          position: absolute;
          top: 100%;
          left: 0;
          right: 0;
          background: white;
          border: 1px solid var(--sl-color-neutral-300);
          border-radius: 4px;
          box-shadow: var(--sl-shadow-large);
          z-index: 100;
          max-height: 200px;
          overflow-y: auto;
          margin-top: 2px;
          min-width: 120px;
        }
        .milestone-option {
          padding: 0.5rem;
          cursor: pointer;
          border-bottom: 1px solid var(--sl-color-neutral-100);
          transition: background 0.1s ease;
        }
        .milestone-option:hover {
          background: var(--sl-color-neutral-50);
        }
        .milestone-option.selected {
          background: var(--sl-color-primary-50);
          font-weight: bold;
        }
        .milestone-option.selected:hover {
          background: var(--sl-color-primary-100);
        }
        .pending-reviews-btn {
          margin-left: 1rem;
        }
        
        /* New Scalable Navigation & Redirect Banner Styles */
        .header-nav-strip {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 2rem;
          gap: 1.5rem;
          flex-wrap: wrap;
        }
        .channel-quick-jumps {
          display: flex;
          gap: 0.5rem;
          align-items: center;
        }
        .channel-quick-jumps sl-button::part(base) {
          padding: 2px;
        }
        .milestone-selector-controls {
          display: flex;
          align-items: center;
          gap: 1rem;
        }
        .dropdown-no-results {
          padding: 1rem;
          text-align: center;
          color: var(--sl-color-neutral-600);
          font-size: 0.9rem;
        }
        .dropdown-no-results .error-icon {
          font-size: 1.5rem;
          color: var(--sl-color-danger-600);
          margin-bottom: 0.5rem;
          display: block;
          margin-left: auto;
          margin-right: auto;
        }
        .dropdown-no-results .error-text {
          font-weight: 500;
          display: block;
          margin-bottom: 0.25rem;
          color: var(--sl-color-neutral-800);
        }
        .dropdown-no-results .helper-text {
          font-size: 0.8rem;
          color: var(--sl-color-neutral-500);
        }
        .milestone-option {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 0.5rem;
        }
        .ms-badge {
          margin-left: auto;
        }
        .dcc-redirect-banner {
          display: flex;
          align-items: flex-start;
          gap: 1rem;
          background: var(--sl-color-primary-50);
          border: 1px solid var(--sl-color-primary-200);
          border-radius: var(--default-border-radius);
          padding: 1.5rem;
          margin-bottom: 2rem;
        }
        .banner-icon {
          font-size: 2.2rem;
          color: var(--sl-color-primary-600);
          margin-top: 0.2rem;
        }
        .banner-content {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
          align-items: flex-start;
        }
        .banner-title {
          font-size: 1.2rem;
          font-weight: bold;
          color: var(--sl-color-primary-900);
        }
        .banner-text {
          color: var(--sl-color-neutral-700);
          font-size: 0.95rem;
          margin-bottom: 0.5rem;
        }
        .banner-btn {
          margin-top: 0.2rem;
        }
        @media (max-width: 900px) {
          .header-nav-strip {
            flex-direction: column;
            align-items: center;
            gap: 1.5rem;
          }
        }
      `,
    ];
  }

  @property({attribute: false})
  user!: User;
  @state()
  selectedMilestone!: number;
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
  @state()
  showDropdown = false;
  @state()
  filterText = '';

  _featuresTask = new Task(this, {
    task: async ([milestone]) => {
      if (!milestone) return {};
      const rawFeatures = await window.csClient.getFeaturesInMilestone(milestone);
      
      // Normalize basic features to include verbose role keys for self-contained consistency
      for (const category of Object.keys(rawFeatures)) {
        rawFeatures[category] = rawFeatures[category].map(f => ({
          ...f,
          owner_emails: f.owner_emails || f.owners || [],
          editor_emails: f.editor_emails || f.editors || [],
          creator_email: f.creator_email || f.creator,
        }));
      }
      return rawFeatures;
    },
    args: () => [this.selectedMilestone],
  });

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
      const devVersion = channels.dev.version;

      // Generate all milestones from 1 to devVersion + 5 (sorted descending)
      const latestValidMilestone = devVersion + 5;
      this.milestonesList = Array.from(
        {length: latestValidMilestone},
        (_, i) => latestValidMilestone - i
      );

      const queryParams = parseRawQuery(window.location.search);
      if (queryParams.milestone) {
        this.selectedMilestone = parseInt(queryParams.milestone, 10);
      } else {
        this.selectedMilestone = stableVersion;
        updateURLParams('milestone', this.selectedMilestone.toString());
      }
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

  async navigateMilestone(direction: number) {
    this.selectedMilestone += direction;
    updateURLParams('milestone', this.selectedMilestone.toString());
  }

  handleMilestoneSelectChange(e: Event) {
    const target = e.target;
    if (target && 'value' in target) {
      this.selectedMilestone = parseInt(String(target.value), 10);
      updateURLParams('milestone', this.selectedMilestone.toString());
    }
  }

  handleSearchInput(e: Event) {
    const target = e.target as HTMLInputElement;
    if (target) {
      this.filterText = target.value;
      this.showDropdown = true;
    }
  }

  handleInputFocus() {
    this.showDropdown = true;
  }

  handleInputBlur() {
    setTimeout(() => {
      this.showDropdown = false;
    }, 150);
  }

  selectMilestone(m: number) {
    this.selectedMilestone = m;
    this.filterText = '';
    this.showDropdown = false;
    updateURLParams('milestone', this.selectedMilestone.toString());
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

    if (this.selectedMilestone < this.channels.stable.version - 5) {
      return html`
        <sl-alert variant="neutral" open style="margin-bottom: 1.5rem;">
          <sl-icon slot="icon" name="info-circle"></sl-icon>
          Looking for official historical logs? View the published
          <a href="https://developer.chrome.com/release-notes/${this.selectedMilestone}" target="_blank">
            Chrome ${this.selectedMilestone} Release Notes on developer.chrome.com
          </a>.
        </sl-alert>
      `;
    }

    let bannerText = '';
    let variant = 'primary';
    let iconName = 'info-circle';

    if (this.selectedMilestone === this.channels.stable.version) {
      bannerText = `Chrome ${this.selectedMilestone} is now available on the Stable channel.`;
      variant = 'success';
      iconName = 'check-circle';
    } else if (this.selectedMilestone === this.channels.beta?.version) {
      bannerText = `Chrome ${this.selectedMilestone} is currently in Beta. Feature owners should review and apply summary suggestions.`;
      variant = 'warning';
      iconName = 'exclamation-triangle';
    } else if (this.selectedMilestone === this.channels.dev?.version) {
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

    return html`
      <div class="releases-container">
        ${this.renderMilestoneChannelBanner()}
        <!-- Symmetrical Navigation Control Strip -->
        <div class="header-nav-strip">
          
          <!-- Left: Channel Quick-Jumps -->
          ${this.channels
            ? html`
                <div class="channel-quick-jumps">
                  <sl-button
                    size="small"
                    variant="neutral"
                    ?outline=${this.selectedMilestone !== this.channels.stable.version}
                    @click=${() => this.selectMilestone(this.channels!.stable.version)}
                  >
                    <sl-badge variant="success" pill>Stable: ${this.channels.stable.version}</sl-badge>
                  </sl-button>
                  <sl-button
                    size="small"
                    variant="neutral"
                    ?outline=${this.selectedMilestone !== this.channels.beta.version}
                    @click=${() => this.selectMilestone(this.channels!.beta.version)}
                  >
                    <sl-badge variant="warning" pill>Beta: ${this.channels.beta.version}</sl-badge>
                  </sl-button>
                  <sl-button
                    size="small"
                    variant="neutral"
                    ?outline=${this.selectedMilestone !== this.channels.dev.version}
                    @click=${() => this.selectMilestone(this.channels!.dev.version)}
                  >
                    <sl-badge variant="primary" pill>Dev: ${this.channels.dev.version}</sl-badge>
                  </sl-button>
                </div>
              `
            : nothing}

          <!-- Right: Milestone Selector Controls -->
          <div class="milestone-selector-controls">
            <sl-button size="small" @click=${() => this.navigateMilestone(-1)}>
              &larr; Chrome ${this.selectedMilestone - 1}
            </sl-button>

            <div class="milestone-selector-container">
              <h2>Chrome</h2>
              <div class="combobox-wrapper">
                <input
                  type="text"
                  class="milestone-search-input"
                  .value=${live(this.filterText !== '' ? this.filterText : this.selectedMilestone.toString())}
                  @input=${this.handleSearchInput}
                  @focus=${this.handleInputFocus}
                  @blur=${this.handleInputBlur}
                  placeholder="Search..."
                />
                
                ${this.showDropdown
                  ? html`
                      <div class="milestone-options-dropdown">
                        ${this.milestonesList.filter(m => m.toString().includes(this.filterText)).length === 0
                          ? html`
                              <div class="dropdown-no-results">
                                <sl-icon name="exclamation-triangle" class="error-icon"></sl-icon>
                                <span class="error-text">No milestone "<strong>${this.filterText}</strong>" found.</span>
                                <div class="helper-text">Valid milestones: 1 to ${this.milestonesList[0]}.</div>
                              </div>
                            `
                          : this.milestonesList
                              .filter(m => m.toString().includes(this.filterText))
                              .map(m => {
                                const isStable = m === this.channels?.stable.version;
                                const isBeta = m === this.channels?.beta.version;
                                const isDev = m === this.channels?.dev.version;
                                return html`
                                  <div
                                    class="milestone-option ${m === this.selectedMilestone ? 'selected' : ''}"
                                    @mousedown=${(e: Event) => {
                                      e.preventDefault();
                                    }}
                                    @click=${() => this.selectMilestone(m)}
                                  >
                                    <span>Chrome ${m}</span>
                                    ${isStable ? html`<sl-badge variant="success" size="small" class="ms-badge">Stable</sl-badge>` : nothing}
                                    ${isBeta ? html`<sl-badge variant="warning" size="small" class="ms-badge">Beta</sl-badge>` : nothing}
                                    ${isDev ? html`<sl-badge variant="primary" size="small" class="ms-badge">Dev</sl-badge>` : nothing}
                                  </div>
                                `;
                              })}
                      </div>
                    `
                  : nothing}
              </div>
              <h2>Releases</h2>
            </div>

            <sl-button size="small" @click=${() => this.navigateMilestone(1)}>
              Chrome ${this.selectedMilestone + 1} &rarr;
            </sl-button>
          </div>
        </div>

        <!-- Symmetrical Redirect Banner for Historical Milestones -->
        ${this.selectedMilestone < 120
          ? html`
              <div class="dcc-redirect-banner">
                <sl-icon name="journal-text" class="banner-icon"></sl-icon>
                <div class="banner-content">
                  <div class="banner-title">Looking for older release notes?</div>
                  <div class="banner-text">
                    Official editorial release notes for Chrome ${this.selectedMilestone} are hosted on the Chrome Developer Blog.
                  </div>
                  <sl-button href="https://developer.chrome.com/release-notes/${this.selectedMilestone}" target="_blank" variant="primary" size="small" pill class="banner-btn">
                    <sl-icon slot="prefix" name="box-arrow-up-right"></sl-icon>
                    View Chrome ${this.selectedMilestone} Release Notes on developer.chrome.com
                  </sl-button>
                </div>
              </div>
            `
          : nothing}

        ${this._featuresTask.render({
          pending: () => html`
            <div style="text-align: center; margin-top: 5rem;">
              <sl-spinner style="font-size: 2.5rem;"></sl-spinner>
              <p>Loading features for Chrome ${this.selectedMilestone}...</p>
            </div>
          `,
          complete: (featuresByType: any) => {
            const hasAnyFeatures = Object.values(featuresByType).some(
              (list: any) => list.length > 0
            );
            return !hasAnyFeatures
              ? html`<p>No features found in this milestone.</p>`
              : Object.keys(featuresByType).map(category =>
                  this.renderCategoryGroup(category, featuresByType[category])
                );
          },
          error: err => html`
            <div style="text-align: center; margin-top: 3rem; color: var(--sl-color-danger-600);">
              <p>Error loading features: ${err}</p>
            </div>
          `,
        })}
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
