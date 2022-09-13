import {LitElement, css, html, nothing} from 'lit';
import {showToastMessage} from './utils';
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
        .main-toolbar .toolbar-content {
          width: 100%;
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

        @media only screen and (max-width: 700px) {
          #content {
            margin-left: 0;
            margin-right: 0;
          }
        }
    `];
  }

  static get properties() {
    return {
      user: {type: Object},
      loading: {type: Boolean},
      appTitle: {type: String},
      googleSignInClientId: {type: String},
      currentPage: {type: String},
      bannerMessage: {type: String},
      bannerTime: {type: Number},
      pageComponent: {attribute: false},
      contextLink: {type: String}, // used for the back button in the feature page
    };
  }

  constructor() {
    super();
    this.user = {};
    this.loading = true;
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
    this.loading = true;
    window.csClient.getPermissions().then((user) => {
      this.user = user;
    }).catch(() => {
      showToastMessage('Some errors occurred. Please refresh the page or try again later.');
    }).finally(() => {
      this.setUpRoutes();
      this.loading = false;
    });
  }

  setUpRoutes() {
    page.strict(true); // Be precise about trailing slashes in routes.

    // SPA routing rules.  Note that rules are considered in order.
    // And :var can match any string (including a slash) if there is no slash after it.
    page('/', () => page.redirect('/roadmap'));
    page('/roadmap', (ctx) => {
      this.pageComponent = document.createElement('chromedash-roadmap-page');
      this.pageComponent.user = this.user;
      this.contextLink = ctx.path;
      this.currentPage = ctx.path;
    });
    page('/myfeatures', (ctx) => {
      this.pageComponent = document.createElement('chromedash-myfeatures-page');
      this.pageComponent.user = this.user;
      this.contextLink = ctx.path;
      this.currentPage = ctx.path;
    });
    page('/newfeatures', (ctx) => {
      this.pageComponent = document.createElement('chromedash-all-features-page');
      this.pageComponent.user = this.user;
      this.contextLink = ctx.path;
      this.currentPage = ctx.path;
    });
    page('/feature/:featureId', (ctx) => {
      this.pageComponent = document.createElement('chromedash-feature-page');
      this.pageComponent.featureId = parseInt(ctx.params.featureId);
      this.pageComponent.user = this.user;
      this.pageComponent.contextLink = this.contextLink;
      this.pageComponent.appTitle = this.appTitle;
    });
    page('/guide/new', () => {
      this.pageComponent = document.createElement('chromedash-guide-new-page');
      this.pageComponent.userEmail = this.user.email;
    });
    page('/guide/edit/:featureId', (ctx) => {
      this.pageComponent = document.createElement('chromedash-guide-edit-page');
      this.pageComponent.featureId = ctx.params.featureId;
      this.pageComponent.appTitle = this.appTitle;
    });
    page('/guide/editall/:featureId', (ctx) => {
      this.pageComponent = document.createElement('chromedash-guide-editall-page');
      this.pageComponent.featureId = ctx.params.featureId;
      this.pageComponent.appTitle = this.appTitle;
    });
    page('/guide/verify_accuracy/:featureId', (ctx) => {
      this.pageComponent = document.createElement('chromedash-guide-verify-accuracy-page');
      this.pageComponent.featureId = ctx.params.featureId;
      this.pageComponent.appTitle = this.appTitle;
    });
    page('/guide/stage/:featureId/:stageId', (ctx) => {
      this.pageComponent = document.createElement('chromedash-guide-stage-page');
      this.pageComponent.featureId = ctx.params.featureId;
      this.pageComponent.stageId = ctx.params.stageId;
      this.pageComponent.appTitle = this.appTitle;
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
    page('/metrics', () => page.redirect('/metrics/css/popularity'));
    page('/metrics/css', () => page.redirect('/metrics/css/popularity'));
    page('/metrics/css/timeline/popularity', () => page.redirect('/metrics/css/popularity'));
    page('/metrics/css/timeline/animated', () => page.redirect('/metrics/css/animated'));
    page('/metrics/feature/timeline/popularity', () =>
      page.redirect('/metrics/feature/popularity'));
    page.start();
  }

  render() {
    // The <slot> below is for the Google sign-in button, this is because
    // Google Identity Services Library cannot find elements in a shadow DOM,
    // so we create signInButton element at the document level and insert it
    return this.loading ? nothing : html`
      <div id="app-content-container">
        <div>
          <div class="main-toolbar">
            <div class="toolbar-content">
              <chromedash-header
                .user=${this.user}
                .appTitle=${this.appTitle}
                .googleSignInClientId=${this.googleSignInClientId}
                .currentPage=${this.currentPage}>
                <slot></slot>
              </chromedash-header>
            </div>
          </div>

          <div id="content">
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
