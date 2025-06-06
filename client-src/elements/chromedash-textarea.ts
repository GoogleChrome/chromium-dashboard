import SlTextarea from '@shoelace-style/shoelace/dist/components/textarea/textarea.js';
import {customElement, property} from 'lit/decorators.js';

@customElement('chromedash-textarea')
export class ChromedashTextarea extends SlTextarea {
  @property({type: Boolean})
  multiple;
  @property({type: String})
  pattern;
  @property({type: String})
  chromedash_single_pattern;
  @property({type: String})
  chromedash_split_pattern;
  @property({type: Number})
  cols = 50;
  @property({type: Number})
  rows = 10;
  // This is the longest string that a cloud ndb StringProperty seems to accept.
  // Fields that accept a URL list can be longer, provided that each individual
  // URL is no more than this length.
  @property({type: Number})
  maxlength = 1400;

  /**
   * Checks whether the value conforms to custom validation constraints.
   * @return true if value is valid.
   */
  customCheckValidity(value: string): boolean {
    if (this.multiple) {
      if (this.chromedash_split_pattern && this.chromedash_single_pattern) {
        const items = value.split(new RegExp(this.chromedash_split_pattern));
        const singleItemRegex = new RegExp(
          '^' + this.chromedash_single_pattern + '$',
          ''
        );
        const valid = items.every(item => {
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
    if (this.input === null) {
      return;
    }
    const invalidMsg = this.customCheckValidity(this.input.value)
      ? ''
      : 'invalid';
    if (this.setCustomValidity) {
      this.setCustomValidity(invalidMsg);
    }
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
