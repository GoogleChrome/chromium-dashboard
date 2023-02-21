import {LitElement, css, html} from 'lit';
import {showToastMessage} from './utils.js';
import {ContextConsumer} from '@lit-labs/context';
import {chromestatusOpenApiContext} from '../contexts/openapi-context';
import {SHARED_STYLES} from '../sass/shared-css.js';
import {VARS} from '../sass/_vars-css.js';
import {LAYOUT_CSS} from '../sass/_layout-css.js';


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

      #components_list.editing .owners_list_add_remove {
          opacity: 1;
          pointer-events: all
      }

      #components_list.editing .owners_list select[multiple] {
          background-color: #fff;
          border-color: rgba(0, 0, 0, 0);
      }

      #components_list.editing .owners_list select[multiple] option {
          padding-left: 4px;
      }

      #components_list li {
          padding: var(--content-padding) 0;
      }

      #components_list .component_name {
          flex: 1 0 130px;
          margin-right: var(--content-padding);
      }

      #components_list .component_name h3 {
          color: initial;
          padding-top: 4px
      }

      .column_header {
          margin-bottom: calc(var(--content-padding) / 2);
      }

      .owners_list {
          flex: 1 0 auto
      }

      .component_owner {
          font-weight: 600
      }

      .owners_list_add_remove {
          margin-left: calc(var(--content-padding) / 2);
          opacity: 0;
          transition: 200ms opacity cubic-bezier(0, 0, 0.2, 1);
          pointer-events: none
      }

      .owners_list_add_remove button[disabled] {
          pointer-events: none;
          opacity: .5
      }

      .remove_owner_button {
          color: darkred
      }

      select[multiple] {
          min-width: 275px;
          background-color: #eee;
          border: none;
          transition: 200ms background-color cubic-bezier(0, 0, 0.2, 1);
          font-size: inherit
      }

      select[multiple]:disabled option {
          color: initial;
          padding: 4px 0
      }`];
  }
  static get properties() {
    return {
      loading: {type: Boolean},
      user: {type: Object},
      componentSubscribersResponse: {type: Object},
      _clientConsumer: {attribute: false},
      _editMode: {type: Boolean, attribute: false},
      components: {type: Array},
      usersMap: {type: Object},
    };
  }

  /** @type {ContextConsumer<import("../contexts/openapi-context").chromestatusOpenApiContext>} */
  _clientConsumer;

  /** @type {Array<import('chromestatus-openapi').ComponentsUsersComponentsInner>} */
  components;

  /** @type {Map<int, import('chromestatus-openapi').ComponentsUsersUsersInner} */
  usersMap;

  constructor() {
    super();
    this._clientConsumer = new ContextConsumer(this, chromestatusOpenApiContext, undefined, true);
    this.loading = true;
  }

  connectedCallback() {
    super.connectedCallback();
    this.fetchData();
  }

  fetchData() {
    this.loading = true;
    this._clientConsumer.value.listComponentUsers()
      .then((response) => {
        this.usersMap = new Map(response.users.map(user => [user.id, user]));
        this.components = response.components;
        this.loading = false;
      }).catch((error) => {
        console.error(error);
        showToastMessage('Some errors occurred. Please refresh the page or try again later.');
      });
  }

  _onEditModeToggle() {
    this._editMode = !this._editMode;
    this.shadowRoot.querySelector('#components_list').classList.toggle('editing', this._editMode);
  }

  _findSelectedOptionElement(e) {
    return e.target.parentElement.querySelector('.owner_candidates').selectedOptions[0];
  }

  _isOwnerCheckboxChecked(e) {
    return e.target.parentElement.querySelector('.is_primary_checkbox').checked;
  }

  _findComponentListElement(index) {
    return this.shadowRoot.querySelector(`#owner_list_${index}`);
  }

  _isUserInOwnerList(index, userId) {
    const ownersList = this.shadowRoot.querySelector(`#owner_list_${index}`);
    return Array.from(
      ownersList.options).find(option => option.value === userId);
  }

  _addUser(e, index) {
    const toggleAsOwner = this._isOwnerCheckboxChecked(e);
    const selectedCandidate = this._findSelectedOptionElement(e);

    const userId = parseInt(selectedCandidate.value);

    if (selectedCandidate.disabled) {
      alert('Please select a user before trying to add');
      return;
    }
    // Don't try to add user if they're already in the list, and we're not
    // modifying their owner state.
    if (this._isUserInOwnerList(index, userId) && !toggleAsOwner) {
      return;
    }
    const component = this.components[index];

    this._clientConsumer.value.addUserToComponent(
      {componentId: component.id, userId: userId, componentUsersRequest: {owner: toggleAsOwner}})
      .then(() =>{
        this.components[index].subscriberIds = [...this.components[index].subscriberIds, userId];
        if (toggleAsOwner) {
          this.components[index].ownerIds = [...this.components[index].ownerIds, userId];
        }
        this.requestUpdate();

        showToastMessage(`"${this.usersMap.get(userId).name} added to ${component.name}".`);
      })
      .catch(()=> {
        showToastMessage(`"Unable to add ${this.usersMap.get(userId).name} to ${component.name}".`);
      });
  }
  /**
   * @param {PointerEvent} e event
   * @param {int} index component index
   */
  _removeUser(e, index) {
    const toggleAsOwner = this._isOwnerCheckboxChecked(e);
    const selectedCandidate = this._findSelectedOptionElement(e);

    const userId = parseInt(selectedCandidate.value);
    if (selectedCandidate.disabled) {
      alert('Please select a user before trying to remove');
      return;
    }

    const component = this.components[index];

    this._clientConsumer.value.removeUserFromComponent(
      {componentId: component.id, userId: userId, componentUsersRequest: {owner: toggleAsOwner}})
      .then(() =>{
        this.components[index].subscriberIds.filter((currentUserId) => userId !== currentUserId);
        if (toggleAsOwner) {
          this.components[index].ownerIds.filter((currentUserId) => userId !== currentUserId);
        }

        showToastMessage(`"${this.usersMap.get(userId).name} removed from ${component.name}".`);
      })
      .catch(()=> {
        showToastMessage(`"Unable to remove ${this.usersMap.get(userId).name} from ${component.name}".`);
      });
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
    const userListTemplate = [];
    for (const user of this.usersMap.values()) {
      userListTemplate.push(
        html`<option class="owner_name" value="${user.id}" data-email="${user.email}" data-name="${user.name}">${user.name}: ${user.email}</option>`);
    }
    return html`
      <ul id="components_list" ${this._editMode? html`class="editing"`: html``}>
        ${this.components.map((component, index) => html`
          <li class="layout horizontal" id="${component.name}">
            <div class="component_name">
              <div class="column_header">Component</div>
              <h3>${component.name}</h3>
            </div>
            <div class="owners_list layout horizontal center">
              <div>
                <div class="column_header">Receives email updates:</div>
                <select multiple disabled id="owner_list_${index}" size="${component.subscriberIds.length}">
                  ${component.subscriberIds.map((subscriberId) => component.ownerIds.includes(subscriberId) ?
      html `<option class="owner_name component_owner" value="${subscriberId}">${this.usersMap.get(subscriberId).name}: ${this.usersMap.get(subscriberId).email}</option>`:
      html `<option class="owner_name" value="${subscriberId}">${this.usersMap.get(subscriberId).name}: ${this.usersMap.get(subscriberId).email}</option>`,
                  )};
                </select>
              </div>
              <div class="owners_list_add_remove">
                <div>
                  <select class="owner_candidates">
                    <option selected disabled>Select owner to add/remove</option>
                    ${userListTemplate}
                  </select><br>
                  <label title="Toggles the user as an owner. If you click 'Remove' ans this is not checked, the user is removed from the component.">Owner? <input type="checkbox" class="is_primary_checkbox"></label>
                </div>
                <button @click="${(e) => this._addUser(e, index)}" class="add_owner_button" data-index="${index}"
                        data-component-name="${component.name}">Add</button>
                <button @click="${(e) => this._removeUser(e, index)}" class="remove_owner_button" data-index="${index}"
                        data-component-name="${component.name}">Remove</button>
              </div>
            </div>
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

