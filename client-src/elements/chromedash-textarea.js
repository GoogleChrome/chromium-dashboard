
import SlTextarea from '@shoelace-style/shoelace/dist/components/textarea/textarea.js';

export class ChromedashTextarea extends SlTextarea {
  static get properties() {
    return {
      ...super.properties,
      multiple: {type: Boolean},
      pattern: {type: String},
      chromedash_single_pattern: {type: String},
      chromedash_split_pattern: {type: String},
    };
  }

  constructor() {
    super();
    this.cols = 50;
    this.rows = 10;

    // This is the longest string that a cloud ndb StringProperty seems to accept.
    // Fields that accept a URL list can be longer, provided that each individual
    // URL is no more than this length.
    this.maxlength = 1400;
  }

  /**
   * Checks whether the value conforms to custom validation constraints.
   * @param {string} value
   * @return {boolean} Return true if value is valid.
   */
  customCheckValidity(value) {
    if (this.multiple) {
      if (this.chromedash_split_pattern &&
          this.chromedash_single_pattern) {
        const items = value.split(new RegExp(this.chromedash_split_pattern));
        const singleItemRegex =
            new RegExp('^' + this.chromedash_single_pattern + '$', '');
        const valid = items.every((item) => {
          if (!item) {
            // ignore empty items
            return true;
          }
          const itemValid = singleItemRegex.test(item);
          return itemValid;
        });
        if (!valid) {
          return false;
        }
      }
    }
    // If there is a pattern, and the value doesn't match the pattern, then fail.
    // This applies regardless whether this.multiple is true.
    if (this.pattern) {
      const valueRegex = new RegExp('^' + this.pattern + '$', '');
      return valueRegex.test(value);
    }
    // Otherwise, assume it is valid.  What about required? disabled?
    return true;
  }

  validate() {
    const invalidMsg = this.customCheckValidity(this.input.value) ? '' : 'invalid';
    this.setCustomValidity(invalidMsg);
  }

  firstUpdated() {
    this.validate();
  }

  updated() {
    if (!this.input) {
      return;
    }
    this.validate();
  }
}

customElements.define('chromedash-textarea', ChromedashTextarea);
