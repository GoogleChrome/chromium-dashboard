import {LitElement, css, html} from 'lit-element';
import SHARED_STYLES from '../css/shared.css';
import {nothing} from 'lit-html';


class ChromedashUserlist extends LitElement {
  static get properties() {
    return {
      actionPath: {type: String},
      token: {type: String},
      users: {attribute: false},
    };
  }

  constructor() {
    super();
    this.users = [];
  }

  static get styles() {
    return [
      SHARED_STYLES,
      css`
      form {
        padding: var(--content-padding);
        background: var(--card-background);
        border: var(--card-border);
        box-shadow: var(--card-box-shadow);
        margin-bottom: var(--content-padding);
        max-width: 20em;
      }
      form > * + * {
        margin-top: var(--content-padding-half);
      }

      ul {
        margin-top: 10px;
      }
      ul li {
        transition: opacity 600ms ease-in-out;
        margin-bottom: 5px;
      }
      ul li.faded {
         opacity: 0;
      }
      ul li a {
        margin-right: 10px;
      }
    `];
  }

  addUser(user) {
    this.users.splice(0, 0, user);
    this.users = this.users.slice(0); // Refresh the list
  }

  removeUser(idx) {
    this.users.splice(idx, 1);
    this.users = this.users.slice(0); // Refresh the list
  }

  async ajaxSubmit(e) {
    e.preventDefault();
    const formEl = this.shadowRoot.querySelector('form');

    if (formEl.checkValidity()) {
      const email = formEl.querySelector('input[name="email"]').value;
      const isAdmin = formEl.querySelector('input[name="is_admin"]').checked;
      const formData = new FormData();
      formData.append('email', email);
      if (isAdmin) {
        formData.append('is_admin', 'on');
      }
      formData.append('token', this.token);

      const resp = await fetch(this.actionPath, {
        method: 'POST',
        body: formData,
        credentials: 'same-origin', // Needed for admin permissions to be sent.
      });

      if (resp.status !== 200) {
        throw new Error('Server error adding new user');
      } else {
        const json = await resp.json();
        if (json.error_message) {
          alert(json.error_message);
        } else {
          this.addUser(json);
          formEl.reset();
        }
      }
    }
  }

  ajaxDelete(e) {
    e.preventDefault();
    if (!confirm('Remove user?')) {
      return;
    }

    const idx = e.target.dataset.index;
    const formData = new FormData();
    formData.append('token', this.token);

    fetch(e.currentTarget.href, {
      method: 'POST',
      body: formData,
      credentials: 'same-origin',
    }).then(() => {
      this.removeUser(idx);
    });
  }

  render() {
    return html`
      <form id="form" name="user_form" method="POST" action="${this.actionPath}" onsubmit="return false;">
        <div>
          <input type="email" placeholder="Email address" name="email"
                 required>
        </div>
        <div>
          <label><input type="checkbox" name="is_admin"> User is admin</label>
        </div>
        <div>
          <input type="submit" @click="${this.ajaxSubmit}" value="Add user">
        </div>
      </form>

      <ul id="user-list">
        ${this.users.map((user, index) => html`
          <li>
            <a href="/admin/users/delete/${user.id}"
               data-index="${index}" @click="${this.ajaxDelete}">delete</a>
            <span>${user.email}</span>
            ${user.is_admin ? html`(admin)` : nothing}
          </li>
          `)}
      </ul>
    `;
  }
}

customElements.define('chromedash-userlist', ChromedashUserlist);
