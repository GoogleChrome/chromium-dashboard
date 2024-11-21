import {LitElement, css, html, nothing} from 'lit';
import {customElement, property} from 'lit/decorators.js';
import {createRef, ref, Ref} from 'lit/directives/ref.js';
import {styleMap} from 'lit-html/directives/style-map.js';
import {ChromedashTextarea} from './chromedash-textarea.js';
import {URL_REGEX} from './form-field-specs.js';

const DEFAULT_PLACEHOLDER = 'https://...\nhttps://...';
const DEFAULT_SPLIT_PATTERN = String.raw`\s+`;

@customElement('chromedash-attachments')
export class ChromedashAttachments extends LitElement {
  textareaRef: Ref<ChromedashTextarea> = createRef();

  @property({type: String})
  name;
  @property({type: String})
  value;
  @property({type: String})
  pattern;
  @property({type: String})
  chromedash_single_pattern = URL_REGEX;
  @property({type: String})
  chromedash_split_pattern = DEFAULT_SPLIT_PATTERN;

  // Note: Form element components cannot have their own styles.

  // Must render to light DOM, so sl-form-fields work as intended.
  createRenderRoot() {
    return this;
  }

  validate() {
    if (this.textareaRef?.value?.validate) {
      this.textareaRef.value.validate();
    }
  }

  handleFieldUpdated(e) {
    let fieldValue: string = e.target.value;
    this.value = fieldValue;
  }

  renderOneThumbnail(url) {
    if (url == '') {
      return nothing;
    }

    const linkStyles = {
      display: 'inline-block',
      padding: 'var(--content-padding-quarter)',
      margin: 'var(--content-padding-half)',
      border: `2px solid var(--link-color)`,
      cursor: `zoom-in`,
    };
    const imgStyles = {
      maxHeight: '150px',
      maxWidth: '200px',
    };

    return html`
      <a href=${url} target="_blank" style=${styleMap(linkStyles)}>
        <img style=${styleMap(imgStyles)} src=${url}></img>
      </a>
    `;
  }

  renderThumbnails() {
    if (!this.value?.length) {
      return nothing;
    }
    const items = this.value.split(new RegExp(this.chromedash_split_pattern));
    return items.map(url => this.renderOneThumbnail(url));
  }

  render() {
    return html`
      <chromedash-textarea
        ${ref(this.textareaRef)}
        size="small"
        name=${this.name}
        value=${this.value}
        multiple
        placeholder=${DEFAULT_PLACEHOLDER}
        pattern=${this.pattern}
        chromedash_single_pattern=${this.chromedash_single_pattern}
        chromedash_split_pattern=${this.chromedash_split_pattern}
        @sl-change=${this.handleFieldUpdated}
        @keyup=${this.handleFieldUpdated}
      ></chromedash-textarea>
      <div id="thumbnails">${this.renderThumbnails()}</div>
    `;
  }

  firstUpdated() {
    this.validate();
  }

  updated() {
    this.validate();
  }
}
