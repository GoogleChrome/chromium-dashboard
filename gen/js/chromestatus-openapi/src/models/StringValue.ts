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
 * @interface StringValue
 */
export interface StringValue {
    /**
     * 
     * @type {string}
     * @memberof StringValue
     */
    valueType?: string;
    /**
     * 
     * @type {string}
     * @memberof StringValue
     */
    value?: string;
}

/**
 * Check if a given object implements the StringValue interface.
 */
export function instanceOfStringValue(value: object): value is StringValue {
    return true;
}

export function StringValueFromJSON(json: any): StringValue {
    return StringValueFromJSONTyped(json, false);
}

export function StringValueFromJSONTyped(json: any, ignoreDiscriminator: boolean): StringValue {
    if (json == null) {
        return json;
    }
    return {
        
        'valueType': json['valueType'] == null ? undefined : json['valueType'],
        'value': json['value'] == null ? undefined : json['value'],
    };
}

export function StringValueToJSON(value?: StringValue | null): any {
    if (value == null) {
        return value;
    }
    return {
        
        'valueType': value['valueType'],
        'value': value['value'],
    };
}

