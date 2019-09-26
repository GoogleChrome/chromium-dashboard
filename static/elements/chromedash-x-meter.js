import {LitElement, html} from 'lit-element';
import style from '../css/elements/chromedash-x-meter.css';

class ChromedashXMeter extends LitElement {
  static styles = style;

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
      <div style="width: ${(this.value / this.max * 100)}%">  
        <span>${this.valueFormatted}</span> 
      </div>  
    `;
  }
}

customElements.define('chromedash-x-meter', ChromedashXMeter);
