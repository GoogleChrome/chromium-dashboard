import {LitElement, css, html} from 'lit-element';
import {nothing} from 'lit-html';
import SHARED_STYLES from '../css/shared.css';

class ChromedashGantt extends LitElement {
  static get properties() {
    return {
      feature: {type: Object},
    };
  }

  constructor() {
    super();
    this.feature = {};
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
        border-color: gray;
      }
      .diamond span {
        font-size: 14px;
        font-weight: bold;
        display: table-cell;
        transform: rotate(-45deg);
        width: 36px;
        height: 36px;
        vertical-align: middle;
      }
      .offset_1 { padding-left: 16px; }
      .offset_2 { padding-left: 24px; }
      .offset_3 { padding-left: 32px; }
    `];
  }

  renderDevTrial(milestone) {
    if (!milestone) return nothing;
    return html`
      <div class="diamond dev_trial"
       title="First milestone with this feature available to developers"
      ><span>${milestone}</span></div>`;
  }

  renderOriginTrial(milestone) {
    if (!milestone) return nothing;
    return html`
      <div class="diamond origin_trial"
       title="First milestone with this feature enabled on specific origins"
      ><span>${milestone}</span></div>`;
  }

  renderShipping(milestone) {
    if (!milestone) return nothing;
    return html`
      <div class="diamond shipping"
       title="Milestone with this feature enabled by default"
      ><span>${milestone}</span></div>`;
  }

  renderRow(
    platform, devTrialMilestone, originTrialMilestone, shippingMilestone) {
    return html`
       <ul class="bar ${originTrialMilestone ? 'with-ot' : 'without-ot'}">
         <li class="platform">${platform}</li>
         <li>${this.renderDevTrial(devTrialMilestone)}</li>
         <li class="${originTrialMilestone == 92 ? 'offset_1' : nothing}">
           ${this.renderOriginTrial(originTrialMilestone)}
         </li>
         <li>${this.renderShipping(shippingMilestone)}</li>
       </ul>
    `;
  }

  render() {
    return html`
       <ul class="header">
         <li></li>
         <li>Dev Trial</li>
         <li>Origin Trial</li>
         <li>Shipping</li>
       </ul>
       ${this.renderRow('Desktop', 89, 91, 94)}
       ${this.renderRow('Android', 89, 92, 94)}
       ${this.renderRow('iOS', 89, null, null)}
       ${this.renderRow('Webview', null, null, 94)}
    `;
  }
}

customElements.define('chromedash-gantt', ChromedashGantt);
