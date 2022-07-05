import {LitElement, html, css} from 'lit';

import {SHARED_STYLES} from '../sass/shared-css.js';

export class ChromedashFooter extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        footer {
          background: var(--page-background);
          box-shadow: 0 -2px 5px var(--shadow-color);
          display: flex;
          flex-direction: column;
          justify-content: center;
          text-align: center;
          align-items: center;
          margin-top: 2em;
          padding: var(--content-padding-half);
        }

        footer div > * + * {
          margin-left: var(--content-padding);
          padding-left: var(--content-padding);
        }

        @media only screen and (min-width: 601px) and (min-height: 601px) {
          footer {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
          }
        } 
    `];
  }

  render() {
    return html`
      <footer>
        <div>
          <a href="https://github.com/GoogleChrome/chromium-dashboard/wiki/"
            target="_blank" rel="noopener">Help</a>
          <a href="https://groups.google.com/a/chromium.org/forum/#!newtopic/blink-dev"
            target="_blank" rel="noopener">Discuss</a>
          <a href="https://github.com/GoogleChrome/chromium-dashboard/issues"
            target="_blank" rel="noopener">File an issue</a>
          <a href="https://policies.google.com/privacy"
            target="_blank" rel="noopener">Privacy</a>
        </div>
      </footer>
    `;
  }
}

customElements.define('chromedash-footer', ChromedashFooter);
