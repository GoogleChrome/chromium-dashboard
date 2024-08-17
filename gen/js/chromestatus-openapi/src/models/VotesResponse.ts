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
import type { Vote } from './Vote';
import {
    VoteFromJSON,
    VoteFromJSONTyped,
    VoteToJSON,
} from './Vote';

/**
 * 
 * @export
 * @interface VotesResponse
 */
export interface VotesResponse {
    /**
     * 
     * @type {Array<Vote>}
     * @memberof VotesResponse
     */
    votes?: Array<Vote>;
}

/**
 * Check if a given object implements the VotesResponse interface.
 */
export function instanceOfVotesResponse(value: object): value is VotesResponse {
    return true;
}

export function VotesResponseFromJSON(json: any): VotesResponse {
    return VotesResponseFromJSONTyped(json, false);
}

export function VotesResponseFromJSONTyped(json: any, ignoreDiscriminator: boolean): VotesResponse {
    if (json == null) {
        return json;
    }
    return {
        
        'votes': json['votes'] == null ? undefined : ((json['votes'] as Array<any>).map(VoteFromJSON)),
    };
}

export function VotesResponseToJSON(value?: VotesResponse | null): any {
    if (value == null) {
        return value;
    }
    return {
        
        'votes': value['votes'] == null ? undefined : ((value['votes'] as Array<any>).map(VoteToJSON)),
    };
}

