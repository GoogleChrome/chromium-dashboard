import {html, css, LitElement} from 'lit';
import {SHARED_STYLES} from '../sass/shared-css.js';
import {VARS} from '../sass/_vars-css.js';
import {LAYOUT_CSS} from '../sass/_layout-css.js';

export class ChromedashAdminBlinkComponentListing extends LitElement {
  static get styles() {
    return [
      SHARED_STYLES,
      VARS,
      LAYOUT_CSS,
      css`
      :host {
        display: flex;
      }

      :host([editing]) .owners_list_add_remove {
          opacity: 1;
          pointer-events: all;
      }

      :host([editing]) .owners_list select[multiple] {
          background-color: #fff;
          border-color: rgba(0, 0, 0, 0);
      }

      :host([editing]) .owners_list select[multiple] option {
          padding-left: 4px;
      }

      .component_name {
          flex: 1 0 130px;
          margin-right: var(--content-padding);
      }

      .component_name h3 {
          color: initial;
          padding-top: 4px;
      }

      .column_header {
          margin-bottom: calc(var(--content-padding) / 2);
      }

      .owners_list {
          flex: 1 0 auto;
      }

      .component_owner {
          font-weight: 600;
      }

      .owners_list_add_remove {
          margin-left: calc(var(--content-padding) / 2);
          opacity: 0;
          transition: 200ms opacity cubic-bezier(0, 0, 0.2, 1);
          pointer-events: none;
      }

      .owners_list_add_remove button[disabled] {
          pointer-events: none;
          opacity: .5;
      }

      .remove_owner_button {
          color: darkred;
      }

      select[multiple] {
          min-width: 275px;
          background-color: #eee;
          border: none;
          transition: 200ms background-color cubic-bezier(0, 0, 0.2, 1);
          font-size: inherit;
      }

      select[multiple]:disabled option {
          color: initial;
          padding: 4px 0;
      }`];
  }
  /** @type {import('chromestatus-openapi').DefaultApiInterface} */
  _client;

  static get properties() {
    return {
      _client: {attribute: false},
      editing: {type: Boolean, reflect: true},
      component: {type: Object},
      index: {type: Number},
      usersMap: {type: Object},
      id: {type: Number},
      name: {type: String},
      subscriberIds: {type: Array},
      ownerIds: {type: Array},
    };
  }

  constructor() {
    super();
    this._client = window.csOpenApiClient;
  }

  _getOptionsElement() {
    return this.shadowRoot.querySelector('.owner_candidates');
  }

  _findSelectedOptionElement() {
    return this._getOptionsElement().selectedOptions[0];
  }

  _isOwnerCheckboxChecked() {
    return this.shadowRoot.querySelector('.is_primary_checkbox').checked;
  }

  /**
   * @param {int} userId
   * @return {boolean}
   */
  _isUserInOwnerList(userId) {
    const ownersList = this.shadowRoot.querySelector(`#owner_list_${this.index}`);
    return Array.from(
      ownersList.options).find(option => parseInt(option.value) === userId);
  }

  _addUser() {
    const toggleAsOwner = this._isOwnerCheckboxChecked();
    const selectedCandidate = this._findSelectedOptionElement();

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

    let isError = false;
    this._client.addUserToComponent({
      componentId: this.id,
      userId: userId,
      componentUsersRequest: {owner: toggleAsOwner},
    })
      .then(() => {})
      .catch(()=> {
        isError = true;
      })
      .finally(() => {
        this.dispatchEvent(new CustomEvent('adminAddComponentUser', {
          detail: {
            userId: userId,
            toggleAsOwner: toggleAsOwner,
            index: this.index,
            isError: isError,
          },
          bubbles: true,
          composed: true,
        }));
      });
  }
  /**
   * @param {PointerEvent} e event
   */
  _removeUser() {
    const toggleAsOwner = this._isOwnerCheckboxChecked();
    const selectedCandidate = this._findSelectedOptionElement();

    const userId = parseInt(selectedCandidate.value);
    if (selectedCandidate.disabled) {
      alert('Please select a user before trying to remove');
      return;
    }

    // Don't try to remove user if they do not exist in the list
    if (!this._isUserInOwnerList(userId)) {
      return;
    }

    let isError = false;
    this._client.removeUserFromComponent({
      componentId: this.id,
      userId: userId,
      componentUsersRequest: {owner: toggleAsOwner},
    })
      .then(() => {})
      .catch(()=> {
        isError = true;
      })
      .finally(() => {
        this.dispatchEvent(new CustomEvent('adminRemoveComponentUser', {
          detail: {
            userId: userId,
            toggleAsOwner: toggleAsOwner,
            index: this.index,
            isError: isError,
          },
          bubbles: true,
          composed: true,
        }));
      });
  }

  _printUserDetails(userId) {
    return html`${this.usersMap.get(userId).name}: ${this.usersMap.get(userId).email}`;
  }

  render() {
    const userListTemplate = [];
    for (const user of this.usersMap.values()) {
      userListTemplate.push(
        html`<option class="owner_name" value="${user.id}" data-email="${user.email}" data-name="${user.name}">${user.name}: ${user.email}</option>`);
    }
    return html `
      <div class="component_name">
        <div class="column_header">Component</div>
        <h3>${this.name}</h3>
      </div>
      <div class="owners_list layout horizontal center">
        <div>
          <div class="column_header">Receives email updates:</div>
          <select multiple disabled id="owner_list_${this.index}" size="${this.subscriberIds.length}">
            ${this.subscriberIds.map((subscriberId) => this.ownerIds.includes(subscriberId) ?
      html `<option class="owner_name component_owner" value="${subscriberId}">${this._printUserDetails(subscriberId)}</option>`:
      html `<option class="owner_name" value="${subscriberId}">${this._printUserDetails(subscriberId)}</option>`,
            )};
          </select>
        </div>
        <div class="owners_list_add_remove">
          <div>
            <select class="owner_candidates">
              <option selected disabled data-placeholder="true">Select owner to add/remove</option>
              ${userListTemplate}
            </select><br>
            <label title="Toggles the user as an owner. If you click 'Remove' ans this is not checked, the user is removed from the component.">Owner? <input type="checkbox" class="is_primary_checkbox"></label>
          </div>
          <button @click="${this._addUser}" class="add_owner_button"
                  data-component-name="${this.name}">Add</button>
          <button @click="${this._removeUser}" class="remove_owner_button"
                  data-component-name="${this.name}">Remove</button>
        </div>
      </div>    
    `;
  }
}

customElements.define(
  'chromedash-admin-blink-component-listing', ChromedashAdminBlinkComponentListing);

