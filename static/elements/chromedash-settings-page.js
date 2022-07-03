import {LitElement, css, html, nothing} from 'lit';
import {showToastMessage} from './utils';

export class ChromedashSettingsPage extends LitElement {
  static get styles() {
    return [
      css`
        th,
        td {
          padding: 4px;
        }
      
        input[type="submit"] {
          margin: 20px;
        }

        input[disabled] {
          opacity: 0.5;
          pointer-events: none;
        }

        #spinner {
          display: flex;
          align-items: center;
          justify-content: center;
          position: fixed;
          height: 60%;
          width: 100%;
        }

        table .helptext {
          display: block;
          font-style: italic;
          font-size: smaller;
          max-width: 40em;
          margin-top: 2px;
        }
    `];
  }

  static get properties() {
    return {
      notify_as_starrer: {type: Boolean},
      submitting: {type: Boolean},
    };
  }

  constructor() {
    super();
    this.notify_as_starrer = false;
    this.submitting = false;
  }

  connectedCallback() {
    super.connectedCallback();
    window.csClient.getSettings().then((res) => {
      this.notify_as_starrer = res.notify_as_starrer;

      // TODO(kevinshen56714): Remove this once SPA index page is set up.
      // Has to include this for now to remove the spinner at _base.html.
      document.body.classList.remove('loading');
    }).catch(() => {
      showToastMessage('Some errors occurred. Please refresh the page or try again later.');
    });
  }

  handleSubmit(e) {
    e.preventDefault();
    this.submitting = true;
    window.csClient.setSettings(this.notify_as_starrer).then(() => {
      showToastMessage('Settings saved.');
    }).catch(() => {
      showToastMessage('Unable to save the settings. Please try again.');
    }).finally(() => {
      this.submitting = false;
    });
  }

  handleChange() {
    this.notify_as_starrer = !this.notify_as_starrer;
  }

  render() {
    // TODO: Create precomiled main and forms css files,
    // and import them instead of inlining them here
    return html`
      <link rel="stylesheet" href="/static/css/main.css">
      <link rel="stylesheet" href="/static/css/forms.css">
      <div id="subheader">
        <h2>User preferences</h2>
      </div>
      <section>
        <form name="user_pref_form" @submit=${this.handleSubmit}>
          <table cellspacing=6>
            <tbody>
              <tr>
                <th>
                  <label for="id_notify_as_starrer">Notify as starrer:</label>
                </th>
                <td>
                  <chromedash-checkbox
                    id="id_notify_as_starrer"
                    name="notify_as_starrer"
                    ?checked=${this.notify_as_starrer}
                    @input=${this.handleChange}>
                  </chromedash-checkbox>
                  <span class="helptext"> Send you notification emails for features that you starred?</span>
                </td>
              </tr>
            </tbody>
          </table>
          <input type="submit" value="Submit" ?disabled=${this.submitting}>
        </form>
      </section>
      ${this.submitting ? html`
        <div class="loading">
          <div id="spinner"><img src="/static/img/ring.svg"></div>
        </div>` : nothing}
    `;
  }
}

customElements.define('chromedash-settings-page', ChromedashSettingsPage);
