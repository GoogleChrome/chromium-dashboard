import {LitElement, css, html} from 'lit';
import {showToastMessage} from './utils.js';
import {SHARED_STYLES} from '../sass/shared-css.js';
import {VARS} from '../sass/_vars-css.js';
import {LAYOUT_CSS} from '../sass/_layout-css.js';
import './chromedash-admin-blink-component-listing';

export class ChromedashAdminBlinkPage extends LitElement {
  static get styles() {
    return [
      SHARED_STYLES,
      VARS,
      LAYOUT_CSS,
      css`      
      body {
          scroll-behavior: smooth;
      }

      #spinner {
          display: none !important;
      }

      #subheader .subheader_toggles {
          display: flex !important;
          justify-content: flex-end;
          flex: 1 0 auto;
      }

      #subheader ul {
          list-style-type: none;
          margin-left: var(--content-padding);
      }

      #subheader ul li {
          text-align: center;
          border-radius: var(--default-border-radius);
          box-shadow: 1px 1px 4px var(--bar-shadow-color);
          padding: .5em;
          background: var(--chromium-color-dark);
          color: #fff;
          font-weight: 500;
          text-transform: uppercase;
      }

      #subheader ul li a {
          color: inherit;
          text-decoration: none;
      }

      #subheader .view_owners_linke {
          margin-left: var(--content-padding);
      }

      #components_list {
          list-style: none;
          margin-bottom: calc(var(--content-padding) * 4);
      }

      #components_list li {
          padding: var(--content-padding) 0;
      }`];
  }
  static get properties() {
    return {
      loading: {type: Boolean},
      user: {type: Object},
      _client: {attribute: false},
      _editMode: {type: Boolean},
      components: {type: Array},
      usersMap: {type: Object},
    };
  }

  /** @type {import('chromestatus-openapi').DefaultApiInterface} */
  _client;

  /** @type {Array<import('chromestatus-openapi').OwnersAndSubscribersOfComponent>} */
  components;

  /** @type {Map<int, import('chromestatus-openapi').ComponentsUser}> */
  usersMap;

  constructor() {
    super();
    this.loading = true;
    this._editMode = false;
    this._client = window.csOpenApiClient;
  }

  connectedCallback() {
    super.connectedCallback();
    this.fetchData();
  }

  fetchData() {
    this.loading = true;
    this._client.listComponentUsers()
      .then((response) => {
        this.usersMap = new Map(response.users.map(user => [user.id, user]));
        this.components = response.components;
        this.loading = false;
      }).catch(() => {
        showToastMessage('Some errors occurred. Please refresh the page or try again later.');
      });
  }

  _onEditModeToggle() {
    this._editMode = !this._editMode;
  }

  _addComponentUserListener(e) {
    const component = Object.assign({}, this.components[e.detail.index]);
    if (e.detail.isError) {
      showToastMessage(`"Unable to add ${this.usersMap.get(e.detail.userId).name} to ${component.name}".`);
      return;
    }

    // If the user is already a subscriber, we do not want to append it.
    // We can get here if we are adding the user the owner list.
    if (!component.subscriberIds.includes(e.detail.userId)) {
      component.subscriberIds = [...component.subscriberIds, e.detail.userId];
    }
    if (e.detail.toggleAsOwner) {
      component.ownerIds = [...component.ownerIds, e.detail.userId];
    }
    showToastMessage(`"${this.usersMap.get(e.detail.userId).name} added to ${component.name}".`);
    this.components[e.detail.index] = component;
    this.requestUpdate();
  }

  _removeComponentUserListener(e) {
    const component = Object.assign({}, this.components[e.detail.index]);
    if (e.detail.isError) {
      showToastMessage(`"Unable to remove ${this.usersMap.get(e.detail.userId).name} from ${component.name}".`);
      return;
    }

    component.subscriberIds = component.subscriberIds.filter(
      (currentUserId) => e.detail.userId !== currentUserId);
    if (e.detail.toggleAsOwner) {
      component.ownerIds = component.ownerIds.filter(
        (currentUserId) => e.detail.userId !== currentUserId);
    }
    showToastMessage(`"${this.usersMap.get(e.detail.userId).name} removed from ${component.name}".`);
    this.components[e.detail.index] = component;
    this.requestUpdate();
  }

  renderSubheader() {
    return html`
      <div id="subheader">
        <div class="layout horizontal center">
          <div>
            <h2>Blink components</h2>
            ${this.loading ?
              html`<div>loading components</div>` :
              html`<div id="component-count">listing ${this.components.length} components</div>`
            }
          </div>
          <a href="/admin/subscribers" class="view_owners_linke">List by owner &amp; their features →</a>
        </div>
        <div class="layout horizontal subheader_toggles">
          <!-- <paper-toggle-button> doesn't working here. Related links:
            https://github.com/PolymerElements/paper-toggle-button/pull/132 -->
          <label><input type="checkbox" class="paper-toggle-button" ?checked="${this._editMode}" @change="${this._onEditModeToggle}">Edit mode</label>
        </div>
      </div>
    `;
  }
  scrollToPosition() {
    if (location.hash) {
      const hash = decodeURIComponent(location.hash);
      if (hash) {
        const el = this.shadowRoot.querySelector(hash);
        el.scrollIntoView(true, {behavior: 'smooth'});
      }
    }
  }
  renderComponents() {
    return html`
      <ul id="components_list">
        ${this.components.map((component, index) => html`
          <li class="layout horizontal" id="${component.name}">
            <chromedash-admin-blink-component-listing
              .id=${component.id}
              .name=${component.name}
              .subscriberIds=${component.subscriberIds ?? []}
              .ownerIds=${component.ownerIds ?? []}
              .index=${index}
              .usersMap=${this.usersMap}
              ?editing=${this._editMode}
              @adminRemoveComponentUser=${this._removeComponentUserListener}
              @adminAddComponentUser=${this._addComponentUserListener}
            ></chromedash-admin-blink-component-listing>
          </li>
        `)}
      </ul>
    `;
  }
  render() {
    return html`
      ${this.renderSubheader()}
      ${this.loading ?
              html`` :
              this.renderComponents()
      }
    `;
  }
}

customElements.define('chromedash-admin-blink-page', ChromedashAdminBlinkPage);

