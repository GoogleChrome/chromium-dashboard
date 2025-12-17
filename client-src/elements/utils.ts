// This file contains helper functions for our elements.

import {html, nothing, TemplateResult} from 'lit';
import {unsafeHTML} from 'lit/directives/unsafe-html.js';
import DOMPurify from 'dompurify';
import {marked} from 'marked';
import {
  Channels,
  Feature,
  FeatureLink,
  StageDict,
  User,
} from '../js-src/cs-client.js';
import {markupAutolinks} from './autolink.js';
import {FORMS_BY_STAGE_TYPE, FormattedFeature} from './form-definition.js';
import {
  ENTERPRISE_FEATURE_CATEGORIES_DISPLAYNAME,
  ENTERPRISE_IMPACT_DISPLAYNAME,
  ENTERPRISE_PRODUCT_CATEGORY_DISPLAYNAME,
  OT_MILESTONE_END_FIELDS,
  OT_SETUP_STATUS_OPTIONS,
  PLATFORMS_DISPLAYNAME,
  ROLLOUT_PLAN_DISPLAYNAME,
  ROLLOUT_STAGE_PLAN_DISPLAYNAME,
  STAGE_ENT_ROLLOUT,
  STAGE_FIELD_NAME_MAPPING,
  STAGE_SPECIFIC_FIELDS,
  STAGE_TYPES_ORIGIN_TRIAL,
  STAGE_TYPES_SHIPPING,
} from './form-field-enums';

let toastEl;

// Determine if the browser looks like the user is on a mobile device.
// We assume that a small enough window width implies a mobile device.
const NARROW_WINDOW_MAX_WIDTH = 700;

// Represent a 4-week period in milliseconds. This grace period needs
// to be consistent with ACCURACY_GRACE_PERIOD in internals/reminders.py.
const ACCURACY_GRACE_PERIOD = 4 * 7 * 24 * 60 * 60 * 1000;

// A 9-week grace period used to approximate 2 months for shipped features.
const SHIPPED_FEATURE_OUTDATED_GRACE_PERIOD = 9 * 7 * 24 * 60 * 60 * 1000;

export const IS_MOBILE = (() => {
  const width =
    window.innerWidth ||
    document.documentElement.clientWidth ||
    document.body.clientWidth;
  return width <= NARROW_WINDOW_MAX_WIDTH;
})();

/* Convert user-entered text into safe HTML with clickable links
 * where appropriate.
 */
export function autolink(
  s: string | null | undefined,
  featureLinks: FeatureLink[] = [],
  isMarkdown: boolean = false
): TemplateResult[] {
  s = s ?? '';
  if (isMarkdown) {
    const rendered: string = marked.parse(s) as string;
    const sanitized: string = DOMPurify.sanitize(rendered);
    const markup: TemplateResult = html`${unsafeHTML(sanitized)}`;
    return [markup];
  } else {
    const withLinks = markupAutolinks(s, featureLinks);
    return withLinks;
  }
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
    for (const otMilestoneField of Object.values(OT_MILESTONE_END_FIELDS)) {
      const extensionValue = getStageValue(extension, otMilestoneField);
      if (extensionValue) {
        maxMilestone = Math.max(maxMilestone, extensionValue);
      }
    }
  }
  // Save the findings with the "max_" prefix as a prop of the stage for reference.
  feStage[`max_${fieldName}`] = maxMilestone;
}

// Get the milestone value that is displayed to the user regarding the origin trial end date.
function _getMilestoneExtensionValue(feStage, fieldName) {
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
    if (fieldName === 'rollout_platforms' && value) {
      return value.map(platformId => PLATFORMS_DISPLAYNAME[platformId]);
    }
    if (fieldName === 'rollout_stage_plan') {
      return ROLLOUT_STAGE_PLAN_DISPLAYNAME[value];
    }
    if (fieldName in OT_MILESTONE_END_FIELDS) {
      // If an origin trial end date is being displayed, handle extension milestones as well.
      return _getMilestoneExtensionValue(feStage, fieldName);
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

  if (fieldName === 'enterprise_product_category' && value !== undefined) {
    return ENTERPRISE_PRODUCT_CATEGORY_DISPLAYNAME[value];
  }
  if (fieldName === 'enterprise_feature_categories' && value) {
    return value.map(
      categoryId => ENTERPRISE_FEATURE_CATEGORIES_DISPLAYNAME[categoryId]
    );
  }
  if (fieldName === 'enterprise_impact' && value) {
    return ENTERPRISE_IMPACT_DISPLAYNAME[value];
  }
  if (fieldName === 'rollout_plan' && value !== undefined) {
    return ROLLOUT_PLAN_DISPLAYNAME[value];
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

/**
 * Redirects the user to the current page without query parameters.
 * This is typically used after login or logout to refresh the page state.
 *
 * Removes any query string from the current URL and reloads the page.
 */
export function redirectToCurrentPage(): void {
  const url = window.location.href.split('?')[0];
  window.location.href = url;
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
 * @return {Record<string, string>} A key-value pair dictionary for the query string.
 */
export function parseRawQuery(rawQuery): Record<string, string> {
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

// Get any help text for a specific field based on the condition of if it should be disabled.
export function getDisabledHelpText(field, feStage?) {
  // OT milestone fields should not be editable when the automated
  // OT creation process is in progress or in a failed state.
  if (
    field === 'ot_milestone_desktop_start' ||
    field === 'ot_milestone_desktop_end'
  ) {
    if (
      feStage?.ot_setup_status ===
        OT_SETUP_STATUS_OPTIONS.OT_READY_FOR_CREATION ||
      feStage?.ot_setup_status === OT_SETUP_STATUS_OPTIONS.OT_CREATION_FAILED ||
      feStage?.ot_setup_status === OT_SETUP_STATUS_OPTIONS.OT_ACTIVATION_FAILED
    ) {
      return 'Origin trial milestone cannot be edited while a creation request is in progress';
    }
  }
  return '';
}

/**
 * Update window.location with new query params.
 * @param {string} key is the key of the query param.
 * @param {string} val is the unencoded value of the query param.
 */
export function updateURLParams(key, val) {
  const newURL = formatURLParams(key, val);
  if (newURL.toString() === window.location.toString()) {
    return;
  }
  // Update URL without refreshing the page. {path:} is needed for
  // an issue in page.js:
  // https://github.com/visionmedia/page.js/issues/293#issuecomment-456906679
  window.history.pushState({path: newURL.toString()}, '', newURL);
}

/**
 * Format the existing URL with new query params.
 * @param {string} key is the key of the query param.
 * @param {string} val is the unencoded value of the query param.
 */
export function formatURLParams(key, val) {
  // Update the query param object.
  const rawQuery = parseRawQuery(window.location.search);
  rawQuery[key] = encodeURIComponent(val);

  // Assemble the new URL.
  const newURL = getNewLocation(rawQuery, window.location);
  newURL.hash = '';
  return newURL;
}

export function formatUrlForRelativeOffset(
  start: number,
  delta: number,
  pageSize: number,
  totalCount: number
): string | undefined {
  const offset = start + delta;
  if (totalCount === undefined || offset <= -pageSize || offset >= totalCount) {
    return undefined;
  }
  return formatUrlForOffset(Math.max(0, offset));
}

export function formatUrlForOffset(offset: number): string {
  return formatURLParams('start', offset).toString();
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
  isMarkdown?: boolean;
  alwaysHidden?: boolean;
  isApprovalsField?: boolean;
  checkMessage?: string;
}

interface UpdateSubmitBody {
  feature_changes: FeatureUpdateInfo;
  stages: StageUpdateInfo[];
  has_changes: boolean;
}

interface StageUpdateInfo {
  [stageField: string]: any;
}

interface FeatureUpdateInfo {
  [featureField: string]: any;
}

// Prepare feature/stage changes to be submitted.
export function formatFeatureChanges(
  fieldValues,
  featureId,
  formStageId?: number
): UpdateSubmitBody {
  let hasChanges = false;
  const featureChanges = {id: featureId};
  // Multiple stages can be mutated, so this object is a stage of stages.
  const stages = {};
  // When editing an individual stage, always provide stage ID so that
  // active_stage_id can be set by the server.
  if (formStageId) {
    stages[formStageId] = {id: formStageId};
  }
  for (const {
    name,
    touched,
    value,
    stageId,
    implicitValue,
    isMarkdown,
  } of fieldValues) {
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
      if (isMarkdown !== undefined) {
        featureChanges[name + '_is_markdown'] = isMarkdown;
      }
    } else {
      // TODO(jrobbins): When we are ready to support markdown on stage fields,
      // just make all long text fields always use markdown.
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

// Check if a specific user has edit permission for a specific feature.
export function userCanEdit(user: User | undefined, featureId): boolean {
  return Boolean(
    user && (user.can_edit_all || user.editable_features.includes(featureId))
  );
}

/**
 * Check if feature.accurate_as_of is verified, within the four-week
 * grace period to currentDate.
 *
 *  @param accurateAsOf The accurate_as_of date as an ISO string.
 *  @param currentDate The current date in milliseconds.
 *  @param gracePeriod The grace period in milliseconds. Defaults
 *                      to ACCURACY_GRACE_PERIOD.
 */
export function isVerifiedWithinGracePeriod(
  accurateAsOf: string | undefined,
  currentDate: number,
  gracePeriod: number = ACCURACY_GRACE_PERIOD
) {
  if (!accurateAsOf) {
    return false;
  }

  const accurateDate = Date.parse(accurateAsOf);
  if (accurateDate + gracePeriod < currentDate) {
    return false;
  }

  return true;
}

export const METRICS_TYPE_AND_VIEW_TO_SUBTITLE = {
  csspopularity: 'CSS usage metrics > all properties',
  cssanimated: 'CSS usage metrics > animated properties',
  featurepopularity: 'HTML & JavaScript usage metrics > all features',
  webfeaturepopularity: 'Web features usage metrics > all features',
};

/**
 * A feature is outdated if it has shipped, and its
 * accurate_as_of is before its latest shipping date before today.
 */
function isShippedFeatureOutdated(
  feature: Feature,
  hasShipped: boolean,
  closestShippingDate: string
): boolean {
  // Check if a feature has shipped.
  if (!hasShipped) {
    return false;
  }

  // If accurate_as_of is missing from a shipped feature, it is likely
  // an old feature. Treat it as not oudated.
  if (!feature.accurate_as_of || !closestShippingDate) {
    return false;
  }

  return Date.parse(feature.accurate_as_of) < Date.parse(closestShippingDate);
}

/**
 * Determine if it should show warnings to a feature author, if
 * a shipped feature is outdated, and it has edit access.
 */
function isShippedFeatureOutdatedForAuthor(
  feature: Feature,
  userCanEdit: boolean,
  hasShipped: boolean,
  closestShippingDate: string
): boolean {
  return (
    userCanEdit &&
    isShippedFeatureOutdated(feature, hasShipped, closestShippingDate)
  );
}

/**
 * Determine if it should show warnings to all readers, if
 * a shipped feature is outdated, and last update was > 9 weeks.
 */
function isShippedFeatureOutdatedForAll(
  feature: Feature,
  hasShipped: boolean,
  currentDate: number,
  closestShippingDate: string
): boolean {
  if (!isShippedFeatureOutdated(feature, hasShipped, closestShippingDate)) {
    return false;
  }

  const isVerified = isVerifiedWithinGracePeriod(
    feature.accurate_as_of,
    currentDate,
    SHIPPED_FEATURE_OUTDATED_GRACE_PERIOD
  );
  return !isVerified;
}

/**
 * Fetches the shipping date (final_beta) for a specific milestone.
 */
async function fetchClosestShippingDate(milestone: number): Promise<string> {
  if (milestone === 0) {
    return '';
  }
  try {
    const newMilestonesInfo = await window.csClient.getSpecifiedChannels(
      milestone,
      milestone
    );
    return newMilestonesInfo[milestone]?.final_beta;
  } catch {
    showToastMessage(
      'Some errors occurred. Please refresh the page or try again later.'
    );
    return '';
  }
}

export interface closestShippingDateInfo {
  // The closest milestone shipping date as an ISO string.
  closestShippingDate: string;
  isUpcoming: boolean;
  hasShipped: boolean;
}

/**
 * Determine if this feature is upcoming - scheduled to ship
 * within two milestones, then find the closest shipping date
 * for that upcoming milestone or an already shipped milestone.
 */
export async function findClosestShippingDate(
  channels: Channels,
  stages: StageDict[]
): Promise<closestShippingDateInfo> {
  const latestStableVersion = channels?.stable?.version;
  if (!latestStableVersion || !stages) {
    return {
      closestShippingDate: '',
      isUpcoming: false,
      hasShipped: false,
    };
  }

  let closestShippingDate = '';
  let isUpcoming = false;
  let hasShipped = false;

  const shippingTypeMilestones = new Set<number | undefined>();
  for (const stage of stages) {
    if (
      STAGE_TYPES_SHIPPING.has(stage.stage_type) ||
      stage.stage_type === STAGE_ENT_ROLLOUT
    ) {
      shippingTypeMilestones.add(stage.desktop_first);
      shippingTypeMilestones.add(stage.android_first);
      shippingTypeMilestones.add(stage.ios_first);
      shippingTypeMilestones.add(stage.webview_first);
    }
  }

  const upcomingMilestonesTarget = new Set<number | undefined>([
    ...shippingTypeMilestones,
  ]);
  // Check if this feature is shipped within two milestones.
  let foundMilestone = 0;
  if (upcomingMilestonesTarget.has(latestStableVersion + 1)) {
    foundMilestone = latestStableVersion + 1;
    isUpcoming = true;
  } else if (upcomingMilestonesTarget.has(latestStableVersion + 2)) {
    foundMilestone = latestStableVersion + 2;
    isUpcoming = true;
  }

  if (isUpcoming) {
    Object.keys(channels).forEach(key => {
      if (channels[key].version === foundMilestone) {
        closestShippingDate = channels[key].final_beta || '';
      }
    });
  } else {
    const shippedMilestonesTarget = shippingTypeMilestones;
    // If not upcoming, find the closest milestone that has shipped.
    let latestMilestone = 0;
    for (const ms of shippedMilestonesTarget) {
      if (ms && ms <= latestStableVersion) {
        latestMilestone = Math.max(latestMilestone, ms);
      }
    }

    if (latestMilestone === latestStableVersion) {
      closestShippingDate = channels['stable']?.final_beta || '';
      hasShipped = true;
    } else {
      closestShippingDate = await fetchClosestShippingDate(latestMilestone);
      hasShipped = true;
    }
  }
  return {
    closestShippingDate,
    isUpcoming,
    hasShipped,
  };
}

/**
 * A feature is outdated if it is scheduled to ship in the next 2 milestones,
 * and its accurate_as_of date is at least 4 weeks ago.
 */
function isUpcomingFeatureOutdated(
  feature: Feature,
  isUpcoming: boolean,
  currentDate: number
): boolean {
  return (
    isUpcoming &&
    !isVerifiedWithinGracePeriod(feature.accurate_as_of, currentDate)
  );
}

/**
 * Returns a warning banner TemplateResult if a feature is considered outdated,
 * otherwise returns null.
 * @param {Feature} feature The feature object.
 * @param {closestShippingDateInfo} shippingInfo The shipping information from findClosestShippingDate.
 * @param {number | undefined} currentDate The current date as a timestamp.
 * @param {boolean} userCanEdit Whether the current user can edit the feature.
 * @returns {TemplateResult | null} A lit-html template or null.
 */
export function getFeatureOutdatedBanner(
  feature: Feature,
  shippingInfo: closestShippingDateInfo,
  currentDate: number | undefined,
  userCanEdit: boolean
): TemplateResult | null {
  if (!currentDate) {
    currentDate = Date.now();
  }
  const {closestShippingDate, hasShipped, isUpcoming} = shippingInfo;
  if (isUpcomingFeatureOutdated(feature, isUpcoming, currentDate)) {
    if (userCanEdit) {
      return html`
        <div class="warning layout horizontal center">
          <span class="tooltip" id="outdated-icon" title="Feature outdated ">
            <sl-icon name="exclamation-circle-fill" data-tooltip></sl-icon>
          </span>
          <span>
            Your feature hasn't been verified as accurate since&nbsp;
            <sl-relative-time
              date=${feature.accurate_as_of ?? ''}
            ></sl-relative-time
            >, but it is scheduled to ship&nbsp;
            <sl-relative-time date=${closestShippingDate}></sl-relative-time>.
            Please
            <a href="/guide/verify_accuracy/${feature.id}"
              >verify that your feature is accurate</a
            >.
          </span>
        </div>
      `;
    } else {
      return html`
        <div class="warning layout horizontal center">
          <span class="tooltip" id="outdated-icon" title="Feature outdated ">
            <sl-icon name="exclamation-circle-fill" data-tooltip></sl-icon>
          </span>
          <span>
            This feature hasn't been verified as accurate since&nbsp;
            <sl-relative-time
              date=${feature.accurate_as_of ?? ''}
            ></sl-relative-time
            >, but it is scheduled to ship&nbsp;
            <sl-relative-time date=${closestShippingDate}></sl-relative-time>.
          </span>
        </div>
      `;
    }
  } else if (
    isShippedFeatureOutdated(feature, hasShipped, closestShippingDate)
  ) {
    if (
      isShippedFeatureOutdatedForAuthor(
        feature,
        userCanEdit,
        hasShipped,
        closestShippingDate
      )
    ) {
      return html`
        <div class="warning layout horizontal center">
          <span
            class="tooltip"
            id="shipped-outdated-author"
            title="Feature outdated "
          >
            <sl-icon name="exclamation-circle-fill" data-tooltip></sl-icon>
          </span>
          <span>
            Your feature hasn't been verified as accurate since&nbsp;
            <sl-relative-time
              date=${feature.accurate_as_of ?? ''}
            ></sl-relative-time
            >, but it claims to have shipped&nbsp;
            <sl-relative-time date=${closestShippingDate}></sl-relative-time>.
            Please
            <a href="/guide/verify_accuracy/${feature.id}"
              >verify that your feature is accurate</a
            >.
          </span>
        </div>
      `;
    } else if (
      isShippedFeatureOutdatedForAll(
        feature,
        hasShipped,
        currentDate,
        closestShippingDate
      )
    ) {
      return html`
        <div class="warning layout horizontal center">
          <span
            class="tooltip"
            id="shipped-outdated-all"
            title="Feature outdated "
          >
            <sl-icon name="exclamation-circle-fill" data-tooltip></sl-icon>
          </span>
          <span>
            This feature hasn't been verified as accurate since&nbsp;
            <sl-relative-time
              date=${feature.accurate_as_of ?? ''}
            ></sl-relative-time
            >, but it claims to have shipped&nbsp;
            <sl-relative-time date=${closestShippingDate}></sl-relative-time>.
          </span>
        </div>
      `;
    }
  }

  return null;
}
