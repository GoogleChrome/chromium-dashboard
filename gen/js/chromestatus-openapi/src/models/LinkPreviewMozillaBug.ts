/* tslint:disable */
/* eslint-disable */
/**
 * chomestatus API
 * The API for chromestatus.com. chromestatus.com is the official tool used for tracking feature launches in Blink (the browser engine that powers Chrome and many other web browsers). This tool guides feature owners through our launch process and serves as a primary source for developer information that then ripples throughout the web developer ecosystem. More details at: https://github.com/GoogleChrome/chromium-dashboard
 *
 * The version of the OpenAPI document: 1.0.0
 * 
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * https://openapi-generator.tech
 * Do not edit the class manually.
 */

import { exists, mapValues } from '../runtime';
import type { LinkPreviewOpenGraph } from './LinkPreviewOpenGraph';
import {
    LinkPreviewOpenGraphFromJSON,
    LinkPreviewOpenGraphFromJSONTyped,
    LinkPreviewOpenGraphToJSON,
} from './LinkPreviewOpenGraph';
import type { LinkPreviewOpenGraphAllOfInformation } from './LinkPreviewOpenGraphAllOfInformation';
import {
    LinkPreviewOpenGraphAllOfInformationFromJSON,
    LinkPreviewOpenGraphAllOfInformationFromJSONTyped,
    LinkPreviewOpenGraphAllOfInformationToJSON,
} from './LinkPreviewOpenGraphAllOfInformation';

/**
 * 
 * @export
 * @interface LinkPreviewMozillaBug
 */
export interface LinkPreviewMozillaBug extends LinkPreviewOpenGraph {
}

/**
 * Check if a given object implements the LinkPreviewMozillaBug interface.
 */
export function instanceOfLinkPreviewMozillaBug(value: object): boolean {
    let isInstance = true;

    return isInstance;
}

export function LinkPreviewMozillaBugFromJSON(json: any): LinkPreviewMozillaBug {
    return LinkPreviewMozillaBugFromJSONTyped(json, false);
}

export function LinkPreviewMozillaBugFromJSONTyped(json: any, ignoreDiscriminator: boolean): LinkPreviewMozillaBug {
    return json;
}

export function LinkPreviewMozillaBugToJSON(value?: LinkPreviewMozillaBug | null): any {
    return value;
}

