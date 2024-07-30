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


import * as runtime from '../runtime';
import type {
  AccountResponse,
  ComponentUsersRequest,
  ComponentsUsersResponse,
  CreateAccountRequest,
  DeleteAccount200Response,
  ExternalReviewsResponse,
  FeatureLatency,
  GetIntentResponse,
  MessageResponse,
  PostIntentRequest,
  ReviewLatency,
  SpecMentor,
} from '../models/index';
import {
    AccountResponseFromJSON,
    AccountResponseToJSON,
    ComponentUsersRequestFromJSON,
    ComponentUsersRequestToJSON,
    ComponentsUsersResponseFromJSON,
    ComponentsUsersResponseToJSON,
    CreateAccountRequestFromJSON,
    CreateAccountRequestToJSON,
    DeleteAccount200ResponseFromJSON,
    DeleteAccount200ResponseToJSON,
    ExternalReviewsResponseFromJSON,
    ExternalReviewsResponseToJSON,
    FeatureLatencyFromJSON,
    FeatureLatencyToJSON,
    GetIntentResponseFromJSON,
    GetIntentResponseToJSON,
    MessageResponseFromJSON,
    MessageResponseToJSON,
    PostIntentRequestFromJSON,
    PostIntentRequestToJSON,
    ReviewLatencyFromJSON,
    ReviewLatencyToJSON,
    SpecMentorFromJSON,
    SpecMentorToJSON,
} from '../models/index';

export interface AddUserToComponentRequest {
    componentId: number;
    userId: number;
    componentUsersRequest?: ComponentUsersRequest;
}

export interface CreateAccountOperationRequest {
    createAccountRequest?: CreateAccountRequest;
}

export interface DeleteAccountRequest {
    accountId: number;
}

export interface GetIntentBodyRequest {
    featureId: number;
    stageId: number;
    gateId: number;
}

export interface ListExternalReviewsRequest {
    reviewGroup: ListExternalReviewsReviewGroupEnum;
}

export interface ListFeatureLatencyRequest {
    startAt: Date;
    endAt: Date;
}

export interface ListSpecMentorsRequest {
    after?: Date;
}

export interface PostIntentToBlinkDevRequest {
    featureId: number;
    stageId: number;
    gateId: number;
    postIntentRequest?: PostIntentRequest;
}

export interface RemoveUserFromComponentRequest {
    componentId: number;
    userId: number;
    componentUsersRequest?: ComponentUsersRequest;
}

/**
 * DefaultApi - interface
 * 
 * @export
 * @interface DefaultApiInterface
 */
export interface DefaultApiInterface {
    /**
     * 
     * @summary Add a user to a component
     * @param {number} componentId Component ID
     * @param {number} userId User ID
     * @param {ComponentUsersRequest} [componentUsersRequest] 
     * @param {*} [options] Override http request option.
     * @throws {RequiredError}
     * @memberof DefaultApiInterface
     */
    addUserToComponentRaw(requestParameters: AddUserToComponentRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<void>>;

    /**
     * Add a user to a component
     */
    addUserToComponent(requestParameters: AddUserToComponentRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<void>;

    /**
     * 
     * @summary Create a new account
     * @param {CreateAccountRequest} [createAccountRequest] 
     * @param {*} [options] Override http request option.
     * @throws {RequiredError}
     * @memberof DefaultApiInterface
     */
    createAccountRaw(requestParameters: CreateAccountOperationRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<AccountResponse>>;

    /**
     * Create a new account
     */
    createAccount(requestParameters: CreateAccountOperationRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<AccountResponse>;

    /**
     * 
     * @summary Delete an account
     * @param {number} accountId ID of the account to delete
     * @param {*} [options] Override http request option.
     * @throws {RequiredError}
     * @memberof DefaultApiInterface
     */
    deleteAccountRaw(requestParameters: DeleteAccountRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<DeleteAccount200Response>>;

    /**
     * Delete an account
     */
    deleteAccount(requestParameters: DeleteAccountRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<DeleteAccount200Response>;

    /**
     * 
     * @summary Get the HTML body of an intent draft
     * @param {number} featureId Feature ID
     * @param {number} stageId Stage ID
     * @param {number} gateId Gate ID
     * @param {*} [options] Override http request option.
     * @throws {RequiredError}
     * @memberof DefaultApiInterface
     */
    getIntentBodyRaw(requestParameters: GetIntentBodyRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<GetIntentResponse>>;

    /**
     * Get the HTML body of an intent draft
     */
    getIntentBody(requestParameters: GetIntentBodyRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<GetIntentResponse>;

    /**
     * 
     * @summary List all components and possible users
     * @param {*} [options] Override http request option.
     * @throws {RequiredError}
     * @memberof DefaultApiInterface
     */
    listComponentUsersRaw(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<ComponentsUsersResponse>>;

    /**
     * List all components and possible users
     */
    listComponentUsers(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<ComponentsUsersResponse>;

    /**
     * 
     * @summary List features whose external reviews are incomplete
     * @param {'tag' | 'gecko' | 'webkit'} reviewGroup Which review group to focus on:  * &#x60;tag&#x60; - The W3C TAG  * &#x60;gecko&#x60; - The rendering engine that powers Mozilla Firefox  * &#x60;webkit&#x60; - The rendering engine that powers Apple Safari 
     * @param {*} [options] Override http request option.
     * @throws {RequiredError}
     * @memberof DefaultApiInterface
     */
    listExternalReviewsRaw(requestParameters: ListExternalReviewsRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<ExternalReviewsResponse>>;

    /**
     * List features whose external reviews are incomplete
     */
    listExternalReviews(requestParameters: ListExternalReviewsRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<ExternalReviewsResponse>;

    /**
     * 
     * @summary List how long each feature took to launch
     * @param {Date} startAt Start date (RFC 3339, section 5.6, for example, 2017-07-21). The date is inclusive.
     * @param {Date} endAt End date (RFC 3339, section 5.6, for example, 2017-07-21). The date is exclusive.
     * @param {*} [options] Override http request option.
     * @throws {RequiredError}
     * @memberof DefaultApiInterface
     */
    listFeatureLatencyRaw(requestParameters: ListFeatureLatencyRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<Array<FeatureLatency>>>;

    /**
     * List how long each feature took to launch
     */
    listFeatureLatency(requestParameters: ListFeatureLatencyRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<Array<FeatureLatency>>;

    /**
     * 
     * @summary List recently reviewed features and their review latency
     * @param {*} [options] Override http request option.
     * @throws {RequiredError}
     * @memberof DefaultApiInterface
     */
    listReviewsWithLatencyRaw(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<Array<ReviewLatency>>>;

    /**
     * List recently reviewed features and their review latency
     */
    listReviewsWithLatency(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<Array<ReviewLatency>>;

    /**
     * 
     * @summary List spec mentors and their activity
     * @param {Date} [after] 
     * @param {*} [options] Override http request option.
     * @throws {RequiredError}
     * @memberof DefaultApiInterface
     */
    listSpecMentorsRaw(requestParameters: ListSpecMentorsRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<Array<SpecMentor>>>;

    /**
     * List spec mentors and their activity
     */
    listSpecMentors(requestParameters: ListSpecMentorsRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<Array<SpecMentor>>;

    /**
     * 
     * @summary Submit an intent to be posted on blink-dev
     * @param {number} featureId Feature ID
     * @param {number} stageId Stage ID
     * @param {number} gateId Gate ID
     * @param {PostIntentRequest} [postIntentRequest] Gate ID and additional users to CC email to.
     * @param {*} [options] Override http request option.
     * @throws {RequiredError}
     * @memberof DefaultApiInterface
     */
    postIntentToBlinkDevRaw(requestParameters: PostIntentToBlinkDevRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<MessageResponse>>;

    /**
     * Submit an intent to be posted on blink-dev
     */
    postIntentToBlinkDev(requestParameters: PostIntentToBlinkDevRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<MessageResponse>;

    /**
     * 
     * @summary Remove a user from a component
     * @param {number} componentId Component ID
     * @param {number} userId User ID
     * @param {ComponentUsersRequest} [componentUsersRequest] 
     * @param {*} [options] Override http request option.
     * @throws {RequiredError}
     * @memberof DefaultApiInterface
     */
    removeUserFromComponentRaw(requestParameters: RemoveUserFromComponentRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<void>>;

    /**
     * Remove a user from a component
     */
    removeUserFromComponent(requestParameters: RemoveUserFromComponentRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<void>;

}

/**
 * 
 */
export class DefaultApi extends runtime.BaseAPI implements DefaultApiInterface {

    /**
     * Add a user to a component
     */
    async addUserToComponentRaw(requestParameters: AddUserToComponentRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<void>> {
        if (requestParameters['componentId'] == null) {
            throw new runtime.RequiredError(
                'componentId',
                'Required parameter "componentId" was null or undefined when calling addUserToComponent().'
            );
        }

        if (requestParameters['userId'] == null) {
            throw new runtime.RequiredError(
                'userId',
                'Required parameter "userId" was null or undefined when calling addUserToComponent().'
            );
        }

        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        headerParameters['Content-Type'] = 'application/json';

        if (this.configuration && this.configuration.apiKey) {
            headerParameters["X-Xsrf-Token"] = await this.configuration.apiKey("X-Xsrf-Token"); // XsrfToken authentication
        }

        const response = await this.request({
            path: `/components/{componentId}/users/{userId}`.replace(`{${"componentId"}}`, encodeURIComponent(String(requestParameters['componentId']))).replace(`{${"userId"}}`, encodeURIComponent(String(requestParameters['userId']))),
            method: 'PUT',
            headers: headerParameters,
            query: queryParameters,
            body: ComponentUsersRequestToJSON(requestParameters['componentUsersRequest']),
        }, initOverrides);

        return new runtime.VoidApiResponse(response);
    }

    /**
     * Add a user to a component
     */
    async addUserToComponent(requestParameters: AddUserToComponentRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<void> {
        await this.addUserToComponentRaw(requestParameters, initOverrides);
    }

    /**
     * Create a new account
     */
    async createAccountRaw(requestParameters: CreateAccountOperationRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<AccountResponse>> {
        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        headerParameters['Content-Type'] = 'application/json';

        const response = await this.request({
            path: `/accounts`,
            method: 'POST',
            headers: headerParameters,
            query: queryParameters,
            body: CreateAccountRequestToJSON(requestParameters['createAccountRequest']),
        }, initOverrides);

        return new runtime.JSONApiResponse(response, (jsonValue) => AccountResponseFromJSON(jsonValue));
    }

    /**
     * Create a new account
     */
    async createAccount(requestParameters: CreateAccountOperationRequest = {}, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<AccountResponse> {
        const response = await this.createAccountRaw(requestParameters, initOverrides);
        return await response.value();
    }

    /**
     * Delete an account
     */
    async deleteAccountRaw(requestParameters: DeleteAccountRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<DeleteAccount200Response>> {
        if (requestParameters['accountId'] == null) {
            throw new runtime.RequiredError(
                'accountId',
                'Required parameter "accountId" was null or undefined when calling deleteAccount().'
            );
        }

        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        const response = await this.request({
            path: `/accounts/{account_id}`.replace(`{${"account_id"}}`, encodeURIComponent(String(requestParameters['accountId']))),
            method: 'DELETE',
            headers: headerParameters,
            query: queryParameters,
        }, initOverrides);

        return new runtime.JSONApiResponse(response, (jsonValue) => DeleteAccount200ResponseFromJSON(jsonValue));
    }

    /**
     * Delete an account
     */
    async deleteAccount(requestParameters: DeleteAccountRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<DeleteAccount200Response> {
        const response = await this.deleteAccountRaw(requestParameters, initOverrides);
        return await response.value();
    }

    /**
     * Get the HTML body of an intent draft
     */
    async getIntentBodyRaw(requestParameters: GetIntentBodyRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<GetIntentResponse>> {
        if (requestParameters['featureId'] == null) {
            throw new runtime.RequiredError(
                'featureId',
                'Required parameter "featureId" was null or undefined when calling getIntentBody().'
            );
        }

        if (requestParameters['stageId'] == null) {
            throw new runtime.RequiredError(
                'stageId',
                'Required parameter "stageId" was null or undefined when calling getIntentBody().'
            );
        }

        if (requestParameters['gateId'] == null) {
            throw new runtime.RequiredError(
                'gateId',
                'Required parameter "gateId" was null or undefined when calling getIntentBody().'
            );
        }

        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        const response = await this.request({
            path: `/features/{feature_id}/{stage_id}/{gate_id}/intent`.replace(`{${"feature_id"}}`, encodeURIComponent(String(requestParameters['featureId']))).replace(`{${"stage_id"}}`, encodeURIComponent(String(requestParameters['stageId']))).replace(`{${"gate_id"}}`, encodeURIComponent(String(requestParameters['gateId']))),
            method: 'GET',
            headers: headerParameters,
            query: queryParameters,
        }, initOverrides);

        return new runtime.JSONApiResponse(response, (jsonValue) => GetIntentResponseFromJSON(jsonValue));
    }

    /**
     * Get the HTML body of an intent draft
     */
    async getIntentBody(requestParameters: GetIntentBodyRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<GetIntentResponse> {
        const response = await this.getIntentBodyRaw(requestParameters, initOverrides);
        return await response.value();
    }

    /**
     * List all components and possible users
     */
    async listComponentUsersRaw(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<ComponentsUsersResponse>> {
        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        if (this.configuration && this.configuration.apiKey) {
            headerParameters["X-Xsrf-Token"] = await this.configuration.apiKey("X-Xsrf-Token"); // XsrfToken authentication
        }

        const response = await this.request({
            path: `/componentsusers`,
            method: 'GET',
            headers: headerParameters,
            query: queryParameters,
        }, initOverrides);

        return new runtime.JSONApiResponse(response, (jsonValue) => ComponentsUsersResponseFromJSON(jsonValue));
    }

    /**
     * List all components and possible users
     */
    async listComponentUsers(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<ComponentsUsersResponse> {
        const response = await this.listComponentUsersRaw(initOverrides);
        return await response.value();
    }

    /**
     * List features whose external reviews are incomplete
     */
    async listExternalReviewsRaw(requestParameters: ListExternalReviewsRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<ExternalReviewsResponse>> {
        if (requestParameters['reviewGroup'] == null) {
            throw new runtime.RequiredError(
                'reviewGroup',
                'Required parameter "reviewGroup" was null or undefined when calling listExternalReviews().'
            );
        }

        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        const response = await this.request({
            path: `/external_reviews/{review_group}`.replace(`{${"review_group"}}`, encodeURIComponent(String(requestParameters['reviewGroup']))),
            method: 'GET',
            headers: headerParameters,
            query: queryParameters,
        }, initOverrides);

        return new runtime.JSONApiResponse(response, (jsonValue) => ExternalReviewsResponseFromJSON(jsonValue));
    }

    /**
     * List features whose external reviews are incomplete
     */
    async listExternalReviews(requestParameters: ListExternalReviewsRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<ExternalReviewsResponse> {
        const response = await this.listExternalReviewsRaw(requestParameters, initOverrides);
        return await response.value();
    }

    /**
     * List how long each feature took to launch
     */
    async listFeatureLatencyRaw(requestParameters: ListFeatureLatencyRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<Array<FeatureLatency>>> {
        if (requestParameters['startAt'] == null) {
            throw new runtime.RequiredError(
                'startAt',
                'Required parameter "startAt" was null or undefined when calling listFeatureLatency().'
            );
        }

        if (requestParameters['endAt'] == null) {
            throw new runtime.RequiredError(
                'endAt',
                'Required parameter "endAt" was null or undefined when calling listFeatureLatency().'
            );
        }

        const queryParameters: any = {};

        if (requestParameters['startAt'] != null) {
            queryParameters['startAt'] = (requestParameters['startAt'] as any).toISOString().substring(0,10);
        }

        if (requestParameters['endAt'] != null) {
            queryParameters['endAt'] = (requestParameters['endAt'] as any).toISOString().substring(0,10);
        }

        const headerParameters: runtime.HTTPHeaders = {};

        const response = await this.request({
            path: `/feature-latency`,
            method: 'GET',
            headers: headerParameters,
            query: queryParameters,
        }, initOverrides);

        return new runtime.JSONApiResponse(response, (jsonValue) => jsonValue.map(FeatureLatencyFromJSON));
    }

    /**
     * List how long each feature took to launch
     */
    async listFeatureLatency(requestParameters: ListFeatureLatencyRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<Array<FeatureLatency>> {
        const response = await this.listFeatureLatencyRaw(requestParameters, initOverrides);
        return await response.value();
    }

    /**
     * List recently reviewed features and their review latency
     */
    async listReviewsWithLatencyRaw(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<Array<ReviewLatency>>> {
        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        const response = await this.request({
            path: `/review-latency`,
            method: 'GET',
            headers: headerParameters,
            query: queryParameters,
        }, initOverrides);

        return new runtime.JSONApiResponse(response, (jsonValue) => jsonValue.map(ReviewLatencyFromJSON));
    }

    /**
     * List recently reviewed features and their review latency
     */
    async listReviewsWithLatency(initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<Array<ReviewLatency>> {
        const response = await this.listReviewsWithLatencyRaw(initOverrides);
        return await response.value();
    }

    /**
     * List spec mentors and their activity
     */
    async listSpecMentorsRaw(requestParameters: ListSpecMentorsRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<Array<SpecMentor>>> {
        const queryParameters: any = {};

        if (requestParameters['after'] != null) {
            queryParameters['after'] = (requestParameters['after'] as any).toISOString().substring(0,10);
        }

        const headerParameters: runtime.HTTPHeaders = {};

        const response = await this.request({
            path: `/spec_mentors`,
            method: 'GET',
            headers: headerParameters,
            query: queryParameters,
        }, initOverrides);

        return new runtime.JSONApiResponse(response, (jsonValue) => jsonValue.map(SpecMentorFromJSON));
    }

    /**
     * List spec mentors and their activity
     */
    async listSpecMentors(requestParameters: ListSpecMentorsRequest = {}, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<Array<SpecMentor>> {
        const response = await this.listSpecMentorsRaw(requestParameters, initOverrides);
        return await response.value();
    }

    /**
     * Submit an intent to be posted on blink-dev
     */
    async postIntentToBlinkDevRaw(requestParameters: PostIntentToBlinkDevRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<MessageResponse>> {
        if (requestParameters['featureId'] == null) {
            throw new runtime.RequiredError(
                'featureId',
                'Required parameter "featureId" was null or undefined when calling postIntentToBlinkDev().'
            );
        }

        if (requestParameters['stageId'] == null) {
            throw new runtime.RequiredError(
                'stageId',
                'Required parameter "stageId" was null or undefined when calling postIntentToBlinkDev().'
            );
        }

        if (requestParameters['gateId'] == null) {
            throw new runtime.RequiredError(
                'gateId',
                'Required parameter "gateId" was null or undefined when calling postIntentToBlinkDev().'
            );
        }

        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        headerParameters['Content-Type'] = 'application/json';

        const response = await this.request({
            path: `/features/{feature_id}/{stage_id}/{gate_id}/intent`.replace(`{${"feature_id"}}`, encodeURIComponent(String(requestParameters['featureId']))).replace(`{${"stage_id"}}`, encodeURIComponent(String(requestParameters['stageId']))).replace(`{${"gate_id"}}`, encodeURIComponent(String(requestParameters['gateId']))),
            method: 'POST',
            headers: headerParameters,
            query: queryParameters,
            body: PostIntentRequestToJSON(requestParameters['postIntentRequest']),
        }, initOverrides);

        return new runtime.JSONApiResponse(response, (jsonValue) => MessageResponseFromJSON(jsonValue));
    }

    /**
     * Submit an intent to be posted on blink-dev
     */
    async postIntentToBlinkDev(requestParameters: PostIntentToBlinkDevRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<MessageResponse> {
        const response = await this.postIntentToBlinkDevRaw(requestParameters, initOverrides);
        return await response.value();
    }

    /**
     * Remove a user from a component
     */
    async removeUserFromComponentRaw(requestParameters: RemoveUserFromComponentRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<void>> {
        if (requestParameters['componentId'] == null) {
            throw new runtime.RequiredError(
                'componentId',
                'Required parameter "componentId" was null or undefined when calling removeUserFromComponent().'
            );
        }

        if (requestParameters['userId'] == null) {
            throw new runtime.RequiredError(
                'userId',
                'Required parameter "userId" was null or undefined when calling removeUserFromComponent().'
            );
        }

        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        headerParameters['Content-Type'] = 'application/json';

        if (this.configuration && this.configuration.apiKey) {
            headerParameters["X-Xsrf-Token"] = await this.configuration.apiKey("X-Xsrf-Token"); // XsrfToken authentication
        }

        const response = await this.request({
            path: `/components/{componentId}/users/{userId}`.replace(`{${"componentId"}}`, encodeURIComponent(String(requestParameters['componentId']))).replace(`{${"userId"}}`, encodeURIComponent(String(requestParameters['userId']))),
            method: 'DELETE',
            headers: headerParameters,
            query: queryParameters,
            body: ComponentUsersRequestToJSON(requestParameters['componentUsersRequest']),
        }, initOverrides);

        return new runtime.VoidApiResponse(response);
    }

    /**
     * Remove a user from a component
     */
    async removeUserFromComponent(requestParameters: RemoveUserFromComponentRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<void> {
        await this.removeUserFromComponentRaw(requestParameters, initOverrides);
    }

}

/**
 * @export
 */
export const ListExternalReviewsReviewGroupEnum = {
    tag: 'tag',
    gecko: 'gecko',
    webkit: 'webkit'
} as const;
export type ListExternalReviewsReviewGroupEnum = typeof ListExternalReviewsReviewGroupEnum[keyof typeof ListExternalReviewsReviewGroupEnum];
