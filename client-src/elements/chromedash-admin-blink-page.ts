import {LitElement, css, html} from 'lit';
import {showToastMessage} from './utils.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {VARS} from '../css/_vars-css.js';
import {LAYOUT_CSS} from '../css/_layout-css.js';
import {customElement, property, state} from 'lit/decorators.js';
import './chromedash-admin-blink-component-listing';
import {
  DefaultApiInterface,
  OwnersAndSubscribersOfComponent,
  ComponentsUser,
} from 'chromestatus-openapi';

@customElement('chromedash-admin-blink-page')
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
          padding: 0.5em;
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
        }
      `,
    ];
  }

  @property({type: Boolean})
  loading = true;
  @property({type: Object})
  user = null;
  @property({type: Boolean})
  _editMode = false;
  @state()
  components: OwnersAndSubscribersOfComponent[] | undefined;
  @state()
  usersMap!: Map<number, ComponentsUser>;

  _client: DefaultApiInterface = window.csOpenApiClient;

  connectedCallback() {
    super.connectedCallback();
    this.fetchData();
  }

  fetchData() {
    this.loading = true;
    this._client
      .listComponentUsers()
      .then(response => {
        this.usersMap = new Map(response.users!.map(user => [user.id, user]));
        this.components = response.components;
        this.loading = false;
      })
      .catch(() => {
        showToastMessage(
          'Some errors occurred. Please refresh the page or try again later.'
        );
      });
  }

  _onEditModeToggle() {
    this._editMode = !this._editMode;
  }

  _addComponentUserListener(e) {
    const component = Object.assign({}, this.components![e.detail.index]);
    if (e.detail.isError) {
      showToastMessage(
        `"Unable to add ${this.usersMap.get(e.detail.userId)!.name} to ${component.name}".`
      );
      return;
    }

    // If the user is already a subscriber, we do not want to append it.
    // We can get here if we are adding the user the owner list.
    if (!component.subscriber_ids?.includes(e.detail.userId)) {
      component.subscriber_ids = [
        ...(component.subscriber_ids ?? []),
        e.detail.userId,
      ];
    }
    if (e.detail.toggleAsOwner) {
      component.owner_ids = [...(component.owner_ids ?? []), e.detail.userId];
    }
    showToastMessage(
      `"${this.usersMap.get(e.detail.userId)!.name} added to ${component.name}".`
    );
    this.components![e.detail.index] = component;
    this.requestUpdate();
  }

  _removeComponentUserListener(e) {
    const component = Object.assign({}, this.components![e.detail.index]);
    if (e.detail.isError) {
      showToastMessage(
        `"Unable to remove ${this.usersMap.get(e.detail.userId)!.name} from ${component.name}".`
      );
      return;
    }

    component.subscriber_ids = component.subscriber_ids!.filter(
      currentUserId => e.detail.userId !== currentUserId
    );
    if (e.detail.toggleAsOwner) {
      component.owner_ids = component.owner_ids!.filter(
        currentUserId => e.detail.userId !== currentUserId
      );
    }
    showToastMessage(
      `"${this.usersMap.get(e.detail.userId)!.name} removed from ${component.name}".`
    );
    this.components![e.detail.index] = component;
    this.requestUpdate();
  }

  renderSubheader() {
    return html`
      <div id="subheader">
        <div class="layout horizontal center">
          <div>
            <h2>Blink components</h2>
            ${this.loading
              ? html`<div>loading components</div>`
              : html`<div id="component-count">
                  listing ${this.components!.length} components
                </div>`}
          </div>
        </div>
        <div class="layout horizontal subheader_toggles">
          <!-- <paper-toggle-button> doesn't working here. Related links:
            https://github.com/PolymerElements/paper-toggle-button/pull/132 -->
          <label
            ><input
              type="checkbox"
              class="paper-toggle-button"
              ?checked="${this._editMode}"
              @change="${this._onEditModeToggle}"
            />Edit mode</label
          >
        </div>
      </div>
    `;
  }
  scrollToPosition() {
    if (location.hash) {
      const hash = decodeURIComponent(location.hash);
      if (hash) {
        const el = this.shadowRoot!.querySelector(hash);
        el!.scrollIntoView({behavior: 'smooth'});
      }
    }
  }
  renderComponents() {
    return html`
      <ul id="components_list">
        ${this.components!.map(
          (component, index) => html`
            <li class="layout horizontal" id="${component.name}">
              <chromedash-admin-blink-component-listing
                .componentId=${component.id}
                .name=${component.name}
                .subscriberIds=${component.subscriber_ids ?? []}
                .ownerIds=${component.owner_ids ?? []}
                .index=${index}
                .usersMap=${this.usersMap}
                ?editing=${this._editMode}
                @adminRemoveComponentUser=${this._removeComponentUserListener}
                @adminAddComponentUser=${this._addComponentUserListener}
              ></chromedash-admin-blink-component-listing>
            </li>
          `
        )}
      </ul>
    `;
  }
  render() {
    return html`
      ${this.renderSubheader()}
      ${this.loading ? html`` : this.renderComponents()}
    `;
  }
}
