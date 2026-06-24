import {LitElement, css, html, nothing} from 'lit';
import {customElement, property} from 'lit/decorators.js';
import {Task} from '@lit/task';
import {SHARED_STYLES} from '../css/shared-css.js';
import {SuggestionData} from '../js-src/cs-client.js';

@customElement('chromedash-feature-suggestion-status')
export class ChromedashFeatureSuggestionStatus extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        .suggestion-control-panel {
          margin-top: var(--content-padding-half);
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .gemini-icon {
          width: 1.4em;
          height: 1.4em;
          transform-origin: center center;
          transition: transform 0.7s ease-in-out;
        }

        sl-button:hover .gemini-icon {
          transform: rotate(360deg);
        }
      `,
    ];
  }

  @property({type: Object})
  feature!: any;

  @property({type: Boolean})
  canReview = false;

  private _pollingInterval?: number;

  private _suggestionTask = new Task(this, {
    task: async ([featureId], {signal}) => {
      const sug = await window.csClient.getSummarySuggestion(featureId);

      // Dispatch event to update parent state (for header baseline badge)
      this.dispatchEvent(
        new CustomEvent('suggestion-loaded', {
          detail: {featureId, suggestion: sug},
          bubbles: true,
          composed: true,
        })
      );

      if (sug.status === 'in_progress') {
        this.startPolling();
      } else {
        this.stopPolling();
      }
      return sug;
    },
    args: () => [this.feature.id],
  });

  startPolling() {
    if (this._pollingInterval) return;
    this._pollingInterval = window.setInterval(() => {
      this._suggestionTask.run();
    }, 2000); // Fast poll every 2 seconds
  }

  stopPolling() {
    if (this._pollingInterval) {
      window.clearInterval(this._pollingInterval);
      this._pollingInterval = undefined;
    }
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    this.stopPolling();
  }

  async triggerGeneration() {
    try {
      await window.csClient.triggerSummaryGeneration(this.feature.id);
      this._suggestionTask.run(); // Instantly rerun task to enter 'in_progress' state
    } catch (err) {
      console.error(err);
    }
  }

  renderBadge(status: string) {
    switch (status) {
      case 'in_progress':
        return html`
          <sl-tag variant="warning" pill>
            <sl-spinner
              style="font-size: 10px; margin-right: 5px;"
            ></sl-spinner>
            Generating
          </sl-tag>
        `;
      case 'complete':
        return html`<sl-tag variant="success" pill>Draft Available</sl-tag>`;
      case 'applied':
        return html`<sl-tag variant="primary" pill>Applied</sl-tag>`;
      case 'discarded':
        return html`<sl-tag variant="neutral" pill>Discarded</sl-tag>`;
      case 'failed':
        return html`<sl-tag variant="danger" pill>Failed</sl-tag>`;
      default:
        return nothing;
    }
  }

  getActiveSuggestionsCount(sug: SuggestionData | null) {
    if (!sug) return 0;
    let count = 0;

    // 1. Check summary
    if (
      sug.suggested_summary &&
      sug.suggested_summary !== this.feature.summary
    ) {
      count++;
    }

    // 2. Check baseline status
    if (sug.baseline_status && sug.baseline_status !== 'none') {
      count++;
    }

    // 3. Check new doc links
    const originalLinks = this.feature.resources?.docs || [];
    const suggestedLinks = sug.suggested_doc_links || [];
    const newLinks = suggestedLinks.filter(
      link => !originalLinks.includes(link)
    );
    if (newLinks.length > 0) {
      count++;
    }

    return count;
  }

  getButtonText(sug: SuggestionData | null) {
    const count = this.getActiveSuggestionsCount(sug);
    if (count <= 1) {
      return 'Review Suggestion';
    }
    return `Review ${count} suggestions`;
  }

  renderGeminiIcon() {
    return html`
      <img
        slot="prefix"
        class="gemini-icon"
        src="https://www.gstatic.com/images/branding/productlogos/gemini_2025/v1/192px.svg"
        alt="Gemini AI Logo"
      />
    `;
  }

  render() {
    if (!this.canReview) return nothing;

    return this._suggestionTask.render({
      pending: () => html`
        <div class="suggestion-control-panel">
          <sl-skeleton
            effect="sheen"
            style="width: 150px; height: 24px;"
          ></sl-skeleton>
        </div>
      `,
      complete: sug => {
        const status = sug?.status || 'none';
        return html`
          <div class="suggestion-control-panel">
            <strong>AI Summary suggestion:</strong>
            ${this.renderBadge(status)}
            ${status === 'none' ||
            status === 'failed' ||
            status === 'discarded' ||
            status === 'in_progress'
              ? html`
                  <sl-button
                    size="small"
                    ?disabled=${status === 'in_progress'}
                    @click=${this.triggerGeneration}
                  >
                    ${this.renderGeminiIcon()} Generate Summary
                  </sl-button>
                `
              : nothing}
            ${status === 'complete'
              ? html`
                  <sl-button
                    size="small"
                    variant="primary"
                    @click=${() =>
                      this.dispatchEvent(
                        new CustomEvent('review-suggestion', {
                          detail: {feature: this.feature},
                          bubbles: true,
                          composed: true,
                        })
                      )}
                  >
                    ${this.renderGeminiIcon()} ${this.getButtonText(sug)}
                  </sl-button>
                `
              : nothing}
            ${status === 'applied'
              ? html`
                  <sl-button
                    size="small"
                    @click=${() =>
                      this.dispatchEvent(
                        new CustomEvent('review-suggestion', {
                          detail: {feature: this.feature},
                          bubbles: true,
                          composed: true,
                        })
                      )}
                  >
                    ${this.renderGeminiIcon()} Edit applied summary
                  </sl-button>
                `
              : nothing}
          </div>
        `;
      },
      error: () => html`<p>Error loading suggestions</p>`,
    });
  }

  refresh() {
    this._suggestionTask.run();
  }
}
