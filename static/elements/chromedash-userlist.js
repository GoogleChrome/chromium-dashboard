import {LitElement, html} from 'https://unpkg.com/@polymer/lit-element@latest/lit-element.js?module';

class ChromedashUserlist extends LitElement {
  static get properties() {
    return {
      action: {type: String},
      users: {type: Array},
    };
  }

  constructor() {
    super();
    this.users = [];
  }

  addUser(user) {
    this.splice('users', 0, 0, user);
  }

  removeUser(idx) {
    return this.splice('users', idx, 1);
  }

  ajaxSubmit(e) {
    e.preventDefault();

    if (this.$.form.checkValidity()) {
      // TODO(ericbidelman): move back to this.$.form.email.value when SD
      // polyfill merges the commit that wraps element.form.
      const email = this.$.form.querySelector('input[name="email"]').value;
      const formData = new FormData();
      formData.append('email', email);

      fetch(this.action, {
        method: 'POST',
        body: formData,
        credentials: 'same-origin', // Needed for admin permissions to be sent.
      }).then((resp) => {
        if (resp.status === 200) {
          alert('Thanks. But that user already exists');
          throw new Error('User already added');
        } else if (resp.status !== 201) {
          throw new Error('Sever error adding new user');
        }

        return resp.json();
      }).then((json) => {
        this.addUser(json);
        this.$.form.reset();
      });
    }
  }

  ajaxDelete(e) {
    e.preventDefault();
    if (!confirm('Remove user?')) {
      return;
    }

    // Get index of user model instance that was clicked from template.
    const user = e.model.user;
    const idx = this.users.indexOf(user);

    fetch(e.currentTarget.href, {
      method: 'POST',
      credentials: 'same-origin',
    }).then(() => {
      const liEl = e.currentTarget.parentElement;
      liEl.classList.add('faded');
      if ('ontransitionend' in window) {
        liEl.addEventListener('transitionend', () => {
          this.removeUser(idx);
        });
        liEl.classList.add('faded');
      } else {
        this.removeUser(idx);
      }
    });
  }

  render() {
    return html`
      <link rel="stylesheet" href="/static/css/elements/chromedash-userlist.css">

      <form id="form" name="user_form" method="post" action="${this.action}" onsubmit="return false;">
        <table>
          <tr>
            <td><input type="email" placeholder="Email address" name="email" id="id_email" required></td>
            <td><input type="submit" @click="${this.ajaxSubmit}"></td>
          </tr>
        </table>
      </form>
      <ul id="user-list">
        ${this.users.map(user => html`
          <li>
            <a href="${this.action}/${user.id}" @click="${this.ajaxDelete}">delete</a>
            <span>${user.email}</span>
          </li>
          `)}
      </ul>
    `;
  }
}

customElements.define('chromedash-userlist', ChromedashUserlist);
