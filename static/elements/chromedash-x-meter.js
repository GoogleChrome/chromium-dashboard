import {LitElement, css, html} from 'lit';
import {SHARED_STYLES} from '../sass/shared-css.js';

class ChromedashXMeter extends LitElement {
  static get properties() {
    return {
      value: {type: Number},
      max: {type: Number}, // Normalized, maximum width for the bar
      href: {type: String},
    };
  }

  constructor() {
    super();
    this.value = 0;
    this.max = 100;
  }

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
    `];
  }

  render() {
    return html`
      <p id="percentage-number">${this.value < 0.0001 ? '<0.0001%' : this.value.toFixed(4) + '%'}</p>
      <div id="track">
        <div id="indicator" style="width: ${(this.value / this.max * 100)}%"></div>
      </div>
    `;
  }
}

customElements.define('chromedash-x-meter', ChromedashXMeter);
