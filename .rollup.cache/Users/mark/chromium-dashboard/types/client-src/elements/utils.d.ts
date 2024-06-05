export function autolink(s: any, featureLinks?: any[]): any[];
export function showToastMessage(msg: any): void;
/**
 * Returns the rendered elements of the named slot of component.
 * @param {Element} component
 * @param {string} slotName
 * @return {Element}
 */
export function slotAssignedElements(component: Element, slotName: string): Element;
export function clamp(val: any, lowerBound: any, upperBound: any): number;
export function findProcessStage(feStage: any, process: any): any;
export function shouldShowDisplayNameField(feStages: any, stageType: any): boolean;
export function findFirstFeatureStage(intentStage: any, currentStage: any, fe: any): any;
export function getStageValue(stage: any, fieldName: any): any;
/**
 * Check if a value is defined and not empty.
 *
 * @param {any} value - The value to be checked.
 * @return {boolean} Returns true if the value is defined and not empty, otherwise false.
 */
export function isDefinedValue(value: any): boolean;
export function hasFieldValue(fieldName: any, feStage: any, feature: any): boolean;
/**
 * Retrieves the value of a specific field for a given feature.
 * Note: This is independent of any value that might be in a corresponding
 * form field.
 *
 * @param {string} fieldName - The name of the field to retrieve.
 * @param {string} feStage - The stage of the feature.
 * @param {Object} feature - The feature object to retrieve the field value from.
 * @return {*} The value of the specified field for the given feature.
 */
export function getFieldValueFromFeature(fieldName: string, feStage: string, feature: any): any;
export function flattenSections(stage: any): any;
export function setupScrollToHash(pageElement: any): void;
export function renderHTMLIf(condition: any, originalHTML: any): any;
export function renderAbsoluteDate(dateStr: any, includeTime?: boolean): any;
export function renderRelativeDate(dateStr: any): import("lit-html").TemplateResult<1> | typeof nothing;
/** Returns the non-time part of date in the YYYY-MM-DD format.
 *
 * @param {Date} date
 * @return {string}
 */
export function isoDateString(date: Date): string;
/**
 * Parses URL query strings into a dict.
 * @param {string} rawQuery a raw URL query string, e.g. q=abc&num=1;
 * @return {Object} A key-value pair dictionary for the query string.
 */
export function parseRawQuery(rawQuery: string): any;
/**
 * Create a new URL using params and a location.
 * @param {string} params is the new param object.
 * @param {Object} location is an URL location.
 * @return {Object} the new URL.
 */
export function getNewLocation(params: string, location: any): any;
/**
 * Update window.location with new query params.
 * @param {string} key is the key of the query param.
 * @param {string} val is the unencoded value of the query param.
 */
export function updateURLParams(key: string, val: string): void;
/**
 * Update window.location with new query params.
 * @param {string} key is the key of the query param to delete.
 */
export function clearURLParams(key: string): void;
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
export function formatFeatureChanges(fieldValues: Array<FieldInfo>, featureId: number): UpdateSubmitBody;
/**
 * Manage response to change submission.
 * Required to manage beforeUnload handler.
 * @param {string} response The error message to display,
 *     or empty string if save was successful.
 */
export function handleSaveChangesResponse(response: string): void;
export function extensionMilestoneIsValid(value: any, currentMilestone: any): boolean;
export const IS_MOBILE: boolean;
export type FieldInfo = {
    /**
     * The name of the field.
     */
    name: string;
    /**
     * Whether the field was mutated by the user.
     */
    touched: boolean;
    /**
     * The stage that the field is associated with.
     * This field is undefined if the change is a feature change.
     */
    stageId: number;
    /**
     * The value written in the form field.
     */
    value: any;
    /**
     * Value that should be changed for some checkbox fields.
     * e.g. "set_stage" is a checkbox, but should change the field to a stage ID if true.
     */
    implicitValue: any;
};
export type UpdateSubmitBody = {
    /**
     * An object with feature changes.
     * key=field name, value=new field value.
     */
    feature_changes: {
        [x: string]: any;
    };
    /**
     * The list of changes to specific stages.
     */
    stages: Array<any>;
    /**
     * Whether any valid changes are present for submission.
     */
    has_changes: boolean;
};
import { nothing } from 'lit';
