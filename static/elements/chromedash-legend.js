import {LitElement, css, html} from 'lit-element';
import {nothing} from 'lit-html';
import '@polymer/iron-icon';
import './chromedash-color-status';
import SHARED_STYLES from '../css/shared.css';

// This element implements the help dialog that appears when the user
// clicks on the '?' icon near the search field.

class ChromedashLegend extends LitElement {
  static get properties() {
    return {
      opened: {type: Boolean, reflect: true},
      views: {attribute: false}, // Assigned in features-page.js, value from Django
    };
  }

  static get styles() {
    return [
      SHARED_STYLES,
      css`
      :host {
        position: fixed;
        top: 0;
        bottom: 0;
        left: 0;
        right: 0;
        display: flex;
        justify-content: center;
        align-items: center;
        visibility: hidden;
      }

      :host::after {
        position: absolute;
        top: 0;
        bottom: 0;
        left: 0;
        right: 0;
        z-index: -1;
        content: '';
        transition: opacity 300ms;
        background: #000;
        opacity: 0;
        pointer-events: none;
        will-change: opacity;
      }

      :host([opened]) {
        visibility: visible;
        z-index: 1;
      }

      :host([opened])::after {
        opacity: 0.6;
      }

      #overlay {
        background: #fff;
        padding: 16px;
        position: relative;
        width: 100%;
        height: 100%;
        overflow: auto;
      }

      h3 {
        border-bottom: var(--heading-underbar);
        padding: 0 !important;
      }

      ul {
        margin: 0 0 15px 0;
      }

      ul > li {
        margin: 5px 0;
      }

      label {
        font-weight: 500;
        text-transform: uppercase;
      }

      section {
        margin-top: 10px;
      }
      section.views {
        display: flex;
      }
      section.views > div {
        flex: 1 0 0;
      }
      section.views li > span {
        margin-left: 3px;
      }

      .queries li span {
        margin-right: 5px;
        width: 260px;
        display: inline-block;
      }

      p {
        margin-top: 5px;
      }

      .close {
        background: transparent;
        border: 0;
        position: absolute;
        top: var(--content-padding-half);
        right: var(--content-padding-half);
        cursor: pointer;
      }

      @media only screen and (min-width: 701px) {
        #overlay {
          width: 80vw;
          max-height: 80vh;
        }
      }
    `];
  }

  toggle() {
    this.opened = !this.opened;
    document.body.style.overflow = this.opened ? 'opened' : '';
  }

  render() {
    if (!this.views) {
      return nothing;
    }
    return html`
      <div id="overlay">
        <h3>About the data</h3>
        <section class="content-wrapper">
          <p class="description">What you're looking at is a mostly
          comprehensive list of web platform features that have landed in
          Chromium, ordered chronologically by the milestone in which they were
          added. Features marked "No active development" are being considered or
          have yet to be started. Features marked "In development" are currently
          being worked on.</p>
          <button class="close buttons" @click=${this.toggle}>
            <iron-icon icon="chromestatus:close"></iron-icon>
          </button>
        </section>
        <h3>Color legend</h3>
        <p>Colors indicate the "interoperability risk" for a given feature. The
          risk increases as
          <chromedash-color-status value="0"
              .max="${this.views.vendors.length}"></chromedash-color-status> →
          <chromedash-color-status .value="${this.views.vendors.length}"
              .max="${this.views.vendors.length}"></chromedash-color-status>, and the
          color meaning differs for browser vendors, web developers, and the
          standards process.</p>
        <section class="views">
          <div>
            <p>Browser vendors</p>
            <ul>
              ${this.views.vendors.map((vendor) => html`
                <li>
                  <chromedash-color-status .value="${vendor.key}"
                                           .max="${this.views.vendors.length}">
                                           </chromedash-color-status>
                  <span>${vendor.val}</span></li>
                `)}
            </ul>
          </div>
          <div>
            <p>Web developer</p>
            <ul>
              ${this.views.webdevs.map((webdev) => html`
                <li>
                  <chromedash-color-status .value="${webdev.key}"
                                           .max="${this.views.webdevs.length}">
                                           </chromedash-color-status>
                  <span>${webdev.val}</span></li>
                `)}
            </ul>
          </div>
        </section>
        <h3>Search</h3>
        <section>
          <p>Example search queries</p>
          <ul class="queries">
            <li>
              <span>"browsers.chrome.desktop&lt;30"</span>features that landed before 30
            </li>
            <li>
              <span>"browsers.chrome.desktop&lt;=50"</span>features in desktop chrome 50
            </li>
            <li>
              <span>"browsers.chrome.android&gt;40"</span>features that landed on Chrome Android after 40 (milestone types: browsers.chrome.android, browsers.chrome.ios, browsers.chrome.webview)
            </li>
            <li>
              <span>"browsers.chrome.status.val=4"</span>features behind a flag
            </li>
            <li>
              <span>"category:CSS"</span>features in the CSS category
            </li>
            <li>
              <span>"component:Blink>CSS"</span>features under the Blink component "Blink>CSS"
            </li>
            <li>
              <span>"browsers.chrome.owners:user@example.org"</span>features owned by user@example.org
            </li>
          </ul>
        </section>
      </div>
    `;
  }
}

customElements.define('chromedash-legend', ChromedashLegend);
