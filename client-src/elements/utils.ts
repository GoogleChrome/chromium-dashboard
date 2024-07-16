// This file contains helper functions for our elements.

import {html, nothing} from 'lit';
import {Feature, FeatureLink, StageDict} from '../js-src/cs-client.js';
import {markupAutolinks} from './autolink.js';
import {FORMS_BY_STAGE_TYPE, FormattedFeature} from './form-definition.js';
import {
  ENTERPRISE_FEATURE_CATEGORIES_DISPLAYNAME,
  ENTERPRISE_IMPACT_DISPLAYNAME,
  OT_MILESTONE_END_FIELDS,
  PLATFORMS_DISPLAYNAME,
  ROLLOUT_IMPACT_DISPLAYNAME,
  STAGE_FIELD_NAME_MAPPING,
  STAGE_SPECIFIC_FIELDS,
} from './form-field-enums';

let toastEl;

// Determine if the browser looks like the user is on a mobile device.
// We assume that a small enough window width implies a mobile device.
const NARROW_WINDOW_MAX_WIDTH = 700;

export const IS_MOBILE = (() => {
  const width =
    window.innerWidth ||
    document.documentElement.clientWidth ||
    document.body.clientWidth;
  return width <= NARROW_WINDOW_MAX_WIDTH;
})();

/* Convert user-entered text into safe HTML with clickable links
 * where appropriate.  Returns an array with text and anchor tags.
 */
export function autolink(s, featureLinks: FeatureLink[] = []) {
  const withLinks = markupAutolinks(s, featureLinks);
  return withLinks;
}

export function showToastMessage(msg) {
  if (!toastEl) toastEl = document.querySelector('chromedash-toast');
  if (toastEl?.showMessage) {
    toastEl.showMessage(msg);
  }
}

/**
 * Returns the rendered elements of the named slot of component.
 * @param {Element} component
 * @param {string} slotName
 * @return {Element}
 */
export function slotAssignedElements(component, slotName) {
  const slotSelector = slotName ? `slot[name=${slotName}]` : 'slot';
  return component.shadowRoot
    .querySelector(slotSelector)
    .assignedElements({flatten: true});
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

/**
 * Returns `stage`'s name, using either its `display_name` or a counter to disambiguate from other
 * stages of the same type within `feature`.
 */
export function unambiguousStageName(
  stage: StageDict,
  feature: Feature | FormattedFeature
): string | undefined {
  const processStageName = FORMS_BY_STAGE_TYPE[stage.stage_type]?.name;
  if (!processStageName) {
    console.error(
      `Unexpected stage type ${stage.stage_type} in stage ${stage.id}.`
    );
    return undefined;
  }
  if (stage.display_name) {
    return `${processStageName}: ${stage.display_name}`;
  }

  // Count the stages of the same type that appear before this one. This is O(n^2) when it's used to
  // number every stage, but the total number of stages is generally <20.
  const index = feature.stages
    .filter(s => s.stage_type === stage.stage_type)
    .findIndex(s => s.id === stage.id);
  if (index > 0) {
    return `${processStageName} ${index + 1}`;
  }
  // Ignore if the stage wasn't found.
  return processStageName;
}

/* Get the value of a stage field using a form-specific name */
export function getStageValue(stage, fieldName) {
  if (!stage) return undefined;
  if (fieldName in STAGE_FIELD_NAME_MAPPING) {
    return stage[STAGE_FIELD_NAME_MAPPING[fieldName]];
  }
  return stage[fieldName];
}

// Look at all extension milestones and calculate the highest milestone that an origin trial
// is available. This is used to display the highest milestone available, but to preserve the
// milestone that the trial was originally available for without extensions.
function calcMaxMilestone(feStage, fieldName) {
  // If the max milestone has already been calculated, or no trial extensions exist, do nothing.
  if (!feStage) return;
  if (feStage[`max_${fieldName}`] || !feStage.extensions) {
    return;
  }
  let maxMilestone = getStageValue(feStage, fieldName) || 0;
  for (const extension of feStage.extensions) {
    const extensionValue = getStageValue(extension, fieldName);
    if (extensionValue) {
      maxMilestone = Math.max(maxMilestone, extensionValue);
    }
  }
  // Save the findings with the "max_" prefix as a prop of the stage for reference.
  feStage[`max_${fieldName}`] = maxMilestone;
}

// Get the milestone value that is displayed to the user regarding the origin trial end date.
function getMilestoneExtensionValue(feStage, fieldName) {
  if (!feStage) return undefined;
  const milestoneValue = getStageValue(feStage, fieldName);
  calcMaxMilestone(feStage, fieldName);

  const maxMilestoneFieldName = `max_${fieldName}`;
  // Display only extension milestone if the original milestone has not been added.
  if (feStage[maxMilestoneFieldName] && !milestoneValue) {
    return `Extended to ${feStage[maxMilestoneFieldName]}`;
  }
  // If the trial has been extended past the original milestone, display the extension
  // milestone with additional text reminding of the original milestone end date.
  if (
    feStage[maxMilestoneFieldName] &&
    feStage[maxMilestoneFieldName] > milestoneValue
  ) {
    return `${feStage[maxMilestoneFieldName]} (extended from ${milestoneValue})`;
  }
  return milestoneValue;
}

/**
 * Check if a value is defined and not empty.
 *
 * @param {any} value - The value to be checked.
 * @return {boolean} Returns true if the value is defined and not empty, otherwise false.
 */
export function isDefinedValue(value) {
  return !(value === undefined || value === null || value.length == 0);
}

export function hasFieldValue(fieldName, feStage, feature) {
  const value = getFieldValueFromFeature(fieldName, feStage, feature);
  return isDefinedValue(value);
}

/**
 * Retrieves the value of a specific field for a given feature.
 * Note: This is independent of any value that might be in a corresponding
 * form field.
 *
 * @param fieldName - The name of the field to retrieve.
 * @param feStage - The stage of the feature.
 * @param feature - The feature object to retrieve the field value from.
 * @return The value of the specified field for the given feature.
 */
export function getFieldValueFromFeature(
  fieldName: string,
  feStage: StageDict,
  feature: Feature
) {
  if (STAGE_SPECIFIC_FIELDS.has(fieldName)) {
    const value = getStageValue(feStage, fieldName);
    if (fieldName === 'rollout_impact' && value) {
      return ROLLOUT_IMPACT_DISPLAYNAME[value];
    }
    if (fieldName === 'rollout_platforms' && value) {
      return value.map(platformId => PLATFORMS_DISPLAYNAME[platformId]);
    } else if (fieldName in OT_MILESTONE_END_FIELDS) {
      // If an origin trial end date is being displayed, handle extension milestones as well.
      return getMilestoneExtensionValue(feStage, fieldName);
    }
    return value;
  }

  if (!feature) {
    return null;
  }

  const fieldNameMapping = {
    owner: 'browsers.chrome.owners',
    editors: 'editors',
    search_tags: 'tags',
    spec_link: 'standards.spec',
    standard_maturity: 'standards.maturity.text',
    sample_links: 'resources.samples',
    docs_links: 'resources.docs',
    bug_url: 'browsers.chrome.bug',
    blink_components: 'browsers.chrome.blink_components',
    devrel: 'browsers.chrome.devrel',
    prefixed: 'browsers.chrome.prefixed',
    impl_status_chrome: 'browsers.chrome.status.text',
    shipped_milestone: 'browsers.chrome.desktop',
    shipped_android_milestone: 'browsers.chrome.android',
    shipped_webview_milestone: 'browsers.chrome.webview',
    shipped_ios_milestone: 'browsers.chrome.ios',
    ff_views: 'browsers.ff.view.text',
    ff_views_link: 'browsers.ff.view.url',
    ff_views_notes: 'browsers.ff.view.notes',
    safari_views: 'browsers.safari.view.text',
    safari_views_link: 'browsers.safari.view.url',
    safari_views_notes: 'browsers.safari.view.notes',
    web_dev_views: 'browsers.webdev.view.text',
    web_dev_views_link: 'browsers.webdev.view.url',
    web_dev_views_notes: 'browsers.webdev.view.notes',
    other_views_notes: 'browsers.other.view.notes',
  };
  let value;
  if (fieldNameMapping[fieldName]) {
    let propertyValue = feature;
    for (const step of fieldNameMapping[fieldName].split('.')) {
      if (propertyValue) {
        propertyValue = propertyValue[step];
      }
    }
    value = propertyValue;
  } else {
    value = feature[fieldName];
  }

  if (fieldName === 'enterprise_feature_categories' && value) {
    return value.map(
      categoryId => ENTERPRISE_FEATURE_CATEGORIES_DISPLAYNAME[categoryId]
    );
  }
  if (fieldName === 'enterprise_impact' && value) {
    return ENTERPRISE_IMPACT_DISPLAYNAME[value];
  }
  if (fieldName === 'active_stage_id' && value) {
    for (const stage of feature.stages) {
      if (stage.id === value) {
        return unambiguousStageName(stage, feature);
      }
    }
    return undefined;
  }
  return value;
}

/* Given a stage form definition, return a flat array of the fields associated with the stage. */
export function flattenSections(stage) {
  return stage.sections.reduce(
    (combined, section) => [...combined, ...section.fields],
    []
  );
}

/* Set up scrolling to a hash url (e.g. #id_explainer_links). */
export function setupScrollToHash(pageElement) {
  // Scroll to the element identified by the hash parameter, which must include
  // the '#' prefix.  E.g. for a form field: '#id_<form-field-name>'.
  // Note that this function is bound to the pageElement for a page.
  const scrollToElement = hash => {
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
            block: 'center',
            behavior: 'smooth',
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
  window.scrollToElement = hash => {
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
  if (isNaN(Number(dateObj))) {
    return null;
  }
  return dateObj;
}

export function renderAbsoluteDate(dateStr, includeTime = false) {
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
  return html` <span class="relative_date">
    (<sl-relative-time date="${dateObj.toISOString()}"> </sl-relative-time>)
  </span>`;
}

/** Returns the non-time part of date in the YYYY-MM-DD format.
 *
 * @param {Date} date
 * @return {string}
 */
export function isoDateString(date) {
  return date.toISOString().slice(0, 10);
}

export interface RawQuery {
  q?: string;
  columns?: string;
  showEnterprise?: string;
  sort?: string;
  start?: string;
  after?: string;
  num?: string;
  [key: string]: string | undefined;
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
      url.searchParams.append(k, v.toString());
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

export interface FieldInfo {
  /** The name of the field. */
  name: string | keyof FormattedFeature;
  /** Whether the field was mutated by the user. */
  touched: boolean;
  /**
   * The stage that the field is associated with.
   * This field is undefined if the change is a feature change.
   */
  stageId?: number | null;
  /** The value written in the form field. */
  value: any;
  /**
   * Value that should be changed for some checkbox fields.
   * e.g. "set_stage" is a checkbox, but should change the field to a stage ID if true.
   */
  implicitValue?: any;
  alwaysHidden?: boolean;
  isApprovalsField?: boolean;
  checkMessage?: string;
}

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
    // Only submit changes for touched fields or accuracy verification updates.
    if (!touched) {
      continue;
    }

    // Arrays should be submitted as comma-separated strings.
    let formattedValue = value;
    if (Array.isArray(formattedValue)) {
      formattedValue = formattedValue.join(',');
    }

    // If an explicit value is present, the field value should be truthy.
    // Otherwise, we ignore the change.
    // For example, if this is a checkbox to set the active stage, it would need
    // to be set to true (value), then the active stage would be set to a stage ID (implicitValue).
    if (implicitValue !== undefined) {
      // Falsey value with an implicit value should be ignored (like an unchecked checkbox).
      if (!formattedValue) {
        continue;
      }
      // fields with implicit values are always changes to feature entities.
      featureChanges[name] = implicitValue;
    } else if (!stageId) {
      // If the field doesn't specify a stage ID, that means this change is for a feature field.
      featureChanges[name] = formattedValue;
    } else {
      if (!(stageId in stages)) {
        stages[stageId] = {id: stageId};
      }
      stages[stageId][STAGE_FIELD_NAME_MAPPING[name] || name] = {
        form_field_name: name,
        value: formattedValue,
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
  (app as any).setUnsavedChanges(response !== '');
}

export function extensionMilestoneIsValid(value, currentMilestone) {
  if (isNaN(value)) {
    return false;
  }
  // Milestone should only have digits.
  for (let i = 0; i < value.length; i++) {
    if (value[i] < '0' || value[i] > '9') {
      return false;
    }
  }
  const intValue = parseInt(value);
  if (intValue >= 1000) {
    return false;
  }
  // End milestone should not be in the past.
  return parseInt(currentMilestone) <= intValue;
}
