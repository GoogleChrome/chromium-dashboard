import {LitElement, css, html} from 'lit-element';
import SHARED_STYLES from '../css/shared.css';


class ChromedashUserlist extends LitElement {
  static get properties() {
    return {
      actionPath: {type: String},
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
      const formData = new FormData();
      formData.append('email', email);

      const resp = await fetch(this.actionPath, {
        method: 'POST',
        body: formData,
        credentials: 'same-origin', // Needed for admin permissions to be sent.
      });

      if (resp.status === 200) {
        alert('Thanks. But that user already exists');
        throw new Error('User already added');
      } else if (resp.status !== 201) {
        throw new Error('Sever error adding new user');
      } else {
        const json = await resp.json();
        this.addUser(json);
        formEl.reset();
      }
    }
  }

  ajaxDelete(e) {
    e.preventDefault();
    if (!confirm('Remove user?')) {
      return;
    }

    const idx = e.target.dataset.index;

    fetch(e.currentTarget.href, {
      method: 'POST',
      credentials: 'same-origin',
    }).then(() => {
      this.removeUser(idx);
    });
  }

  render() {
    return html`  
      <form id="form" name="user_form" method="POST" action="${this.actionPath}" onsubmit="return false;">
        <input type="email" placeholder="Email address" name="email" id="id_email" required>
        <td><input type="submit" @click="${this.ajaxSubmit}">
      </form>
      <ul id="user-list">
        ${this.users.map((user, index) => html`
          <li>
            <a href="${this.actionPath}/${user.id}" data-index="${index}" @click="${this.ajaxDelete}">delete</a>
            <span>${user.email}</span>
          </li>
          `)}
      </ul>
    `;
  }
}

customElements.define('chromedash-userlist', ChromedashUserlist);
