import {LitElement, css, html, nothing} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';


class ChromedashBanner extends LitElement {
  static get properties() {
    return {
      timestamp: {type: Number},
      message: {type: String},
    };
  }

  constructor() {
    super();
    this.timestamp = null; // Unix timestamp: seconds since 1970-01-01.
    this.message = '';
  }

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
      div {
        display: inline-block;
        background: var(--warning-background);
        color: var(--warning-color);
        border-radius: var(--border-radius);
        padding: var(--content-padding);
        width:100%;
      }
    `];
  }

  computeLocalDateString() {
    if (!this.timestamp) {
      return nothing;
    }
    const date = new Date(this.timestamp * 1000);
    const formatOptions = {
      weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
      hour: 'numeric', minute: 'numeric'}; // No seconds
    return date.toLocaleString(undefined, formatOptions);
  }

  render() {
    if (!this.message) {
      return nothing;
    }

    return html`
      <div>
        ${this.message}
        ${this.computeLocalDateString()}
      </div>
    `;
  }
}

customElements.define('chromedash-banner', ChromedashBanner);
