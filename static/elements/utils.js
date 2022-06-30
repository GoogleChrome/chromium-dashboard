// This file contains helper functions for our elements.

import {html} from 'lit';
import {unsafeHTML} from 'lit/directives/unsafe-html.js';
import Autolinker from 'autolinker';

let toastEl; let approvalDialogEl;

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
  if (!toastEl) toastEl = document.querySelector('chromedash-toast');
  toastEl.showMessage(msg);
}

export function openApprovalsDialog(featureId) {
  if (!approvalDialogEl) approvalDialogEl = document.querySelector('chromedash-approvals-dialog');
  approvalDialogEl.openWithFeature(featureId);
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
