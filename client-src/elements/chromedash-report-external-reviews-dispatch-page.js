// @ts-check
import {LitElement, html} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';

export class ChromedashReportExternalReviewsDispatchPage extends LitElement {
  static get styles() {
    return SHARED_STYLES;
  }

  render() {
    return html`
      <div id="subheader">Which group's reviews do you want to see?</div>
      <ul>
        <li><a href="/reports/external_reviews/tag">W3C TAG</a></li>
        <li>
          <a href="/reports/external_reviews/gecko"
            >Gecko / Firefox / Mozilla</a
          >
        </li>
        <li>
          <a href="/reports/external_reviews/webkit">WebKit / Safari / Apple</a>
        </li>
      </ul>
    `;
  }
}

customElements.define(
  'chromedash-report-external-reviews-dispatch-page',
  ChromedashReportExternalReviewsDispatchPage
);
