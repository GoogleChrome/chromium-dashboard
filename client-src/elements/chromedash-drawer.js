import {LitElement, html, css, nothing} from 'lit';
import {ISMOBILE} from './utils';
import {SHARED_STYLES} from '../css/shared-css.js';


export class ChromedashDrawer extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        :host {
          --md-gray-100-alpha: hsla(0, 0%, 0%, 0.12);
          --md-gray-700-alpha: hsla(0, 0%, 0%, 0.62);
          --md-blue-900: #01579b;

          --nav-link-color: var(--md-gray-700-alpha);
          --nav-link-font-size: 16px;
          --nav-link-hover-background: var(--md-gray-100-alpha);
          --nav-link-border: 2px solid transparent;
          --nav-link-active-color: var(--md-blue-900);
          --nav-link-active-border: 2px solid var(--nav-link-active-color);
        }
        nav {
          display: flex;
          flex: 1;
          align-items: baseline;
          user-select: none;
          background: var(--card-background);
          border-bottom: var(--card-border);
          box-shadow: var(--card-box-shadow);
          align-items: center;
          margin: 0 var(--content-padding);
          -webkit-font-smoothing: initial;
        }
        nav a {
          text-decoration: none !important;
          cursor: pointer;
          font-size: var(--nav-link-font-size);
          text-align: left;
          padding: var(--content-padding-half) var(--content-padding);
          color: var(--nav-link-color);
          white-space: nowrap;
          border-bottom: var(--nav-link-border);
        }
        nav a:hover {
          color: black;
          background: var(--nav-link-hover-background);
        }
        nav a.disabled {
          opacity: 0.5;
          pointer-events: none;
        }
        nav [active] {
          color: var(--nav-link-active-color);
          border-bottom: var(--nav-link-active-border);
        }
        nav [active] a {
          color: var(--nav-link-active-color);
        }
        ul {
          top: 80%;
          left: 10px;
          z-index: 1;
          text-align: left;
          padding-left: 15px;
        }

        .flex-item {
          padding-top: 10px;
          padding-bottom: 10px;
          text-align: left;
        }
        .flex-item-inner {
          margin-top: -10px;
        }
        .flex-item-inner:hover {
          color: var(--nav-link-color);
          background: var(--card-background);
        }
        sl-drawer a {
          display: block;
        }
        sl-drawer::part(header) {
          display: none;
        }
        sl-button {
          margin-left: 10px;
        }
        @media only screen and (max-width: 700px) {
          header {
            --logoSize: 24px;

            margin: 0;
            display: block;
          }
          sl-drawer a {
            display: block;
          }
          sl-drawer::part(header) {
            display: none;
          }
        }
    `];
  }

  static get properties() {
    return {
      currentPage: {type: String},
      user: {type: Object},
      loading: {type: Boolean},
    };
  }

  constructor() {
    super();
    this.currentPage = '';
    this.user = {};
    this.loading = false;
  }

  isCurrentPage(href) {
    return this.currentPage.startsWith(href);
  }

  handleDrawerActions() {
    const drawer = this.shadowRoot.querySelector('.drawer-placement-start');
    if (drawer.open) {
      drawer.hide();
    } else {
      drawer.show();
    }
    return drawer.open;
  }

  renderTabs() {
    let accountMenu = nothing;
    if (ISMOBILE && !this.loading) {
      accountMenu = html`
      ${this.renderAccountMenu()}
      `;
    }

    return html`
      <sl-drawer label="Menu" placement="start" class="drawer-placement-start"
        style="--size: 300px;" contained noHeader open>
        ${accountMenu}
        <a class="flex-item" href="/roadmap" ?active=${this.isCurrentPage('/roadmap')}>Roadmap</a>
        ${this.user ? html`
          <a class="flex-item" href="/myfeatures" ?active=${this.isCurrentPage('/myfeatures')}>My features</a>
        ` : nothing}
        <a class="flex-item" href="/features" ?active=${this.isCurrentPage('/features') || this.isCurrentPage('/newfeatures')}>All features</a>
        <div class="flex-item">
          <a class="flex-item-inner">Stats</a>
          <ul>
            <li><a href="/metrics/css/popularity" ?active=${this.isCurrentPage('/metrics/css/popularity')}>CSS</a></li>
            <li><a href="/metrics/css/animated" ?active=${this.isCurrentPage('/metrics/css/animated')}>CSS Animation</a></li>
            <li><a href="/metrics/feature/popularity" ?active=${this.isCurrentPage('/metrics/feature/popularity')}>JS/HTML</a></li>
          </ul>
        </div>
      </sl-drawer>
    `;
  }

  renderAccountMenu() {
    return html`
      ${this.user ? html`
        <div class="flex-item">
          <a class="flex-item-inner">
            ${this.user.email}
          </a>
          <ul>
            <li><a href="/settings">Settings</a></li>
            <li><a href="#" id="sign-out-link" @click=${this.handleSignOutClick}>Sign out</a></li>
          </ul>
        </div>
        ${this.user.can_create_feature && !this.isCurrentPage('/guide/new') ? html`
          <sl-button class="flex-item" href="/guide/new" variant="primary" size="small">
            Create feature
          </sl-button>
        `: nothing }
      ` : html`
        <slot></slot>
      `}
    `;
  }

  render() {
    return html`
      <nav>
        ${this.renderTabs()}
      </nav>
    `;
  }
}

customElements.define('chromedash-drawer', ChromedashDrawer);
