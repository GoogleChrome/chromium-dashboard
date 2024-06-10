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