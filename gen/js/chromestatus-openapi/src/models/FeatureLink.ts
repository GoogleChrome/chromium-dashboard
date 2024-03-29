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
 * @interface FeatureLink
 */
export interface FeatureLink {
    /**
     * 
     * @type {number}
     * @memberof FeatureLink
     */
    id: number;
    /**
     * 
     * @type {string}
     * @memberof FeatureLink
     */
    name: string;
}

/**
 * Check if a given object implements the FeatureLink interface.
 */
export function instanceOfFeatureLink(value: object): boolean {
    let isInstance = true;
    isInstance = isInstance && "id" in value;
    isInstance = isInstance && "name" in value;

    return isInstance;
}

export function FeatureLinkFromJSON(json: any): FeatureLink {
    return FeatureLinkFromJSONTyped(json, false);
}

export function FeatureLinkFromJSONTyped(json: any, ignoreDiscriminator: boolean): FeatureLink {
    if ((json === undefined) || (json === null)) {
        return json;
    }
    return {
        
        'id': json['id'],
        'name': json['name'],
    };
}

export function FeatureLinkToJSON(value?: FeatureLink | null): any {
    if (value === undefined) {
        return undefined;
    }
    if (value === null) {
        return null;
    }
    return {
        
        'id': value.id,
        'name': value.name,
    };
}

