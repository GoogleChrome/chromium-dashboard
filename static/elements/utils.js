// This file contains helper functions for our elements.

import {html} from 'lit';
import {unsafeHTML} from 'lit/directives/unsafe-html.js';
import Autolinker from 'autolinker';

const toastEl = document.querySelector('chromedash-toast');

/* Convert user-entered text into safe HTML with clickable links
 * where appropriate.  Returns a lit-html TemplateResult.
 */
// TODO(jrobbins): autolink monorail-style issue references, go-links, etc.
export function autolink(s) {
  const markup = Autolinker.link(
    s,
    {stripPrefix: false, sanitizeHtml: true});
  return html`${unsafeHTML(markup)}`;
}

export function showToastMessage(msg) {
  toastEl.showMessage(msg);
}
