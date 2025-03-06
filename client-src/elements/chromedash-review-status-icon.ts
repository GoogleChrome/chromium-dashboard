import {LitElement, css, html} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';
import {customElement, property} from 'lit/decorators.js';
import {Feature} from '../js-src/cs-client.js';
import {GateDict} from './chromedash-gate-chip.js';




@customElement('chromedash-review-status-icon')
class ChromedashReviewStatusIcon extends LitElement {
  @property({type: Object})
  feature!: Feature;

  @property({type: Number})
  version!: number;

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
      sl-icon {
      width: 26px;
      height: 18px;
      }
        sl-icon.approved  {
          color: var(--gate-approved-icon-color);
        }
      `,
    ];
  }

  render() {
    let className = 'approved';
    let iconName  = 'check_circle_20px';
    let hoverText = 'Reviews: Approved';
    return html`
    <sl-icon library="material" title="${hoverText}" class="${className}" name="${iconName}"></sl-icon>
    `;
  }
}
