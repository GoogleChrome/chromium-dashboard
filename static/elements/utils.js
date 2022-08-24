// This file contains helper functions for our elements.

import {html} from 'lit';
import {markupAutolinks} from 'autolink.js';
import {unsafeHTML} from 'lit/directives/unsafe-html.js';

let toastEl;

/* Convert user-entered text into safe HTML with clickable links
 * where appropriate.  Returns a lit-html TemplateResult.
 */
export function autolink(s) {
  const markup = markupAutolinks(s);
  return html`${unsafeHTML(markup)}`;
}

export function showToastMessage(msg) {
  if (!toastEl) toastEl = document.querySelector('chromedash-toast');
  toastEl.showMessage(msg);
}

/**
 * Returns the rendered elements of the named slot of component.
 * @param {Element} component
 * @param {string} slotName
 * @return {Element}
 */
export function slotAssignedElements(component, slotName) {
  const slotSelector = slotName ? `slot[name=${slotName}]` : 'slot';
  return component.shadowRoot.querySelector(slotSelector).assignedElements({flatten: true});
}
