import {LitElement, html} from 'https://unpkg.com/@polymer/lit-element@latest/lit-element.js?module';
import 'https://unpkg.com/@polymer/iron-icon/iron-icon.js?module';

class ChromedashSchedule extends LitElement {
  static get properties() {
    return {
    };
  }

  constructor() {
    super();
  }

  _objKeys(obj) {
    if (!obj) {
      return [];
    }
    return Object.keys(obj).sort();
  }

  _featuresFor(features, componentName) {
    return features[componentName];
  }

  isRemoved(implStatusChrome) {
    return implStatusChrome === 'Removed';
  }

  isDeprecated(implStatusChrome) {
    return implStatusChrome === 'Deprecated' || implStatusChrome === 'No longer pursuing';
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

  pushDisabled() {
    return PushNotifier.GRANTED_ACCESS ? '' : 'disabled';
  }

  _computePushSubscribed(subscribed) {
    return subscribed ? 'chromestatus:notifications' : 'chromestatus:notifications-off';
  }

  subscribeToFeature(e) {
    e.preventDefault();
    e.stopPropagation();

    const featureId = Polymer.dom(e).event.model.f.id;
    const icon = Polymer.dom(e).localTarget;
    const receivePush = icon.icon !== 'chromestatus:notifications';
    icon.icon = this._computePushSubscribed(receivePush);

    if (receivePush) {
      PushNotifications.subscribeToFeature(featureId);
    } else {
      PushNotifications.unsubscribeFromFeature(featureId);
    }
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

  render() {
    return html`
      <div>
        <div class="releases layout horizontal wrap">
          <section class="release">
            <div class="layout vertical center">
              <h1 class="channel_label">stable</h1>
              <h1 class="chrome_version layout horizontal center">
                <span class="chrome-logo"></span>
                <a href="https://www.google.com/chrome/browser/desktop/index.html" target="_blank" title="Download Chrome stable">Chrome [[channels.stable.version]]</a>
              </h1>
            </div>
            <div class="milestone_info layout horizontal center-center">
              <h3><span class="channel_label">Beta</span> was <span class="milestone_info-beta">[[_computeDate(channels.stable.earliest_beta)]] - [[_computeDate(channels.stable.latest_beta)]]</span></h3>
            </div>
            <div class="milestone_info layout horizontal center-center">
              <h3><span class="channel_label">Stable</span> [[_computeDaysUntil(channels.stable.stable_date)]]
                <span class="release-stable">( [[_computeDate(channels.stable.stable_date)]] )</span>
              </h3>
            </div>
            <div class="features_list">
              <div class="features_header">Features in this release:</div>

              <template is="dom-repeat" items="[[_objKeys(channels.stable.components)]]" as="componentName">
                <h3 class="feature_components">{{componentName}}</h3>
                <ul>
                  <template is="dom-repeat" items="[[_featuresFor(channels.stable.components, componentName)]]" as="f">
                    <li data-feature-id$="[[f.id]]">
                      <a href$="/feature/[[f.id]]">[[f.name]]</a>
                      <span class="icon_row">
                        <template is="dom-if" if="[[f.browsers.chrome.origintrial]]">
                          <span class="tooltip" title="Origin Trial">
                            <iron-icon icon="chromestatus:extension" class="experimental" data-tooltip></iron-icon>
                          </span>
                        </template>
                        <template is="dom-if" if="[[f.browsers.chrome.intervention]]">
                          <span class="tooltip" title="Browser intervention">
                            <iron-icon icon="chromestatus:pan-tool" class="intervention" data-tooltip></iron-icon>
                          </span>
                        </template>
                        <template is="dom-if" if="[[isRemoved(f.browsers.chrome.status.text)]]">
                          <span class="tooltip" title="Removed">
                            <iron-icon icon="chromestatus:cancel" class="remove" data-tooltip></iron-icon>
                          </span>
                        </template>
                        <template is="dom-if" if="[[isDeprecated(f.browsers.chrome.status.text)]]">
                          <span class="tooltip" title="Deprecated">
                            <iron-icon icon="chromestatus:warning" class="deprecated" data-tooltip></iron-icon>
                          </span>
                        </template>
                        <span class="tooltip no-push-notifications" title="Subscribe to notification updates">
                          <iron-icon icon="chromestatus:notifications-off"
                                    on-click="subscribeToFeature" class$="pushicon [[pushDisabled()]]"></iron-icon>
                        </span>
                      </span>
                    </li>
                  </template>
                </ul>
              </template>

            </div>
          </section>
          <section class="release release-beta">
            <div class="layout vertical center">
              <h1 class="channel_label">Next up</h1>
              <h1 class="chrome_version chrome_version--beta layout horizontal center">
                <span class="chrome-logo"></span>
                <a href="https://www.google.com/chrome/browser/beta.html" target="_blank" title="Download Chrome Beta">Chrome [[channels.beta.version]]</a>
              </h1>
            </div>
            <div class="milestone_info layout horizontal center-center">
              <h3><span class="channel_label">Beta</span> between <span class="milestone_info-beta">[[_computeDate(channels.beta.earliest_beta)]] - [[_computeDate(channels.beta.latest_beta)]]</span></h3>
            </div>
            <div class="milestone_info layout horizontal center-center">
              <h3><span class="channel_label">Stable</span> [[_computeDaysUntil(channels.beta.stable_date)]]
                <span class="release-stable">( [[_computeDate(channels.beta.stable_date)]] )</span>
              </h3>
            </div>
            <div class="features_list">
              <div class="features_header">Features planned in this release:</div>

              <template is="dom-repeat" items="[[_objKeys(channels.beta.components)]]" as="componentName">
                <h3 class="feature_components">{{componentName}}</h3>
                <ul>
                  <template is="dom-repeat" items="[[_featuresFor(channels.beta.components, componentName)]]" as="f">
                    <li data-feature-id$="[[f.id]]">
                      <a href$="/feature/[[f.id]]">[[f.name]]</a>
                      <span class="icon_row">
                        <template is="dom-if" if="[[f.browsers.chrome.origintrial]]">
                          <span class="tooltip" title="Origin Trial">
                            <iron-icon icon="chromestatus:extension" class="experimental" data-tooltip></iron-icon>
                          </span>
                        </template>
                        <template is="dom-if" if="[[f.browsers.chrome.intervention]]">
                          <span class="tooltip" title="Browser intervention">
                            <iron-icon icon="chromestatus:pan-tool" class="intervention" data-tooltip></iron-icon>
                          </span>
                        </template>
                        <template is="dom-if" if="[[isRemoved(f.browsers.chrome.status.text)]]">
                          <span class="tooltip" title="Removed">
                            <iron-icon icon="chromestatus:cancel" class="remove" data-tooltip></iron-icon>
                          </span>
                        </template>
                        <template is="dom-if" if="[[isDeprecated(f.browsers.chrome.status.text)]]">
                          <span class="tooltip" title="Deprecated">
                            <iron-icon icon="chromestatus:warning" class="deprecated" data-tooltip></iron-icon>
                          </span>
                        </template>
                        <span class="tooltip no-push-notifications" title="Subscribe to notification updates">
                          <iron-icon icon="chromestatus:notifications-off"
                                    on-click="subscribeToFeature" class$="pushicon [[pushDisabled()]]"></iron-icon>
                        </span>
                      </span>
                    </li>
                  </template>
                </ul>
              </template>

            </div>
          </section>
          <section class="release">
            <div class="layout vertical center">
              <h1 class="channel_label">&nbsp;</h1>
              <h1 class="chrome_version chrome_version--dev layout horizontal center">
                <span class="chrome-logo"></span>
                <a href="https://www.google.com/chrome/browser/canary.html" target="_blank" title="Download Chrome Canary">Chrome [[channels.dev.version]]</a>
              </h1>
            </div>
            <div class="milestone_info layout horizontal center-center">
              <h3><span class="channel_label">Beta </span> coming <span class="milestone_info-beta">[[_computeDate(channels.dev.earliest_beta)]] - [[_computeDate(channels.dev.latest_beta)]]</span></h3>
            </div>
            <div class="milestone_info layout horizontal center-center">
              <h3><span class="channel_label">Stable</span> [[_computeDaysUntil(channels.dev.stable_date)]]
                <span class="release-stable">( [[_computeDate(channels.dev.stable_date)]] )</span>
              </h3>
            </div>
            <div class="features_list">
              <div class="features_header">Features planned in this release:</div>

              <template is="dom-repeat" items="[[_objKeys(channels.dev.components)]]" as="componentName">
                <h3 class="feature_components">{{componentName}}</h3>
                <ul>
                  <template is="dom-repeat" items="[[_featuresFor(channels.dev.components, componentName)]]" as="f">
                    <li data-feature-id$="[[f.id]]">
                      <a href$="/feature/[[f.id]]">[[f.name]]</a>
                      <span class="icon_row">
                        <template is="dom-if" if="[[f.browsers.chrome.origintrial]]">
                          <span class="tooltip" title="Origin Trial">
                            <iron-icon icon="chromestatus:extension" class="experimental" data-tooltip></iron-icon>
                          </span>
                        </template>
                        <template is="dom-if" if="[[f.browsers.chrome.intervention]]">
                          <span class="tooltip" title="Browser intervention">
                            <iron-icon icon="chromestatus:pan-tool" class="intervention" data-tooltip></iron-icon>
                          </span>
                        </template>
                        <template is="dom-if" if="[[isRemoved(f.browsers.chrome.status.text)]]">
                          <span class="tooltip" title="Removed">
                            <iron-icon icon="chromestatus:cancel" class="remove" data-tooltip></iron-icon>
                          </span>
                        </template>
                        <template is="dom-if" if="[[isDeprecated(f.browsers.chrome.status.text)]]">
                          <span class="tooltip" title="Deprecated">
                            <iron-icon icon="chromestatus:warning" class="deprecated" data-tooltip></iron-icon>
                          </span>
                        </template>
                        <span class="tooltip no-push-notifications" title="Subscribe to notification updates">
                          <iron-icon icon="chromestatus:notifications-off"
                                    on-click="subscribeToFeature" class$="pushicon [[pushDisabled()]]"></iron-icon>
                        </span>
                      </span>
                    </li>
                  </template>
                </ul>
              </template>

            </div>
          </section>
        </div>
      </div>
    `;
  }
}

customElements.define('chromedash-schedule', ChromedashSchedule);
