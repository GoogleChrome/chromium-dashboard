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
/**
 * 
 * @export
 * @interface LinkPreviewBase
 */
export interface LinkPreviewBase {
    /**
     * 
     * @type {string}
     * @memberof LinkPreviewBase
     */
    url: string;
    /**
     * 
     * @type {string}
     * @memberof LinkPreviewBase
     */
    type: string;
    /**
     * 
     * @type {object}
     * @memberof LinkPreviewBase
     */
    information: object;
    /**
     * 
     * @type {number}
     * @memberof LinkPreviewBase
     */
    http_error_code: number;
}

/**
 * Check if a given object implements the LinkPreviewBase interface.
 */
export function instanceOfLinkPreviewBase(value: object): boolean {
    let isInstance = true;
    isInstance = isInstance && "url" in value;
    isInstance = isInstance && "type" in value;
    isInstance = isInstance && "information" in value;
    isInstance = isInstance && "http_error_code" in value;

    return isInstance;
}

export function LinkPreviewBaseFromJSON(json: any): LinkPreviewBase {
    return LinkPreviewBaseFromJSONTyped(json, false);
}

export function LinkPreviewBaseFromJSONTyped(json: any, ignoreDiscriminator: boolean): LinkPreviewBase {
    if ((json === undefined) || (json === null)) {
        return json;
    }
    return {
        
        'url': json['url'],
        'type': json['type'],
        'information': json['information'],
        'http_error_code': json['http_error_code'],
    };
}

export function LinkPreviewBaseToJSON(value?: LinkPreviewBase | null): any {
    if (value === undefined) {
        return undefined;
    }
    if (value === null) {
        return null;
    }
    return {
        
        'url': value.url,
        'type': value.type,
        'information': value.information,
        'http_error_code': value.http_error_code,
    };
}
