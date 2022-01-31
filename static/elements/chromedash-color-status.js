import {LitElement, css, html} from 'lit';

import SHARED_STYLES from '../css/shared.css';

const CYAN = 120;
const DEFAULT_MAX = 7;

class ChromedashColorStatus extends LitElement {
  static get properties() {
    return {
      max: {type: Number},
      value: {type: Number},
    };
  }

  constructor() {
    super();
    this.max = DEFAULT_MAX;
  }

  static get styles() {
    return [
      SHARED_STYLES,
      css`
      span {
        background-color: rgb(255,0,0);
        border-radius: 50%;
        display: inline-block;
        height: 10px; /* Default. */
        width: 10px; /* Default. */
      }

      :host(.corner) {
        height: 100%;
      }
      :host(.corner) #status {
        border-radius: 0;
        height: 100%; /* Ensures we can color coverage when feature is scrolled.*/
        width: 4px;
      }

      :host(.bottom) {
        height: 8px;
        width: 100%;
        position: absolute;
        bottom: 0;
        left: 0;
      }
      :host(.bottom) #status {
        border-radius: 0;
        height: 100%;
        width: 100%;
      }
    `];
  }

  render() {
    const color = `hsl(${Math.round(CYAN - this.value * CYAN / this.max)}, 100%, 50%)`;
    return html`
      <span id="status" style="background-color: ${color}"></span>
    `;
  }
}

customElements.define('chromedash-color-status', ChromedashColorStatus);
