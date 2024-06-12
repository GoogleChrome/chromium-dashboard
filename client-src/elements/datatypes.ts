//chromedash-timeline
export interface Property {
  [key: string]: any;
  0: number;
  1: string;
}

declare global {
  interface Window {
    google: any;
  }
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
