import {LitElement, css, html} from 'lit';
import {ifDefined} from 'lit/directives/if-defined.js';
import {live} from 'lit/directives/live.js';
import {SHARED_STYLES} from '../sass/shared-css.js';

export class ChromedashCheckbox extends LitElement {
  static get properties() {
    return {
      id: {type: String},
      name: {type: String},
      label: {type: String},
      class: {type: String},
      checked: {type: Boolean},
      disabled: {type: Boolean},
      required: {type: Boolean},
      value: {type: String},
    };
  }

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        :host sl-checkbox::part(label) {
            font-size: var(--sl-input-font-size-small);
        }
    `];
  }

  render() {
    return html`
    <sl-checkbox
      id=${ifDefined(this.id)}
      name=${ifDefined(this.name)}
      class=${ifDefined(this.class)}
      size="small"
      .checked=${live(this.checked)}
      .disabled=${this.disabled}
      .required=${this.required}
      value=${ifDefined(this.value)}
      >
      ${this.label}
    </sl-checkbox>`;
  }
}

customElements.define('chromedash-checkbox', ChromedashCheckbox);

