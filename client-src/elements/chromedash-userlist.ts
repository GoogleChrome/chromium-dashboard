import {LitElement, css, html, nothing} from 'lit';
import {customElement, state} from 'lit/decorators.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {User} from '../js-src/cs-client.js';

@customElement('chromedash-userlist')
class ChromedashUserlist extends LitElement {
  @state()
  users: User[] = [];

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        form {
          padding: var(--content-padding);
          background: var(--card-background);
          border: var(--card-border);
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
      `,
    ];
  }

  addUser(user) {
    this.users.splice(0, 0, user);
    this.users = this.users.slice(0); // Refresh the list
  }

  removeUser(idx) {
    this.users.splice(idx, 1);
    this.users = this.users.slice(0); // Refresh the list
  }

  sortUsers() {
    this.users.sort((a, b) => {
      if (
        (a.is_admin && !b.is_admin) ||
        (a.is_site_editor && !b.is_site_editor && !b.is_admin)
      ) {
        return -1;
      }
      if (
        (b.is_admin && !a.is_admin) ||
        (b.is_site_editor && !a.is_site_editor && !a.is_admin)
      ) {
        return 1;
      }
      return a.email.localeCompare(b.email);
    });
  }

  _onAdminToggle() {
    const formEl = this.renderRoot.querySelector('form');
    const adminCheckbox = formEl?.querySelector(
      'input[name="is_admin"]',
    ) as HTMLInputElement;
    const siteEditorCheckbox = formEl?.querySelector(
      'input[name="is_site_editor"]',
    ) as HTMLInputElement;
    // Admins will always be site editors, so if the admin box is checked,
    // the site editor box is also checked and disabled.
    if (adminCheckbox.checked) {
      siteEditorCheckbox.checked = true;
      siteEditorCheckbox.disabled = true;
    } else {
      siteEditorCheckbox.disabled = false;
    }
  }

  // TODO(jrobbins): Change this to be a JSON API call via csClient.
  async ajaxSubmit(e) {
    e.preventDefault();
    const formEl = this.renderRoot.querySelector('form')!;

    if (formEl.checkValidity()) {
      const emailInput = formEl.querySelector(
        'input[name="email"]',
      ) as HTMLInputElement;
      const adminCheckbox = formEl.querySelector(
        'input[name="is_admin"]',
      ) as HTMLInputElement;
      const siteEditorCheckbox = formEl.querySelector(
        'input[name="is_site_editor"]',
      ) as HTMLInputElement;
      const email = emailInput?.value;
      const isAdmin = adminCheckbox?.checked;
      const isSiteEditor = siteEditorCheckbox?.checked;
      window.csClient.createAccount(email, isAdmin, isSiteEditor).then(json => {
        if (json.error_message) {
          alert(json.error_message);
        } else {
          this.addUser(json);
          formEl.reset();
          (
            formEl.querySelector(
              'input[name="is_site_editor"]',
            ) as HTMLInputElement
          ).disabled = false;
        }
      });
    }
  }

  ajaxDelete(e) {
    e.preventDefault();
    if (!confirm('Remove user?')) {
      return;
    }

    const idx = e.target.dataset.index;
    window.csClient.deleteAccount(e.target.dataset.account).then(() => {
      this.removeUser(idx);
    });
  }

  render() {
    this.sortUsers();
    return html`
      <form id="form" name="user_form" method="post">
        <div>
          <input
            type="email"
            placeholder="Email address"
            name="email"
            required
          />
        </div>
        <div>
          <label
            ><input
              type="checkbox"
              name="is_admin"
              @click="${this._onAdminToggle}"
            />
            User is admin</label
          >
        </div>
        <div>
          <label
            ><input type="checkbox" name="is_site_editor" /> User is site
            editor</label
          >
        </div>
        <div>
          <input type="submit" @click="${this.ajaxSubmit}" value="Add user" />
        </div>
      </form>

      <ul id="user-list">
        ${this.users.map(
          (user, index) => html`
            <li>
              <a
                href="#"
                data-index="${index}"
                data-account="${user.id}"
                @click="${this.ajaxDelete}"
                >delete</a
              >
              ${user.is_admin ? html`(admin)` : nothing}
              ${!user.is_admin && user.is_site_editor
                ? html`(site editor)`
                : nothing}
              <span>${user.email}</span>
            </li>
          `,
        )}
      </ul>
    `;
  }
}
