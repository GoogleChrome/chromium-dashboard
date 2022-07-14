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

        .drawer-content-wrapper {
          max-width: var(--app-drawer-width);
        }

        #column-container {
          display: flex;
          align-items: stretch;
          flex-direction: row;
        }

        #drawer-column {
          padding: 1em 2em 1em 1em;
          margin-left: 8px;
        }

        #content-column {
          flex: 1;
          padding-left: 2em;
        }

        .data-panel {
          max-width: var(--max-content-width);
        }
        .data-panel .description {
          margin-bottom: 1em;
        }

        .metric-nav {
          list-style-type: none;
        }
        .metric-nav h3:not(:first-of-type) {
          margin-top: calc(var(--content-padding) * 2);
        }
        .metric-nav li {
          padding: 0.5em;
          margin-bottom: 10px;
        }

        @media only screen and (max-width: 1100px) {
          .metric-nav {
            display: none
          }

          #column-container {
            flex-direction: column;
          }

          #content-column {
            padding-left: var(--content-padding-half);
            padding-right: var(--content-padding-half);
          }

          #drawer-column {
            padding: 0;
          }

          #subheader {
            margin: var(--content-padding) 0;
            text-align: center;
          }

          .data-panel {
            margin: 0 10px;
          }
        }

        @media only screen and (min-width: 1100px) {
          #horizontal-sub-nav {
            display: none
          }
        }
      `];
  }

  static get properties() {
    return {
      type: {type: String}, // "css" or "feature"
      view: {type: String}, // "popularity" or "animated"
      props: {attribute: false},
    };
  }

  constructor() {
    super();
    this.type = '';
    this.view = '';
    this.props = [];
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

  renderCSSNavBar() {
    return html`
      <ul class="metric-nav">
        <h3>All properties</h3>
        <li><a href="/metrics/css/popularity">Stack rank</a></li>
        <li><a href="/metrics/css/timeline/popularity">Timeline</a></li>
        <h3>Animated properties</h3>
        <li><a href="/metrics/css/animated">Stack rank</a></li>
        <li><a href="/metrics/css/timeline/animated">Timeline</a></li>
      </ul>

      <div id="horizontal-sub-nav">
        <nav class="data-panel">
          <table>
            <tr>
              <td>View All Properties As:</td>
              <td>
                <a href="/metrics/css/timeline/popularity" class="sub-nav-links">Timeline</a>
                |
                <a href="/metrics/css/popularity" class="sub-nav-links">Stack Rank</a>
              </td>
            </tr>
          </table>
        </nav>

        <nav class="data-panel">
          <table>
            <tr>
              <td>View Animated Properties As:</td>
              <td>
                <a href="/metrics/css/timeline/animated" class="sub-nav-links">Timeline</a>
                |
                <a href="/metrics/css/animated" class="sub-nav-links">Stack Rank</a>
              </td>
            </tr>
          </table>
        </nav>
      </div>
    `;
  }

  renderJSNavBar() {
    return html`
      <ul class="metric-nav">
        <h3>All features</h3>
        <li><a href="/metrics/feature/popularity">Stack rank</a></li>
        <li><a href="/metrics/feature/timeline/popularity">Timeline</a></li>
      </ul>

      <div id="horizontal-sub-nav">
        <nav class="data-panel">
          <table>
            <tr>
              <td>View As:</td>
              <td>
                <a href="/metrics/feature/timeline/popularity" class="sub-nav-links"
                  >Timeline</a
                >
                |
                <a href="/metrics/feature/popularity" class="sub-nav-links"
                  >Stack Rank</a
                >
              </td>
            </tr>
          </table>
        </nav>
      </div>
    `;
  }

  renderSubheader() {
    const typeText = this.type == 'css'? 'CSS': 'HTML & JavaScript';
    const viewText = this.view == 'animated' ? 'animated' : 'all';
    const propText = this.type == 'css' ? 'properties' : 'features';
    const subTitleText = `${typeText} usage metrics > ${viewText} ${propText} > timeline`;
    return html`<h2>${subTitleText}</h2>`;
  }

  renderDataPanel() {
    return html`
      <p class="description">To begin, select a feature in the dropdown below.</p>
      <chromedash-timeline
        .type=${this.type}
        .view=${this.view}
        .props=${this.props}>
      </chromedash-timeline>
    `;
  }

  render() {
    // TODO: Create a precomiled main css file and import it instead of inlining it here
    return html`
      <link rel="stylesheet" href="/static/css/main.css">
      <div id="column-container">
        <div id="drawer-column">
          ${this.type == 'css' ? this.renderCSSNavBar() : this.renderJSNavBar()}
        </div>
        <div id="content-column">
          <div id="subheader">
            ${this.renderSubheader()}
          </div>
          <div class="data-panel">
            ${this.renderDataPanel()}
          </div>
        </div>
      </div>
    `;
  }
}

customElements.define('chromedash-timeline-page', ChromedashTimelinePage);
