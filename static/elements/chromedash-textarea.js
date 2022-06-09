
import SlTextarea from '@shoelace-style/shoelace/dist/components/textarea/textarea.js';

class ChromedashTextarea extends SlTextarea {
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
  }

  updated() {
    if (!this.input) {
      return;
    }
    const value = this.input.value;

    const customCheckValidity = () => {
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
      // Otherwise, assume it is valid.
      return true;
    };

    const invalidMsg = customCheckValidity() ? '' : 'invalid';
    this.setCustomValidity(invalidMsg);
  }
}

customElements.define('chromedash-textarea', ChromedashTextarea);
