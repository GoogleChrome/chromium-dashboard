import {LitElement, html} from 'lit-element';
import {nothing} from 'lit-html';
import '@polymer/iron-icon';
import style from '../css/elements/chromedash-schedule.css';

const TEMPLATE_CONTENT = {
  stable: {
    channelLabel: 'Stable',
    h1Class: '',
    downloadUrl: 'https://www.google.com/chrome/browser/desktop/index.html',
    downloadTitle: 'Download Chrome stable',
    dateText: 'was',
    featureHeader: 'Features in this release',
  },
  beta: {
    channelLabel: 'Next up',
    h1Class: 'chrome_version--beta',
    downloadUrl: 'https://www.google.com/chrome/browser/beta.html',
    downloadTitle: 'Download Chrome Beta',
    dateText: 'between',
    featureHeader: 'Features planned in this release',
  },
  dev: {
    channelLabel: 'Dev',
    h1Class: 'chrome_version--dev',
    downloadUrl: 'https://www.google.com/chrome/browser/canary.html',
    downloadTitle: 'Download Chrome Canary',
    dateText: 'coming',
    featureHeader: 'Features planned in this release',
  },
};

const REMOVED_STATUS = ['Removed'];
const DEPRECATED_STATUS = ['Deprecated', 'No longer pursuing'];
const SHOW_DATES = true;

class ChromedashSchedule extends LitElement {
  static styles = style;

  constructor() {
    super();
    this.starredFeatures = new Set();
  }

  static get properties() {
    return {
      // Assigned in schedule-apge.js, value from Django
      channels: {attribute: false},
      showBlink: {attribute: false}, // Set by code in schedule-page.js
      signedin: {type: Boolean},
      loginUrl: {type: String},
      starredFeatures: {attribute: false},
    };
  }

  _objKeys(obj) {
    if (!obj) {
      return [];
    }
    return Object.keys(obj).sort();
  }

  _computeDaysUntil(dateStr) {
    const today = new Date();
    const diff = this._dateDiffInDays(new Date(dateStr), today);
    const prefix = diff.future ? 'in' : '';
    const days = diff.days > 1 ? 's' : '';
    const ago = !diff.future ? 'ago' : '';
    return `${prefix} ${diff.days} day${days} ${ago}`;
  }

  _computeDate(dateStr) {
    const opts = {/* weekday: 'short', */month: 'short', day: 'numeric'};
    const date = new Date(dateStr);
    return new Intl.DateTimeFormat('en-US', opts).format(date);
  }

  /**
   *  Returns the number of days between a and b.
   *  @param {!Date} a
   *  @param {!Date} b
   *  @return {!{days: number, future: boolean}}
   */
  _dateDiffInDays(a, b) {
    // Discard time and time-zone information.
    const utc1 = Date.UTC(a.getFullYear(), a.getMonth(), a.getDate());
    const utc2 = Date.UTC(b.getFullYear(), b.getMonth(), b.getDate());

    const MS_PER_DAY = 1000 * 60 * 60 * 24;
    const daysDiff = Math.floor((utc2 - utc1) / MS_PER_DAY);
    return {days: Math.abs(daysDiff), future: daysDiff < 1};
  }

  toggleStar(e) {
    e.preventDefault();
    e.stopPropagation();

    const iconEl = e.target;
    const featureId = Number(iconEl.dataset.featureId);
    const newStarred = !this.starredFeatures.has(featureId);
    window.StarService.setStar(featureId, newStarred);

    const newStarredFeatures = new Set(this.starredFeatures);
    if (newStarred) {
      newStarredFeatures.add(featureId);
    } else {
      newStarredFeatures.delete(featureId);
    }
    this.starredFeatures = newStarredFeatures;
  }

  render() {
    if (!this.channels) {
      return html``;
    }
    return html`
      ${['stable', 'beta', 'dev'].map((type) => html`
        <section class="release ${this.showBlink ? nothing : 'no-components'}">
          <div class="layout vertical center">
            <h1 class="channel_label">${TEMPLATE_CONTENT[type].channelLabel}</h1>
            <h1 class="chrome_version layout horizontal center ${TEMPLATE_CONTENT[type].h1Class}">
              <span class="chrome-logo"></span>
              <a href="${TEMPLATE_CONTENT[type].downloadUrl}" title="${TEMPLATE_CONTENT[type].downloadTitle}"
                 target="_blank">Chrome ${this.channels[type].version}</a>
            </h1>
          </div>
          ${SHOW_DATES && this.channels[type].earliest_beta ? html`
            <div class="milestone_info layout horizontal center-center">
              <h3>
                <span class="channel_label">Beta</span> ${TEMPLATE_CONTENT[type].dateText}
                <span class="milestone_info-beta">${this._computeDate(this.channels[type].earliest_beta)} - ${this._computeDate(this.channels[type].latest_beta)}</span>
              </h3>
            </div>
            <div class="milestone_info layout horizontal center-center">
              <h3>
                <span class="channel_label">Stable</span> ${this._computeDaysUntil(this.channels[type].stable_date)}
                <span class="release-stable">( ${this._computeDate(this.channels[type].stable_date)} )</span>
              </h3>
            </div>
          ` : nothing}
          <div class="features_list">
            <div class="features_header">${TEMPLATE_CONTENT[type].featureHeader}:</div>

            ${this._objKeys(this.channels[type].components).map((componentName) => html`
              <h3 class="feature_components">${componentName}</h3>
              <ul>
                ${this.channels[type].components[componentName].map((f) => html`
                  <li data-feature-id="${f.id}">
                    <a href="/feature/${f.id}">${f.name}</a>
                    <span class="icon_row">
                      ${f.browsers.chrome.origintrial ? html`
                        <span class="tooltip" title="Origin Trial">
                          <iron-icon icon="chromestatus:extension" class="experimental" data-tooltip></iron-icon>
                        </span>
                        ` : nothing}
                      ${f.browsers.chrome.intervention ? html`
                        <span class="tooltip" title="Browser intervention">
                          <iron-icon icon="chromestatus:pan-tool" class="intervention" data-tooltip></iron-icon>
                        </span>
                        ` : nothing}
                      ${REMOVED_STATUS.includes(f.browsers.chrome.status.text) ? html`
                        <span class="tooltip" title="Removed">
                          <iron-icon icon="chromestatus:cancel" class="remove" data-tooltip></iron-icon>
                        </span>
                        ` : nothing}
                      ${DEPRECATED_STATUS.includes(f.browsers.chrome.status.text) ? html`
                        <span class="tooltip" title="Deprecated">
                          <iron-icon icon="chromestatus:warning" class="deprecated" data-tooltip></iron-icon>
                        </span>
                        ` : nothing}
                      ${this.signedin ? html`
                        <span class="tooltip"
                              title="Receive an email notification when there are updates">
                          <iron-icon
                             icon="${this.starredFeatures.has(Number(f.id)) ?
                               'chromestatus:star' :
                               'chromestatus:star-border'}"
                             class="pushicon"
                             data-feature-id="${f.id}"
                             @click="${this.toggleStar}"></iron-icon>
                        </span>
                      ` : html`
                        <span class="tooltip"
                              title="Sign in to get email notifications for updates">
                          <a href="#"  @click="${window.promptSignIn}" data-tooltip>
                            <iron-icon icon="chromestatus:star-border"
                                       class="pushicon"></iron-icon>
                          </a>
                        </span>
                    `}
                    </span>
                  </li>
                  `)}
              </ul>
              `)}
          </div>
        </section>
        `)}
    `;
  }
}

customElements.define('chromedash-schedule', ChromedashSchedule);
