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
  fileInputRef: Ref<HTMLInputElement> = createRef();

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
  @property({type: Number})
  featureId;

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
    this.dispatchEvent(new CustomEvent('sl-change'));
  }

  handleFileSelected(e: Event) {
    let inputEl: HTMLInputElement = e.target as HTMLInputElement;
    if (inputEl.files?.[0]) {
      const file: File = inputEl.files?.[0];
      window.csClient
        .addAttachment(this.featureId, inputEl.name, file)
        .then(resp => {
          this.value += '\n' + resp.attachment_url;
          this.dispatchEvent(new CustomEvent('sl-change'));
        });
    }
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
    var imgSrc = url;
    if (url.includes('/feature/' + this.featureId + '/attachment/')) {
      imgSrc += '/thumbnail'; // If it an image we serve, try thumbnail.
    }

    return html`
      <a href=${url} target="_blank" style=${styleMap(linkStyles)}>
        <img style=${styleMap(imgStyles)} src=${imgSrc}></img>
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

  renderUploadButton() {
    const buttonContainerStyles = {
      display: 'inline-block',
      margin: 'var(--content-padding-half)',
    };

    return html`
      <input
        ${ref(this.fileInputRef)}
        id="file-field"
        type="file"
        name="screenshots"
        @change=${e => this.handleFileSelected(e)}
        accept="image/png, image/jpeg, image/png, image/wepb, text/plain"
        style="display:none"
      />
      <div style=${styleMap(buttonContainerStyles)}>
        <sl-button
          id="upload-button"
          @click=${e => this.fileInputRef?.value?.click()}
        >
          <sl-icon slot="prefix" name="upload"></sl-icon>
          Upload image
        </sl-button>
        <div>Max size: 1MB</div>
      </div>
    `;
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
      <div>${this.renderThumbnails()} ${this.renderUploadButton()}</div>
    `;
  }

  firstUpdated() {
    this.validate();
  }

  updated() {
    this.validate();
  }
}
