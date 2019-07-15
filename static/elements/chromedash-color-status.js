import {LitElement, html} from 'lit-element';

const CYAN = 120;
const DEFAULT_MAX = 7;

class ChromedashColorStatus extends LitElement {
  static get properties() {
    return {
      max: {type: Number}, // From attribute
      value: {type: Number}, // From attribute
    };
  }

  constructor() {
    super();
    this.max = DEFAULT_MAX;
  }

  render() {
    const color = `hsl(${Math.round(CYAN - this.value * CYAN / this.max)}, 100%, 50%)`;
    return html`
      <link rel="stylesheet" href="/static/css/elements/chromedash-color-status.css">

      <span id="status" style="background-color: ${color}"></span>
    `;
  }
}

customElements.define('chromedash-color-status', ChromedashColorStatus);
