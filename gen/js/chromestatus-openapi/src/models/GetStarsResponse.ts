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

import { mapValues } from '../runtime';
/**
 * 
 * @export
 * @interface GetStarsResponse
 */
export interface GetStarsResponse {
    /**
     * 
     * @type {Array<number>}
     * @memberof GetStarsResponse
     */
    feature_ids?: Array<number>;
}

/**
 * Check if a given object implements the GetStarsResponse interface.
 */
export function instanceOfGetStarsResponse(value: object): value is GetStarsResponse {
    return true;
}

export function GetStarsResponseFromJSON(json: any): GetStarsResponse {
    return GetStarsResponseFromJSONTyped(json, false);
}

export function GetStarsResponseFromJSONTyped(json: any, ignoreDiscriminator: boolean): GetStarsResponse {
    if (json == null) {
        return json;
    }
    return {
        
        'feature_ids': json['feature_ids'] == null ? undefined : json['feature_ids'],
    };
}

export function GetStarsResponseToJSON(value?: GetStarsResponse | null): any {
    if (value == null) {
        return value;
    }
    return {
        
        'feature_ids': value['feature_ids'],
    };
}

