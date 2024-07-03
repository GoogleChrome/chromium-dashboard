// @ts-check

import {LitElement, html} from 'lit';
import {customElement, property} from 'lit/decorators.js';
import {FeatureLink} from '../js-src/cs-client';

/**
 * Use like `<chromedash-vendor-views href="https://evidence/for/the/view"
 * .featureLinks=${this.featureLinks}>Text description of the view</chromedash-vendor-views>`
 */
@customElement('chromedash-vendor-views')
export class ChromedashVendorViews extends LitElement {
  /** URL of the evidence for this view.*/
  @property({type: String})
  href;
  @property({attribute: false})
  featureLinks: FeatureLink[] = [];

  urlIsStandardsPosition(url: string): boolean {
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
