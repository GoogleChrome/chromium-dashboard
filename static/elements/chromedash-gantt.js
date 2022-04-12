import {LitElement, css, html, nothing} from 'lit';
import {SHARED_STYLES} from '../sass/shared-css.js';

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
      ...SHARED_STYLES,
      css`
      :host {
        width: 600px;
        margin-top: 8px;
      }
      .platform {
        display: inline-block;
        padding-top: 15px;
        vertical-align: top;
        width: 100px;
      }
      .chart {
        display: inline-block;
      }


      .strip div {
        display: inline-block;
        width: 50px;
        height: 30px;
        overflow: visible;
        white-space: nowrap;
        background: #eee;
        padding: 4px;
        line-height: 22px;
        margin: 3px 2px;
      }

      .strip div.dev_trial {
        background: #cfe2f3ff;
      }
      .strip div.origin_trial {
        background: #6fa8dcff;
      }
      .strip div.shipping {
        background: #0b5394ff;
        color: white;
      }
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

  renderPlatform(
    platform, devTrialMilestone, originTrialMilestoneFirst,
    originTrialMilestoneLast, shippingMilestone,
    sortedMilestones) {
    if (!devTrialMilestone && !originTrialMilestoneFirst && !shippingMilestone) {
      return nothing;
    }

    const dtOffset = sortedMilestones.dt.indexOf(devTrialMilestone);
    const otOffset = sortedMilestones.ot.indexOf(originTrialMilestoneFirst);
    const shipOffset = sortedMilestones.ship.indexOf(shippingMilestone);

    return html`
       <li><div class="platform">${platform}</div>

       <div class="chart">
           <div class="strip">
             <div>97</div><div>98</div
             ><div style="width: ${7*50 + 4*6}px" class="dev_trial">${devTrialMilestone}  ${dtOffset}</div
             ><div>106</div><div>107</div>
           </div>
           <div class="strip">
             <div>97</div><div>98</div><div>99</div><div>100</div
             ><div style="width: ${4*50 + 4*3}px" class="origin_trial">${originTrialMilestoneFirst}  ${otOffset}</div
             ><div>105</div><div>106</div><div>107</div>
           </div>
           <div class="strip">
             <div>97</div><div>98</div><div>99</div><div>100</div><div>101</div><div>102</div><div>103</div><div>104</div><div>105</div
             ><div style="width: ${2*50 + 4*1}px" class="shipping">${shippingMilestone} ${shipOffset}</div>
           </div>
         </div>
       </li>
    `;
  }

  render() {
    const f = this.feature;
    const dtDesktop = f.dt_milestone_desktop_start;
    const otDesktopFirst = f.ot_milestone_desktop_start;
    const otDesktopLast = f.ot_milestone_desktop_end;
    const shipDesktop = f.browsers.chrome.desktop;
    const dtAndroid = f.dt_milestone_android_start;
    const otAndroidFirst = f.ot_milestone_android_start;
    const otAndroidLast = f.ot_milestone_android_end;
    const shipAndroid = f.browsers.chrome.android;
    const dtIos = f.dt_milestone_ios_start;
    const otIos = null; // Chrome on iOS does not support OT.
    const shipIos = f.browsers.chrome.ios;
    const dtWebview = f.dt_milestone_webview_start;
    const otWebview = null; // Webview does not support OT.
    const shipWebview = f.browsers.chrome.webview;

    if (!dtDesktop && !otDesktopFirst && !shipDesktop &&
        !dtAndroid && !otAndroidFirst && !shipAndroid &&
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
      ot: [otDesktopFirst, otAndroidFirst, otIos, otWebview].sort(),
      ship: [shipDesktop, shipAndroid, shipIos, shipWebview].sort(),
    };

    return html`
       <p>Estimated milestones:</p>
       <ul>
       ${this.renderPlatform('Desktop',
          dtDesktop, otDesktopFirst, otDesktopLast, shipDesktop,
          sortedMilestones)}
       ${this.renderPlatform('Android',
          dtAndroid, otAndroidFirst, otAndroidLast, shipAndroid,
          sortedMilestones)}
       ${this.renderPlatform('iOS',
          dtIos, otIos, otIos, shipIos,
          sortedMilestones)}
       ${this.renderPlatform('Webview',
          dtWebview, otWebview, otWebview, shipWebview,
          sortedMilestones)}
       </ul>
    `;
  }
}

customElements.define('chromedash-gantt', ChromedashGantt);
