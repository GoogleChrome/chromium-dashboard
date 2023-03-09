import {LitElement, css, html, nothing} from 'lit';
import {ref, createRef} from 'lit/directives/ref.js';
import {showToastMessage} from './utils';
import page from 'page';
import {SHARED_STYLES} from '../sass/shared-css.js';


class ChromedashApp extends LitElement {
  gateColumnRef = createRef();

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

        #rollout {
          width: 100%;
          text-align: center;
          padding: 1em;
          color: black;
          background: lightgrey;
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

        #content-sidebar-space {
          position: sticky;
          flex-shrink: 100;
          width: var(--sidebar-space);
        }

        #sidebar {
          position: absolute;
          top: 0;
          right: 0;
          width: var(--sidebar-width);
          max-width: var(--sidebar-max-width);
          bottom: 0;
        }
        #sidebar[hidden] {
          display: none;
        }
        #sidebar-content {
          position: sticky;
          top: 10px;
          height: 85vh;
          overflow-y: auto;
          border: var(--sidebar-border);
          border-radius: var(--sidebar-radius);
          background: var(--sidebar-bg);
          padding: var(--content-padding);
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
      sidebarHidden: {type: Boolean},
      selectedGateId: {type: Number},
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
    this.sidebarHidden = true;
    this.selectedGateId = 0;
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

    const scrollIfHash = (ctx) => {
      // If current page is ctx.path and only the hash changes, don't create a new element
      // but instead just scroll to the element identified by the hash.
      if (this.currentPage == ctx.path && ctx.hash) {
        if (window.scrollToElement) {
          window.scrollToElement(`#${ctx.hash}`);
        }
        return true;
      }
    };

    // SPA routing rules.  Note that rules are considered in order.
    // And :var can match any string (including a slash) if there is no slash after it.
    page('/', () => page.redirect('/roadmap'));
    page('/roadmap', (ctx) => {
      this.pageComponent = document.createElement('chromedash-roadmap-page');
      this.pageComponent.user = this.user;
      this.contextLink = ctx.path;
      this.currentPage = ctx.path;
      this.hideSidebar();
    });
    page('/myfeatures', (ctx) => {
      this.pageComponent = document.createElement('chromedash-myfeatures-page');
      this.pageComponent.user = this.user;
      this.pageComponent.selectedGateId = this.selectedGateId;
      this.contextLink = ctx.path;
      this.currentPage = ctx.path;
      this.hideSidebar();
    });
    page('/newfeatures', (ctx) => {
      this.pageComponent = document.createElement('chromedash-all-features-page');
      this.pageComponent.user = this.user;
      this.pageComponent.rawQuery = window.csClient.parseRawQuery(ctx.querystring);
      this.contextLink = ctx.path;
      this.currentPage = ctx.path;
      this.pageComponent.addEventListener('pagination', this.handlePagination.bind(this));
      this.pageComponent.addEventListener('search', this.handleSearchQuery.bind(this));
      this.hideSidebar();
    });
    page('/feature/:featureId(\\d+)', (ctx) => {
      this.pageComponent = document.createElement('chromedash-feature-page');
      this.pageComponent.featureId = parseInt(ctx.params.featureId);
      this.pageComponent.user = this.user;
      this.pageComponent.contextLink = this.contextLink;
      this.pageComponent.selectedGateId = this.selectedGateId;
      this.pageComponent.rawQuery = window.csClient.parseRawQuery(ctx.querystring);
      this.currentPage = ctx.path;
      this.pageComponent.appTitle = this.appTitle;
      if (this.pageComponent.featureId != this.gateColumnRef.value?.feature?.id) {
        this.hideSidebar();
      }
    });
    page('/guide/new', (ctx) => {
      if (scrollIfHash(ctx)) return;
      this.pageComponent = document.createElement('chromedash-guide-new-page');
      this.pageComponent.userEmail = this.user.email;
      this.currentPage = ctx.path;
      this.hideSidebar();
    });
    page('/guide/enterprise/new', (ctx) => {
      if (scrollIfHash(ctx)) return;
      this.pageComponent = document.createElement('chromedash-guide-new-page');
      this.pageComponent.userEmail = this.user.email;
      this.pageComponent.isEnterpriseFeature = true;
      this.currentPage = ctx.path;
      this.hideSidebar();
    });
    page('/guide/edit/:featureId(\\d+)', (ctx) => {
      if (scrollIfHash(ctx)) return;
      this.pageComponent = document.createElement('chromedash-guide-edit-page');
      this.pageComponent.featureId = parseInt(ctx.params.featureId);
      this.pageComponent.appTitle = this.appTitle;
      this.currentPage = ctx.path;
      this.hideSidebar();
    });
    page('/guide/editall/:featureId(\\d+)', (ctx) => {
      if (scrollIfHash(ctx)) return;
      this.pageComponent = document.createElement('chromedash-guide-editall-page');
      this.pageComponent.featureId = parseInt(ctx.params.featureId);
      this.pageComponent.appTitle = this.appTitle;
      this.pageComponent.nextPage = this.currentPage;
      this.currentPage = ctx.path;
      this.hideSidebar();
    });
    page('/guide/verify_accuracy/:featureId(\\d+)', (ctx) => {
      this.pageComponent = document.createElement('chromedash-guide-verify-accuracy-page');
      this.pageComponent.featureId = parseInt(ctx.params.featureId);
      this.pageComponent.appTitle = this.appTitle;
      this.hideSidebar();
    });
    page('/guide/stage/:featureId(\\d+)/:intentStage(\\d+)', (ctx) => {
      if (scrollIfHash(ctx)) return;
      this.pageComponent = document.createElement('chromedash-guide-stage-page');
      this.pageComponent.featureId = parseInt(ctx.params.featureId);
      this.pageComponent.intentStage = parseInt(ctx.params.intentStage);
      this.pageComponent.nextPage = this.currentPage;
      this.pageComponent.appTitle = this.appTitle;
      this.currentPage = ctx.path;
      this.hideSidebar();
    });
    page('/guide/stage/:featureId(\\d+)/:intentStage(\\d+)/:stageId(\\d+)', (ctx) => {
      if (scrollIfHash(ctx)) return;
      this.pageComponent = document.createElement('chromedash-guide-stage-page');
      this.pageComponent.featureId = parseInt(ctx.params.featureId);
      this.pageComponent.stageId = parseInt(ctx.params.stageId);
      this.pageComponent.intentStage = parseInt(ctx.params.intentStage);
      this.pageComponent.nextPage = this.currentPage;
      this.pageComponent.appTitle = this.appTitle;
      this.currentPage = ctx.path;
      this.hideSidebar();
    });
    page('/guide/stage/:featureId(\\d+)/metadata', (ctx) => {
      if (scrollIfHash(ctx)) return;
      this.pageComponent = document.createElement('chromedash-guide-metadata-page');
      this.pageComponent.featureId = parseInt(ctx.params.featureId);
      this.pageComponent.nextPage = this.currentPage;
      this.pageComponent.appTitle = this.appTitle;
      this.currentPage = ctx.path;
      this.hideSidebar();
    });
    page('/settings', (ctx) => {
      this.pageComponent = document.createElement('chromedash-settings-page');
      this.currentPage = ctx.path;
      this.hideSidebar();
    });
    page('/metrics/:type/:view', (ctx) => {
      // if already on this page and only the hash changes, don't create a new element
      if (this.currentPage == ctx.path && ctx.hash) return;
      this.pageComponent = document.createElement('chromedash-stack-rank-page');
      this.pageComponent.type = ctx.params.type;
      this.pageComponent.view = ctx.params.view;
      this.currentPage = ctx.path;
      this.hideSidebar();
    });
    page('/metrics/:type/timeline/:view/:bucketId', (ctx) => {
      this.pageComponent = document.createElement('chromedash-timeline-page');
      this.pageComponent.type = ctx.params.type;
      this.pageComponent.view = ctx.params.view;
      this.pageComponent.selectedBucketId = ctx.params.bucketId;
      this.currentPage = ctx.path;
      this.hideSidebar();
    });
    page('/metrics', () => page.redirect('/metrics/css/popularity'));
    page('/metrics/css', () => page.redirect('/metrics/css/popularity'));
    page('/metrics/css/timeline/popularity', () => page.redirect('/metrics/css/popularity'));
    page('/metrics/css/timeline/animated', () => page.redirect('/metrics/css/animated'));
    page('/metrics/feature/timeline/popularity', () =>
      page.redirect('/metrics/feature/popularity'));
    page('/enterprise', (ctx) => {
      this.pageComponent = document.createElement('chromedash-enterprise-page');
      this.pageComponent.user = this.user;
      this.contextLink = ctx.path;
      this.currentPage = ctx.path;
      this.hideSidebar();
    });
    page.start();
  }

  handlePagination(e) {
    this.updateURLParams('start', e.detail.index);
  }

  handleSearchQuery(e) {
    this.updateURLParams('q', e.detail.query);
  }

  showSidebar() {
    this.sidebarHidden = false;
  }

  hideSidebar() {
    this.sidebarHidden = true;
    this.selectedGateId = 0;
    this.pageComponent.selectedGateId = 0;
  }

  showGateColumn(feature, stageId, gate) {
    this.gateColumnRef.value.setContext(feature, stageId, gate);
    this.selectedGateId = gate.id;
    this.pageComponent.selectedGateId = gate.id;
    this.showSidebar();
  }

  handleShowGateColumn(e) {
    this.showGateColumn(e.detail.feature, e.detail.stage.id, e.detail.gate);
  }

  /**
 * Update window.locaton with new query params.
 * @param {string} key is the key of the query param.
 * @param {string} val is the unencoded value of the query param.
 */
  updateURLParams(key, val) {
    // Update the query param object.
    const rawQuery = window.csClient.parseRawQuery(window.location.search);
    rawQuery[key] = encodeURIComponent(val);

    // Assemble the new URL.
    const newURL = this.getNewLocation(rawQuery, window.location);
    newURL.hash = '';
    if (newURL.toString() === window.location.toString()) {
      return;
    }
    // Update URL without refreshing the page. {path:} is needed for
    // an issue in page.js:
    // https://github.com/visionmedia/page.js/issues/293#issuecomment-456906679
    window.history.pushState({path: newURL.toString()}, '', newURL);
  }

  /**
   * Create a new URL using params and a location.
   * @param {string} params is the new param object.
   * @param {Object} location is an URL location.
   * @return {Object} the new URL.
   */
  getNewLocation(params, location) {
    const url = new URL(location);
    url.search = '';
    if (params) {
      for (const [k, v] of Object.entries(params)) {
        // Skip if the value is empty.
        if (!v) {
          continue;
        }
        url.searchParams.append(k, v);
      }
    }
    return url;
  }

  /* The user edited something, so tell components to refetch data. */
  refetch() {
    if (this.pageComponent?.refetch) {
      this.pageComponent.refetch();
    }
    if (this.gateColumnRef.value?.refetch) {
      this.gateColumnRef.value.refetch();
    }
  }

  renderContentAndSidebar() {
    const wide = (this.pageComponent &&
                  this.pageComponent.tagName == 'CHROMEDASH-ROADMAP-PAGE');
    if (wide) {
      return html`
        <div id="content-component-wrapper" wide>
          ${this.pageComponent}
        </div>
      `;
    } else {
      return html`
        <div id="content-component-wrapper"
          @show-gate-column=${this.handleShowGateColumn}
          @refetch-needed=${this.refetch}
          >
          ${this.pageComponent}
        </div>
        <div id="content-sidebar-space">
          <div id="sidebar" ?hidden=${this.sidebarHidden}>
            <div id="sidebar-content">
              <chromedash-gate-column
                .user=${this.user} ${ref(this.gateColumnRef)}
                @close=${this.hideSidebar}
                @refetch-needed=${this.refetch}
                >
              </chromedash-gate-column>
            </div>
          </div>
        </div>
      `;
    }
  }

  renderRolloutBanner(currentPage) {
    if (currentPage.startsWith('/newfeatures')) {
      return html`
      <div id="rollout">
        <a href="/features">Back to the old features page</a>
      </div>
    `;
    }

    return nothing;
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
            ${this.renderRolloutBanner(this.currentPage)}
            <div id="content-flex-wrapper">
              ${this.renderContentAndSidebar()}
            </div>
          </div>

        </div>
        <chromedash-footer></chromedash-footer>
      </div>
    `;
  }
}

customElements.define('chromedash-app', ChromedashApp);
