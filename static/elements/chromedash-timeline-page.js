import {LitElement, css, html} from 'lit';
import './chromedash-timeline';
import {SHARED_STYLES} from '../sass/shared-css.js';


export class ChromedashTimelinePage extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        h3 {
          margin-bottom: var(--content-padding);
        }
        
        .description {
          margin-bottom: 1em;
        }

        #breadcrumbs a {
          text-decoration: none;
          color: inherit;
        }
      `];
  }

  static get properties() {
    return {
      type: {type: String}, // "css" or "feature"
      view: {type: String}, // "popularity" or "animated"
      props: {attribute: false},
      selectedBucketId: {attribute: false},
    };
  }

  constructor() {
    super();
    this.type = '';
    this.view = '';
    this.props = [];
    this.selectedBucketId = '1';
  }

  connectedCallback() {
    super.connectedCallback();

    let endpoint = `/data/blink/${this.type}props`;

    // [DEV] Change to true to use the staging server endpoint for development
    const devMode = false;
    if (devMode) endpoint = 'https://cr-status-staging.appspot.com' + endpoint;

    fetch(endpoint).then((res) => res.json()).then((props) => {
      this.props = props;

      // TODO(kevinshen56714): Remove this once SPA index page is set up.
      // Has to include this for now to remove the spinner at _base.html.
      document.body.classList.remove('loading');
    }).catch(() => {
      showToastMessage('Some errors occurred. Please refresh the page or try again later.');
    });
  }

  renderSubheader() {
    const typeText = this.type == 'css'? 'CSS': 'HTML & JavaScript';
    const viewText = this.view == 'animated' ? 'animated' : 'all';
    const propText = this.type == 'css' ? 'properties' : 'features';
    const subTitleText = `${typeText} usage metrics > ${viewText} ${propText} > timeline`;
    return html`
      <h2 id="breadcrumbs">
        <a href="/metrics/${this.type}/${this.view}">
          <iron-icon icon="chromestatus:arrow-back"></iron-icon>
        </a>${subTitleText}
      </h2>
    `;
  }

  renderDataPanel() {
    return html`
      <chromedash-timeline
        .type=${this.type}
        .view=${this.view}
        .props=${this.props}
        .selectedBucketId=${this.selectedBucketId}>
      </chromedash-timeline>
    `;
  }

  render() {
    // TODO: Create a precomiled main css file and import it instead of inlining it here
    return html`
      <link rel="stylesheet" href="/static/css/main.css">
      <div id="subheader">
        ${this.renderSubheader()}
      </div>
      ${this.renderDataPanel()}
    `;
  }
}

customElements.define('chromedash-timeline-page', ChromedashTimelinePage);
