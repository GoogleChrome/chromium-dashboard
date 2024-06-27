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
