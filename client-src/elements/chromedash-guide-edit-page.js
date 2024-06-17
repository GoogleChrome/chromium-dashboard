import {LitElement, css, html} from 'lit';
import './chromedash-guide-metadata';
import './chromedash-process-overview';
import {showToastMessage} from './utils.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {FORM_STYLES} from '../css/forms-css.js';

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

        sl-dialog p {
          margin-top: var(--content-padding);
        }
      `,
    ];
  }

  static get properties() {
    return {
      user: {type: Object},
      featureId: {type: Number},
      feature: {type: Object},
      featureGates: {type: Array},
      process: {type: Object},
      progress: {type: Object},
      dismissedCues: {type: Array},
      loading: {type: Boolean},
      appTitle: {type: String},
    };
  }

  constructor() {
    super();
    this.user = {};
    this.featureId = 0;
    this.feature = {};
    this.featureGates = [];
    this.process = {};
    this.progress = {};
    this.dismissedCues = [];
    this.loading = true;
    this.appTitle = '';
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
      window.csClient.getGates(this.featureId),
      window.csClient.getFeatureProcess(this.featureId),
      window.csClient.getFeatureProgress(this.featureId),
      window.csClient.getDismissedCues(),
    ])
      .then(([user, feature, gatesRes, process, progress, dismissedCues]) => {
        this.user = user;
        this.feature = feature;
        this.featureGates = gatesRes.gates;
        this.process = process;
        this.progress = progress;
        this.dismissedCues = dismissedCues;
        this.loading = false;

        // re-check permission every time users visit the edit page
        const canEdit =
          this.user &&
          (this.user.can_edit_all ||
            this.user.editable_features.includes(this.featureId));
        if (!canEdit) location.reload();

        if (this.feature.name) {
          document.title = `${this.feature.name} - ${this.appTitle}`;
        }
      })
      .catch(() => {
        showToastMessage(
          'Some errors occurred. Please refresh the page or try again later.'
        );
      });
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    document.title = this.appTitle;
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

      <sl-dialog open label="Obsolete page">
        <p>This page will soon be removed from chromestatus.com.</p>

        <p>You can now edit all fields by using the "Edit fields" buttons or
        "Edit all fields" link on the feature detail page.</p>

        <p>To generate intent thread messages: go to the feature detail page,
        click the "API Owners" gate chip for the appropriate stage, then click
        the blue "Draft Intent to ... email" button at the top of the gate
        column.</p>

        <p><sl-button variant="primary" size="small"
         href="/feature/${this.featureId}">Try it</sl-button></p>
      </sl-dialog>
    `;
  }

  renderMetadata() {
    return html`
      <chromedash-guide-metadata
        .feature=${this.feature}
        .isAdmin=${this.user && this.user.is_admin}
        .email=${this.user.email}
      >
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
          .featureGates=${this.featureGates}
          .dismissedCues=${this.dismissedCues}
        >
        </chromedash-process-overview>
      </section>
    `;
  }

  renderFootnote() {
    return html`
      <section id="footnote">
        Please see the
        <a
          href="https://www.chromium.org/blink/launching-features"
          target="_blank"
          rel="noopener"
        >
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
      ${this.loading
        ? this.renderSkeletons()
        : html`
            ${this.renderMetadata()} ${this.renderProcessOverview()}
            ${this.renderFootnote()}
          `}
    `;
  }
}

customElements.define('chromedash-guide-edit-page', ChromedashGuideEditPage);
