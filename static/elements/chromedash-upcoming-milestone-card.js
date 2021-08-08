import {LitElement, html} from 'lit-element';
import {nothing} from 'lit-html';
import style from '../css/elements/chromedash-upcoming-milestone-card.css';

class ChromedashUpcomingMilestoneCard extends LitElement {
  static styles = style;
  static get properties() {
    return {
      // Assigned in schedule-apge.js, value from Django
      showShippingType: {type: Boolean},
      starredFeatures: {type: Object},
      templateContent: {type: Object},
      channel: {type: Object},
      showDates: {type: Boolean},
      removedStatus: {type: Array},
      deprecatedStatus: {type: Array},
      signedIn: {type: Boolean},
      cardWidth: {type: Number},
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

  _computeDate(dateStr) {
    const opts = {/* weekday: 'short', */month: 'short', day: 'numeric'};
    const date = new Date(dateStr);
    return new Intl.DateTimeFormat('en-US', opts).format(date);
  }

  _fireEvent(eventName, detail) {
    let event = new CustomEvent(eventName, {
      bubbles: true,
      composed: true,
      detail,
    });
    this.dispatchEvent(event);
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

  _computeDaysUntil(dateStr) {
    const today = new Date();
    const diff = this._dateDiffInDays(new Date(dateStr), today);
    const dayWord = diff.days == 1 ? 'day' : 'days';

    if (diff.future) {
      return `in ${diff.days} ${dayWord}`;
    } else {
      return `${diff.days} ${dayWord} ago`;
    }
  }

  _objKeys(obj) {
    if (!obj) {
      return [];
    }
    return Object.keys(obj).sort();
  }

  _cardHeaderTemplate() {
    return html `
      <div class="layout vertical center">
        <h1 class="channel_label">${this.templateContent.channelLabel}</h1>
        <h1 class="chrome_version layout horizontal center ${this.templateContent.h1Class}">
        <span class="chrome-logo"></span>
        <a href="${this.templateContent.downloadUrl}" title="${this.templateContent.downloadTitle}"
          target="_blank">Chrome ${this.channel.version}</a>
        </h1>
      </div>
      ${this.showDates && this.channel.earliest_beta ? html`
      <div class="milestone_info layout horizontal center-center">
        <h3>
          <span class="channel_label">Beta</span> ${this.templateContent.dateText}
          <span class="milestone_info-beta">${this._computeDate(this.channel.earliest_beta)} - ${this._computeDate(this.channel.latest_beta)}</span>
        </h3>
      </div>
      <div class="milestone_info layout horizontal center-center">
        <h3>
          <span class="channel_label">Stable</span> ${this._computeDaysUntil(this.channel.stable_date)}
          <span class="release-stable">( ${this._computeDate(this.channel.stable_date)} )</span>
        </h3>
      </div>
      ` : nothing}
    `;
  }

  _cardFeatureItemTemplate(f) {
    return html `
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
        ${this.removedStatus.includes(f.browsers.chrome.status.text) ? html`
        <span class="tooltip" title="Removed">
          <iron-icon icon="chromestatus:cancel" class="remove" data-tooltip></iron-icon>
        </span>
        ` : nothing}
        ${this.deprecatedStatus.includes(f.browsers.chrome.status.text) ? html`
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
        ` : html`
        <span class="tooltip"
          title="Sign in to get email notifications for updates">
          <a href="#"  @click="${window.promptSignIn}" data-tooltip>
            <iron-icon icon="chromestatus:star-border"
              class="pushicon">
            </iron-icon>
          </a>
        </span>
        `}
      </span>
    </li>
    
    `;
  }

  _cardFeatureListTemplate() {
    return html `
      <div class="features_list">
        <div class="features_header">${this.templateContent.featureHeader}:</div>

          ${this._objKeys(this.channel.features).map((shippingType) => html`
          <h3 class="feature_shipping_type">${shippingType}</h3>
          <ul>
            ${this.channel.features[shippingType].map((f) => html`
              ${this._cardFeatureItemTemplate(f)}
            `)}
          </ul>
        `)}
      </div>
    `;
  }


  _widthStyle() {
    return html`
      <style>
        :host {
          width: ${this.cardWidth}px;
        }
      </style>
    `;
  }

  render() {
    return html`
      ${this._widthStyle()}
      <section class="release ${this.showShippingType ? '' : 'no-components'}">
        ${this._cardHeaderTemplate()}
        ${this._cardFeatureListTemplate()}    
      </section>
    `;
  }
}

customElements.define('chromedash-upcoming-milestone-card', ChromedashUpcomingMilestoneCard);
