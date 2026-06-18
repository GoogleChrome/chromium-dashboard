import {LitElement, css, html, nothing} from 'lit';
import {customElement, property} from 'lit/decorators.js';
import {Task} from '@lit/task';
import {SHARED_STYLES} from '../css/shared-css.js';

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
                    Generate Summary
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
                    Review Suggestion
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
                    Edit applied summary
                  </sl-button>
                `
              : nothing}
          </div>
        `;
      },
      error: () => html`<p>Error loading suggestions</p>`,
    });
  }
}
