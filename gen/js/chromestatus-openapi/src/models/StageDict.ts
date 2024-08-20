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
import type { StageDictExtension } from './StageDictExtension';
import {
    StageDictExtensionFromJSON,
    StageDictExtensionFromJSONTyped,
    StageDictExtensionToJSON,
} from './StageDictExtension';

/**
 * 
 * @export
 * @interface StageDict
 */
export interface StageDict {
    /**
     * 
     * @type {number}
     * @memberof StageDict
     */
    id: number;
    /**
     * 
     * @type {Date}
     * @memberof StageDict
     */
    created: Date;
    /**
     * 
     * @type {number}
     * @memberof StageDict
     */
    feature_id: number;
    /**
     * 
     * @type {number}
     * @memberof StageDict
     */
    stage_type: number;
    /**
     * 
     * @type {string}
     * @memberof StageDict
     */
    display_name: string;
    /**
     * 
     * @type {number}
     * @memberof StageDict
     */
    intent_stage: number;
    /**
     * 
     * @type {string}
     * @memberof StageDict
     */
    intent_thread_url?: string;
    /**
     * 
     * @type {string}
     * @memberof StageDict
     */
    announcement_url?: string;
    /**
     * 
     * @type {string}
     * @memberof StageDict
     */
    origin_trial_id?: string;
    /**
     * 
     * @type {string}
     * @memberof StageDict
     */
    experiment_goals?: string;
    /**
     * 
     * @type {string}
     * @memberof StageDict
     */
    experiment_risks?: string;
    /**
     * 
     * @type {Array<StageDictExtension>}
     * @memberof StageDict
     */
    extensions?: Array<StageDictExtension>;
    /**
     * 
     * @type {string}
     * @memberof StageDict
     */
    origin_trial_feedback_url?: string;
    /**
     * 
     * @type {boolean}
     * @memberof StageDict
     */
    ot_action_requested: boolean;
    /**
     * 
     * @type {Date}
     * @memberof StageDict
     */
    ot_activation_date?: Date;
    /**
     * 
     * @type {number}
     * @memberof StageDict
     */
    ot_approval_buganizer_component?: number;
    /**
     * 
     * @type {number}
     * @memberof StageDict
     */
    ot_approval_buganizer_custom_field_id?: number;
    /**
     * 
     * @type {string}
     * @memberof StageDict
     */
    ot_approval_criteria_url?: string;
    /**
     * 
     * @type {string}
     * @memberof StageDict
     */
    ot_approval_group_email?: string;
    /**
     * 
     * @type {string}
     * @memberof StageDict
     */
    ot_chromium_trial_name?: string;
    /**
     * 
     * @type {string}
     * @memberof StageDict
     */
    ot_description?: string;
    /**
     * 
     * @type {string}
     * @memberof StageDict
     */
    ot_display_name?: string;
    /**
     * 
     * @type {string}
     * @memberof StageDict
     */
    ot_documentation_url?: string;
    /**
     * 
     * @type {Array<string>}
     * @memberof StageDict
     */
    ot_emails: Array<string>;
    /**
     * 
     * @type {string}
     * @memberof StageDict
     */
    ot_feedback_submission_url?: string;
    /**
     * 
     * @type {boolean}
     * @memberof StageDict
     */
    ot_has_third_party_support: boolean;
    /**
     * 
     * @type {boolean}
     * @memberof StageDict
     */
    ot_is_critical_trial: boolean;
    /**
     * 
     * @type {boolean}
     * @memberof StageDict
     */
    ot_is_deprecation_trial: boolean;
    /**
     * 
     * @type {string}
     * @memberof StageDict
     */
    ot_owner_email?: string;
    /**
     * 
     * @type {boolean}
     * @memberof StageDict
     */
    ot_require_approvals: boolean;
    /**
     * 
     * @type {number}
     * @memberof StageDict
     */
    ot_setup_status?: number;
    /**
     * 
     * @type {string}
     * @memberof StageDict
     */
    ot_webfeature_use_counter?: string;
    /**
     * 
     * @type {string}
     * @memberof StageDict
     */
    ot_request_note?: string;
    /**
     * 
     * @type {number}
     * @memberof StageDict
     */
    ot_stage_id?: number;
    /**
     * 
     * @type {string}
     * @memberof StageDict
     */
    experiment_extension_reason?: string;
    /**
     * 
     * @type {string}
     * @memberof StageDict
     */
    finch_url?: string;
    /**
     * 
     * @type {string}
     * @memberof StageDict
     */
    rollout_details?: string;
    /**
     * 
     * @type {number}
     * @memberof StageDict
     */
    rollout_impact?: number;
    /**
     * 
     * @type {number}
     * @memberof StageDict
     */
    rollout_milestone?: number;
    /**
     * 
     * @type {Array<string>}
     * @memberof StageDict
     */
    rollout_platforms?: Array<string>;
    /**
     * 
     * @type {Array<string>}
     * @memberof StageDict
     */
    enterprise_policies?: Array<string>;
    /**
     * 
     * @type {Array<string>}
     * @memberof StageDict
     */
    pm_emails?: Array<string>;
    /**
     * 
     * @type {Array<string>}
     * @memberof StageDict
     */
    tl_emails?: Array<string>;
    /**
     * 
     * @type {Array<string>}
     * @memberof StageDict
     */
    ux_emails?: Array<string>;
    /**
     * 
     * @type {Array<string>}
     * @memberof StageDict
     */
    te_emails?: Array<string>;
}

/**
 * Check if a given object implements the StageDict interface.
 */
export function instanceOfStageDict(value: object): value is StageDict {
    if (!('id' in value) || value['id'] === undefined) return false;
    if (!('created' in value) || value['created'] === undefined) return false;
    if (!('feature_id' in value) || value['feature_id'] === undefined) return false;
    if (!('stage_type' in value) || value['stage_type'] === undefined) return false;
    if (!('display_name' in value) || value['display_name'] === undefined) return false;
    if (!('intent_stage' in value) || value['intent_stage'] === undefined) return false;
    if (!('ot_action_requested' in value) || value['ot_action_requested'] === undefined) return false;
    if (!('ot_emails' in value) || value['ot_emails'] === undefined) return false;
    if (!('ot_has_third_party_support' in value) || value['ot_has_third_party_support'] === undefined) return false;
    if (!('ot_is_critical_trial' in value) || value['ot_is_critical_trial'] === undefined) return false;
    if (!('ot_is_deprecation_trial' in value) || value['ot_is_deprecation_trial'] === undefined) return false;
    if (!('ot_require_approvals' in value) || value['ot_require_approvals'] === undefined) return false;
    return true;
}

export function StageDictFromJSON(json: any): StageDict {
    return StageDictFromJSONTyped(json, false);
}

export function StageDictFromJSONTyped(json: any, ignoreDiscriminator: boolean): StageDict {
    if (json == null) {
        return json;
    }
    return {
        
        'id': json['id'],
        'created': (new Date(json['created'])),
        'feature_id': json['feature_id'],
        'stage_type': json['stage_type'],
        'display_name': json['display_name'],
        'intent_stage': json['intent_stage'],
        'intent_thread_url': json['intent_thread_url'] == null ? undefined : json['intent_thread_url'],
        'announcement_url': json['announcement_url'] == null ? undefined : json['announcement_url'],
        'origin_trial_id': json['origin_trial_id'] == null ? undefined : json['origin_trial_id'],
        'experiment_goals': json['experiment_goals'] == null ? undefined : json['experiment_goals'],
        'experiment_risks': json['experiment_risks'] == null ? undefined : json['experiment_risks'],
        'extensions': json['extensions'] == null ? undefined : ((json['extensions'] as Array<any>).map(StageDictExtensionFromJSON)),
        'origin_trial_feedback_url': json['origin_trial_feedback_url'] == null ? undefined : json['origin_trial_feedback_url'],
        'ot_action_requested': json['ot_action_requested'],
        'ot_activation_date': json['ot_activation_date'] == null ? undefined : (new Date(json['ot_activation_date'])),
        'ot_approval_buganizer_component': json['ot_approval_buganizer_component'] == null ? undefined : json['ot_approval_buganizer_component'],
        'ot_approval_buganizer_custom_field_id': json['ot_approval_buganizer_custom_field_id'] == null ? undefined : json['ot_approval_buganizer_custom_field_id'],
        'ot_approval_criteria_url': json['ot_approval_criteria_url'] == null ? undefined : json['ot_approval_criteria_url'],
        'ot_approval_group_email': json['ot_approval_group_email'] == null ? undefined : json['ot_approval_group_email'],
        'ot_chromium_trial_name': json['ot_chromium_trial_name'] == null ? undefined : json['ot_chromium_trial_name'],
        'ot_description': json['ot_description'] == null ? undefined : json['ot_description'],
        'ot_display_name': json['ot_display_name'] == null ? undefined : json['ot_display_name'],
        'ot_documentation_url': json['ot_documentation_url'] == null ? undefined : json['ot_documentation_url'],
        'ot_emails': json['ot_emails'],
        'ot_feedback_submission_url': json['ot_feedback_submission_url'] == null ? undefined : json['ot_feedback_submission_url'],
        'ot_has_third_party_support': json['ot_has_third_party_support'],
        'ot_is_critical_trial': json['ot_is_critical_trial'],
        'ot_is_deprecation_trial': json['ot_is_deprecation_trial'],
        'ot_owner_email': json['ot_owner_email'] == null ? undefined : json['ot_owner_email'],
        'ot_require_approvals': json['ot_require_approvals'],
        'ot_setup_status': json['ot_setup_status'] == null ? undefined : json['ot_setup_status'],
        'ot_webfeature_use_counter': json['ot_webfeature_use_counter'] == null ? undefined : json['ot_webfeature_use_counter'],
        'ot_request_note': json['ot_request_note'] == null ? undefined : json['ot_request_note'],
        'ot_stage_id': json['ot_stage_id'] == null ? undefined : json['ot_stage_id'],
        'experiment_extension_reason': json['experiment_extension_reason'] == null ? undefined : json['experiment_extension_reason'],
        'finch_url': json['finch_url'] == null ? undefined : json['finch_url'],
        'rollout_details': json['rollout_details'] == null ? undefined : json['rollout_details'],
        'rollout_impact': json['rollout_impact'] == null ? undefined : json['rollout_impact'],
        'rollout_milestone': json['rollout_milestone'] == null ? undefined : json['rollout_milestone'],
        'rollout_platforms': json['rollout_platforms'] == null ? undefined : json['rollout_platforms'],
        'enterprise_policies': json['enterprise_policies'] == null ? undefined : json['enterprise_policies'],
        'pm_emails': json['pm_emails'] == null ? undefined : json['pm_emails'],
        'tl_emails': json['tl_emails'] == null ? undefined : json['tl_emails'],
        'ux_emails': json['ux_emails'] == null ? undefined : json['ux_emails'],
        'te_emails': json['te_emails'] == null ? undefined : json['te_emails'],
    };
}

export function StageDictToJSON(value?: StageDict | null): any {
    if (value == null) {
        return value;
    }
    return {
        
        'id': value['id'],
        'created': ((value['created']).toISOString()),
        'feature_id': value['feature_id'],
        'stage_type': value['stage_type'],
        'display_name': value['display_name'],
        'intent_stage': value['intent_stage'],
        'intent_thread_url': value['intent_thread_url'],
        'announcement_url': value['announcement_url'],
        'origin_trial_id': value['origin_trial_id'],
        'experiment_goals': value['experiment_goals'],
        'experiment_risks': value['experiment_risks'],
        'extensions': value['extensions'] == null ? undefined : ((value['extensions'] as Array<any>).map(StageDictExtensionToJSON)),
        'origin_trial_feedback_url': value['origin_trial_feedback_url'],
        'ot_action_requested': value['ot_action_requested'],
        'ot_activation_date': value['ot_activation_date'] == null ? undefined : ((value['ot_activation_date'] as any).toISOString()),
        'ot_approval_buganizer_component': value['ot_approval_buganizer_component'],
        'ot_approval_buganizer_custom_field_id': value['ot_approval_buganizer_custom_field_id'],
        'ot_approval_criteria_url': value['ot_approval_criteria_url'],
        'ot_approval_group_email': value['ot_approval_group_email'],
        'ot_chromium_trial_name': value['ot_chromium_trial_name'],
        'ot_description': value['ot_description'],
        'ot_display_name': value['ot_display_name'],
        'ot_documentation_url': value['ot_documentation_url'],
        'ot_emails': value['ot_emails'],
        'ot_feedback_submission_url': value['ot_feedback_submission_url'],
        'ot_has_third_party_support': value['ot_has_third_party_support'],
        'ot_is_critical_trial': value['ot_is_critical_trial'],
        'ot_is_deprecation_trial': value['ot_is_deprecation_trial'],
        'ot_owner_email': value['ot_owner_email'],
        'ot_require_approvals': value['ot_require_approvals'],
        'ot_setup_status': value['ot_setup_status'],
        'ot_webfeature_use_counter': value['ot_webfeature_use_counter'],
        'ot_request_note': value['ot_request_note'],
        'ot_stage_id': value['ot_stage_id'],
        'experiment_extension_reason': value['experiment_extension_reason'],
        'finch_url': value['finch_url'],
        'rollout_details': value['rollout_details'],
        'rollout_impact': value['rollout_impact'],
        'rollout_milestone': value['rollout_milestone'],
        'rollout_platforms': value['rollout_platforms'],
        'enterprise_policies': value['enterprise_policies'],
        'pm_emails': value['pm_emails'],
        'tl_emails': value['tl_emails'],
        'ux_emails': value['ux_emails'],
        'te_emails': value['te_emails'],
    };
}

