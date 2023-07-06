import {LitElement, html, css, nothing} from 'lit';
import {showToastMessage, IS_MOBILE} from './utils';
import {SHARED_STYLES} from '../css/shared-css.js';


export class ChromedashHeader extends LitElement {
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

        header {
          display: flex;
          align-items: baseline;
          user-select: none;
          background: var(--card-background);
          border-bottom: var(--card-border);
          box-shadow: var(--card-box-shadow);
        }
        header a {
          text-decoration: none !important;
        }
        header nav {
          display: flex;
          flex: 1;
          align-items: center;
          margin: 0 var(--content-padding);
          -webkit-font-smoothing: initial;
        }
        header nav a {
          cursor: pointer;
          font-size: var(--nav-link-font-size);
          text-align: center;
          padding: var(--content-padding-half) var(--content-padding);
          color: var(--nav-link-color);
          white-space: nowrap;
          border-bottom: var(--nav-link-border);
        }
        header nav a:hover {
          color: black;
          background: var(--nav-link-hover-background);
        }
        header nav a.disabled {
          opacity: 0.5;
          pointer-events: none;
        }
        header nav [active] {
          color: var(--nav-link-active-color);
          border-bottom: var(--nav-link-active-border);
        }
        header nav [active] a {
          color: var(--nav-link-active-color);
        }
        header nav .nav-dropdown-container {
          position: relative;
        }
        header nav .nav-dropdown-container ul {
          display: none;
          position: absolute;
          top: 80%;
          left: 0;
          list-style: none;
          z-index: 1;
          background: var(--card-background);
          border-bottom: var(--card-border);
          box-shadow: var(--card-box-shadow);
        }
        header nav .nav-dropdown-container a {
          display: block;
        }
        header nav .nav-dropdown-container .nav-dropdown-trigger:hover + ul,
        header nav .nav-dropdown-container ul:hover {
          display: block;
        }
        header aside {
          --logoSize: 32px;

          background: url(/static/img/chrome_logo.svg) no-repeat var(--content-padding) 50%;
          background-size: var(--logoSize);
          padding: 0.75em 2em;
          padding-left: calc(var(--logoSize) + var(--content-padding) + var(--content-padding) / 2);
        }
        header aside hgroup a {
          color: var(--logo-color);
        }
        header aside h1 {
          line-height: 1;
        }
        header aside img {
          height: 45px;
          width: 45px;
          margin-right: 7px;
        }

        .flex-container {
          display: flex;
          justify-content: flex-end;
          flex-wrap: wrap;
          width: 100%;
        }

        .menu{
          margin-left: 15px;
          margin-right: 7px;
          align-items: center;
        }
        .menu:hover {
          color: black;
          background: var(--nav-link-hover-background);
        }
        .menu [active] {
          color: var(--nav-link-active-color);
          border-bottom: var(--nav-link-active-border);
        }

        @media only screen and (max-width: 700px) {
          header {
            --logoSize: 24px;

            margin: 0;
            display: flex;
          }
          header aside {
            display: flex;
            padding: var(--content-padding-half);
            border-radius: 0;
            background: inherit;
          }
        }
    `];
  }

  static get properties() {
    return {
      appTitle: {type: String},
      googleSignInClientId: {type: String},
      currentPage: {type: String},
      user: {type: Object},
      loading: {type: Boolean},
    };
  }

  constructor() {
    super();
    this.appTitle = '';
    this.googleSignInClientId = '',
    this.currentPage = '';
    this.user = {};
    this.loading = false;
  }

  connectedCallback() {
    super.connectedCallback();
    // The user sign-in is desktop only.
    if (IS_MOBILE) {
      return;
    }

    // user is passed in from chromedash-app
    if (this.user && this.user.email) return;

    // user is passed in from chromedash-app, but the user is not logged in
    if (!this.user) {
      this.initializeGoogleSignIn();
      return;
    };

    // user is not passed in from anywhere, i.e. this.user is still {}
    // this is for MPA pages where this component is initialized in _base.html
    this.loading = true;
    window.csClient.getPermissions().then((user) => {
      this.user = user;
      if (!this.user) this.initializeGoogleSignIn();
    }).catch(() => {
      showToastMessage('Some errors occurred. Please refresh the page or try again later.');
    }).finally(() => {
      this.loading = false;
    });
  }

  initializeGoogleSignIn() {
    google.accounts.id.initialize({
      client_id: this.googleSignInClientId,
      callback: this.handleCredentialResponse,
    });
    google.accounts.id.prompt();

    // Google Identity Services Library cannot find elements in a shadow DOM,
    // so we create signInButton element at the document level and insert it
    // in the light DOM of the header, which will be rendered in the <slot> below
    const signInButton = document.createElement('div');
    google.accounts.id.renderButton(signInButton, {type: 'standard'});
    const appComponent = document.querySelector('chromedash-app');
    if (appComponent) {
      appComponent.insertAdjacentElement('afterbegin', signInButton); // for SPA
    } else {
      this.insertAdjacentElement('afterbegin', signInButton); // for MPA
    }
  }

  handleCredentialResponse(credentialResponse) {
    window.csClient.signIn(credentialResponse)
      .then(() => {
        window.location.replace(window.location.href.split('?')[0]);
      })
      .catch(() => {
        console.error('Sign in failed, so signing out to allow retry');
        signOut();
      });
  }

  handleSignOutClick(e) {
    e.preventDefault();
    this.signOut();
  }

  signOut() {
    window.csClient.signOut().then(() => {
      window.location.reload();
    });
  }

  isCurrentPage(href) {
    return this.currentPage.startsWith(href);
  }

  _fireEvent(eventName, detail) {
    const event = new CustomEvent(eventName, {
      bubbles: true,
      composed: true,
      detail,
    });
    this.dispatchEvent(event);
  }

  handleDrawer() {
    this._fireEvent('drawer-clicked', {});
  }

  renderAccountMenu() {
    return html`
      ${this.user ? html`
        ${this.user.can_create_feature && !this.isCurrentPage('/guide/new') ? html`
          <sl-button href="/guide/new" variant="primary" size="small">
            Create feature
          </sl-button>
        `: nothing }
        <div class="nav-dropdown-container">
          <a class="nav-dropdown-trigger">
            ${this.user.email}
            <iron-icon icon="chromestatus:arrow-drop-down"></iron-icon>
          </a>
          <ul>
            <li><a href="/settings">Settings</a></li>
            <li><a href="#" id="sign-out-link" @click=${this.handleSignOutClick}>Sign out</a></li>
          </ul>
        </div>
      ` : html`
        <slot></slot>
      `}
    `;
  }

  render() {
    let accountMenu = nothing;
    if (!IS_MOBILE && !this.loading) {
      accountMenu = html`
      <div class="flex-container">
        ${this.renderAccountMenu()}
      </div>`;
    }

    return html`
      <header>
        <sl-icon-button variant="text" library="material" class="menu"
          style="font-size: 1.2rem;" name="menu_20px" @click="${this.handleDrawer}">
        </sl-icon-button >
        <aside>
          <hgroup>
            <a href="/features" target="_top"><h1>${this.appTitle}</h1></a>
          </hgroup>
        </aside>
        <nav>
          ${accountMenu}
        </nav>
      </header>
    `;
  }
}

customElements.define('chromedash-header', ChromedashHeader);
