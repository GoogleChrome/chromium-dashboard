import {LitElement, css, html} from 'lit';
import page from 'page';
import {SHARED_STYLES} from '../sass/shared-css.js';


class ChromedashApp extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        #content-component-wrapper[wide] {
          width: 100%;
        }
    `];
  }

  static get properties() {
    return {
      pageComponent: {type: Element},
      contextLink: {type: String}, // used for the back button in the feature page
    };
  }

  constructor() {
    super();
    this.pageComponent = null;
    this.contextLink = '/features';
  }

  connectedCallback() {
    super.connectedCallback();
    this.setUpRoutes();
  }

  setUpRoutes() {
    page.strict(true); // Be precise about trailing slashes in routes.
    const header = document.querySelector('chromedash-header');

    // SPA routing rules.  Note that rules are considered in order.
    // And :var can match any string (including a slash) if there is no slash after it.
    page('/spa', () => page.redirect('/roadmap'));
    page('/roadmap', (ctx) => {
      this.pageComponent = document.createElement('chromedash-roadmap-page');
      header.currentPage = ctx.path;
    });
    page('/myfeatures', (ctx) => {
      this.pageComponent = document.createElement('chromedash-myfeatures-page');
      this.contextLink = '/myfeatures';
      header.currentPage = ctx.path;
    });
    page('/features', (ctx) => {
      this.pageComponent = document.createElement('chromedash-all-features-page');
      this.contextLink = '/features';
      header.currentPage = ctx.path;
    });
    page('/feature/:featureId', (ctx) => {
      this.pageComponent = document.createElement('chromedash-feature-page');
      this.pageComponent.featureId = ctx.params.featureId;
      this.pageComponent.contextLink = this.contextLink;
    });
    page('/settings', (ctx) => {
      this.pageComponent = document.createElement('chromedash-settings-page');
      header.currentPage = ctx.path;
    });
    page('/metrics/:type/:view', (ctx) => {
      this.pageComponent = document.createElement('chromedash-stack-rank-page');
      this.pageComponent.type = ctx.params.type;
      this.pageComponent.view = ctx.params.view;
      header.currentPage = ctx.path;
    });
    page('/metrics/:type/timeline/:view/:bucketId', (ctx) => {
      this.pageComponent = document.createElement('chromedash-timeline-page');
      this.pageComponent.type = ctx.params.type;
      this.pageComponent.view = ctx.params.view;
      this.pageComponent.selectedBucketId = ctx.params.bucketId;
      header.currentPage = ctx.path;
    });

    page.start();
  }

  render() {
    // TODO: Create precomiled main css file and import it instead of inlining it here
    return html`
      <link rel="stylesheet" href="/static/css/main.css">
      <div id="app-content-container">
        <div>
          <div class="main-toolbar">
            <div class="toolbar-content">
              <slot name="header"></slot>
            </div>
          </div>

          <div id="content">
            <div id="spinner">
              <img src="/static/img/ring.svg">
            </div>
            <slot name="banner"></slot>
            <div id="content-flex-wrapper">
              <div id="content-component-wrapper" 
                ?wide=${this.pageComponent && this.pageComponent.tagName == 'CHROMEDASH-ROADMAP-PAGE'}>
                ${this.pageComponent}
              </div>
            </div>
          </div>

        </div>
        <chromedash-footer></chromedash-footer>
      </div>

      <chromedash-toast msg="Welcome to chromestatus.com!"></chromedash-toast>
    `;
  }
}

customElements.define('chromedash-app', ChromedashApp);

