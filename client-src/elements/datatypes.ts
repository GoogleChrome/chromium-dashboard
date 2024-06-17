import {TemplateResult} from 'lit';

declare global {
  interface Window {
    google?: any;
    csClient?: any;
  }
}

//chromedash-timeline
export interface Property {
  [key: string]: any;
  0: number;
  1: string;
}

//autolink
export interface TextRun {
  content: string;
  tag?: string;
  href?: string;
}

export interface Component {
  refRegs: RegExp[];
  replacer: (match: any) => never[] | TextRun[];
}

//external-reviewers
export type LabelInfo = {
  description: string;
  variant: 'primary' | 'success' | 'neutral' | 'warning' | 'danger';
};

//form-definition
export interface BaseBrowser {
  view: {
    val: string;
    text: string;
    url: string;
    notes: string;
  };
}

export interface ChromeBrowser extends BaseBrowser {
  bug: string;
  blink_components: string[];
  devrel: string[];
  owners: string[];
  prefixed: boolean;
  status: {val: string};
  desktop: string;
  android: string;
  webview: string;
  ios: string;
}

export interface FirefoxBrowser extends BaseBrowser {}
export interface SafariBrowser extends BaseBrowser {}
export interface WebDevBrowser extends BaseBrowser {}
export interface OtherBrowser {
  view: {notes: string};
}

export interface Resources {
  docs: string[];
  samples: string[];
}

export interface Standards {
  spec: string;
  maturity: {val: number; text: string};
}

type FeatureName = string;

export interface Feature {
  name?: FeatureName;
  category_int: number;
  enterprise_feature_categories: string[];
  feature_type_int: number;
  intent_stage_int: number;
  standards: Standards;
  tag_review_status_int: number;
  security_review_status_int: number;
  privacy_review_status_int: number;
  resources: Resources;
  tags: string[];
  browsers: {
    chrome: ChromeBrowser;
    ff: FirefoxBrowser;
    safari: SafariBrowser;
    webdev: WebDevBrowser;
    other: OtherBrowser;
  };
}

export interface FormattedFeature {
  category: number;
  enterprise_feature_categories: string[];
  feature_type: number;
  intent_stage: number;
  accurate_as_of: boolean;
  spec_link: string;
  standard_maturity: number;
  tag_review_status: number;
  security_review_status: number;
  privacy_review_status: number;
  sample_links: string[];
  doc_links: string[];
  search_tags: string[];
  blink_components: string;
  bug_url: string;
  devrel: string[];
  owner: string[];
  prefixed: boolean;
  impl_status_chrome: string;
  shipped_milestone: string;
  shipped_android_milestone: string;
  shipped_webview_milestone: string;
  shipped_ios_milestone: string;
  ff_views: string;
  ff_views_link: string;
  ff_views_notes: string;
  safari_views: string;
  safari_views_link: string;
  safari_views_notes: string;
  web_dev_views: string;
  web_dev_views_link: string;
  web_dev_views_notes: string;
  other_views_notes: string;
  [key: string]: any; // Allow additional properties
}

//form-field-specs
export interface FieldAttrs {
  title?: string;
  type?: string;
  multiple?: boolean;
  placeholder?: string;
  pattern?: string;
  rows?: number;
  cols?: number;
  maxlength?: number;
  chromedash_single_pattern?: string;
  chromedash_split_pattern?: string;
  disabled?: boolean;
  min?: number;
}

export interface MilestoneRange {
  earlier?: string;
  later?: string;
  allEarlier?: string;
  allLater?: string;
  warning?: string;
  error?: string;
}

export interface Field {
  type?: string;
  name?: FeatureName;
  attrs?: FieldAttrs;
  required?: boolean;
  label?: string;
  help_text?: TemplateResult | string;
  enterprise_help_text?: TemplateResult;
  extra_help?: TemplateResult;
  enterprise_extra_help?: TemplateResult | string;
  check?: Function;
  initial?: number | boolean;
  enterprise_initial?: number;
  choices?:
    | Record<string, [number, string, string]>
    | Record<string, [number, string]>;
  displayLabel?: string;
  disabled?: boolean;
}

//form-definition
export interface Section {
  name?: string;
  fields: string[];
  isImplementationSection?: boolean;
  implStatusValue?: number | null;
}

export interface MetadataFields {
  name: string;
  sections: Section[];
}
