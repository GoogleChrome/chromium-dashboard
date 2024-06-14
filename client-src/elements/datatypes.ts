declare global {
  interface Window {
    google: any;
  }
}

declare global {
  interface Window {
    google: any;
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

export interface Browser {
  chrome: {
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
  };
  ff: {
    view: {val: string; text: string; url: string; notes: string};
  };
  safari: {
    view: {val: string; text: string; url: string; notes: string};
  };
  webdev: {
    view: {val: string; text: string; url: string; notes: string};
  };
  other: {
    view: {notes: string};
  };
}

export interface Resources {
  docs: string[];
  samples: string[];
}

export interface Standards {
  spec: string;
  maturity: {val: number; text: string};
}

export interface Feature {
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
  browsers: Browser;
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
