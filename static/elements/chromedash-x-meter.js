import {LitElement, css, html} from 'lit';
import {SHARED_STYLES} from '../sass/shared-css.js';

class ChromedashXMeter extends LitElement {
  static get properties() {
    return {
      value: {type: Number},
      max: {type: Number}, // Normalized, maximum width for the bar
      href: {type: String},
      name: {type: String},
    };
  }

  constructor() {
    super();
    this.value = 0;
    this.max = 100;
    this.href = '#';
    this.name = '';
  }

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
      :host {
        display: grid;
        grid-template-columns: 65px 1fr;
        grid-column-gap: 15px;
        height: 1.6em;
        font-size: 14px;
      }

      #percentage-number {
        place-self: center;
      }

      #track {
        background: var(--barchart-background);
        border-radius: var(--border-radius);
        overflow: hidden;
        height: 100%;
      }

      #indicator {
        background: var(--barchart-foreground);
        height: 100%;
        white-space: nowrap;
        padding: 3px 0;
      }

      .stack-rank-item-name {
        grid-column-gap: 5px;
      }

      .stack-rank-item-result {
        margin-right: 5px;
        flex: 1;
      }

      .stack-rank-item-name {
        display: grid;
        grid-template-columns: var(--icon-size) 1fr;
        grid-column-gap: 15px;
        position: relative;
        left: -20px;
      }

      .stack-rank-item-name .hash-link {
        place-self: center;
        visibility: hidden;
      }

      .stack-rank-item-name:hover .hash-link {
        visibility: visible;
      }

      .stack-rank-item {
        border-top: var(--table-divider)
      }

      a.icon-wrapper {
        display: flex;
        gap: 3px;
        align-items: center;
      }

      a.icon-wrapper:hover {
        text-decoration: none;
      }
    `];
  }

  scrollToPosition(e) {
    let hash;
    if (e) {
      hash = e.currentTarget.getAttribute('href');
    } else if (location.hash) {
      hash = decodeURIComponent(location.hash);
    }

    if (hash) {
      const el = this.shadowRoot.querySelector('.stack-rank-item ' + hash);
      el.scrollIntoView(true, {behavior: 'smooth'});
    }
  }

  render() {
    return html`
      <li class="stack-rank-item" id="${this.name}">
        <div title="${this.name}. Click to deep link to this property.">
          <a class="stack-rank-item-name" href="#${this.name}" @click=${this.scrollToPosition}>
            <iron-icon class="hash-link" icon="chromestatus:link"></iron-icon>
            <p>${this.name}</p>
          </a>
        </div>
        <div class="stack-rank-item-result">
          <p id="percentage-number">${this.value < 0.0001 ? '<0.0001%' : this.value.toFixed(4) + '%'}</p>
          <a href="${this.href}">
            <div id="track">
              <div id="indicator" style="width: ${(this.value / this.max * 100)}%"></div>
            </div>
          </a>
          <a class="icon-wrapper"
            href="${this.href}"
            title="Click to see a timeline view of this property">
            <iron-icon icon="chromestatus:timeline"></iron-icon>
            <p class="icon-text">Timeline</p>
          </a>
        </div>
      </li>
    `;
  }
}

customElements.define('chromedash-x-meter', ChromedashXMeter);
