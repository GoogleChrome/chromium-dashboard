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
import type { Amendment } from './Amendment';
import {
    AmendmentFromJSON,
    AmendmentFromJSONTyped,
    AmendmentToJSON,
} from './Amendment';

/**
 * 
 * @export
 * @interface Activity
 */
export interface Activity {
    /**
     * 
     * @type {number}
     * @memberof Activity
     */
    comment_id: number;
    /**
     * 
     * @type {number}
     * @memberof Activity
     */
    feature_id: number;
    /**
     * 
     * @type {number}
     * @memberof Activity
     */
    gate_id?: number;
    /**
     * 
     * @type {string}
     * @memberof Activity
     */
    created: string;
    /**
     * 
     * @type {string}
     * @memberof Activity
     */
    author: string;
    /**
     * 
     * @type {string}
     * @memberof Activity
     */
    content: string;
    /**
     * 
     * @type {string}
     * @memberof Activity
     */
    deleted_by?: string;
    /**
     * 
     * @type {Array<Amendment>}
     * @memberof Activity
     */
    amendments?: Array<Amendment>;
}

/**
 * Check if a given object implements the Activity interface.
 */
export function instanceOfActivity(value: object): value is Activity {
    if (!('comment_id' in value) || value['comment_id'] === undefined) return false;
    if (!('feature_id' in value) || value['feature_id'] === undefined) return false;
    if (!('created' in value) || value['created'] === undefined) return false;
    if (!('author' in value) || value['author'] === undefined) return false;
    if (!('content' in value) || value['content'] === undefined) return false;
    return true;
}

export function ActivityFromJSON(json: any): Activity {
    return ActivityFromJSONTyped(json, false);
}

export function ActivityFromJSONTyped(json: any, ignoreDiscriminator: boolean): Activity {
    if (json == null) {
        return json;
    }
    return {
        
        'comment_id': json['comment_id'],
        'feature_id': json['feature_id'],
        'gate_id': json['gate_id'] == null ? undefined : json['gate_id'],
        'created': json['created'],
        'author': json['author'],
        'content': json['content'],
        'deleted_by': json['deleted_by'] == null ? undefined : json['deleted_by'],
        'amendments': json['amendments'] == null ? undefined : ((json['amendments'] as Array<any>).map(AmendmentFromJSON)),
    };
}

export function ActivityToJSON(value?: Activity | null): any {
    if (value == null) {
        return value;
    }
    return {
        
        'comment_id': value['comment_id'],
        'feature_id': value['feature_id'],
        'gate_id': value['gate_id'],
        'created': value['created'],
        'author': value['author'],
        'content': value['content'],
        'deleted_by': value['deleted_by'],
        'amendments': value['amendments'] == null ? undefined : ((value['amendments'] as Array<any>).map(AmendmentToJSON)),
    };
}
