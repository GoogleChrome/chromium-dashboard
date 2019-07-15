import {LitElement, html} from 'lit-element';
import './chromedash-color-status';

class ChromedashLegend extends LitElement {
  static get properties() {
    return {
      opened: {type: Boolean, reflect: true}, // Used to control visibility. See the css
      views: {type: Object}, // Assigned in features-page.js, value from Django
    };
  }

  constructor() {
    super();
    this.views = {};
  }

  toggle() {
    this.opened = !this.opened;
    document.body.style.overflow = this.opened ? 'opened' : '';
  }

  render() {
    return html`
      <link rel="stylesheet" href="/static/css/elements/chromedash-legend.css">

      <div id="overlay">
        <h3>About the data</h3>
        <section class="content-wrapper">
          <p class="description">What you're looking at is a mostly
          comprehensive list of web platform features that have landed in
          Chromium, ordered chronologically by the milestone in which they were
          added. Features marked "No active development" are being considered or
          have yet to be started. Features marked "In development" are currently
          being worked on.</p>
          <button class="close buttons">
            <iron-icon icon="chromestatus:close" @click=${this.toggle}></iron-icon>
          </button>
        </section>
        <h3>Color legend</h3>
        <p>Colors indicate the "interoperability risk" for a given feature. The
          risk increases as
          <chromedash-color-status .value="1"
              .max="${this.views.vendors.length}"></chromedash-color-status> → 
          <chromedash-color-status .value="${this.views.vendors.length}"
              .max="${this.views.vendors.length}"></chromedash-color-status>, and the
          color meaning differs for browser vendors, web developers, and the
          standards process.</p>
        <section class="views">
          <div>
            <label>Browser vendors</label>
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
            <label>Web developer</label>
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
          <div>
            <label>Standards values</label>
            <ul>
              ${this.views.standards.map((standard) => html`
                <li>
                  <chromedash-color-status .value="${standard.key}"
                                           .max="${this.views.standards.length}">
                                           </chromedash-color-status>
                  <span>${standard.val}</span></li>
                `)}
            </ul>
          </div>
        </section>
        <h3>Search</h3>
        <section>
          <label>Example search queries</label>
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
