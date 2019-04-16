import {LitElement, html} from 'https://unpkg.com/@polymer/lit-element@latest/lit-element.js?module';

const CYAN = 120;

class ChromedashColorStatus extends LitElement {
  static get properties() {
    return {
      max: {
        type: Number,
      },
      value: {
        type: Number,
      },
    };
  }

  constructor() {
    super();
    this.max = 7;
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
