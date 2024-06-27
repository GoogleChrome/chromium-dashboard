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

interface SampleFeatureLink {
  url: string;
  http_error_code?: number;
  feature_ids: number[];
}

interface FeatureLinksSummary {
  total_count: number;
  covered_count: number;
  uncovered_count: number;
  error_count: number;
  http_error_count: number;
  link_types: {key: string; count: number}[];
  uncovered_link_domains: {key: string; count: number}[];
  error_link_domains: {key: string; count: number}[];
}
