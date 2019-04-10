import { LitElement, html } from 'lit-element';

class ChromedashColorStatus extends LitElement {
  static get properties() {
    return {
      max: {
        type: Number,
      },
      value: {
        type: Number,
      }
    };
  }

  constructor() {
    super();
    this.max = 7;
  }

  render() {
    return html`
      <link rel="stylesheet" href="/static/css/elements/chromedash-color-status.css">
      <span id="status" style="background-color: ${this._getColor()}"></span>
    `;
  }

  _getColor() {
    const cyan = 120;
    const hue = Math.round(cyan - this.value * cyan / this.max);
    return `hsl(${hue}, 100%, 50%)`;
  }
}

customElements.define('chromedash-color-status', ChromedashColorStatus);
