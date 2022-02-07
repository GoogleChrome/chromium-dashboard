// This file contains helper functions for our elements.

import {html} from 'lit';
import {unsafeHTML} from 'lit/directives/unsafe-html.js';

/* Convert user-entered text into safe HTML with clickable links
 * where appropriate.  Returns a lit-html TemplateResult.
 */
// TODO(jrobbins): autolink monorail-style issue references, go-links, etc.
export function autolink(s) {
  const markup = urlize(
    s,
    {target: '_blank', trim: 'www', autoescape: true});
  return html`${unsafeHTML(markup)}`;
}
