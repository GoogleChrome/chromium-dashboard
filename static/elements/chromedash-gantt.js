import {LitElement, css, html} from 'lit-element';
import {nothing} from 'lit-html';
import SHARED_STYLES from '../css/shared.css';

class ChromedashGantt extends LitElement {
  static get properties() {
    return {
      feature: {type: Object},
      stableMilestone: {type: Number},
    };
  }

  constructor() {
    super();
    this.feature = {};
    this.stableMilestone = null;
    window.csClient.getChannels().then((channels) =>
      this.stableMilestone = channels['stable'].version);
  }

  static get styles() {
    return [
      SHARED_STYLES,
      css`
      :host {
        width: 200px;
        margin-top: 8px;
      }
      ul {
        display: block;
        font-size: 12px;
        vertical-align: top;
        padding: 0;
        margin: var(--content-padding-half);
      }
      li {
        display: inline-block;
        width: 80px;
        padding: 4px 8px;
      }
      .header li {
        text-align: center;
      }
      .bar {
        background-repeat: no-repeat;
        background-size: 210px;
        background-position: 100px;
      }
      .without-ot {
        background-image: url(/static/img/gantt-bar-without-ot.png);
      }
      .with-ot {
        background-image: url(/static/img/gantt-bar-with-ot.png);
      }
      .platform {
        padding-top: 15px;
        vertical-align: top;
      }
      .diamond {
        transform: rotate(45deg);
        width: 36px;
        height: 36px;
        text-align: center;
        margin: auto;
        border: 2px solid white;
      }
      .dev_trial {
        background: #cfe2f3ff;
      }
      .origin_trial {
        background: #6fa8dcff;
      }
      .shipping {
        background: #0b5394ff;
        color: white;
      }
      .stable {
        border-color: #444;
      }
      .diamond span {
        font-size: 14px;
        font-weight: bold;
        display: table-cell;
        transform: rotate(-45deg);
        width: 34px;
        height: 34px;
        vertical-align: middle;
      }
      .offset_0 { padding-left: 0px; }
      .offset_1 { padding-left: 8px; }
      .offset_2 { padding-left: 16px; }
      .offset_3 { padding-left: 24px; }
    `];
  }

  firstPhrase(milestone) {
    if (milestone <= this.stableMilestone) {
      return 'First milestone with this feature';
    } else {
      return 'First expected milestone with this feature';
    }
  }

  _isInactive() {
    const status = this.feature.browsers.chrome.status.text;
    return (status === 'No active development' ||
            status === 'On hold' ||
            status === 'No longer pursuing');
  }

  renderDevTrial(milestone) {
    if (!milestone) return nothing;
    return html`
      <div class="diamond dev_trial
                  ${milestone === this.stableMilestone ? 'stable' : ''}"
       title="${this.firstPhrase(milestone)} available to developers behind a flag"
      ><span>${milestone}</span></div>`;
  }

  renderOriginTrial(milestone) {
    if (!milestone) return nothing;
    return html`
      <div class="diamond origin_trial
                  ${milestone === this.stableMilestone ? 'stable' : ''}"
       title="${this.firstPhrase(milestone)} enabled on participating origins"
      ><span>${milestone}</span></div>`;
  }

  renderShipping(milestone) {
    if (!milestone) return nothing;
    return html`
      <div class="diamond shipping
                  ${milestone === this.stableMilestone ? 'stable' : ''}"
       title="${this.firstPhrase(milestone)} enabled by default"
      ><span>${milestone}</span></div>`;
  }

  renderRow(
    platform, devTrialMilestone, originTrialMilestone, shippingMilestone,
    sortedMilestones) {
    if (!devTrialMilestone && !originTrialMilestone && !shippingMilestone) {
      return nothing;
    }

    const dtOffset = sortedMilestones.dt.indexOf(devTrialMilestone);
    const otOffset = sortedMilestones.ot.indexOf(originTrialMilestone);
    const shipOffset = sortedMilestones.ship.indexOf(shippingMilestone);

    return html`
       <ul class="bar ${originTrialMilestone ? 'with-ot' : 'without-ot'}">
         <li class="platform">${platform}</li>
         <li class="${'offset_' + dtOffset}">
           ${this.renderDevTrial(devTrialMilestone)}
         </li>
         <li class="${'offset_' + otOffset}">
           ${this.renderOriginTrial(originTrialMilestone)}
         </li>
         <li class="${'offset_' + shipOffset}">
           ${this.renderShipping(shippingMilestone)}
         </li>
       </ul>
    `;
  }

  render() {
    const f = this.feature;
    const dtDesktop = f.dt_milestone_desktop_start;
    const otDesktop = f.ot_milestone_desktop_start;
    const shipDesktop = f.browsers.chrome.desktop;
    const dtAndroid = f.dt_milestone_android_start;
    const otAndroid = f.ot_milestone_android_start;
    const shipAndroid = f.browsers.chrome.android;
    const dtIos = f.dt_milestone_ios_start;
    const otIos = null; // Chrome on iOS does not support OT.
    const shipIos = f.browsers.chrome.ios;
    const dtWebview = f.dt_milestone_webview_start;
    const otWebview = null; // Webview does not support OT.
    const shipWebview = f.browsers.chrome.webview;

    if (!dtDesktop && !otDesktop && !shipDesktop &&
        !dtAndroid && !otAndroid && !shipAndroid &&
        !dtIos && !otIos && !shipIos &&
        !dtWebview && !otWebview && !shipWebview) {
      return html`<p>No milestones specified</p>`;
    }

    // Don't show the visualization if there is no active development.
    // But, any milestones are available as text in the details section.
    if (this._isInactive()) {
      return nothing;
    }

    const sortedMilestones = {
      dt: [dtDesktop, dtAndroid, dtIos, dtWebview].sort(),
      ot: [otDesktop, otAndroid, otIos, otWebview].sort(),
      ship: [shipDesktop, shipAndroid, shipIos, shipWebview].sort(),
    };

    return html`
       <p>Estimated milestones:</p>
       <ul class="header">
         <li></li>
         <li>Dev Trial</li>
         <li>Origin Trial</li>
         <li>Shipping</li>
       </ul>
       ${this.renderRow('Desktop',
          dtDesktop, otDesktop, shipDesktop, sortedMilestones)}
       ${this.renderRow('Android',
          dtAndroid, otAndroid, shipAndroid, sortedMilestones)}
       ${this.renderRow('iOS',
          dtIos, otIos, shipIos, sortedMilestones)}
       ${this.renderRow('Webview',
          dtWebview, otWebview, shipWebview, sortedMilestones)}
    `;
  }
}

customElements.define('chromedash-gantt', ChromedashGantt);
