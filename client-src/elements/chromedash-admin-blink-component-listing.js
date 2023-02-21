import {html, css, LitElement} from 'lit';
import {SHARED_STYLES} from '../sass/shared-css.js';
import {VARS} from '../sass/_vars-css.js';
import {LAYOUT_CSS} from '../sass/_layout-css.js';
import {showToastMessage} from './utils.js';
import {ContextConsumer} from '@lit-labs/context';
import {chromestatusOpenApiContext} from '../contexts/openapi-context';

export class ChromedashAdminBlinkComponentListing extends LitElement {
  static get styles() {
    return [
      SHARED_STYLES,
      VARS,
      LAYOUT_CSS,
      css`
      :host[editing] .owners_list_add_remove {
          opacity: 1;
          pointer-events: all
      }

      :host[editing] .owners_list select[multiple] {
          background-color: #fff;
          border-color: rgba(0, 0, 0, 0);
      }

      :host[editing] .owners_list select[multiple] option {
          padding-left: 4px;
      }

      .component_name {
          flex: 1 0 130px;
          margin-right: var(--content-padding);
      }

      .component_name h3 {
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
  /** @type {ContextConsumer<import("../contexts/openapi-context").chromestatusOpenApiContext>} */
  _clientConsumer;

  /** @type {import('chromestatus-openapi').ComponentsUsersComponentsInner} */
  component;

  static get properties() {
    return {
      _clientConsumer: {attribute: false},
      editing: {type: Boolean, reflect: false},
      component: {type: Object},
      index: {type: Number},
      usersMap: {type: Object},
    };
  }

  constructor() {
    super();
    this._clientConsumer = new ContextConsumer(this, chromestatusOpenApiContext, undefined, true);
  }

  _findSelectedOptionElement(e) {
    return e.target.parentElement.querySelector('.owner_candidates').selectedOptions[0];
  }

  _isOwnerCheckboxChecked(e) {
    return e.target.parentElement.querySelector('.is_primary_checkbox').checked;
  }

  _isUserInOwnerList(userId) {
    const ownersList = this.shadowRoot.querySelector(`#owner_list_${this.index}`);
    return Array.from(
      ownersList.options).find(option => option.value === userId);
  }

  _addUser(e) {
    const toggleAsOwner = this._isOwnerCheckboxChecked(e);
    const selectedCandidate = this._findSelectedOptionElement(e);

    const userId = parseInt(selectedCandidate.value);

    if (selectedCandidate.disabled) {
      alert('Please select a user before trying to add');
      return;
    }
    // Don't try to add user if they're already in the list, and we're not
    // modifying their owner state.
    if (this._isUserInOwnerList(userId) && !toggleAsOwner) {
      return;
    }

    this._clientConsumer.value.addUserToComponent(
      {componentId: component.id, userId: userId, componentUsersRequest: {owner: toggleAsOwner}})
      .then(() =>{
        this.component.subscriberIds = [...this.component.subscriberIds, userId];
        if (toggleAsOwner) {
          this.component.ownerIds = [...this.component.ownerIds, userId];
        }
        this.requestUpdate();

        showToastMessage(`"${this.usersMap.get(userId).name} added to ${this.component.name}".`);
      })
      .catch(()=> {
        showToastMessage(`"Unable to add ${this.usersMap.get(userId).name} to ${this.component.name}".`);
      });
  }
  /**
   * @param {PointerEvent} e event
   */
  _removeUser(e) {
    const toggleAsOwner = this._isOwnerCheckboxChecked(e);
    const selectedCandidate = this._findSelectedOptionElement(e);

    const userId = parseInt(selectedCandidate.value);
    if (selectedCandidate.disabled) {
      alert('Please select a user before trying to remove');
      return;
    }

    this._clientConsumer.value.removeUserFromComponent(
      {componentId: component.id, userId: userId, componentUsersRequest: {owner: toggleAsOwner}})
      .then(() =>{
        this.component.subscriberIds.filter((currentUserId) => userId !== currentUserId);
        if (toggleAsOwner) {
          this.component.ownerIds.filter((currentUserId) => userId !== currentUserId);
        }

        showToastMessage(`"${this.usersMap.get(userId).name} removed from ${this.component.name}".`);
      })
      .catch(()=> {
        showToastMessage(`"Unable to remove ${this.usersMap.get(userId).name} from ${this.component.name}".`);
      });
  }

  render() {
    return html `
      <div class="component_name">
        <div class="column_header">Component</div>
        <h3>${this.component.name}</h3>
      </div>
      <div class="owners_list layout horizontal center">
        <div>
          <div class="column_header">Receives email updates:</div>
          <select multiple disabled id="owner_list_${this.index}" size="${this.component.subscriberIds.length}">
            ${this.component.subscriberIds.map((subscriberId) => component.ownerIds.includes(subscriberId) ?
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
          <button @click="${(e) => this._addUser(e)}" class="add_owner_button"
                  data-component-name="${this.component.name}">Add</button>
          <button @click="${(e) => this._removeUser(e)}" class="remove_owner_button"
                  data-component-name="${this.component.name}">Remove</button>
        </div>
      </div>    
    `;
  }
}

customElements.define(
  'chromedash-admin-blink-component-listing', ChromedashAdminBlinkComponentListing);

