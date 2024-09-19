import {SlDrawer} from '@shoelace-style/shoelace';
import {LitElement, TemplateResult, css, html, nothing} from 'lit';
import {customElement, property, state} from 'lit/decorators.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {User} from '../js-src/cs-client.js';
import {IS_MOBILE, showToastMessage} from './utils';

export const DRAWER_WIDTH_PX = 200;

@customElement('chromedash-drawer')
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
          --nav-link-hover-background: var(--md-gray-50-alpha);
          --nav-link-active-color: var(--md-blue-900);
          --nav-link-active-background: var(--light-accent-color);
        }
        nav {
          display: flex;
          flex: 1;
          align-items: baseline;
          user-select: none;
          background: var(--card-background);
          border: none;
          align-items: center;
          margin: 0 var(--content-padding-half);
          -webkit-font-smoothing: initial;
        }
        nav a {
          text-decoration: none !important;
          cursor: pointer;
          font-size: var(--nav-link-font-size);
          text-align: left;
          padding: var(--content-padding-half);
          color: var(--nav-link-color);
          white-space: nowrap;
          border-radius: var(--pill-border-radius);
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
          background: var(--nav-link-active-background);
        }
        nav [active]:hover {
          background: var(--md-gray-100-alpha);
        }
        hr {
          margin: 15px var(--content-padding-half);
        }

        .section-header {
          margin: 0px var(--content-padding-half) 10px;
          font-weight: bold;
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
      `,
    ];
  }

  @property({type: String})
  currentPage = '';
  @property({type: String})
  devMode = 'False';
  @property({type: String})
  googleSignInClientId = '';
  @property({type: Boolean})
  defaultOpen = false;
  @state()
  user!: User;
  @state()
  loading = false;

  connectedCallback() {
    super.connectedCallback();

    // user is passed in from chromedash-app
    if (this.user && this.user.email) return;

    // Try to load user.
    this.loading = true;
    window.csClient
      .getPermissions()
      .then(user => {
        this.user = user;
        // If it is on mobile, log-in is intialized in this component.
        // Othewise, log-in is initialized in chromedash-header.
        if (!this.user && IS_MOBILE) {
          if (!window['isPlaywright']) {
            this.initializeGoogleSignIn();
          }
          if (this.devMode == 'True') {
            // Insert the testing signin second, so it appears to the left
            // of the google signin button, with a large margin on the right.
            this.initializeTestingSignIn();
          }
        }
      })
      .catch(() => {
        showToastMessage(
          'Some errors occurred. Please refresh the page or try again later.'
        );
      })
      .finally(() => {
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
    // in this DOM, which will be rendered in the <slot> below
    const signInButton = document.createElement('div');
    google.accounts.id.renderButton(signInButton, {type: 'standard'});
    this.insertAdjacentElement('afterbegin', signInButton);
  }

  initializeTestingSignIn() {
    // Create DEV_MODE login button for testing
    const signInTestingButton = document.createElement('button');
    signInTestingButton.innerText = 'Sign in as example@chromium.org';
    signInTestingButton.setAttribute('type', 'button');
    signInTestingButton.setAttribute('data-testid', 'dev-mode-sign-in-button');
    signInTestingButton.setAttribute(
      'style',
      'position:fixed; right:0; z-index:1000; background: lightblue; border: 1px solid blue;'
    );

    signInTestingButton.addEventListener('click', () => {
      // POST to '/dev/mock_login' to login as example@chromium.
      fetch('/dev/mock_login', {method: 'POST'})
        .then(response => {
          if (!response.ok) {
            throw new Error(`Sign in failed! Response: ${response.status}`);
          }
        })
        .then(() => {
          setTimeout(() => {
            const url = window.location.href.split('?')[0];
            window.location.href = url;
          }, 1000);
        })
        .catch(error => {
          console.error('Sign in failed.', error);
        });
    });

    const signInButtonContainer = document.querySelector('body');
    if (signInButtonContainer) {
      signInButtonContainer.insertAdjacentElement(
        'afterbegin',
        signInTestingButton
      ); // for SPA
    }
  }

  handleCredentialResponse(credentialResponse) {
    window.csClient
      .signIn(credentialResponse)
      .then(() => {
        setTimeout(() => {
          const url = window.location.href.split('?')[0];
          window.location.href = url;
        }, 1000);
      })
      .catch(() => {
        console.error('Sign in failed, so signing out to allow retry');
        this.signOut();
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

  userCanApprove() {
    return (
      this.user &&
      (this.user.is_admin || this.user.approvable_gate_types?.length > 0)
    );
  }

  isCurrentPage(href) {
    return this.currentPage.startsWith(href);
  }

  toggleDrawerActions() {
    const drawer = this.shadowRoot!.querySelector(
      '.drawer-placement-start'
    ) as SlDrawer;
    if (drawer.open) {
      drawer.hide();
    } else {
      drawer.show();
    }
    return drawer.open;
  }

  renderNavItem(url, label) {
    return html`<a href="${url}" ?active=${this.isCurrentPage(url)}
      >${label}</a
    >`;
  }

  renderDrawer() {
    let accountMenu: typeof nothing | TemplateResult = nothing;
    if (IS_MOBILE && !this.loading) {
      accountMenu = this.renderAccountMenu();
    }

    const myFeaturesMenu = this.renderMyFeaturesMenu();
    const adminMenu = this.renderAdminMenu();

    return html`
      <sl-drawer
        label="Menu"
        placement="start"
        class="drawer-placement-start"
        style="--size: ${DRAWER_WIDTH_PX}px;"
        contained
        noHeader
        ?open=${!IS_MOBILE && this.defaultOpen}
      >
        ${accountMenu} ${this.renderNavItem('/roadmap', 'Roadmap')}
        ${this.renderNavItem('/features', 'All features')} ${myFeaturesMenu}
        <hr />
        <div class="section-header">Stats</div>
        ${this.renderNavItem('/metrics/css/popularity', 'CSS')}
        ${this.renderNavItem('/metrics/css/animated', 'CSS Animation')}
        ${this.renderNavItem('/metrics/feature/popularity', 'JS/HTML')}
        <hr />
        <div class="section-header">Reports</div>
        ${this.renderNavItem('/reports/spec_mentors', 'Spec Mentors')}
        ${this.renderNavItem('/reports/external_reviews', 'External Reviews')}
        ${adminMenu}
      </sl-drawer>
    `;
  }

  renderAccountMenu() {
    if (!this.user) {
      return nothing;
    }

    return html`
      <div class="section-header">${this.user.email}</div>
      <a href="/settings">Settings</a>
      <a
        href="#"
        id="sign-out-link"
        data-testid="sign-out-link"
        @click=${this.handleSignOutClick}
        >Sign out</a
      >
      ${this.user.can_create_feature && !this.isCurrentPage('/guide/new')
        ? html`
            <sl-button
              data-testid="create-feature-button"
              href="/guide/new"
              variant="primary"
              size="small"
            >
              Create feature
            </sl-button>
          `
        : nothing}
      <hr />
    `;
  }

  renderMyFeaturesMenu() {
    if (!this.user?.email) {
      return nothing;
    }

    return html`
      <hr />
      <div class="section-header">My features</div>
      ${this.userCanApprove()
        ? this.renderNavItem('/myfeatures/review', 'Pending review')
        : nothing}
      ${this.renderNavItem('/myfeatures/starred', 'Starred')}
      ${this.renderNavItem('/myfeatures/editable', 'Owner / editor')}
    `;
  }
  renderAdminMenu() {
    if (!this.user?.is_admin) {
      return nothing;
    }

    return html`
      <hr />
      <div class="section-header">Admin</div>
      ${this.renderNavItem('/admin/users/new', 'Users')}
      ${this.renderNavItem('/admin/ot_requests', 'OT requests')}
      ${this.renderNavItem('/admin/feature_links', 'Feature links')}
      ${this.renderNavItem('/reports/feature-latency', 'Feature latency')}
      ${this.renderNavItem('/reports/review-latency', 'Review latency')}
      ${this.renderNavItem('/admin/blink', 'Subscriptions')}
      ${this.renderNavItem('/admin/find_stop_words', 'Find stop words JSON')}
    `;
  }

  render() {
    return html` <nav>${this.renderDrawer()}</nav> `;
  }
}
