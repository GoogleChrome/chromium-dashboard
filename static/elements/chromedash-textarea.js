
import SlTextarea from '@shoelace-style/shoelace/dist/components/textarea/textarea.js';

class ChromedashTextarea extends SlTextarea {
  static get properties() {
    return {
      ...super.properties,
      chromedash_single_pattern: {type: String},
      chromedash_split_pattern: {type: String},
    };
  }

  constructor() {
    super();
    this.originalCheckValidity = null;
  }

  updated() {
    if (!this.input) {
      return;
    }
    if (!this.originalCheckValidity) {
      // Set up custom validation.
      this.originalCheckValidity = this.input.checkValidity;
      this.input.checkValidity = () => {
        const value = this.input.value;
        // First do default validity check.
        if (this.originalCheckValidity && !this.originalCheckValidity.apply(this.input)) {
          return false;
        }
        // If multiple, then use chrome
        if (this.multiple) {
          if (this.chromedash_split_pattern && this.chromedash_single_pattern) {
            const items = value.split(new RegExp(this.chromedash_split_pattern));
            const singleItemRegex = new RegExp('^' + this.chromedash_single_pattern + '$', '');
            const valid = items.every((item) => {
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
        // Otherwise, it must be valid.
        return true;
      };
    }
  }
}

customElements.define('chromedash-textarea', ChromedashTextarea);
