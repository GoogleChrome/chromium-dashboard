// @ts-check

import {LitElement, html} from 'lit';

/**
 * Use like `<chromedash-vendor-views href="https://evidence/for/the/view"
 * .featureLinks=${this.featureLinks}>Text description of the view</chromedash-vendor-views>`
 */
export class ChromedashVendorViews extends LitElement {
  static get properties() {
    return {
      href: {type: String},
      featureLinks: {attribute: false},
    };
  }

  constructor() {
    super();
    /** URL of the evidence for this view.
     * @type {string|undefined} */
    this.href = undefined;
    /** @type {import("../js-src/cs-client").FeatureLink[]} */
    this.featureLinks = [];
  }

  /**
   * @param {string} url
   * @returns {boolean}
   */
  urlIsStandardsPosition(url) {
    return /github.com\/(mozilla|WebKit)\/standards-positions\/issues/.test(
      url
    );
  }

  render() {
    if (this.href) {
      return html`<chromedash-link
        href=${this.href}
        ?showContentAsLabel=${!this.urlIsStandardsPosition(this.href)}
        .featureLinks=${this.featureLinks}
        ><slot></slot
      ></chromedash-link>`;
    } else {
      return html`<slot></slot>`;
    }
  }
}

customElements.define('chromedash-vendor-views', ChromedashVendorViews);
