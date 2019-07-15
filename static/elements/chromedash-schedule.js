import {LitElement, html} from 'lit-element';
import '@polymer/iron-icon';

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

class ChromedashSchedule extends LitElement {
  static get properties() {
    return {
      channels: {type: Object}, // Assigned in schedule.js, value from Django
      hideBlink: {type: Boolean}, // Edited in schedule.js
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

  _subscribeToFeature(e) {
    e.preventDefault();
    e.stopPropagation();

    const iconEl = e.target;
    const featureId = iconEl.dataset.featureId;
    const receivePush = iconEl.icon !== 'chromestatus:notifications';
    iconEl.icon = receivePush ? 'chromestatus:notifications' : 'chromestatus:notifications-off';

    if (receivePush) {
      window.PushNotifications.subscribeToFeature(featureId);
    } else {
      window.PushNotifications.unsubscribeFromFeature(featureId);
    }
  }

  render() {
    if (!this.channels) {
      return html``;
    }
    return html`
      <link rel="stylesheet" href="/static/css/elements/chromedash-schedule.css">

      ${['stable', 'beta', 'dev'].map((type) => html`
        <section class="release ${this.hideBlink ? 'no-components' : ''}">
          <div class="layout vertical center">
            <h1 class="channel_label">${TEMPLATE_CONTENT[type].channelLabel}</h1>
            <h1 class="chrome_version layout horizontal center ${TEMPLATE_CONTENT[type].h1Class}">
              <span class="chrome-logo"></span>
              <a href="${TEMPLATE_CONTENT[type].downloadUrl}" title="${TEMPLATE_CONTENT[type].downloadTitle}"
                 target="_blank">Chrome ${this.channels[type].version}</a>
            </h1>
          </div>
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
                        ` : ''}
                      ${f.browsers.chrome.intervention ? html`
                        <span class="tooltip" title="Browser intervention">
                          <iron-icon icon="chromestatus:pan-tool" class="intervention" data-tooltip></iron-icon>
                        </span>
                        ` : ''}
                      ${REMOVED_STATUS.includes(f.browsers.chrome.status.text) ? html`
                        <span class="tooltip" title="Removed">
                          <iron-icon icon="chromestatus:cancel" class="remove" data-tooltip></iron-icon>
                        </span>
                        ` : ''}
                      ${DEPRECATED_STATUS.includes(f.browsers.chrome.status.text) ? html`
                        <span class="tooltip" title="Deprecated">
                          <iron-icon icon="chromestatus:warning" class="deprecated" data-tooltip></iron-icon>
                        </span>
                        ` : ''}
                      ${window.PushNotifier && window.PushNotifier.SUPPORTS_NOTIFICATIONS ? html`
                        <span class="tooltip" title="Subscribe to notification updates">
                          <iron-icon icon="chromestatus:notifications-off"
                                     class="pushicon ${window.PushNotifier && window.PushNotifier.GRANTED_ACCESS ? '' : 'disabled'}"
                                     data-feature-id="${f.id}"
                                     @click="${this._subscribeToFeature}"></iron-icon>
                        </span>
                      </span>
                        ` : ''}
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
