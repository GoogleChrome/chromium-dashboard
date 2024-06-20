declare class ChromeStatusHttpError extends Error {
  resource: string;
  method: string;
  status: number;
  constructor(
    message: string,
    resource: string,
    method: string,
    status: number
  );
}

declare class FeatureNotFoundError extends Error {
  featureID: number;
  constructor(featureID: number);
}

interface FeatureLink {
  url: string;
  type: string;
  information: any;
  http_error_code: number;
}

declare interface ChromeStatusClient {
  token: string;
  tokenExpiresSec: number;
  baseUrl: string;

  new (token: string, tokenExpiresSec: number): ChromeStatusClient;

  ensureTokenIsValid(): Promise<void>;
  doFetch(
    resource: string,
    httpMethod: string,
    body: any,
    includeToken?: boolean
  ): Promise<any>;
  doGet(resource: string, body: any): Promise<any>;
  doPost(resource: string, body: any): Promise<any>;
  doPatch(resource: string, body: any): Promise<any>;
  doDelete(resource: string): Promise<any>;

  // Please add types and the rest of the methods.
  getFeatureLinks(
    featureId: number,
    updateStaleLinks?: boolean
  ): Promise<{data: FeatureLink[]; has_stale_links: boolean}>;
  getComments(featureId: number, gateId: string): Promise<any>;
  undeleteComment(featureId: number, commentId: number): Promise<any>;
  deleteComment(featureId: number, commentId: number): Promise<any>;
  postComment(featureId, gateId, comment, postToThreadType): Promise<any>;
  getComments(featureId, gateId): Promise<any>;
}
