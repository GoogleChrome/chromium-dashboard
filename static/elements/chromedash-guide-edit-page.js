import {LitElement, css, html} from 'lit';
import './chromedash-guide-metadata';
import './chromedash-process-overview';
import {showToastMessage} from './utils.js';
import {SHARED_STYLES} from '../sass/shared-css.js';
import {FORM_STYLES} from '../sass/forms-css.js';


export class ChromedashGuideEditPage extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      ...FORM_STYLES,
      css`
        section {
          margin: 1em 0;
        }

        #subheader {
          justify-content: space-between;
        }

        .actionlinks {
          display: flex;
          gap: 1.5em;
        }

        sl-skeleton {
          margin-bottom: 1em;
          width: 60%;
        }
        sl-skeleton:nth-of-type(even) {
          width: 50%;
        }

        h3 sl-skeleton {
          width: 30%;
          height: 1.5em;
        }
      `];
  }

  static get properties() {
    return {
      user: {type: Object},
      featureId: {type: Number},
      feature: {type: Object},
      overviewForm: {type: String},
      process: {type: Object},
      progress: {type: Object},
      dismissedCues: {type: Array},
      loading: {type: Boolean},
    };
  }

  constructor() {
    super();
    this.user = {};
    this.featureId = 0;
    this.feature = {};
    this.overviewForm = '';
    this.process = {};
    this.progress = {};
    this.dismissedCues = [];
    this.loading = true;
  }

  connectedCallback() {
    super.connectedCallback();
    this.fetchData();
  }

  fetchData() {
    this.loading = true;
    Promise.all([
      window.csClient.getPermissions(),
      window.csClient.getFeature(this.featureId),
      window.csClient.getFeatureProcess(this.featureId),
      window.csClient.getFeatureProgress(this.featureId),
      window.csClient.getDismissedCues(),
    ]).then(([user, feature, process, progress, dismissedCues]) => {
      this.user = user;
      this.feature = feature;
      this.process = process;
      this.progress = progress;
      this.dismissedCues = dismissedCues;
      this.loading = false;

      // TODO(kevinshen56714): Remove this once SPA index page is set up.
      // Has to include this for now to remove the spinner at _base.html.
      document.body.classList.remove('loading');
    }).catch(() => {
      showToastMessage('Some errors occurred. Please refresh the page or try again later.');
    });
  }

  renderSubHeader() {
    return html`
      <div id="subheader">
        <h2 id="breadcrumbs">
          <a href="/feature/${this.featureId}">
            <iron-icon icon="chromestatus:arrow-back"></iron-icon>
            Edit feature: ${this.feature.name}
          </a>
        </h2>
        <div class="actionlinks">
          <a href="/guide/editall/${this.featureId}">Edit all fields</a>
          <a href="https://github.com/GoogleChrome/chromium-dashboard/issues/new?labels=Feedback&amp;template=process-and-guide-ux-feedback.md"
            target="_blank" rel="noopener">Process and UI feedback</a></span>
        </div>
      </div>
    `;
  }

  renderMetadata() {
    return html`
      <chromedash-guide-metadata
        .feature=${this.feature}
        .isAdmin=${this.user && this.user.is_admin}
        .overviewForm=${this.overviewForm}>
      </chromedash-guide-metadata>
    `;
  }

  renderProcessOverview() {
    return html`
      <section>
        <chromedash-process-overview
          .feature=${this.feature}
          .process=${this.process}
          .progress=${this.progress}
          .dismissedCues=${this.dismissedCues}>
        </chromedash-process-overview>
      </section>
    `;
  }

  renderFootnote() {
    return html`
      <section id="footnote">
        Please see the
        <a href="https://www.chromium.org/blink/launching-features"
          target="_blank" rel="noopener">
          Launching features
        </a>
        page for process instructions.
      </section>
    `;
  }

  renderSkeletons() {
    return html`
      <section id="metadata">
        <h3><sl-skeleton effect="sheen"></sl-skeleton></h3>
        <p>
          <sl-skeleton effect="sheen"></sl-skeleton>
          <sl-skeleton effect="sheen"></sl-skeleton>
          <sl-skeleton effect="sheen"></sl-skeleton>
          <sl-skeleton effect="sheen"></sl-skeleton>
          <sl-skeleton effect="sheen"></sl-skeleton>
          <sl-skeleton effect="sheen"></sl-skeleton>
        </p>
      </section>
    `;
  }

  render() {
    return html`
      ${this.renderSubHeader()}

      ${this.loading ?
        this.renderSkeletons() :
        html`
          ${this.renderMetadata()}
          ${this.renderProcessOverview()}
          ${this.renderFootnote()}
      `}
    `;
  }
}

customElements.define('chromedash-guide-edit-page', ChromedashGuideEditPage);
