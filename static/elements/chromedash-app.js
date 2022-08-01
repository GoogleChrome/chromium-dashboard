import {LitElement, css, html} from 'lit';
import page from 'page';
import {SHARED_STYLES} from '../sass/shared-css.js';


class ChromedashApp extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        .main-toolbar {
          display: flex;
          position: relative;
          padding: 0;
        }

        #app-content-container {
          display: flex;
          flex-direction: column;
          height: 100%;
        }

        #content {
          margin: var(--content-padding);
          position: relative;
        }

        #content-flex-wrapper {
          display: flex;
          justify-content: center;
          width: 100%;
        }

        #content-component-wrapper {
          width: var(--max-content-width);
          max-width: 95%;
        }
        #content-component-wrapper[wide] {
          width: 100%;
        }

        @media only screen and (min-width: 701px) {
          .main-toolbar .toolbar-content {
            width: 100%;
          }
        }
    `];
  }

  static get properties() {
    return {
      appTitle: {type: String},
      googleSignInClientId: {type: String},
      currentPage: {type: String},
      bannerMessage: {type: String},
      bannerTime: {type: Number},
      pageComponent: {type: Element},
      contextLink: {type: String}, // used for the back button in the feature page
    };
  }

  constructor() {
    super();
    this.appTitle = '';
    this.googleSignInClientId = '',
    this.currentPage = '';
    this.bannerMessage = '';
    this.bannerTime = null;
    this.pageComponent = null;
    this.contextLink = '/features';
  }

  connectedCallback() {
    super.connectedCallback();
    this.setUpRoutes();
  }

  setUpRoutes() {
    page.strict(true); // Be precise about trailing slashes in routes.

    // SPA routing rules.  Note that rules are considered in order.
    // And :var can match any string (including a slash) if there is no slash after it.
    page('/spa', () => page.redirect('/roadmap'));
    page('/roadmap', (ctx) => {
      this.pageComponent = document.createElement('chromedash-roadmap-page');
      this.contextLink = ctx.path;
      this.currentPage = ctx.path;
    });
    page('/myfeatures', (ctx) => {
      this.pageComponent = document.createElement('chromedash-myfeatures-page');
      this.contextLink = ctx.path;
      this.currentPage = ctx.path;
    });
    page('/features', (ctx) => {
      this.pageComponent = document.createElement('chromedash-all-features-page');
      this.contextLink = ctx.path;
      this.currentPage = ctx.path;
    });
    page('/feature/:featureId', (ctx) => {
      this.pageComponent = document.createElement('chromedash-feature-page');
      this.pageComponent.featureId = ctx.params.featureId;
      this.pageComponent.contextLink = this.contextLink;
    });
    page('/settings', (ctx) => {
      this.pageComponent = document.createElement('chromedash-settings-page');
      this.currentPage = ctx.path;
    });
    page('/metrics/:type/:view', (ctx) => {
      this.pageComponent = document.createElement('chromedash-stack-rank-page');
      this.pageComponent.type = ctx.params.type;
      this.pageComponent.view = ctx.params.view;
      this.currentPage = ctx.path;
    });
    page('/metrics/:type/timeline/:view/:bucketId', (ctx) => {
      this.pageComponent = document.createElement('chromedash-timeline-page');
      this.pageComponent.type = ctx.params.type;
      this.pageComponent.view = ctx.params.view;
      this.pageComponent.selectedBucketId = ctx.params.bucketId;
      this.currentPage = ctx.path;
    });

    page.start();
  }

  render() {
    // TODO: Create precomiled main css file and import it instead of inlining it here
    // The <slot> below is for the Google sign-in button, this is because
    // Google Identity Services Library cannot find elements in a shadow DOM,
    // so we create signInButton element at the document level and insert it
    return html`
      <link rel="stylesheet" href="/static/css/main.css">
      <div id="app-content-container">
        <div>
          <div class="main-toolbar">
            <div class="toolbar-content">
              <chromedash-header 
                .appTitle=${this.appTitle}
                .googleSignInClientId=${this.googleSignInClientId}
                .currentPage=${this.currentPage}>
                <slot></slot>
              </chromedash-header>
            </div>
          </div>

          <div id="content">
            <div id="spinner">
              <img src="/static/img/ring.svg">
            </div>
            <chromedash-banner
              .message=${this.bannerMessage}
              .timestamp=${this.bannerTime}>
            </chromedash-banner>
            <div id="content-flex-wrapper">
              <div id="content-component-wrapper"
                ?wide=${this.pageComponent &&
                  this.pageComponent.tagName == 'CHROMEDASH-ROADMAP-PAGE'}>
                ${this.pageComponent}
              </div>
            </div>
          </div>

        </div>
        <chromedash-footer></chromedash-footer>
      </div>
    `;
  }
}

customElements.define('chromedash-app', ChromedashApp);

