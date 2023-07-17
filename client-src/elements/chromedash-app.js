import {LitElement, css, html, nothing} from 'lit';
import {ref, createRef} from 'lit/directives/ref.js';
import {styleMap} from 'lit-html/directives/style-map.js';
import {showToastMessage, parseRawQuery, updateURLParams, IS_MOBILE} from './utils';
import page from 'page';
import {SHARED_STYLES} from '../css/shared-css.js';
import {DRAWER_WIDTH_PX} from './chromedash-drawer.js';


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
          margin: 0;
          position: relative;
          min-height: 500px;
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
      devMode: {type: String},
      currentPage: {type: String},
      bannerMessage: {type: String},
      bannerTime: {type: Number},
      pageComponent: {attribute: false},
      contextLink: {type: String}, // used for the back button in the feature page
      sidebarHidden: {type: Boolean},
      selectedGateId: {type: Number},
      drawerOpen: {type: Boolean},
    };
  }

  constructor() {
    super();
    this.user = {};
    this.loading = true;
    this.appTitle = '';
    this.googleSignInClientId = '',
    this.devMode = '';
    this.currentPage = '';
    this.bannerMessage = '';
    this.bannerTime = null;
    this.pageComponent = null;
    this.contextLink = '/features';
    this.sidebarHidden = true;
    this.selectedGateId = 0;
    this.beforeUnloadHandler = null;
    this.drawerOpen = !IS_MOBILE;
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

  removeBeforeUnloadHandler() {
    if (this.beforeUnloadHandler) {
      window.removeEventListener('beforeunload', this.beforeUnloadHandler);
      this.beforeUnloadHandler = null;
    }
  }

  addBeforeUnloadHandler() {
    // Set up beforeunload event handler for the whole window.
    this.removeBeforeUnloadHandler();
    this.beforeUnloadHandler = (event) => {
      if (!this.getUnsavedChanges()) return;
      // Cancel the event, which asks user whether to stay.
      event.preventDefault();
      // Chrome requires returnValue to be set.
      event.returnValue = `You made changes that have not been saved.
      Are you sure you want to leave?`;
    };
    window.addEventListener('beforeunload', this.beforeUnloadHandler);
  }

  getUnsavedChanges() {
    if (!this.pageComponent) return;
    return this.pageComponent.unsavedChanges;
  }

  setUnsavedChanges(flag) {
    // Whether any unsaved changes have been made to form fields on the
    // current pageComponent. This is false when first "loading" a new page.
    // Undo of changes does not undo this setting.
    if (!this.pageComponent) return;
    this.pageComponent.unsavedChanges = flag;
  }

  handleFormSubmit() {
    // Remember the unsavedChanges status of the current page,
    // then set it to false.
    const currentPageComponent = this.pageComponent;
    const currentUnsavedChanges = this.pageComponent.unsavedChanges;
    this.setUnsavedChanges(false);
    this.removeBeforeUnloadHandler();


    // We can't easily check whether the form is valid, and that
    // is not enough anyway.  Since there is no event to indicate failure,
    // we'll just restore the unsavedChanges status after a timeout,
    // when we are still on the same page.
    window.setTimeout(() => {
      if (this.pageComponent == currentPageComponent &&
        this.getUnsavedChanges()) {
        this.setUnsavedChanges(currentUnsavedChanges);
        this.addBeforeUnloadHandler();
      }
    }, 1000);
  }

  // Maybe set up new page, or if the URL is the same, we stay.
  // If signin is required 'chromedash-login-required-page' is rendered.,
  // we render that component instead page.
  // Returns true if we are proceeding to the new page, false otherwise.
  setupNewPage(ctx, componentName) {
    // If current page is ctx.path and a ctx.hash exists,
    // don't create a new element but instead
    // just scroll to the element identified by the hash.
    // Note, this ignores any query string.
    if (this.currentPage == ctx.path && ctx.hash) {
      if (window.scrollToElement) {
        window.scrollToElement(`#${ctx.hash}`);
      }
      return false;
    }

    // If there was a previous page, check if we would lose unsaved changes.
    // This is like the beforeunload handler, but for "in-page" actions.
    if (this.pageComponent) {
      // Act like we are unloading previous page and loading a new page.
      if (this.getUnsavedChanges()) {
        // Should we use shoelace dialog instead?
        if (!confirm('You will lose unsaved changes.  Proceed anyway?')) {
          // Set ctx.handled to false, so we don't change browser's history.
          ctx.handled = false;
          return false;
        }
      }
    }
    const signinRequired = ctx.querystring.search('loginStatus=False') > -1;

    // Loading new page.
    this.pageComponent = document.createElement(signinRequired ?
      'chromedash-login-required-page' :
      componentName);
    this.setUnsavedChanges(false);
    this.removeBeforeUnloadHandler();

    window.setTimeout(() => {
      // Timeout required since the form may not be created yet.
      // Allow form submit to proceed without warning.
      const form = this.pageComponent.shadowRoot.querySelector('form');
      if (form) {
        this.addBeforeUnloadHandler();

        // Remember if anything has changed since the page was loaded.
        this.pageComponent.addEventListener('sl-change', () => {
          this.setUnsavedChanges(true);
        });

        form.addEventListener('submit', () => {
          this.handleFormSubmit();
        });
      }
    }, 1000);

    // If we didn't return false above, return true now.
    return true;
  };


  setUpRoutes() {
    page.strict(true); // Be precise about trailing slashes in routes.

    // SPA routing rules.  Note that rules are considered in order.
    // And :var can match any string (including a slash) if there is no slash after it.
    page('/', () => page.redirect('/roadmap'));
    page('/roadmap', (ctx) => {
      if (!this.setupNewPage(ctx, 'chromedash-roadmap-page')) return;
      this.pageComponent.user = this.user;
      this.contextLink = ctx.path;
      this.currentPage = ctx.path;
      this.hideSidebar();
    });
    page('/myfeatures', (ctx) => {
      if (!this.setupNewPage(ctx, 'chromedash-myfeatures-page')) return;
      this.pageComponent.user = this.user;
      this.pageComponent.selectedGateId = this.selectedGateId;
      this.contextLink = ctx.path;
      this.currentPage = ctx.path;
      this.hideSidebar();
    });
    page('/newfeatures', (ctx) => {
      if (!this.setupNewPage(ctx, 'chromedash-all-features-page')) return;
      this.pageComponent.user = this.user;
      this.pageComponent.rawQuery = parseRawQuery(ctx.querystring);
      this.pageComponent.addEventListener('pagination', this.handlePagination.bind(this));
      this.pageComponent.addEventListener('search', this.handleSearchQuery.bind(this));
      this.contextLink = ctx.path;
      this.currentPage = ctx.path;
      this.hideSidebar();
    });
    page('/feature/:featureId(\\d+)', (ctx) => {
      if (!this.setupNewPage(ctx, 'chromedash-feature-page')) return;
      this.pageComponent.featureId = parseInt(ctx.params.featureId);
      this.pageComponent.user = this.user;
      this.pageComponent.contextLink = this.contextLink;
      this.pageComponent.selectedGateId = this.selectedGateId;
      this.pageComponent.rawQuery = parseRawQuery(ctx.querystring);
      this.pageComponent.appTitle = this.appTitle;
      this.currentPage = ctx.path;
      if (this.pageComponent.featureId != this.gateColumnRef.value?.feature?.id) {
        this.hideSidebar();
      }
    });
    page('/feature/:featureId(\\d+)/activity', (ctx) => {
      if (!this.setupNewPage(ctx, 'chromedash-activity-page')) return;
      this.pageComponent.featureId = parseInt(ctx.params.featureId);
      this.pageComponent.user = this.user;
      this.pageComponent.contextLink = this.contextLink;
      this.currentPage = ctx.path;
      this.hideSidebar();
    });
    page('/guide/new', (ctx) => {
      if (!this.setupNewPage(ctx, 'chromedash-guide-new-page')) return;
      if (ctx.querystring.search('loginStatus=False') == -1) {
        this.pageComponent.userEmail = this.user.email;
      }
      this.currentPage = ctx.path;
      this.hideSidebar();
    });
    page('/guide/enterprise/new', (ctx) => {
      if (!this.setupNewPage(
        ctx,
        'chromedash-guide-new-page')) return;

      if (ctx.querystring.search('loginStatus=False') == -1) {
        this.pageComponent.userEmail = this.user.email;
      }
      this.pageComponent.isEnterpriseFeature = true;
      this.currentPage = ctx.path;
      this.hideSidebar();
    });
    page('/guide/edit/:featureId(\\d+)', (ctx) => {
      if (!this.setupNewPage(ctx, 'chromedash-guide-edit-page')) return;
      this.pageComponent.featureId = parseInt(ctx.params.featureId);
      this.pageComponent.appTitle = this.appTitle;
      this.currentPage = ctx.path;
      this.hideSidebar();
    });
    page('/guide/editall/:featureId(\\d+)', (ctx) => {
      if (!this.setupNewPage(ctx, 'chromedash-guide-editall-page')) return;
      this.pageComponent.featureId = parseInt(ctx.params.featureId);
      this.pageComponent.appTitle = this.appTitle;
      this.pageComponent.nextPage = this.currentPage;
      this.currentPage = ctx.path;
      this.hideSidebar();
    });
    page('/guide/verify_accuracy/:featureId(\\d+)', (ctx) => {
      if (!this.setupNewPage(ctx, 'chromedash-guide-verify-accuracy-page')) return;
      this.pageComponent.featureId = parseInt(ctx.params.featureId);
      this.pageComponent.appTitle = this.appTitle;
      this.hideSidebar();
    });
    page('/guide/stage/:featureId(\\d+)/:intentStage(\\d+)', (ctx) => {
      if (!this.setupNewPage(ctx, 'chromedash-guide-stage-page')) return;
      this.pageComponent.featureId = parseInt(ctx.params.featureId);
      this.pageComponent.intentStage = parseInt(ctx.params.intentStage);
      this.pageComponent.nextPage = this.currentPage;
      this.pageComponent.appTitle = this.appTitle;
      this.currentPage = ctx.path;
      this.hideSidebar();
    });
    page('/guide/stage/:featureId(\\d+)/:intentStage(\\d+)/:stageId(\\d+)', (ctx) => {
      if (!this.setupNewPage(ctx, 'chromedash-guide-stage-page')) return;
      this.pageComponent.featureId = parseInt(ctx.params.featureId);
      this.pageComponent.stageId = parseInt(ctx.params.stageId);
      this.pageComponent.intentStage = parseInt(ctx.params.intentStage);
      this.pageComponent.nextPage = this.currentPage;
      this.pageComponent.appTitle = this.appTitle;
      this.currentPage = ctx.path;
      this.hideSidebar();
    });
    page('/guide/stage/:featureId(\\d+)/metadata', (ctx) => {
      if (!this.setupNewPage(ctx, 'chromedash-guide-metadata-page')) return;
      this.pageComponent.featureId = parseInt(ctx.params.featureId);
      this.pageComponent.nextPage = this.currentPage;
      this.pageComponent.appTitle = this.appTitle;
      this.currentPage = ctx.path;
      this.hideSidebar();
    });
    page('/settings', (ctx) => {
      if (!this.setupNewPage(ctx, 'chromedash-settings-page')) return;
      this.currentPage = ctx.path;
      this.hideSidebar();
    });
    page('/metrics/:type/:view', (ctx) => {
      if (!this.setupNewPage(ctx, 'chromedash-stack-rank-page')) return;
      this.pageComponent.type = ctx.params.type;
      this.pageComponent.view = ctx.params.view;
      this.currentPage = ctx.path;
      this.hideSidebar();
    });
    page('/metrics/:type/timeline/:view/:bucketId', (ctx) => {
      if (!this.setupNewPage(ctx, 'chromedash-timeline-page')) return;
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
      if (!this.setupNewPage(ctx, 'chromedash-enterprise-page')) return;
      this.pageComponent.user = this.user;
      this.contextLink = ctx.path;
      this.currentPage = ctx.path;
      this.hideSidebar();
    });
    page('/admin/blink', (ctx) => {
      this.pageComponent = document.createElement('chromedash-admin-blink-page');
      this.pageComponent.user = this.user;
      this.contextLink = ctx.path;
      this.currentPage = ctx.path;
      this.hideSidebar();
    });
    page('/enterprise/releasenotes', (ctx) => {
      if (!this.setupNewPage(
        ctx,
        'chromedash-enterprise-release-notes-page')) return;
      this.pageComponent.user = this.user;
      this.contextLink = ctx.path;
      this.currentPage = ctx.path;
      this.hideSidebar();
    });
    page.start();
  }

  handlePagination(e) {
    updateURLParams('start', e.detail.index);
  }

  handleSearchQuery(e) {
    updateURLParams('q', e.detail.query);
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

  handleShowDrawer() {
    const drawer = this.shadowRoot.querySelector('chromedash-drawer');
    this.drawerOpen = drawer.toggleDrawerActions();
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
    let styleMargin = {'margin-left': '20px'};
    if (!IS_MOBILE && this.drawerOpen) {
      styleMargin = {'margin-left': (DRAWER_WIDTH_PX + 10) + 'px'};
    }

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
                .currentPage=${this.currentPage}
                @drawer-clicked=${this.handleShowDrawer}>
                <slot></slot>
              </chromedash-header>
            </div>
          </div>

          <div id="content">
            <div>
              <chromedash-drawer
                .user=${this.user}
                .currentPage=${this.currentPage}
                ?defaultOpen=${true}
                .googleSignInClientId=${this.googleSignInClientId}>
              </chromedash-drawer>
            </div>
            <div style=${styleMap(styleMargin)}>
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

        </div>
        <chromedash-footer></chromedash-footer>
      </div>
    `;
  }
}

customElements.define('chromedash-app', ChromedashApp);
