import {LitElement, html} from 'lit-element';

class ChromedashXMeter extends LitElement {
  static get properties() {
    return {
      value: {type: Number},
      max: {type: Number}, // Normalized, maximum width for the bar
      valueFormatted: {attribute: false},
    };
  }

  constructor() {
    super();
    this.value = 0;
    this.max = 100;
  }

  firstUpdated() {
    this.valueFormatted = this.value <= 0.000001 ? '<=0.000001%' : this.value + '%';
  }

  render() {
    return html`  
      <link rel="stylesheet" href="/static/css/elements/chromedash-x-meter.css"> 
      
      <div style="width: ${(this.value / this.max * 100)}%">  
        <span>${this.valueFormatted}</span> 
      </div>  
    `;
  }
}

customElements.define('chromedash-x-meter', ChromedashXMeter);
