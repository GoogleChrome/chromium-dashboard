import {LitElement, css, html, nothing} from 'lit';
import {showToastMessage} from './utils.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {VARS} from '../css/_vars-css.js';
import {LAYOUT_CSS} from '../css/_layout-css.js';
import {customElement, state} from 'lit/decorators.js';
import {FeatureLinksSummary, SampleFeatureLink} from '../js-src/cs-client.js';

@customElement('chromedash-admin-feature-links-page')
export class ChromedashAdminFeatureLinksPage extends LitElement {
  static get styles() {
    return [
      SHARED_STYLES,
      VARS,
      LAYOUT_CSS,
      css`
        .feature-links-summary .line {
          padding: var(--content-padding-half);
          display: flex;
          align-items: center;
          justify-content: space-between;
          font-size: 16px;
        }
        .feature-links-samples .line {
          background: rgb(232, 234, 237);
        }
        sl-icon-button::part(base) {
          padding: 0;
          margin-left: 8px;
        }
      `,
    ];
  }

  @state()
  sampleId = '';
  @state()
  samplesLoading = false;
  @state()
  loading = true;
  @state()
  featureLinksSamples: SampleFeatureLink[] = [];
  @state()
  featureLinksSummary!: FeatureLinksSummary;

  connectedCallback() {
    super.connectedCallback();
    this.fetchData();
  }

  async fetchData() {
    try {
      this.loading = true;
      this.featureLinksSummary = await window.csClient.getFeatureLinksSummary();
    } catch {
      showToastMessage(
        'Some errors occurred. Please refresh the page or try again later.'
      );
    } finally {
      this.loading = false;
    }
  }

  calcSampleId(domain, type, isError) {
    return `domain=${domain}&type=${type}&isError=${isError}`;
  }

  async fetchLinkSamples(domain, type, isError) {
    this.sampleId = this.calcSampleId(domain, type, isError);
    this.featureLinksSamples = [];
    this.samplesLoading = true;
    try {
      this.featureLinksSamples = await window.csClient.getFeatureLinksSamples(
        domain,
        type,
        isError
      );
    } catch {
      showToastMessage(
        'Some errors occurred. Please refresh the page or try again later.'
      );
    } finally {
      this.samplesLoading = false;
    }
  }

  renderSamples() {
    if (this.samplesLoading) {
      return html`<sl-spinner></sl-spinner>`;
    }
    return html`
      <div class="feature-links-samples">
        ${this.featureLinksSamples.map(
          sample => html`
            <div class="line">
              <div>
                <a href=${sample.url}><i>${sample.url}</i></a>
                ${sample.http_error_code
                  ? html`<i>(${sample.http_error_code})</i>`
                  : nothing}
              </div>
              <a
                href=${`/feature/${sample.feature_ids}`}
                target="_blank"
                rel="noopener"
              >
                <sl-icon
                  library="material"
                  name="link"
                  slot="prefix"
                  title="linked feature"
                ></sl-icon>
              </a>
            </div>
          `
        )}
      </div>
    `;
  }

  renderComponents() {
    return html`
      <div class="feature-links-summary">
        <sl-details summary="Link Summary" open>
          <div class="line">
            All Links <b>${this.featureLinksSummary.total_count}</b>
          </div>
          <div class="line">
            Covered Links <b>${this.featureLinksSummary.covered_count}</b>
          </div>
          <div class="line">
            Uncovered (aka "web") Links
            <b>${this.featureLinksSummary.uncovered_count}</b>
          </div>
          <div class="line">
            All Error Links<b>${this.featureLinksSummary.error_count}</b>
          </div>
          <div class="line">
            HTTP Error Links<b>${this.featureLinksSummary.http_error_count}</b>
          </div>
        </sl-details>
        <sl-details summary="Link Types" open>
          ${this.featureLinksSummary.link_types.map(
            linkType => html`
              <div class="line">
                ${linkType.key.toUpperCase()} <b>${linkType.count}</b>
              </div>
            `
          )}
        </sl-details>
        <sl-details summary="Uncovered Link Domains" open>
          ${this.featureLinksSummary.uncovered_link_domains.map(
            domain => html`
              <div class="line">
                <div>
                  <a href=${domain.key}>${domain.key}</a>
                  <sl-icon-button
                    library="material"
                    name="search"
                    slot="prefix"
                    title="Samples"
                    @click=${() =>
                      this.fetchLinkSamples(domain.key, 'web', undefined)}
                  >
                    ></sl-icon-button
                  >
                </div>
                <b>${domain.count}</b>
              </div>
              ${this.sampleId ===
              this.calcSampleId(domain.key, 'web', undefined)
                ? this.renderSamples()
                : nothing}
            `
          )}
        </sl-details>
        <sl-details summary="Error Link Domains" open>
          ${this.featureLinksSummary.error_link_domains.map(
            domain => html`
              <div class="line">
                <div>
                  <a href=${domain.key}>${domain.key}</a>
                  <sl-icon-button
                    library="material"
                    name="search"
                    slot="prefix"
                    title="Samples"
                    @click=${() =>
                      this.fetchLinkSamples(domain.key, undefined, true)}
                  >
                    ></sl-icon-button
                  >
                </div>
                <b>${domain.count}</b>
              </div>
              ${this.sampleId === this.calcSampleId(domain.key, undefined, true)
                ? this.renderSamples()
                : nothing}
            `
          )}
        </sl-details>
      </div>
    `;
  }

  render() {
    return html` ${this.loading ? html`` : this.renderComponents()} `;
  }
}
