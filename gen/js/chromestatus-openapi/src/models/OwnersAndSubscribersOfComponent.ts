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
 * @interface OwnersAndSubscribersOfComponent
 */
export interface OwnersAndSubscribersOfComponent {
    /**
     * 
     * @type {string}
     * @memberof OwnersAndSubscribersOfComponent
     */
    id: string;
    /**
     * 
     * @type {string}
     * @memberof OwnersAndSubscribersOfComponent
     */
    name: string;
    /**
     * 
     * @type {Array<number>}
     * @memberof OwnersAndSubscribersOfComponent
     */
    subscriber_ids?: Array<number>;
    /**
     * 
     * @type {Array<number>}
     * @memberof OwnersAndSubscribersOfComponent
     */
    owner_ids?: Array<number>;
}

/**
 * Check if a given object implements the OwnersAndSubscribersOfComponent interface.
 */
export function instanceOfOwnersAndSubscribersOfComponent(value: object): boolean {
    let isInstance = true;
    isInstance = isInstance && "id" in value;
    isInstance = isInstance && "name" in value;

    return isInstance;
}

export function OwnersAndSubscribersOfComponentFromJSON(json: any): OwnersAndSubscribersOfComponent {
    return OwnersAndSubscribersOfComponentFromJSONTyped(json, false);
}

export function OwnersAndSubscribersOfComponentFromJSONTyped(json: any, ignoreDiscriminator: boolean): OwnersAndSubscribersOfComponent {
    if ((json === undefined) || (json === null)) {
        return json;
    }
    return {
        
        'id': json['id'],
        'name': json['name'],
        'subscriber_ids': !exists(json, 'subscriber_ids') ? undefined : json['subscriber_ids'],
        'owner_ids': !exists(json, 'owner_ids') ? undefined : json['owner_ids'],
    };
}

export function OwnersAndSubscribersOfComponentToJSON(value?: OwnersAndSubscribersOfComponent | null): any {
    if (value === undefined) {
        return undefined;
    }
    if (value === null) {
        return null;
    }
    return {
        
        'id': value.id,
        'name': value.name,
        'subscriber_ids': value.subscriber_ids,
        'owner_ids': value.owner_ids,
    };
}

