import {LitElement, html} from 'lit-element';
import {nothing} from 'lit-html';
import {ifDefined} from 'lit-html/directives/if-defined.js';
import '@polymer/iron-icon';
import './chromedash-color-status';

import style from '../css/elements/chromedash-feature.css';
import sharedStyle from '../css/shared.css';

const MAX_STANDARDS_VAL = 6;
const MAX_VENDOR_VIEW = 7;
const MAX_WEBDEV_VIEW = 6;

class ChromedashFeature extends LitElement {
  static styles = style;

  static get properties() {
    return {
      feature: {type: Object},
      canEdit: {type: Boolean},
      signedin: {type: Boolean},
      loginUrl: {type: String},
      open: {type: Boolean, reflect: true}, // Attribute used in the parent for styling
      starred: {type: Boolean},
      // Values used in the template
      _interopRisk: {attribute: false},
      _isDeprecated: {attribute: false},
      _hasDocLinks: {attribute: false},
      _hasSampleLinks: {attribute: false},
      _commentHtml: {attribute: false},
      _crBugNumber: {attribute: false},
      _newBugUrl: {attribute: false},
    };
  }

  firstUpdated() {
    this._initializeValues();
  }

  /* Initialize values for the template `_initializeValues()`.
   * - Why not `firstUpdated`: When chromedash-featurelist filters,
   *   chromedash-feature components are updated, rather than destroyed then
   *   recreated, so firstUpdated won't run.
   * - Why not `updated`: We need the new values before the first render. */
  update(changedProperties) {
    if (changedProperties.get('feature')) {
      this._initializeValues();
    }
    super.update(changedProperties);
  }

  _initializeValues() {
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
      'On hold',
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
    let event = new CustomEvent(eventName, {
      bubbles: true,
      composed: true,
      detail,
    });
    this.dispatchEvent(event);
  }

  _togglePanelExpansion(e) {
    // Don't toggle panel if tooltip or link is being clicked.
    const target = e.currentTarget;
    if (target.classList.contains('tooltip') || 'tooltip' in target.dataset ||
        target.tagName == 'A' || target.tagName == 'CHROMEDASH-MULTI-LINKS') {
      return;
    }

    // We toggle the open state by sending an event, which causes a new
    // ChromedashFeature object to be created with the new state.
    const newOpen = !this.open;

    // Handled in `chromedash-featurelist`
    this._fireEvent('feature-toggled', {
      feature: this.feature,
      open: newOpen,
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

  toggleStar(e) {
    e.preventDefault();
    e.stopPropagation();

    const featureId = this.feature.id;
    if (!featureId) {
      return;
    }

    // We toggle the starred state by sending an event, which causes a new
    // ChromedashFeature object to be created with the new state.
    const newStarred = !this.starred;

    window.StarService.setStar(featureId, newStarred);

    // Handled in `chromedash-featurelist`
    this._fireEvent('star-toggled', {
      feature: this.feature,
      starred: newStarred,
    });
  }

  render() {
    return html`
      <hgroup @click="${this._togglePanelExpansion}">
        <h2>${this.feature.name}
          ${this.canEdit ? html`
            <span class="tooltip" title="Edit this feature">
              <a href="/guide/edit/${this.feature.id}" data-tooltip>
                <iron-icon icon="chromestatus:create"></iron-icon>
              </a>
            </span>
            `: nothing}
        </h2>
        <div class="iconrow
            ${window.PushNotifier && window.PushNotifier.SUPPORTS_NOTIFICATIONS ?
              'supports-push-notifications' : nothing}">
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
              ` : nothing}
            ${this._isDeprecated ? html`
              <span class="tooltip" title="Deprecated feature">
                <iron-icon icon="chromestatus:warning"
                           class="deprecated" data-tooltip></iron-icon>
              </span>
              ` : nothing}
            ${this.feature.browsers.chrome.flag ? html`
              <span class="tooltip"
                    title="Experimental feature behind a flag">
                <iron-icon icon="chromestatus:flag"
                           class="experimental"></iron-icon>
              </span>
              ` : nothing}
            ${this.feature.browsers.chrome.origintrial ? html`
              <span class="tooltip" title="Origin trial">
                <iron-icon icon="chromestatus:extension"
                           class="experimental"></iron-icon>
              </span>
              ` : nothing}
            ${this.feature.browsers.chrome.intervention ? html`
              <span class="tooltip" title="Browser intervention">
                <iron-icon icon="chromestatus:pan-tool"
                           class="intervention" data-tooltip></iron-icon>
              </span>
              ` : nothing}
            ${this.signedin ? html`
              <span class="tooltip"
                    title="Receive an email notification when there are updates">
                <a href="#" @click="${this.toggleStar}" data-tooltip>
                  <iron-icon icon="${this.starred ?
                                'chromestatus:star' :
                                'chromestatus:star-border'}"
                             class="pushicon"></iron-icon>
                </a>
              </span>
             ` : html`
                <span class="tooltip"
                    title="Sign in to get email notifications for updates">
                <a href="${this.loginUrl}" data-tooltip>
                  <iron-icon icon="chromestatus:star-border"
                             class="pushicon"></iron-icon>
                </a>
              </span>
             `}
            <span class="tooltip" title="File a bug against this feature">
              <a href="${ifDefined(this._newBugUrl)}" data-tooltip>
                <iron-icon icon="chromestatus:bug-report"></iron-icon>
              </a>
            </span>
            <span class="tooltip" title="View on a standalone page">
              <a href="/feature/${this.feature.id}" target="_blank">
                <iron-icon icon="chromestatus:open-in-new"></iron-icon>
              </a>
            </span>
            <iron-icon
              style="margin-left:2em"
              icon="chromestatus:${this.open ? 'expand-less' : 'expand-more'}">
            </iron-icon>
          </div>
        </div>
      </hgroup>
      <section class="desc" @click="${this._togglePanelExpansion}">
        <summary>
          ${this.feature.unlisted ?
             html`<p><b>This feature is only shown in the feature list
                        to users with edit access.</b></p>
             `: nothing }
          <p><span>${this.feature.summary}</span></p>
        </summary>
        ${this.feature.motivation ?
          html`<p><h3>Motivation</h3></p>
          <p><span>${this.feature.motivation}</span></p>`
          : nothing }
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
                ` : nothing}
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
                ` : nothing}
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
                ` : nothing}
              ${this.feature.browsers.chrome.prefixed ? html`
                <span><label>Prefixed</label><span>Yes</span></span>
                ` : nothing}
              ${this.feature.browsers.chrome.bug ? html`<span>
                  <span>Tracking bug</span>
                  <a href="${this.feature.browsers.chrome.bug}"
                     target="_blank">${this._crBugNumber ?
                       `#${this._crBugNumber}` :
                       this.feature.browsers.chrome.bug}</a>
                </span>
                ` : nothing}
              ${this.feature.browsers.chrome.blink_components &&
                this.feature.browsers.chrome.blink_components.length ? html`
                <span>
                  <label>Blink component</label>
                  <span class="tooltip"
                        title="Filter by component ${this.feature.browsers.chrome.blink_components}">
                    <button @click="${this.filterByComponent}">
                      ${this.feature.browsers.chrome.blink_components}
                    </button>
                  </span>
                </span>
                ` : nothing}
              ${this.feature.browsers.chrome.owners &&
                this.feature.browsers.chrome.owners.length ? html`
                <span class="owner">
                  <label>Owner(s)</label>
                  <span class="owner-list">
                    ${this.feature.browsers.chrome.owners.map((owner) => html`
                      <span class="tooltip" title="Filter by owner ${owner}">
                        <button @click="${this.filterByOwner}">
                          ${owner}
                        </button>
                      </span>
                      `)}
                  </span>
                </span>
                ` : nothing}
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
                      title="Doc"></chromedash-multi-links>
                </div>
                ` : nothing}
              ${this._hasDocLinks && this._hasSampleLinks ?
                html`<span>,</span>` : nothing}
              ${this._hasSampleLinks ? html`
                <div class="sample_links">
                  <chromedash-multi-links title="Sample"
                      .links="${this.feature.resources.samples}"
                      ></chromedash-multi-links>
                </div>
                ` : nothing}
            </div>
          </section>
          ` : nothing}
        ${this.feature.comments ? html`
          <section>
            <h3>Comments</h3>
            <summary class="comments">${this._commentHtml}</summary>
          </section>
          ` : nothing}
        ` : nothing}
    `;
  }
}

customElements.define('chromedash-feature', ChromedashFeature);


class ChromedashMultiLinks extends LitElement {
  static styles = sharedStyle;

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
      ${this.links.map((link, index) => html`
        <a href="${link}" target="_blank"
           class="${index < this.links.length - 1 ? 'comma' : ''}"
           >${this.title} ${index + 1}</a>
        `)}
    `;
  }
}

customElements.define('chromedash-multi-links', ChromedashMultiLinks);
