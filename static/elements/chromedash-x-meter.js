import {LitElement, css, html} from 'lit-element';
import SHARED_STYLES from '../css/shared.css';

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
    this.href = '#';
  }

  static get styles() {
    return [
      SHARED_STYLES,
      css`
      :host {
        display: inline-block;
        contain: content;
        background: var(--barchart-background);
        border-radius: var(--border-radius);
        overflow: hidden;
        height: 1.7em;
        color: var(--barchart-color);
      }

      div {
        background: var(--barchart-foreground);
        height: 100%;
        white-space: nowrap;
        padding: 3px 0;
        text-indent: 5px;
      }
    `];
  }

  showTimeline() {
    window.location.href = this.href;
  }

  render() {
    return html`  
      <div @click="${this.showTimeline}" style="width: ${(this.value / this.max * 100)}%">  
        <span>${this.value <= 0.000001 ? '<=0.000001%' : this.value + '%'}
        </span> 
      </div>  
    `;
  }
}

customElements.define('chromedash-x-meter', ChromedashXMeter);
