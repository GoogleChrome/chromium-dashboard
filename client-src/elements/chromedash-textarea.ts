import {TemplateResult, html, nothing} from 'lit';
import SlTextarea from '@shoelace-style/shoelace/dist/components/textarea/textarea.js';
import {customElement, property, state} from 'lit/decorators.js';
import {autolink} from './utils.js';

/* eslint-disable TS1238 */
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
  @property({type: Boolean})
  offerMarkdown = false;
  @property({type: Boolean})
  isMarkdown = false;
  @property({type: Number}) // Represents which field this is on the form.
  index = -1;
  // This is the longest string that a cloud ndb StringProperty seems to accept.
  // Fields that accept a URL list can be longer, provided that each individual
  // URL is no more than this length.
  @property({type: Number})
  maxlength = 1400;
  @state()
  showPreview = false;

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

  handleMarkdownChecked(e) {
    this.isMarkdown = Boolean(e.target?.checked);
    if (!this.isMarkdown) {
      this.showPreview = false;
    }
    // Note: The sl-change event continues to propagate to chromedash-form-field.
  }

  handlePreviewChecked(e) {
    this.showPreview = Boolean(e.target?.checked);
    e.stopPropagation();
  }

  render() {
    const editor = super.render();
    if (!this.offerMarkdown) {
      return editor;
    }

    // Since this class subclasses SlTextarea, we need to render (but
    // not display) the content from that class, otherwise there will
    // be errors in validation code.
    const preview = html`
      <div style="display:none">${editor}</div>
      <div
        id="preview"
        style="border:var(--card-border); padding:0 var(--content-padding); min-height:14em; background:var(--table-alternate-background)"
      >
        ${autolink(this.value, [], true)}
      </div>
    `;

    return html`
      ${this.showPreview ? preview : editor}
      <sl-checkbox
        id="use-markdown"
        name="${this.name}_is_markdown"
        ?checked=${this.isMarkdown}
        @sl-change=${this.handleMarkdownChecked}
      >
        Use markdown
      </sl-checkbox>
      <sl-icon-button
        name="info-circle"
        id="info-button"
        title="GitHub flavored markdown docs"
        href="https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax"
        target="_blank"
      ></sl-icon-button>
      ${this.isMarkdown
        ? html` <sl-checkbox
            id="show-preview"
            ?checked=${this.showPreview}
            @sl-change=${this.handlePreviewChecked}
          >
            Preview
          </sl-checkbox>`
        : nothing}
    `;
  }
}
