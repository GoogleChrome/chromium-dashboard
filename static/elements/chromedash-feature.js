import {LitElement, html} from 'https://unpkg.com/@polymer/lit-element@latest/lit-element.js?module';
// import 'https://unpkg.com/@polymer/iron-icon/iron-icon.js?module';
// import 'https://unpkg.com/@polymer/paper-styles/color.js?module';
import {urlize} from './urlize.js';
import './chromedash-color-status.js';

class ChromedashMultiLinks extends LitElement {
  static get properties() {
    return {
      title: {type: String}, // From parent
      links: {type: Array}, // From parent
    };
  }

  constructor() {
    super();
    this.title = 'Link';
    this.links = [];
  }

  render() {
    return html`
      <link rel="stylesheet" href="/static/css/shared.css">

      ${this.links.map((link, index) => html`
        <a href="${link}" target="_blank"
           class="${index < this.links.length - 1 ? 'comma' : ''}"
           >${this.title} ${index + 1}</a>
        `)}
    `;
  }
}

customElements.define('chromedash-multi-links', ChromedashMultiLinks);


const MAX_STANDARDS_VAL = 6;
const MAX_VENDOR_VIEW = 7;
const MAX_WEBDEV_VIEW = 6;
const MAX_RISK = MAX_VENDOR_VIEW + MAX_WEBDEV_VIEW + MAX_STANDARDS_VAL;

const IS_PUSH_NOTIFIER_ENABLED = window.PushNotifier.GRANTED_ACCESS;
const IS_PUSH_NOTIFIER_SUPPORTED =
    window.PushNotifier && window.PushNotifier.SUPPORTS_NOTIFICATIONS;

class ChromedashFeature extends LitElement {
  static get properties() {
    return {
      feature: {type: Object}, // From parent
      whitelisted: {type: Boolean}, // From parent
      open: {type: Boolean, reflect: true}, // Attribute for styling
      // Values used in the template
      interopRisk: {type: Number, attribute: false},
      isDeprecated: {type: Boolean, attribute: false},
      hasDocLinks: {type: Boolean, attribute: false},
      hasSampleLinks: {type: Boolean, attribute: false},
      commentHtml: {type: String, attribute: false},
      crBugNumber: {type: String, attribute: false},
      newBugUrl: {type: String, attribute: false},
      receivePush: {type: Boolean, attribute: false},
    };
  }

  constructor() {
    super();
    this.whitelisted = false;
  }

  // Initialize values after receiving `this.feature`.
  firstUpdated() {
    this.open = this.feature.open;
    this.receivePush = this.feature.receivePush;

    this.crBugNumber = this._computeCrBugNumber();
    this.newBugUrl = this._computeNewBugUrl();
    this.interopRisk = this._computeInteropRisk();
    this.isDeprecated = this._computeIsDeprecated();
    this.hasDocLinks = this._computeHasDocLinks();
    this.hasSampleLinks = this._computeHasSampleLinks();
    this.commentHtml = this._computeCommentHtml();
  }

  _computeCrBugNumber() {
    const link = this.feature.browsers.chrome.bug;
    if (!link) {
      return '';
    }

    /* Get the number id from a url.
     * Url has two formats: "http://crbug.com/111111", and
     * "https://bugs.chromium.org/p/chromium/issues/detail?id=111111" */
    const matches = link.match(/(id=|crbug.com\/)([0-9]+)/);
    if (matches) {
      return matches[2];
    }
    return '';
  }

  _computeNewBugUrl() {
    const url = 'https://bugs.chromium.org/p/chromium/issues/entry';
    const params = [
      `components=${this.feature.browsers.chrome.blink_components[0] ||
        'Blink'}`];
    const PRE_LAUNCH_STATUSES = [
      'No active development',
      'Proposed',
      'In development',
      'Behind a flag',
      'Origin trial',
    ];
    if (this.crBugNumber &&
        PRE_LAUNCH_STATUSES.includes(
          this.feature.browsers.chrome.status.text)) {
      params.push(`blocking=${this.crBugNumber}`);
    }
    const owners = this.feature.browsers.chrome.owners;
    if (owners && owners.length) {
      params.push(`cc=${owners.map(encodeURIComponent)}`);
    }
    return `${url}?${params.join('&')}`;
  }

  _computeInteropRisk() {
    const vendors = (this.feature.browsers.ff.view.val +
                   this.feature.browsers.edge.view.val +
                   this.feature.browsers.safari.view.val) / 3;
    const webdevs = this.feature.browsers.webdev.view.val;
    const standards = this.feature.standards.status.val;
    return vendors + webdevs + standards;
  }

  _computeIsDeprecated() {
    const DEPRECATED_STATUSES = ['Deprecated', 'No longer pursuing'];
    return DEPRECATED_STATUSES.includes(
      this.feature.browsers.chrome.status.text);
  }

  _computeHasDocLinks() {
    return this.feature.resources.docs &&
        this.feature.resources.docs.length > 0;
  }

  _computeHasSampleLinks() {
    return this.feature.resources.samples &&
        this.feature.resources.samples.length > 0;
  }

  _computeCommentHtml() {
    return urlize(this.feature.comments,
      {target: '_blank', trim: 'www', autoescape: true});
  }

  _fireEvent(eventName, detail) {
    let event = new CustomEvent(eventName, {detail});
    this.dispatchEvent(event);
  }

  toggle(e) {
    // Don't toggle panel if tooltip or link is being clicked.
    const target = e.currentTarget;
    if (target.classList.contains('tooltip') || 'tooltip' in target.dataset ||
        target.tagName == 'A' || target.tagName == 'CHROMEDASH-MULTI-LINKS') {
      return;
    }

    this.open = !this.open;

    // Handled in `chromedash-featurelist`
    this._fireEvent('feature-toggled', {
      feature: this.feature,
      open: this.open,
    });
  }

  categoryFilter(e) {
    e.stopPropagation();
    e.preventDefault();
    // Directly listened in `templates/features.html`
    this._fireEvent('filter-category', {val: e.currentTarget.textContent});
  }

  filterByOwner(e) {
    e.stopPropagation();
    e.preventDefault();
    // Directly listened in `templates/features.html`
    this._fireEvent('filter-owner', {val: e.currentTarget.textContent});
  }

  filterByComponent(e) {
    e.stopPropagation();
    e.preventDefault();
    // Directly listened in `templates/features.html`
    this._fireEvent('filter-component', {val: e.currentTarget.textContent});
  }

  subscribeToFeature(e) {
    e.preventDefault();
    e.stopPropagation();

    const featureId = this.feature.id;
    if (!featureId) {
      return;
    }

    this.receivePush = !this.receivePush;

    if (this.receivePush) {
      PushNotifications.subscribeToFeature(featureId);
    } else {
      PushNotifications.unsubscribeFromFeature(featureId);
    }
  }

  render() {
    return html`
      <link rel="stylesheet" href="/static/css/elements/chromedash-feature.css">

      <div class="main-content-area" @click="${this.toggle}">
        <hgroup>
          <chromedash-color-status class="tooltip corner"
            title="Interoperability risk: perceived interest from browser
                vendors and web developers"
            .value="${this.interopRisk}"
            .max="${MAX_RISK}"></chromedash-color-status>
          <h2>${this.feature.name}
            ${this.whitelisted ? `
              <span class="tooltip" title="Edit this feature">
                <a href="/admin/features/edit/${this.feature.id}" data-tooltip>
                  <iron-icon icon="chromestatus:create"></iron-icon>
                </a>
              </span>
              `: ''}
          </h2>
          <div class="iconrow
              ${IS_PUSH_NOTIFIER_SUPPORTED ?
                'supports-push-notifications' : ''}">
            <span class="tooltip"
                  title="Filter by category ${this.feature.category}">
              <button class="category"
                      @click="${this.categoryFilter}">
                ${this.feature.category}</button>
            </span>
            <div class="topcorner">
              ${this.feature.browsers.chrome.status.text === 'Removed' ? `
                <span class="tooltip" title="Removed feature">
                  <iron-icon icon="chromestatus:cancel"
                             class="remove" data-tooltip></iron-icon>
                </span>
                ` : ''}
              ${this.isDeprecated ? `
                <span class="tooltip" title="Deprecated feature">
                  <iron-icon icon="chromestatus:warning"
                             class="deprecated" data-tooltip></iron-icon>
                </span>
                ` : ''}
              ${this.feature.browsers.chrome.flag ? `
                <span class="tooltip"
                      title="Experimental feature behind a flag">
                  <iron-icon icon="chromestatus:flag"
                             class="experimental"></iron-icon>
                </span>
                ` : ''}
              ${this.feature.browsers.chrome.origintrial ? `
                <span class="tooltip" title="Origin trial">
                  <iron-icon icon="chromestatus:extension"
                             class="experimental"></iron-icon>
                </span>
                ` : ''}
              ${this.feature.browsers.chrome.intervention ? `
                <span class="tooltip" title="Browser intervention">
                  <iron-icon icon="chromestatus:pan-tool"
                             class="intervention" data-tooltip></iron-icon>
                </span>
                ` : ''}
              <span class="tooltip no-push-notifications"
                    title="Receive a push notification when there are updates">
                <button @click="${this.subscribeToFeature}" data-tooltip>
                  <iron-icon icon="${this.receivePush ?
                                'chromestatus:notifications' :
                                'chromestatus:notifications-off'}"
                             class="pushicon ${IS_PUSH_NOTIFIER_ENABLED ?
                               '' : 'disabled'}"></iron-icon>
                </button>
              </span>
              <span class="tooltip" title="File a bug against this feature">
                <a href="${this.newBugUrl}" data-tooltip>
                  <iron-icon icon="chromestatus:bug-report"></iron-icon>
                </a>
              </span>
              <span class="tooltip" title="View on a standalone page">
                <a href="/feature/${this.feature.id}" target="_blank">
                  <iron-icon icon="chromestatus:open-in-new"></iron-icon>
                </a>
              </span>
            </div>
          </div>
        </hgroup>
        <section class="desc">
          <summary>
            <p><span>${this.feature.summary}</span></p>
            <p><span>${this.feature.motivation}</span></p>
          </summary>
        </section>
        ${this.open ? `
          <section class="sidebyside">
            <div class="flex">
              <h3>Chromium status</h3>
              <div class="impl_status">
                <span class="chromium_status">
                  <label>${this.feature.browsers.chrome.status.text}</label>
                </span>
                ${this.feature.browsers.chrome.desktop ? `
                  <span>
                    <label class="impl_status_label">
                      <span class="impl_status_icons">
                        <span class="chrome_icon"></span>
                      </span>
                      <span>Chrome desktop</span>
                    </label>
                    <span>${this.feature.browsers.chrome.desktop}</span>
                  </span>
                  ` : ''}
                ${this.feature.browsers.chrome.android ? `
                  <span>
                    <label class="impl_status_label">
                      <span class="impl_status_icons">
                        <span class="chrome_icon"></span>
                        <iron-icon icon="chromestatus:android"
                                   class="android"></iron-icon>
                      </span>
                      <span>Chrome for Android</span>
                    </label>
                    <span>${this.feature.browsers.chrome.android}</span>
                  </span>
                  ` : ''}
                ${this.feature.browsers.chrome.webview ? `
                  <span>
                    <label class="impl_status_label">
                      <span class="impl_status_icons">
                        <iron-icon icon="chromestatus:android"
                                   class="android"></iron-icon>
                      </span>
                      <span>Android Webview</span>
                    </label>
                    <span>${this.feature.browsers.chrome.webview}</span>
                  </span>
                  ` : ''}
                ${this.feature.browsers.chrome.prefixed ? `
                  <span><label>Prefixed</label><span>Yes</span></span>
                  ` : ''}
                ${this.feature.browsers.chrome.bug ? `
                  <span>
                    <span>Tracking bug</span>
                    <a href="${this.feature.browsers.chrome.bug}"
                       target="_blank">${this.crBugNumber ?
                         `#${this.crBugNumber}` :
                         this.feature.browsers.chrome.bug}</a>
                  </span>
                  ` : ''}
                ${this.feature.browsers.chrome.blink_components &&
                  this.feature.browsers.chrome.blink_components.length ? `
                  <span>
                    <label>Blink component</label>
                    <span class="tooltip"
                          title="Filter by component
                              ${this.feature.browsers.chrome.blink_components}">
                      <button @click="${this.filterByComponent}">
                        ${this.feature.browsers.chrome.blink_components}
                      </button>
                    </span>
                  </span>
                  ` : ''}
                ${this.feature.browsers.chrome.owners &&
                  this.feature.browsers.chrome.owners.length ? `
                  <span class="owner">
                    <label>Owner(s)</label>
                    <span class="owner-list">
                      ${this.feature.browsers.chrome.owners.map((owner) => `
                        <span class="tooltip" title="Filter by owner ${owner}">
                          <button @click="${this.filterByOwner}">
                            ${owner}
                          </button>
                        </span>
                        `)}
                    </span>
                  </span>
                  ` : ''}
              </div>
            </div>
            <div class="flex">
              <h3>Consensus &amp; standardization</h3>
              <div class="views">
                <span title="${this.feature.browsers.ff.view.text}"
                      class="view tooltip">
                  <chromedash-color-status class="bottom"
                      .value="${this.feature.browsers.ff.view.val}"
                      .max="${MAX_VENDOR_VIEW}"></chromedash-color-status>
                  ${this.feature.browsers.ff.view.url ? `
                    <a href="${this.feature.browsers.ff.view.url}"
                       target="_blank">
                      <span class="vendor-view ff-view"></span>
                    </a>
                    ` : ''}
                  ${this.feature.browsers.ff.view.url ?
                      '<span class="vendor-view ff-view"></span>' : ''}
                </span>
                <span title="${this.feature.browsers.edge.view.text}"
                      class="view tooltip">
                  <chromedash-color-status class="bottom"
                      .value="${this.feature.browsers.edge.view.val}"
                      .max="${MAX_VENDOR_VIEW}"></chromedash-color-status>
                  ${this.feature.browsers.edge.view.url ? `
                    <a href="${this.feature.browsers.edge.view.url}"
                       target="_blank">
                      <span class="vendor-view edge-view"></span>
                    </a>
                    ` : ''}
                  ${this.feature.browsers.edge.view.url ?
                      '<span class="vendor-view edge-view"></span>' : ''}
                </span>
                <span title="${this.feature.browsers.safari.view.text}"
                      class="view tooltip">
                  <chromedash-color-status class="bottom"
                      .value="${this.feature.browsers.safari.view.val}"
                      .max="${MAX_VENDOR_VIEW}"></chromedash-color-status>
                  ${this.feature.browsers.safari.view.url ? `
                    <a href="${this.feature.browsers.safari.view.url}"
                       target="_blank">
                      <span class="vendor-view safari-view"></span>
                    </a>
                    ` : ''}
                  ${this.feature.browsers.safari.view.url ?
                      '<span class="vendor-view safari-view"></span>' : ''}
                </span>
                <span title="Web developers:
                          ${this.feature.browsers.webdev.view.text}"
                      class="view webdev-view tooltip">
                  <chromedash-color-status class="bottom"
                      .value="${this.feature.browsers.webdev.view.val}"
                      .max="${MAX_WEBDEV_VIEW}"></chromedash-color-status>
                  <iron-icon icon="chromestatus:accessibility"></iron-icon>
                </span>
                <span class="standardization view">
                  <chromedash-color-status class="bottom"
                      .value="${this.feature.standards.status.val}"
                      .max="${MAX_STANDARDS_VAL}"></chromedash-color-status>
                  ${this.feature.standards.spec ? `
                    <a href="${this.feature.standards.spec}"
                       target="_blank">${this.feature.standards.status.text}</a>
                    ` : ''}
                  ${this.feature.standards.spec ?
                      `<label>${this.feature.standards.status.text}</label>` :
                      ''}
                </span>
              </div>
              <div style="font-size:smaller">
                After a feature ships in Chrome, the values listed here are not
                guaranteed to be up to date.
              </div>
            </div>
          </section>
          ${this.hasDocLinks || this.hasSampleLinks ? `
            <section>
              <h3>Developer resources</h3>
              <div class="resources">
                <label>Documentation/samples:</label>
                ${this.hasDocLinks ? `
                  <div class="doc_links">
                    <chromedash-multi-links
                        .links="${this.feature.resources.docs}"
                        title="Link"></chromedash-multi-links>
                  </div>
                  ` : ''}
                ${this.hasDocLinks && this.hasSampleLinks ?
                  '<span>,</span>' : ''}
                ${this.hasSampleLinks ? `
                  <div class="sample_links">
                    <chromedash-multi-links title="Sample"
                        .links="${this.feature.resources.samples}"
                        ></chromedash-multi-links>
                  </div>
                  ` : ''}
              </div>
            </section>
            ` : ''}
          ${this.feature.comments ? `
            <section>
              <h3>Comments</h3>
              <summary class="comments">${this.commentHtml}</summary>
            </section>
            ` : ''}
          ` : ''}
      </div>
    `;
  }
}

customElements.define('chromedash-feature', ChromedashFeature);
