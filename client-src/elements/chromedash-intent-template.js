import {LitElement, css, html, nothing} from 'lit';
import {unsafeHTML} from 'lit/directives/unsafe-html.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {showToastMessage} from './utils.js';

export class ChromedashIntentTemplate extends LitElement {
  static get properties() {
    return {
      appTitle: {type: String},
      subject: {type: String},
      intentBody: {type: String},
    };
  }

  constructor() {
    super();
    this.appTitle = '';
    this.subject = '';
    this.intentBody = '';
  }

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        #copy-email-body {
          cursor: pointer;
          color: var(--link-color);
        }
        .email-content-border {
          border: 1px solid #ddd;
          box-shadow: rgba(0, 0, 0, 0.067) 1px 1px 4px;
          margin: 8px 0 24px 0;
        }
        .email-content-div {
          background: white;
          padding: 12px;
        }
        p {
          color: #444;
        }
        h3 {
          margin-bottom: 10px;
          &:before {
            counter-increment: h3;
            content: counter(h3) '.';
            margin-right: 5px;
          }
        }
        #content section > div {
          background: white;
          border: 1px solid #ddd;
          box-shadow: rgba(0, 0, 0, 0.067) 1px 1px 4px;
          padding: 12px;
          margin: 8px 0 16px 0;
        }
        #content section > p {
          color: #444;
        }

        .email .help {
          font-style: italic;
          color: #aaa;
        }
        .email h4 {
          font-weight: 600;
        }
        .alertbox {
          margin: 2em;
          padding: 1em;
          background: var(--warning-background);
          color: var(--warning-color);
        }
        .subject {
          font-size: 16px;
        }
        table {
          tr[hidden] {
            th,
            td {
              padding: 0;
            }
          }

          th {
            padding: 12px 10px 5px 0;
            vertical-align: top;
          }

          td {
            padding: 6px 10px;
            vertical-align: top;
          }

          td:first-of-type {
            width: 60%;
          }

          .helptext {
            display: block;
            font-size: small;
            max-width: 40em;
            margin-top: 2px;
          }

          input[type='text'],
          input[type='url'],
          input[type='email'],
          textarea {
            width: 100%;
            font: var(--form-element-font);
          }

          select {
            max-width: 350px;
          }

          :required {
            border: 1px solid $chromium-color-dark;
          }

          .interacted:valid {
            border: 1px solid green;
          }

          .interacted:invalid {
            border: 1px solid $invalid-color;
          }

          input:not([type='submit']):not([type='search']) {
            outline: 1px dotted var(--error-border-color);
            background-color: #ffedf5;
          }
        }
      `,
    ];
  }

  setCopyEmailListener() {
    const copyEmailBodyEl = this.shadowRoot.querySelector('#copy-email-body');
    const emailBodyEl = this.shadowRoot.querySelector('.email');
    if (copyEmailBodyEl && emailBodyEl) {
      copyEmailBodyEl.addEventListener('click', () => {
        window.getSelection().removeAllRanges();
        const range = document.createRange();
        range.selectNode(emailBodyEl);
        window.getSelection().addRange(range);
        document.execCommand('copy');
        showToastMessage('Email body copied');
      });
    }
  }

  firstUpdated() {
    // We need to wait until the entire page is rendered, so later dependents
    // are available, hence firstUpdated is too soon.
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () =>
        setTimeout(() => {
          this.setCopyEmailListener();
        })
      );
    } else {
      this.setCopyEmailListener();
    }
  }

  renderEmailBody() {
    if (this.intentBody) {
      // Needed for rendering HTML format returned from the API.
      return unsafeHTML(this.intentBody);
    }
    return nothing;
  }

  render() {
    return html`
      <p>Email to</p>
      <div class="email-content-border">
        <div class="subject email-content-div">blink-dev@chromium.org</div>
      </div>

      <p>Subject</p>
      <div class="email-content-border">
        <div class="subject email-content-div" id="email-subject-content">
          ${this.subject}
        </div>
      </div>
      <p>
        Body
        <span
          class="tooltip copy-text"
          style="float:right"
          title="Copy text to clipboard"
        >
          <iron-icon
            icon="chromestatus:content_copy"
            id="copy-email-body"
          ></iron-icon>
        </span>
      </p>

      <div class="email-content-border">
        <div class="email email-content-div" id="email-body-content">
          ${this.renderEmailBody()}
        </div>
      </div>
    `;
  }
}

customElements.define('chromedash-intent-template', ChromedashIntentTemplate);
