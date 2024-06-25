
declare global {
    interface Window {
      csClient: ChromeStatusClient;
      csOpenApiClient: DefaultApiInterface;
    }
  }
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
