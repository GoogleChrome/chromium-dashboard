import {LitElement, html} from 'https://unpkg.com/@polymer/lit-element@latest/lit-element.js?module';
import 'https://unpkg.com/@polymer/iron-icon/iron-icon.js?module';
import '/static/elements/chromedash-color-status.js';

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
      feature: {type: Object}, // From attribute
      whitelisted: {type: Boolean}, // From attribute
      open: {type: Boolean, reflect: true}, // Attribute used in the parent for styling
      // Values used in the template
      _interopRisk: {type: Number, attribute: false},
      _isDeprecated: {type: Boolean, attribute: false},
      _hasDocLinks: {type: Boolean, attribute: false},
      _hasSampleLinks: {type: Boolean, attribute: false},
      _commentHtml: {type: String, attribute: false},
      _crBugNumber: {type: String, attribute: false},
      _newBugUrl: {type: String, attribute: false},
      _receivePush: {type: Boolean, attribute: false},
    };
  }

  constructor() {
    super();
    this.open = false;
  }

  // Initialize values after receiving `this.feature`.
  firstUpdated() {
    this._receivePush = this.feature.receivePush;
    this._crBugNumber = this._getCrBugNumber();
    this._newBugUrl = this._getNewBugUrl();
    this._interopRisk = this._getInteropRisk();
    this._isDeprecated = this._getIsDeprecated();
    this._hasDocLinks = this._getHasDocLinks();
    this._hasSampleLinks = this._getHasSampleLinks();
    this._commentHtml = this._getCommentHtml();
  }

  _getCrBugNumber() {
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

  _getNewBugUrl() {
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
    if (this._crBugNumber &&
        PRE_LAUNCH_STATUSES.includes(
          this.feature.browsers.chrome.status.text)) {
      params.push(`blocking=${this._crBugNumber}`);
    }
    const owners = this.feature.browsers.chrome.owners;
    if (owners && owners.length) {
      params.push(`cc=${owners.map(encodeURIComponent)}`);
    }
    return `${url}?${params.join('&')}`;
  }

  _getInteropRisk() {
    if (!this.feature) return undefined;
    const vendors = (this.feature.browsers.ff.view.val +
                   this.feature.browsers.edge.view.val +
                   this.feature.browsers.safari.view.val) / 3;
    const webdevs = this.feature.browsers.webdev.view.val;
    const standards = this.feature.standards.status.val;
    return vendors + webdevs + standards;
  }

  _getIsDeprecated() {
    const DEPRECATED_STATUSES = ['Deprecated', 'No longer pursuing'];
    return DEPRECATED_STATUSES.includes(
      this.feature.browsers.chrome.status.text);
  }

  _getHasDocLinks() {
    return this.feature.resources.docs &&
        this.feature.resources.docs.length > 0;
  }

  _getHasSampleLinks() {
    return this.feature.resources.samples &&
        this.feature.resources.samples.length > 0;
  }

  _getCommentHtml() {
    return urlize(this.feature.comments,
      {target: '_blank', trim: 'www', autoescape: true});
  }

  _fireEvent(eventName, detail) {
    let event = new CustomEvent(eventName, {detail});
    this.dispatchEvent(event);
  }

  _togglePanelExpansion(e) {
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
    // Listened in `templates/features.html`
    this._fireEvent('filter-category', {val: e.currentTarget.innerText});
  }

  filterByOwner(e) {
    e.stopPropagation();
    e.preventDefault();
    // Listened in `templates/features.html`
    this._fireEvent('filter-owner', {val: e.currentTarget.innerText});
  }

  filterByComponent(e) {
    e.stopPropagation();
    e.preventDefault();
    // Listened in `templates/features.html`
    this._fireEvent('filter-component', {val: e.currentTarget.innerText});
  }

  subscribeToFeature(e) {
    e.preventDefault();
    e.stopPropagation();

    const featureId = this.feature.id;
    if (!featureId) {
      return;
    }

    this._receivePush = !this._receivePush;

    if (this._receivePush) {
      PushNotifications.subscribeToFeature(featureId);
    } else {
      PushNotifications.unsubscribeFromFeature(featureId);
    }
  }

  render() {
    // Debuging lit-virtualizer: replacing the link tag with inlined css resolves the transform issue.
    // <style>*{-webkit-tap-highlight-color:rgba(0,0,0,0)}h1,h2,h3,h4{font-weight:300}h1{font-size:30px}h2,h3,h4{color:#444}h2{font-size:25px}h3{font-size:20px}a{text-decoration:none;color:#4580c0}a:hover{text-decoration:underline;color:#366597}b{font-weight:600}input:not([type="submit"]),textarea{border:1px solid #D4D4D4}input:not([type="submit"])[disabled],textarea[disabled]{opacity:0.5}button,.button{display:inline-block;background:linear-gradient(#F9F9F9 40%, #E3E3E3 70%);border:1px solid #a9a9a9;border-radius:3px;padding:5px 8px;outline:none;white-space:nowrap;-webkit-user-select:none;-moz-user-select:none;-ms-user-select:none;user-select:none;cursor:pointer;text-shadow:1px 1px #fff;font-size:10pt}button:not(:disabled):hover{border-color:#515151}button:not(:disabled):active{background:linear-gradient(#E3E3E3 40%, #F9F9F9 70%)}.comma::after{content:', '}.no-push-notifications,.no-web-share{display:none}.supports-push-notifications .no-push-notifications{display:initial}*{box-sizing:border-box;list-style:none;padding:0;margin:0;font:inherit;text-decoration:inherit}:host{background-color:#FAFAFA;background:linear-gradient(to bottom, white, #F2F2F2);padding:0.75em 0.5em;box-shadow:1px 1px 4px rgba(0,0,0,0.065);display:block;position:relative;border-radius:3px;padding:10px 10px 10px 20px !important;list-style:none;box-sizing:border-box;contain:content;overflow:hidden}:host:active{outline:none}:host([open]){outline:none}:host([open]) .desc summary{white-space:normal}[hidden]{display:none !important}h2{display:inline-block;font-size:25px;flex:1 0 0}iron-icon{--iron-icon-height: 20px;--iron-icon-width: 20px}iron-icon.android{color:#A4C739}iron-icon.remove{color:var(--paper-red-700)}iron-icon.deprecated{color:var(--paper-orange-700)}iron-icon.experimental{color:var(--paper-green-700)}iron-icon.intervention{color:var(--paper-yellow-800)}iron-icon.disabled{opacity:0.5}.opennew{width:18px;height:18px}.open-standalone{position:absolute;right:0;top:0;display:flex;align-items:center;height:100%;border-left:2px solid #eee;padding:4px}.iconrow{display:flex;align-items:center}.category-tooltip,.topcorner .tooltip{margin-left:4px}.category-tooltip a,.topcorner .tooltip a{text-decoration:none}.category-tooltip:hover:before,.category-tooltip:active:before,.topcorner .tooltip:hover:before,.topcorner .tooltip:active:before{content:attr(title) "";position:absolute;background-color:#FAFAFA;background:linear-gradient(to bottom, white, #F2F2F2);padding:0.75em 0.5em;box-shadow:1px 1px 4px rgba(0,0,0,0.065);box-shadow:2px 2px 4px #a9a9a9;border:1px solid #e6e6e6;z-index:100;text-align:center;color:#666;top:35px;right:20px;width:auto;white-space:nowrap}hgroup{display:flex;align-items:flex-start;cursor:pointer}hgroup .category{color:#a9a9a9}hgroup chromedash-color-status{position:absolute;top:0;left:0}section{margin:18px 0}section.desc{margin:10px 0 0 0;cursor:pointer;color:#797979;line-height:20px}section.desc summary{text-overflow:ellipsis;overflow:hidden;white-space:nowrap}section.desc summary p:not(:first-child){margin:10px 0 0 0}section h3{margin:10px 0;font-size:18px;font-weight:400}section div>span{flex-shrink:0}section .impl_status{display:flex;flex-direction:column}section .impl_status>span{display:flex;justify-content:space-between;align-items:center;padding:8px}section .impl_status>span:nth-of-type(odd){background:#eee}section .impl_status .chromium_status{font-weight:500}section .impl_status .vendor_icon,section .impl_status .chrome_icon,section .impl_status .opera_icon{background:url(/static/img/browsers-logos.png) no-repeat;background-size:cover;height:20px;width:20px;margin-right:4px;display:inline-block}section .impl_status .chrome_icon{background-position:0px 50%}section .impl_status .opera_icon{background-position:-75px 50%}section .impl_status_label{display:flex;align-items:center}section .impl_status_icons{display:flex;align-items:center;min-width:50px}section .views{display:flex;flex-wrap:wrap}section .views .view{display:flex;align-items:center;position:relative;height:35px;background:#eee;margin:0 8px 16px 0;padding:8px}section .views .standardization .vendor-view{margin-left:0}section .views iron-icon{margin:0 8px}section .views .vendor-view{background:url(/static/img/browsers-logos.png) no-repeat;background-size:cover;height:16px;margin:8px;display:inline-block}section .views .edge-view{background-position:-80px 50%;width:16px}section .views .safari-view{background-position:-20px 50%;width:17px}section .views .ff-view{background-position:-40px 50%;width:17px}section .views .w3c-view{background-position:-99px 50%;width:22px}section chromedash-color-status{overflow:hidden}section chromedash-color-status.bottom{margin-top:3px}section .owner-list{display:flex;align-items:flex-end;flex-direction:column}section .owner-list a{display:block}section .comments html-echo{white-space:pre-wrap}section .doc_links,section .sample_links,section .owner{flex-shrink:1 !important}section .sample_links{margin-left:8px}.sidebyside{display:flex;justify-content:space-between}.sidebyside .flex{flex:0 0 calc(50% - 16px)}.sidebyside .tooltip{position:relative}.sidebyside .tooltip a{text-decoration:none}.sidebyside .tooltip:hover:before,.sidebyside .tooltip:active:before{content:attr(title) "";position:absolute;background-color:#FAFAFA;background:linear-gradient(to bottom, white, #F2F2F2);padding:0.75em 0.5em;box-shadow:1px 1px 4px rgba(0,0,0,0.065);box-shadow:2px 2px 4px #a9a9a9;border:1px solid #e6e6e6;z-index:100;text-align:center;color:#666;bottom:25px;left:-50px;width:auto;white-space:nowrap}.resources label{margin-right:8px}@media only screen and (max-width: 700px){:host{border-radius:0 !important;margin:7px initial !important;transition:none !important}iron-icon{--iron-icon-height: 16px;--iron-icon-width: 16px}h2{font-size:20px !important}section{margin-left:0}.category{display:none}.impl_status>span:not([hidden]):not(:last-of-type),.impl_status>a{margin-bottom:10px}.views>span{margin-bottom:10px}.sidebyside{display:block}}@media only screen and (min-width: 701px){.resources{display:flex;align-items:center}}</style>
    return html`
      <link rel="stylesheet" href="/static/css/elements/chromedash-feature.css">

      <hgroup @click="${this._togglePanelExpansion}">
        <chromedash-color-status class="tooltip corner"
          title="Interoperability risk: perceived interest from browser
              vendors and web developers"
          .value="${this._interopRisk}"
          .max="${MAX_RISK}"></chromedash-color-status>
        <h2>${this.feature.name}
          ${this.whitelisted ? html`
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
          <span class="tooltip category-tooltip"
                title="Filter by category ${this.feature.category}">
            <a href="#" class="category"
               @click="${this.categoryFilter}">
              ${this.feature.category}</a>
          </span>
          <div class="topcorner">
            ${this.feature.browsers.chrome.status.text === 'Removed' ? html`
              <span class="tooltip" title="Removed feature">
                <iron-icon icon="chromestatus:cancel"
                           class="remove" data-tooltip></iron-icon>
              </span>
              ` : ''}
            ${this._isDeprecated ? html`
              <span class="tooltip" title="Deprecated feature">
                <iron-icon icon="chromestatus:warning"
                           class="deprecated" data-tooltip></iron-icon>
              </span>
              ` : ''}
            ${this.feature.browsers.chrome.flag ? html`
              <span class="tooltip"
                    title="Experimental feature behind a flag">
                <iron-icon icon="chromestatus:flag"
                           class="experimental"></iron-icon>
              </span>
              ` : ''}
            ${this.feature.browsers.chrome.origintrial ? html`
              <span class="tooltip" title="Origin trial">
                <iron-icon icon="chromestatus:extension"
                           class="experimental"></iron-icon>
              </span>
              ` : ''}
            ${this.feature.browsers.chrome.intervention ? html`
              <span class="tooltip" title="Browser intervention">
                <iron-icon icon="chromestatus:pan-tool"
                           class="intervention" data-tooltip></iron-icon>
              </span>
              ` : ''}
            <span class="tooltip no-push-notifications"
                  title="Receive a push notification when there are updates">
              <a href="#" @click="${this.subscribeToFeature}" data-tooltip>
                <iron-icon icon="${this._receivePush ?
                              'chromestatus:notifications' :
                              'chromestatus:notifications-off'}"
                           class="pushicon ${IS_PUSH_NOTIFIER_ENABLED ?
                             '' : 'disabled'}"></iron-icon>
              </a>
            </span>
            <span class="tooltip" title="File a bug against this feature">
              <a href="${this._newBugUrl}" data-tooltip>
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
      <section class="desc" @click="${this._togglePanelExpansion}">
        <summary>
          <p><span>${this.feature.summary}</span></p>
          <p><span>${this.feature.motivation}</span></p>
        </summary>
      </section>
      ${this.open ? html`
        <section class="sidebyside">
          <div class="flex">
            <h3>Chromium status</h3>
            <div class="impl_status">
              <span class="chromium_status">
                <label>${this.feature.browsers.chrome.status.text}</label>
              </span>
              ${this.feature.browsers.chrome.desktop ? html`
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
              ${this.feature.browsers.chrome.android ? html`
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
              ${this.feature.browsers.chrome.webview ? html`
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
              ${this.feature.browsers.chrome.prefixed ? html`
                <span><label>Prefixed</label><span>Yes</span></span>
                ` : ''}
              ${this.feature.browsers.chrome.bug ? html`<span>
                  <span>Tracking bug</span>
                  <a href="${this.feature.browsers.chrome.bug}"
                     target="_blank">${this._crBugNumber ?
                       `#${this._crBugNumber}` :
                       this.feature.browsers.chrome.bug}</a>
                </span>
                ` : ''}
              ${this.feature.browsers.chrome.blink_components &&
                this.feature.browsers.chrome.blink_components.length ? html`
                <span>
                  <label>Blink component</label>
                  <span class="tooltip"
                        title="Filter by component ${this.feature.browsers.chrome.blink_components}">
                    <a href="#" @click="${this.filterByComponent}">
                      ${this.feature.browsers.chrome.blink_components}
                    </a>
                  </span>
                </span>
                ` : ''}
              ${this.feature.browsers.chrome.owners &&
                this.feature.browsers.chrome.owners.length ? html`
                <span class="owner">
                  <label>Owner(s)</label>
                  <span class="owner-list">
                    ${this.feature.browsers.chrome.owners.map((owner) => html`
                      <span class="tooltip" title="Filter by owner ${owner}">
                        <a href="#" @click="${this.filterByOwner}">
                          ${owner}
                        </a>
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
                ${this.feature.browsers.ff.view.url ? html`
                  <a href="${this.feature.browsers.ff.view.url}"
                     target="_blank">
                    <span class="vendor-view ff-view"></span>
                  </a>
                  ` : html`<span class="vendor-view ff-view"></span>`}
              </span>
              <span title="${this.feature.browsers.edge.view.text}"
                    class="view tooltip">
                <chromedash-color-status class="bottom"
                    .value="${this.feature.browsers.edge.view.val}"
                    .max="${MAX_VENDOR_VIEW}"></chromedash-color-status>
                ${this.feature.browsers.edge.view.url ? html`
                  <a href="${this.feature.browsers.edge.view.url}"
                     target="_blank">
                    <span class="vendor-view edge-view"></span>
                  </a>
                  ` : html`<span class="vendor-view edge-view"></span>`}
              </span>
              <span title="${this.feature.browsers.safari.view.text}"
                    class="view tooltip">
                <chromedash-color-status class="bottom"
                    .value="${this.feature.browsers.safari.view.val}"
                    .max="${MAX_VENDOR_VIEW}"></chromedash-color-status>
                ${this.feature.browsers.safari.view.url ? html`
                  <a href="${this.feature.browsers.safari.view.url}"
                     target="_blank">
                    <span class="vendor-view safari-view"></span>
                  </a>
                  ` : html`<span class="vendor-view safari-view"></span>`}
              </span>
              <span title="Web developers: ${this.feature.browsers.webdev.view.text}"
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
                ${this.feature.standards.spec ? html`
                  <a href="${this.feature.standards.spec}"
                     target="_blank">${this.feature.standards.status.text}</a>
                  ` : html`
                  <label>${this.feature.standards.status.text}</label>
                  `}
              </span>
            </div>
            <div style="font-size:smaller">
              After a feature ships in Chrome, the values listed here are not
              guaranteed to be up to date.
            </div>
          </div>
        </section>
        ${this._hasDocLinks || this._hasSampleLinks ? html`
          <section>
            <h3>Developer resources</h3>
            <div class="resources">
              <label>Documentation/samples:</label>
              ${this._hasDocLinks ? html`
                <div class="doc_links">
                  <chromedash-multi-links
                      .links="${this.feature.resources.docs}"
                      title="Link"></chromedash-multi-links>
                </div>
                ` : ''}
              ${this._hasDocLinks && this._hasSampleLinks ?
                html`<span>,</span>` : ''}
              ${this._hasSampleLinks ? html`
                <div class="sample_links">
                  <chromedash-multi-links title="Sample"
                      .links="${this.feature.resources.samples}"
                      ></chromedash-multi-links>
                </div>
                ` : ''}
            </div>
          </section>
          ` : ''}
        ${this.feature.comments ? html`
          <section>
            <h3>Comments</h3>
            <summary class="comments">${this._commentHtml}</summary>
          </section>
          ` : ''}
        ` : ''}
    `;
  }
}

customElements.define('chromedash-feature', ChromedashFeature);


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
