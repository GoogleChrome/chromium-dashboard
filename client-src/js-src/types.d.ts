import {DefaultApiInterface} from 'chromestatus-openapi';
import {ChromeStatusClient} from './chrome-status-client';

declare global {
  interface Window {
    csClient: ChromeStatusClient;
    csOpenApiClient: DefaultApiInterface;
    scrollToElement: (hash: string) => void;
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
