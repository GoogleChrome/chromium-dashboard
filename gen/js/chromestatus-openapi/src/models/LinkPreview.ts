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
import { LinkPreviewGithubIssueFromJSONTyped } from './LinkPreviewGithubIssue';
import { LinkPreviewGithubMarkdownFromJSONTyped } from './LinkPreviewGithubMarkdown';
import { LinkPreviewGithubPullRequestFromJSONTyped } from './LinkPreviewGithubPullRequest';
import { LinkPreviewGoogleDocsFromJSONTyped } from './LinkPreviewGoogleDocs';
import { LinkPreviewMdnDocsFromJSONTyped } from './LinkPreviewMdnDocs';
import { LinkPreviewMozillaBugFromJSONTyped } from './LinkPreviewMozillaBug';
import { LinkPreviewSpecsFromJSONTyped } from './LinkPreviewSpecs';
import { LinkPreviewWebkitBugFromJSONTyped } from './LinkPreviewWebkitBug';
/**
 * 
 * @export
 * @interface LinkPreview
 */
export interface LinkPreview {
    /**
     * 
     * @type {string}
     * @memberof LinkPreview
     */
    url: string;
    /**
     * 
     * @type {string}
     * @memberof LinkPreview
     */
    type: string;
    /**
     * 
     * @type {object}
     * @memberof LinkPreview
     */
    information: object | null;
    /**
     * 
     * @type {number}
     * @memberof LinkPreview
     */
    http_error_code?: number;
}

/**
 * Check if a given object implements the LinkPreview interface.
 */
export function instanceOfLinkPreview(value: object): value is LinkPreview {
    if (!('url' in value) || value['url'] === undefined) return false;
    if (!('type' in value) || value['type'] === undefined) return false;
    if (!('information' in value) || value['information'] === undefined) return false;
    return true;
}

export function LinkPreviewFromJSON(json: any): LinkPreview {
    return LinkPreviewFromJSONTyped(json, false);
}

export function LinkPreviewFromJSONTyped(json: any, ignoreDiscriminator: boolean): LinkPreview {
    if (json == null) {
        return json;
    }
    if (!ignoreDiscriminator) {
        if (json['type'] === 'github_issue') {
            return LinkPreviewGithubIssueFromJSONTyped(json, true);
        }
        if (json['type'] === 'github_markdown') {
            return LinkPreviewGithubMarkdownFromJSONTyped(json, true);
        }
        if (json['type'] === 'github_pull_request') {
            return LinkPreviewGithubPullRequestFromJSONTyped(json, true);
        }
        if (json['type'] === 'google_docs') {
            return LinkPreviewGoogleDocsFromJSONTyped(json, true);
        }
        if (json['type'] === 'mdn_docs') {
            return LinkPreviewMdnDocsFromJSONTyped(json, true);
        }
        if (json['type'] === 'mozilla_bug') {
            return LinkPreviewMozillaBugFromJSONTyped(json, true);
        }
        if (json['type'] === 'specs') {
            return LinkPreviewSpecsFromJSONTyped(json, true);
        }
        if (json['type'] === 'webkit_bug') {
            return LinkPreviewWebkitBugFromJSONTyped(json, true);
        }
    }
    return {
        
        'url': json['url'],
        'type': json['type'],
        'information': json['information'],
        'http_error_code': json['http_error_code'] == null ? undefined : json['http_error_code'],
    };
}

export function LinkPreviewToJSON(value?: LinkPreview | null): any {
    if (value == null) {
        return value;
    }
    return {
        
        'url': value['url'],
        'type': value['type'],
        'information': value['information'],
        'http_error_code': value['http_error_code'],
    };
}

