import {LitElement, html} from 'https://unpkg.com/@polymer/lit-element@latest/lit-element.js?module';

class ChromedashXMeter extends LitElement {
  static get properties() {
    return {
      value: {type: Number},
      valueFormatted: {type: Number},
      max: {type: Number}, // Normalized, maximum width for the bar
    };
  }

  get valueFormatted() {
    return this.valueFormatted_;
  }

  set valueFormatted(value) {
    this.valueFormatted_ = value <= 0.000001 ? '<=0.000001%' : value + '%';
  }

  constructor() {
    super();
    this.value = 0;
    this.max = 100;
  }

  render() {
    return html`
      <link rel="stylesheet" href="/static/css/chromedash-x-meter.css">

      <div class="meter" id="meter">
        <div style="width: ${(this.value / this.max * 100)}%">
          <span>${this.valueFormatted}</span>
        </div>
      </div>
    `;
  }
}

customElements.define('chromedash-x-meter', ChromedashXMeter);
