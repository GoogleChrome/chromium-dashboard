// This file contains helper functions for our elements.

import {markupAutolinks} from './autolink.js';

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
