// This file contains helper functions for our elements.

import {markupAutolinks} from './autolink.js';
import {nothing, html} from 'lit';
import {STAGE_FIELD_NAME_MAPPING} from './form-field-enums';

let toastEl;
// Determines if it is a mobile device.
export const IS_MOBILE = window.screen.width < 701;

/* Convert user-entered text into safe HTML with clickable links
 * where appropriate.  Returns an array with text and anchor tags.
 */
export function autolink(s, featureLinks = []) {
  const withLinks = markupAutolinks(s, featureLinks);
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

/* Determine if the display name field should be displayed for a stage. */
export function shouldShowDisplayNameField(feStages, stageType) {
  // The display name field is only available to a feature's stages
  // that have more than 1 of the same stage type associated.
  // It is used to differentiate those stages.
  let matchingStageCount = 0;
  for (let i = 0; i < feStages.length; i++) {
    if (feStages[i].stage_type === stageType) {
      matchingStageCount++;
      // If we find two of the same stage type, then display the display name field.
      if (matchingStageCount > 1) {
        return true;
      }
    }
  }
  return false;
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

/* Get the value of a stage field using a form-specific name */
export function getStageValue(stage, fieldName) {
  if (fieldName in STAGE_FIELD_NAME_MAPPING) {
    return stage[STAGE_FIELD_NAME_MAPPING[fieldName]];
  }
  return stage[fieldName];
}

/* Given a stage form definition, return a flat array of the fields associated with the stage. */
export function flattenSections(stage) {
  return stage.sections.reduce((combined, section) => [...combined, ...section.fields], []);
}

/* Set up scrolling to a hash url (e.g. #id_explainer_links). */
export function setupScrollToHash(pageElement) {
  // Scroll to the element identified by the hash parameter, which must include
  // the '#' prefix.  E.g. for a form field: '#id_<form-field-name>'.
  // Note that this function is bound to the pageElement for a page.
  const scrollToElement = (hash) => {
    if (hash) {
      const el = pageElement.shadowRoot.querySelector(hash);
      if (el) {
        // Focus on the element, if possible.
        // Note: focus() must be called before scrollToView().
        if (el.input) {
          // Note: shoelace element.focus() calls el.input.focus();
          el.focus();
        } else {
          // No el.input (yet), so try after delay.  TODO: Avoid the timeout.
          setTimeout(() => {
            el.focus();
          }, 100);
        }

        // Find the form field container element, if any.
        const fieldRowSelector = `chromedash-form-field[name="${el.name}"] tr + tr`;
        const fieldRow = pageElement.shadowRoot.querySelector(fieldRowSelector);
        if (fieldRow) {
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

  // Add global function to jump to an element within the pageElement.
  window.scrollToElement = (hash) => {
    scrollToElement(hash);
  };

  // Check now as well, which is used when first rendering a page.
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


/**
 * Parses URL query strings into a dict.
 * @param {string} rawQuery a raw URL query string, e.g. q=abc&num=1;
 * @return {Object} A key-value pair dictionary for the query string.
 */
export function parseRawQuery(rawQuery) {
  const params = new URLSearchParams(rawQuery);
  const result = {};
  for (const param of params.keys()) {
    const values = params.getAll(param);
    if (!values.length) {
      continue;
    }
    // Assume there is only one value.
    result[param] = values[0];
  }
  return result;
}


/**
 * Create a new URL using params and a location.
 * @param {string} params is the new param object.
 * @param {Object} location is an URL location.
 * @return {Object} the new URL.
 */
export function getNewLocation(params, location) {
  const url = new URL(location);
  url.search = '';
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      // Skip if the value is empty.
      if (!v) {
        continue;
      }
      url.searchParams.append(k, v);
    }
  }
  return url;
}


/**
 * Update window.location with new query params.
 * @param {string} key is the key of the query param.
 * @param {string} val is the unencoded value of the query param.
 */
export function updateURLParams(key, val) {
  // Update the query param object.
  const rawQuery = parseRawQuery(window.location.search);
  rawQuery[key] = encodeURIComponent(val);

  // Assemble the new URL.
  const newURL = getNewLocation(rawQuery, window.location);
  newURL.hash = '';
  if (newURL.toString() === window.location.toString()) {
    return;
  }
  // Update URL without refreshing the page. {path:} is needed for
  // an issue in page.js:
  // https://github.com/visionmedia/page.js/issues/293#issuecomment-456906679
  window.history.pushState({path: newURL.toString()}, '', newURL);
}

/**
 * Update window.location with new query params.
 * @param {string} key is the key of the query param to delete.
 */
export function clearURLParams(key) {
  // Update the query param object.
  const rawQuery = parseRawQuery(window.location.search);
  delete rawQuery[key];

  // Assemble the new URL.
  const newURL = getNewLocation(rawQuery, window.location);
  newURL.hash = '';
  if (newURL.toString() === window.location.toString()) {
    return;
  }
  // Update URL without refreshing the page. {path:} is needed for
  // an issue in page.js:
  // https://github.com/visionmedia/page.js/issues/293#issuecomment-456906679
  window.history.pushState({path: newURL.toString()}, '', newURL);
}

/**
 * @typedef {Object} FieldInfo
 * @property {string} name The name of the field.
 * @property {boolean} touched Whether the field was mutated by the user.
 * @property {number} stageId The stage that the field is associated with.
 *   This field is undefined if the change is a feature change.
 * @property {*} value The value written in the form field.
 * @property {*} implicitValue Value that should be changed for some checkbox fields.
 *   e.g. "set_stage" is a checkbox, but should change the field to a stage ID if true.
 */

/**
 * @typedef {Object} UpdateSubmitBody
 * @property {Object.<string, *>} feature_changes An object with feature changes.
 *   key=field name, value=new field value.
 * @property {Array.<Object>} stages The list of changes to specific stages.
 * @property {boolean} has_changes Whether any valid changes are present for submission.
 */

/**
 * Prepare feature/stage changes to be submitted.
 * @param {Array.<FieldInfo>} fieldValues List of fields in the form.
 * @param {number} featureId The ID of the feature being updated.
 * @return {UpdateSubmitBody} Formatted body of new PATCH request.
 */
export function formatFeatureChanges(fieldValues, featureId) {
  let hasChanges = false;
  const featureChanges = {id: featureId};
  // Multiple stages can be mutated, so this object is a stage of stages.
  const stages = {};
  for (const {name, touched, value, stageId, implicitValue} of fieldValues) {
    // Only submit changes for touched fields.
    if (!touched) {
      continue;
    }

    // If an explicit value is present, the field value should be truthy.
    // Otherwise, we ignore the change.
    // For example, if this is a checkbox to set the active stage, it would need
    // to be set to true (value), then the active stage would be set to a stage ID (implicitValue).
    if (implicitValue !== undefined) {
      // Falsey value with an implicit value should be ignored (like an unchecked checkbox).
      if (!value) {
        continue;
      }
      // fields with implicit values are always changes to feature entities.
      featureChanges[name] = implicitValue;
    } else if (!stageId) {
      // If the field doesn't specify a stage ID, that means this change is for a feature field.
      featureChanges[name] = value;
    } else {
      if (!(stageId in stages)) {
        stages[stageId] = {id: stageId};
      }
      stages[stageId][STAGE_FIELD_NAME_MAPPING[name] || name] = {
        form_field_name: name,
        value,
      };
    }
    // If we see a touched field, it means there are changes in the submission.
    hasChanges = true;
  }

  return {
    feature_changes: featureChanges,
    stages: Object.values(stages),
    has_changes: hasChanges,
  };
}

/**
 * Manage response to change submission.
 * Required to manage beforeUnload handler.
 * @param {string} response The error message to display,
 *     or empty string if save was successful.
 */
export function handleSaveChangesResponse(response) {
  const app = document.querySelector('chromedash-app');
  app.setUnsavedChanges(response !== '');
}
