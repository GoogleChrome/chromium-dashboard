export function enhanceUrl(url: any, featureLinks: any[] | undefined, fallback: any, text: any): import("lit-html").TemplateResult<1>;
export function enhanceAutolink(part: any, featureLinks: any): import("lit-html").TemplateResult<1>;
export const _dateTimeFormat: Intl.DateTimeFormat;
export class ChromedashLink extends LitElement {
    static styles: import("lit").CSSResult[];
    static get properties(): {
        href: {
            type: StringConstructor;
        };
        /** Says to show this element's content as <slot/>: [feature link] even if a feature link is
         * available. If this is false, the content is only shown when no feature link is available.
         */
        showContentAsLabel: {
            type: BooleanConstructor;
        };
        class: {
            type: StringConstructor;
        };
        featureLinks: {
            type: ArrayConstructor;
        };
        _featureLink: {
            state: boolean;
        };
        ignoreHttpErrorCodes: {
            type: ArrayConstructor;
        };
        /** Normally, if there's a feature link, this element displays as a <sl-tag>, and if there
         * isn't, it displays as a normal <a> link. If [alwaysInTag] is set, it always uses the
         * <sl-tag>.
         */
        alwaysInTag: {
            type: BooleanConstructor;
        };
    };
    /** @type {string | undefined} */
    href: string | undefined;
    /** @type {boolean} */
    showContentAsLabel: boolean;
    /** @type {string} */
    class: string;
    /** @type {import("../js-src/cs-client").FeatureLink[]} */
    featureLinks: import("../js-src/cs-client").FeatureLink[];
    /** @type {import ("../js-src/cs-client").FeatureLink | undefined} */
    _featureLink: import("../js-src/cs-client").FeatureLink | undefined;
    /** @type {number[]} */
    ignoreHttpErrorCodes: number[];
    /** @type {boolean} */
    alwaysInTag: boolean;
    willUpdate(changedProperties: any): void;
    fallback(): import("lit-html").TemplateResult<1>;
    withLabel(link: any): any;
    render(): any;
}
import { LitElement } from 'lit';
