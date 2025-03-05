import {LitElement, css, html} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';
import {customElement, property} from 'lit/decorators.js';
import {Feature} from '../js-src/cs-client.js';
import {GateDict} from './chromedash-gate-chip.js';

@customElement('chromedash-review-status-icon')
class ChromedashReviewStatusIcon extends LitElement {
  @property({type: Object})
  feature!: Feature;

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        sl-button.approved::part(base) {
          background: var(--gate-approved-background);
          color: var(--gate-approved-color);
        }
        .approved sl-icon {
          color: var(--gate-approved-icon-color);
        }
      `,
    ];
  }

  handleClick() {
  }

  render() {
    const abbrev = 'Ok';
    const className = 'approved';
    let statusIcon = html`<b class="abbrev" slot="prefix">${abbrev}</b>`;

    return html`
      <sl-button
        pill
        size="small"
        class="${className}"
        title="Longer @@@"
        @click=${this.handleClick}
      >
        ${statusIcon}
      </sl-button>
    `;
  }
}
