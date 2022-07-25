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
    page('/roadmap', () => {
      this.pageComponent = document.createElement('chromedash-roadmap-page');
      header.currentPage = '/roadmap';
    });
    page('/myfeatures', () => {
      this.pageComponent = document.createElement('chromedash-myfeatures-page');
      this.contextLink = '/myfeatures';
      header.currentPage = '/myfeatures';
    });
    page('/features', () => {
      this.pageComponent = document.createElement('chromedash-all-features-page');
      this.contextLink = '/features';
      header.currentPage = '/features';
    });
    page('/feature/:featureId', (ctx) => {
      this.pageComponent = document.createElement('chromedash-feature-page');
      this.pageComponent.featureId = ctx.params.featureId;
      this.pageComponent.contextLink = this.contextLink;
    });
    page('/settings', () => {
      this.pageComponent = document.createElement('chromedash-settings-page');
    });
    page('/metrics/feature/popularity', () => {
      this.pageComponent = document.createElement('chromedash-stack-rank-page');
      this.pageComponent.type = 'feature';
      this.pageComponent.view = 'popularity';
      header.currentPage = '/metrics';
    });
    page('/metrics/css/popularity', () => {
      this.pageComponent = document.createElement('chromedash-stack-rank-page');
      this.pageComponent.type = 'css';
      this.pageComponent.view = 'popularity';
      header.currentPage = '/metrics';
    });
    page('/metrics/css/animated', () => {
      this.pageComponent = document.createElement('chromedash-stack-rank-page');
      this.pageComponent.type = 'css';
      this.pageComponent.view = 'animated';
      header.currentPage = '/metrics';
    });
    page('/metrics/feature/timeline/popularity/:bucketId', (ctx) => {
      this.pageComponent = document.createElement('chromedash-timeline-page');
      this.pageComponent.type = 'feature';
      this.pageComponent.view = 'popularity';
      this.pageComponent.selectedBucketId = ctx.params.bucketId;
      header.currentPage = '/metrics';
    });
    page('/metrics/css/timeline/popularity/:bucketId', (ctx) => {
      this.pageComponent = document.createElement('chromedash-timeline-page');
      this.pageComponent.type = 'css';
      this.pageComponent.view = 'popularity';
      this.pageComponent.selectedBucketId = ctx.params.bucketId;
      header.currentPage = '/metrics';
    });
    page('/metrics/css/timeline/animated/:bucketId', (ctx) => {
      this.pageComponent = document.createElement('chromedash-timeline-page');
      this.pageComponent.type = 'css';
      this.pageComponent.view = 'animated';
      this.pageComponent.selectedBucketId = ctx.params.bucketId;
      header.currentPage = '/metrics';
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

