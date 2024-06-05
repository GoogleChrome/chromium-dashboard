/** Represents an external organization that reviews Chromium changes. Currently the W3C TAG,
 * Firefox, and Safari. */
export class ExternalReviewer {
    /** Finds reviewer information based on their github repo name.
     *
     * @param {string} repo Github repository name in the form 'org/name'.
     * @returns {ExternalReviewer | undefined} undefined if the repo doesn't hold external
     * reviewers.
     */
    static get(repo: string): ExternalReviewer | undefined;
    /** @private
     * @param {string} icon
     * @param {Record<string, LabelInfo>} labels
     */
    private constructor();
    /** Finds information about an issue label for this external reviewer.
     * @param {string} name
     * @typedef {{
     *   description: string,
     *   variant: 'primary' | 'success' | 'neutral' | 'warning' | 'danger',
     * }} LabelInfo
     * @returns {LabelInfo}
     */
    label(name: string): {
        description: string;
        variant: 'primary' | 'success' | 'neutral' | 'warning' | 'danger';
    };
    /** @type {string} @readonly */
    readonly icon: string;
    /** @type {Record<string, LabelInfo>} */
    _labels: Record<string, {
        description: string;
        variant: 'primary' | 'success' | 'neutral' | 'warning' | 'danger';
    }>;
}
