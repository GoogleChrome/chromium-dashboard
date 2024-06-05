export type FeatureLink = {
    url: string;
    type: string;
    /**
     * - fields depend on type; see link_helpers.py
     */
    information: object;
    http_error_code: number;
};
export class ChromeStatusClient {
    static isTokenExpired(tokenExpiresSec: any): boolean;
    constructor(token: any, tokenExpiresSec: any);
    token: any;
    tokenExpiresSec: any;
    baseUrl: string;
    ensureTokenIsValid(): Promise<void>;
    doFetch(resource: any, httpMethod: any, body: any, includeToken?: boolean): Promise<any>;
    doGet(resource: any, body: any): Promise<any>;
    doPost(resource: any, body: any): Promise<any>;
    doPatch(resource: any, body: any): Promise<any>;
    doDelete(resource: any): Promise<any>;
    signIn(credentialResponse: any): Promise<any>;
    signOut(): Promise<any>;
    getDismissedCues(): Promise<any>;
    dismissCue(cue: any): Promise<any>;
    getPermissions(returnPairedUser?: boolean): Promise<any>;
    getSettings(): Promise<any>;
    setSettings(notify: any): Promise<any>;
    getStars(): Promise<any>;
    setStar(featureId: any, starred: any): Promise<any>;
    createAccount(email: any, isAdmin: any, isSiteEditor: any): Promise<any>;
    deleteAccount(accountId: any): Promise<any>;
    getVotes(featureId: any, gateId: any): Promise<any>;
    setVote(featureId: any, gateId: any, state: any): Promise<any>;
    getGates(featureId: any): Promise<any>;
    getPendingGates(): Promise<any>;
    updateGate(featureId: any, gateId: any, assignees: any): Promise<any>;
    getComments(featureId: any, gateId: any): Promise<any>;
    postComment(featureId: any, gateId: any, comment: any, postToThreadType: any): Promise<any>;
    deleteComment(featureId: any, commentId: any): Promise<any>;
    undeleteComment(featureId: any, commentId: any): Promise<any>;
    getFeature(featureId: any): Promise<any>;
    getFeaturesInMilestone(milestone: any): Promise<any>;
    getFeaturesForEnterpriseReleaseNotes(milestone: any): Promise<any>;
    searchFeatures(userQuery: any, showEnterprise: any, sortSpec: any, start: any, num: any): Promise<any>;
    updateFeature(featureChanges: any): Promise<any>;
    /**
     * @param {number} featureId
     * @returns {Promise<{data: FeatureLink[], has_stale_links: boolean}>}
     */
    getFeatureLinks(featureId: number, updateStaleLinks?: boolean): Promise<{
        data: FeatureLink[];
        has_stale_links: boolean;
    }>;
    getFeatureLinksSummary(): Promise<any>;
    getFeatureLinksSamples(domain: any, type: any, isError: any): Promise<any>;
    getStage(featureId: any, stageId: any): Promise<any>;
    deleteStage(featureId: any, stageId: any): Promise<any>;
    createStage(featureId: any, body: any): Promise<any>;
    updateStage(featureId: any, stageId: any, body: any): Promise<any>;
    addXfnGates(featureId: any, stageId: any): Promise<any>;
    getOriginTrials(): Promise<any>;
    createOriginTrial(featureId: any, stageId: any, body: any): Promise<any>;
    extendOriginTrial(featureId: any, stageId: any, body: any): Promise<any>;
    getFeatureProcess(featureId: any): Promise<any>;
    getFeatureProgress(featureId: any): Promise<any>;
    getBlinkComponents(): Promise<any>;
    getChannels(): Promise<any>;
    getSpecifiedChannels(start: any, end: any): Promise<any>;
}
/**
 * FeatureNotFoundError represents an error for when a feature was not found
 * for the given ID.
 */
export class FeatureNotFoundError extends Error {
    constructor(featureID: any);
    featureID: any;
}
