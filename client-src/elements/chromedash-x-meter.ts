import {LitElement, css, html} from 'lit';
import {customElement, property} from 'lit/decorators.js';
import {SHARED_STYLES} from '../css/shared-css.js';

@customElement('chromedash-x-meter')
class ChromedashXMeter extends LitElement {
  @property({type: Number})
  value = 0;
  @property({type: Number})
  max = 100;
  @property({type: String})
  href = '#';

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        :host {
          display: grid;
          grid-template-columns: 65px 1fr;
          grid-column-gap: 15px;
          height: 1.6em;
          font-size: 14px;
        }

        #percentage-number {
          place-self: center;
        }

        #track {
          background: var(--barchart-background);
          border-radius: var(--border-radius);
          overflow: hidden;
          height: 100%;
        }

        #indicator {
          background: var(--barchart-foreground);
          height: 100%;
          white-space: nowrap;
          padding: 3px 0;
        }
      `,
    ];
  }

  render() {
    return html`
      <p id="percentage-number">
        ${this.value < 0.0001 ? '<0.0001%' : this.value.toFixed(4) + '%'}
      </p>
      <a href="${this.href}">
        <div id="track">
          <div
            id="indicator"
            style="width: ${(this.value / this.max) * 100}%"
          ></div>
        </div>
      </a>
    `;
  }
}
