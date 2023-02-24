import {LitElement, html, nothing} from 'lit';
import {ref, createRef} from 'lit/directives/ref.js';
import {ROADMAP_MILESTONE_CARD_CSS} from
  '../sass/elements/chromedash-roadmap-milestone-card-css.js';

const REMOVED_STATUS = ['Removed'];
const DEPRECATED_STATUS = ['Deprecated', 'No longer pursuing'];
const ORIGIN_TRIAL = ['Origin trial'];
const BROWSER_INTERVENTION = ['Browser Intervention'];
const NO_FEATURE_STRING = 'NO FEATURES ARE PLANNED FOR THIS MILESTONE YET';


class ChromedashRoadmapMilestoneCard extends LitElement {
  infoPopupRef = createRef();

  static styles = ROADMAP_MILESTONE_CARD_CSS;
  static get properties() {
    return {
      starredFeatures: {type: Object},
      highlightFeature: {type: Number},
      templateContent: {type: Object},
      channel: {type: Object},
      showDates: {type: Boolean},
      signedIn: {type: Boolean},
    };
  }

  constructor() {
    super();
    this.starredFeatures = new Set();
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

  _computeDate(dateStr, addYear=false) {
    const opts = {month: 'short', day: 'numeric'};
    if (addYear) {
      opts.year = 'numeric';
    }
    const date = new Date(dateStr);
    return new Intl.DateTimeFormat('en-US', opts).format(date);
  }

  _fireEvent(eventName, detail) {
    const event = new CustomEvent(eventName, {
      bubbles: true,
      composed: true,
      detail,
    });
    this.dispatchEvent(event);
  }

  _isAnyFeatureReleased() {
    for (const shippingType of this._objKeys(this.channel.features)) {
      if (this.channel.features[shippingType].length != 0) {
        return true;
      }
    }

    return false;
  }

  toggleStar(e) {
    e.preventDefault();
    e.stopPropagation();

    const iconEl = e.target;
    const featureId = Number(iconEl.dataset.featureId);
    const newStarred = !this.starredFeatures.has(featureId);

    this._fireEvent('star-toggle-event', {
      feature: featureId,
      doStar: newStarred,
    });
  }

  highlight(e) {
    e.preventDefault();
    e.stopPropagation();

    const iconEl = e.target.parentNode;
    const featureId = Number(iconEl.dataset.featureId);

    this._fireEvent('highlight-feature-event', {
      feature: featureId,
    });
  }

  removeHighlight(e) {
    e.preventDefault();
    e.stopPropagation();

    this._fireEvent('highlight-feature-event', {
      feature: null,
    });
  }

  _computeDaysUntil(dateStr) {
    const date = new Date(dateStr);
    if (isNaN(date)) {
      return nothing;
    }
    const today = new Date();
    const diff = this._dateDiffInDays(date, today);
    // If stable is (or was) very recent, we don't want to display relative time
    // in small increments (e.g. "in 39 minutes"), so we show "coming soon".
    if (diff.days < 1) {
      return 'coming soon';
    }
    return html`
        <sl-relative-time date="${date.toISOString()}">
        </sl-relative-time>`;
  }

  _objKeys(obj) {
    if (!obj) {
      return [];
    }
    return Object.keys(obj).sort();
  }


  hidePopup(e) {
    if (e.relatedTarget != this.renderRoot.querySelector('#detailed-info-link')) {
      this.infoPopupRef.value.active = null;
    }
  }

  renderInfoIcon() {
    return html`
      <sl-icon-button name="info-circle" id="info-button"
        @click=${() => this.infoPopupRef.value.active = !this.infoPopupRef.value.active} @focusout=${this.hidePopup}
      ></sl-icon-button>

      <sl-popup anchor="info-button" placement="bottom" strategy="fixed"
        ${ref(this.infoPopupRef)}>
        <div class="popup-content">
          New versions are offered to users gradually. <br/>
          See
          <a @focusout=${this.hidePopup} id="detailed-info-link" href="https://chromiumdash.appspot.com/schedule"
             target="_blank">detailed dates</a>.
        </div>
      </sl-popup>
    `;
  }


  renderCardHeader() {
    // Starting with M110, display Early Stable Release dates.
    const stableStart = (this.channel.version >= 110) ?
      this.channel.final_beta : this.channel.stable_date;

    return html `
      <div class="layout vertical center">
        <h1 class="channel_label">${this.templateContent.channelLabel}</h1>
        <h1 class="chrome_version layout horizontal center ${this.templateContent.h1Class}">
        <span class="chrome-logo"></span>
        Chrome ${this.channel.version}
        </h1>
      </div>
      ${this.showDates && this.channel.earliest_beta ? html`
      <div class="milestone_info layout horizontal center-center">
        <h3>
          <span class="channel_label">Beta</span> ${this.templateContent.dateText}
          <span class="milestone_info-beta">
            ${this._computeDate(this.channel.earliest_beta)} -
            ${this._computeDate(this.channel.latest_beta)}
         </span>
        </h3>
      </div>
      <div class="milestone_info layout horizontal center-center">
        <h3>
          <span class="channel_label">Stable</span> ${this._computeDaysUntil(stableStart)}
          <span class="release-stable">(${this._computeDate(stableStart, true)})</span>
          ${this.renderInfoIcon()}

        </h3>
      </div>
      ` : nothing}
    `;
  }

  _cardFeatureItemTemplate(f, shippingType) {
    return html `
    <li data-feature-id="${f.id}" class="${f.id == this.highlightFeature ? 'highlight' : ''}">
      <a id="feature_link" href="/feature/${f.id}" @mouseenter="${this.highlight}" @mouseleave="${this.removeHighlight}">
        ${f.name}
      </a>
      <span class="icon_row">
        ${ORIGIN_TRIAL.includes(shippingType) ? html`
        <span class="tooltip" title="Origin Trial">
          <iron-icon icon="chromestatus:extension" class="experimental" data-tooltip></iron-icon>
        </span>
        ` : nothing}
        ${BROWSER_INTERVENTION.includes(shippingType) ? html`
        <span class="tooltip" title="Browser intervention">
          <iron-icon icon="chromestatus:pan-tool" class="intervention" data-tooltip></iron-icon>
        </span>
        ` : nothing}
        ${REMOVED_STATUS.includes(shippingType) ? html`
        <span class="tooltip" title="Removed">
          <iron-icon icon="chromestatus:cancel" class="remove" data-tooltip></iron-icon>
        </span>
        ` : nothing}
        ${DEPRECATED_STATUS.includes(shippingType) ? html`
        <span class="tooltip" title="Deprecated">
          <iron-icon icon="chromestatus:warning" class="deprecated" data-tooltip></iron-icon>
        </span>
        ` : nothing}
        ${this.signedIn ? html`
        <span class="tooltip"
          title="Receive an email notification when there are updates">
          <iron-icon
            icon="${this.starredFeatures.has(Number(f.id)) ?
            'chromestatus:star' :
            'chromestatus:star-border'}"
            class="pushicon"
            data-feature-id="${f.id}"
            @click="${this.toggleStar}">
          </iron-icon>
        </span>
        ` : nothing}
      </span>
    </li>

    `;
  }

  renderCardFeatureList() {
    return html `
      <div class="features_list">
        ${this._isAnyFeatureReleased() ? html `
        <div class="features_header">${this.templateContent.featureHeader}:</div>
          ${this._objKeys(this.channel.features).map((shippingType) => this.channel.features[shippingType] != 0 ? html`
          <h3 class="feature_shipping_type">${shippingType}</h3>
          <ul>
            ${this.channel.features[shippingType].map((f) => html`
              ${this._cardFeatureItemTemplate(f, shippingType)}
            `)}
          </ul>
          ` : nothing)}
          </div>` : html `
          <div class="features_header no_feature_released">${NO_FEATURE_STRING}</div>
        `}
      </div>
    `;
  }

  renderSkeletons() {
    return html`
      <div class="layout vertical center">
        <h1 class="channel_label">${this.templateContent.channelLabel}</h1>
        <h1 class="chrome_version layout horizontal sl-skeleton-header-container ${this.templateContent.h1Class}">
          <span class="chrome-logo"></span>
          <sl-skeleton effect="sheen"></sl-skeleton>
        </h1>
      </div>
      <div class="milestone_info layout horizontal center-center">
        <h3 class="sl-skeleton-header-container">
          <sl-skeleton effect="sheen"></sl-skeleton>
        </h3>
      </div>
      <div class="milestone_info layout horizontal center-center">
        <h3 class="sl-skeleton-header-container">
          <sl-skeleton effect="sheen"></sl-skeleton>
        </h3>
      </div>
      <div class="features_list">
        <div class="sl-skeleton-title-container">
          <sl-skeleton effect="sheen"></sl-skeleton>
        </div>
        <sl-skeleton effect="sheen"></sl-skeleton>
        <sl-skeleton effect="sheen"></sl-skeleton>
        <sl-skeleton effect="sheen"></sl-skeleton>
        <sl-skeleton effect="sheen"></sl-skeleton>
        </div>
      </div>
      <div class="features_list">
        <div class="sl-skeleton-title-container">
          <sl-skeleton effect="sheen"></sl-skeleton>
        </div>
        <sl-skeleton effect="sheen"></sl-skeleton>
        <sl-skeleton effect="sheen"></sl-skeleton>
        <sl-skeleton effect="sheen"></sl-skeleton>
        <sl-skeleton effect="sheen"></sl-skeleton>
        </div>
      </div>
    `;
  }

  render() {
    return html`
      <section class="release">
        ${this.channel ? html`
          ${this.renderCardHeader()}
          ${this.renderCardFeatureList()}
        `: html`
          ${this.renderSkeletons()}
        `}
      </section>
    `;
  }
}

customElements.define(
  'chromedash-roadmap-milestone-card',
  ChromedashRoadmapMilestoneCard);
