// This file contains helper functions for our elements.

import {markupAutolinks} from './autolink.js';
import {nothing, html} from 'lit';

let toastEl;

/* Convert user-entered text into safe HTML with clickable links
 * where appropriate.  Returns an array with text and anchor tags.
 */
export function autolink(s) {
  const withLinks = markupAutolinks(s);
  return withLinks;
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

/* Return val, or one of the bounds if val is out of the bounds. */
export function clamp(val, lowerBound, upperBound) {
  return Math.max(lowerBound, Math.min(upperBound, val));
}


/* Given a feature entry stage entity, look up the related process stage. */
export function findProcessStage(feStage, process) {
  for (const processStage of process.stages) {
    if (feStage.stage_type == processStage.stage_type) {
      return processStage;
    }
  }
  return null;
}

/* Given a process stage, find the first feature entry stage of the same type. */
export function findFirstFeatureStage(intentStage, currentStage, fe) {
  if (intentStage == currentStage.intent_stage) {
    return currentStage;
  }
  for (const feStage of fe.stages) {
    if (intentStage == feStage.intent_stage) {
      return feStage;
    }
  }
  return null;
}


/* Given a stage form definition, return a flat array of the fields associated with the stage. */
export function flattenSections(stage) {
  return stage.sections.reduce((combined, section) => [...combined, ...section.fields], []);
}

/* Set up scrolling to a hash url (e.g. #id_explainer_links). */
export function setupScrollToHash(pageElement) {
  const scrollToElement = (hash) => {
    if (hash) {
      const el = pageElement.shadowRoot.querySelector(hash);
      if (el) {
        // Find the form field element.
        const fieldRowSelector = `chromedash-form-field[name="${el.name}"] tr + tr`;
        const fieldRow = pageElement.shadowRoot.querySelector(fieldRowSelector);
        if (fieldRow) {
          if (el.input) {
            // el.focus() calls el.input.focus();
            el.focus();
          } else {
            // Not ready yet, so try after delay.  TODO: Avoid the timeout.
            setTimeout(() => {
              el.focus();
            }, 100);
          }
          fieldRow.scrollIntoView({
            block: 'center', behavior: 'smooth',
          });
        } else {
          el.scrollIntoView({
            behavior: 'smooth',
          });
        }
      }
    }
  };

  // Add global function to jump to form field.
  window.scrollToElement = (hash) => {
    scrollToElement(hash);
  };

  // Check now as well, used when first rendering a page.
  if (location.hash) {
    const hash = decodeURIComponent(location.hash);
    scrollToElement(hash);
  }
}

/* Returns a html template if the condition is true, otherwise returns an empty html */
export function renderHTMLIf(condition, originalHTML) {
  return condition ? originalHTML : nothing;
}


function _parseDateStr(dateStr) {
  // Format date to "YYYY-MM-DDTHH:mm:ss.sssZ" to represent UTC.
  dateStr = dateStr || '';
  dateStr = dateStr.replace(' ', 'T');
  const dateObj = new Date(`${dateStr}Z`);
  if (isNaN(dateObj)) {
    return null;
  }
  return dateObj;
}


export function renderAbsoluteDate(dateStr, includeTime=false) {
  if (!dateStr) {
    return '';
  }
  if (includeTime) {
    return dateStr.split('.')[0]; // Ignore microseconds.
  } else {
    return dateStr.split(' ')[0]; // Ignore time.
  }
}


export function renderRelativeDate(dateStr) {
  const dateObj = _parseDateStr(dateStr);
  if (!dateObj) return nothing;
  return html`
      <span class="relative_date">
        (<sl-relative-time date="${dateObj.toISOString()}">
         </sl-relative-time>)
      </span>`;
}
