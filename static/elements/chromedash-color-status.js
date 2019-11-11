import {LitElement, html} from 'lit-element';

import style from '../css/elements/chromedash-color-status.css';

const CYAN = 120;
const DEFAULT_MAX = 7;

class ChromedashColorStatus extends LitElement {
  static styles = style;

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

  render() {
    const color = `hsl(${Math.round(CYAN - this.value * CYAN / this.max)}, 100%, 50%)`;
    return html`
      <span id="status" style="background-color: ${color}"></span>
    `;
  }
}

customElements.define('chromedash-color-status', ChromedashColorStatus);
