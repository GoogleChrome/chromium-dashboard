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
 * @interface SurveyAnswers
 */
export interface SurveyAnswers {
    /**
     * 
     * @type {boolean}
     * @memberof SurveyAnswers
     */
    is_language_polyfill?: boolean;
    /**
     * 
     * @type {boolean}
     * @memberof SurveyAnswers
     */
    is_api_polyfill?: boolean;
    /**
     * 
     * @type {boolean}
     * @memberof SurveyAnswers
     */
    is_same_origin_css?: boolean;
    /**
     * 
     * @type {string}
     * @memberof SurveyAnswers
     */
    launch_or_contact?: string;
}

/**
 * Check if a given object implements the SurveyAnswers interface.
 */
export function instanceOfSurveyAnswers(value: object): value is SurveyAnswers {
    return true;
}

export function SurveyAnswersFromJSON(json: any): SurveyAnswers {
    return SurveyAnswersFromJSONTyped(json, false);
}

export function SurveyAnswersFromJSONTyped(json: any, ignoreDiscriminator: boolean): SurveyAnswers {
    if (json == null) {
        return json;
    }
    return {
        
        'is_language_polyfill': json['is_language_polyfill'] == null ? undefined : json['is_language_polyfill'],
        'is_api_polyfill': json['is_api_polyfill'] == null ? undefined : json['is_api_polyfill'],
        'is_same_origin_css': json['is_same_origin_css'] == null ? undefined : json['is_same_origin_css'],
        'launch_or_contact': json['launch_or_contact'] == null ? undefined : json['launch_or_contact'],
    };
}

export function SurveyAnswersToJSON(value?: SurveyAnswers | null): any {
    if (value == null) {
        return value;
    }
    return {
        
        'is_language_polyfill': value['is_language_polyfill'],
        'is_api_polyfill': value['is_api_polyfill'],
        'is_same_origin_css': value['is_same_origin_css'],
        'launch_or_contact': value['launch_or_contact'],
    };
}

