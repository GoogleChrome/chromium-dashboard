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
 * @interface FeatureLinksSample
 */
export interface FeatureLinksSample {
    /**
     * 
     * @type {string}
     * @memberof FeatureLinksSample
     */
    url: string;
    /**
     * 
     * @type {string}
     * @memberof FeatureLinksSample
     */
    type: string;
    /**
     * 
     * @type {object}
     * @memberof FeatureLinksSample
     */
    information: object | null;
    /**
     * 
     * @type {number}
     * @memberof FeatureLinksSample
     */
    http_error_code: number | null;
    /**
     * 
     * @type {Array<number>}
     * @memberof FeatureLinksSample
     */
    feature_ids?: Array<number>;
}

/**
 * Check if a given object implements the FeatureLinksSample interface.
 */
export function instanceOfFeatureLinksSample(value: object): value is FeatureLinksSample {
    if (!('url' in value) || value['url'] === undefined) return false;
    if (!('type' in value) || value['type'] === undefined) return false;
    if (!('information' in value) || value['information'] === undefined) return false;
    if (!('http_error_code' in value) || value['http_error_code'] === undefined) return false;
    return true;
}

export function FeatureLinksSampleFromJSON(json: any): FeatureLinksSample {
    return FeatureLinksSampleFromJSONTyped(json, false);
}

export function FeatureLinksSampleFromJSONTyped(json: any, ignoreDiscriminator: boolean): FeatureLinksSample {
    if (json == null) {
        return json;
    }
    return {
        
        'url': json['url'],
        'type': json['type'],
        'information': json['information'],
        'http_error_code': json['http_error_code'],
        'feature_ids': json['feature_ids'] == null ? undefined : json['feature_ids'],
    };
}

export function FeatureLinksSampleToJSON(value?: FeatureLinksSample | null): any {
    if (value == null) {
        return value;
    }
    return {
        
        'url': value['url'],
        'type': value['type'],
        'information': value['information'],
        'http_error_code': value['http_error_code'],
        'feature_ids': value['feature_ids'],
    };
}

