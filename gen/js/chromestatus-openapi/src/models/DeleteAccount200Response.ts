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
 * @interface DeleteAccount200Response
 */
export interface DeleteAccount200Response {
    /**
     * 
     * @type {string}
     * @memberof DeleteAccount200Response
     */
    message?: string;
}

/**
 * Check if a given object implements the DeleteAccount200Response interface.
 */
export function instanceOfDeleteAccount200Response(value: object): value is DeleteAccount200Response {
    return true;
}

export function DeleteAccount200ResponseFromJSON(json: any): DeleteAccount200Response {
    return DeleteAccount200ResponseFromJSONTyped(json, false);
}

export function DeleteAccount200ResponseFromJSONTyped(json: any, ignoreDiscriminator: boolean): DeleteAccount200Response {
    if (json == null) {
        return json;
    }
    return {
        
        'message': json['message'] == null ? undefined : json['message'],
    };
}

export function DeleteAccount200ResponseToJSON(value?: DeleteAccount200Response | null): any {
    if (value == null) {
        return value;
    }
    return {
        
        'message': value['message'],
    };
}

