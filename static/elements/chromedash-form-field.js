import {LitElement, css, html} from 'lit';

export class ChromedashFormField extends LitElement {
  static get properties() {
    return {
      name: {type: String},
      helpText: {type: String},
    };
  }

  static get styles() {
    return [
      css`
        :host {
          display: table-row-group;
        }

        tr[hidden] th,
        tr[hidden] td {
          padding: 0;
        }

        th, td {
          text-align: left;
          vertical-align: top;
        }

        th {
          padding: 12px 10px 5px 0;
        }

        td {
          padding: 6px 10px;
        }

        td:first-of-type {
          width: 60%;
        }

        .helptext {
          display: block;
          font-size: small;
          max-width: 40em;
          margin-top: 2px;
        }

        .errorlist {
          color: red;
        }
      `,
    ];
  }

  render() {
    const fieldProps = ALL_FIELDS[this.name] || {};
    this.helpText = fieldProps.help_text;
    return html`
      <tr>
        <th colspan="2">
          <b>
          <slot name="label"></slot>
          </b>
        </th>
      </tr>
      <tr>
        <td>
          <slot name="field"></slot>
          <slot name="error" class="errorlist"></slot>
        </td>
        <td>
          ${this.helpText}
          <slot name="help" class="helptext"></slot>
        </td>
      </tr>`;
  }
}

customElements.define('chromedash-form-field', ChromedashFormField);

const ALL_FIELDS = {
  'name': {
    help_text: html`
      Override: Capitalize only the first letter and the beginnings of proper nouns.
      <a target="_blank" 
        href="https://github.com/GoogleChrome/chromium-dashboard/wiki/EditingHelp#feature-name">Learn more</a>
      <a target="_blank" 
        href="https://github.com/GoogleChrome/chromium-dashboard/wiki/EditingHelp#feature-name-example">Example</a>
    `},
};
