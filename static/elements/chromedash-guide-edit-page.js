import {LitElement, css, html} from 'lit';
import './chromedash-guide-metadata';
import './chromedash-process-overview';
import {SHARED_STYLES} from '../sass/shared-css.js';
import {FORM_STYLES} from '../sass/forms-css.js';


export class ChromedashGuideEditPage extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      ...FORM_STYLES,
      css`
      `];
  }

  static get properties() {
    return {
      user: {type: Object},
      featureId: {type: Number},
      feature: {type: Object},
    };
  }

  constructor() {
    super();
    this.user = {};
    this.featureId = 0;
    this.feature = {};
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
    ]).then(([user, feature]) => {
      this.user = user;
      this.feature = feature;
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
        <a style="float:right"
          href="/guide/editall/${this.featureId}">Edit all fields</a>
        <span style="float:right; margin-right: 2em">
        <a href="https://github.com/GoogleChrome/chromium-dashboard/issues/new?labels=Feedback&amp;template=process-and-guide-ux-feedback.md"
          target="_blank" rel="noopener">Process and UI feedback</a></span>
        <h2 id="breadcrumbs">
          <a href="/feature/${this.featureId}">
            <iron-icon icon="chromestatus:arrow-back"></iron-icon>
            Edit feature: ${this.feature.name}
          </a>
        </h2>
      </div>
    `;
  }

  renderMetadata() {
    return html`
    `;
  }

  renderProcessOverview() {
    return html`
    `;
  }

  render() {
    // TODO: Create precomiled main css file and import it instead of inlining it here
    return html`
      <link rel="stylesheet" href="/static/css/main.css">
      ${this.renderSubHeader()}
      ${this.renderMetadata()}
      ${this.renderProcessOverview()}
    `;
  }
}

customElements.define('chromedash-guide-edit-page', ChromedashGuideEditPage);
