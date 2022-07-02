import {LitElement, css, html} from 'lit';

export class ChromedashFormField extends LitElement {
  static get properties() {
    return {
      name: {type: String},
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
    const helpText = fieldProps.help_text || '';
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
          ${helpText}
          <slot name="help" class="helptext"></slot>
        </td>
      </tr>`;
  }
}

customElements.define('chromedash-form-field', ChromedashFormField);

// Map of specifications for all form fields.
// Actually, this includes only fields for which we have migrated the help_text from the guideforms.py specifications.
// TODO:
//   * Finish migrating remaining fields.
//   * Migrate other properties.
//   * Move to its own file.
const ALL_FIELDS = {
  'name': {
    help_text: html`
      Capitalize only the first letter and the beginnings of proper nouns.
      <a target="_blank" 
        href="https://github.com/GoogleChrome/chromium-dashboard/wiki/EditingHelp#feature-name">Learn more</a>
      <a target="_blank" 
        href="https://github.com/GoogleChrome/chromium-dashboard/wiki/EditingHelp#feature-name-example">Example</a>
    `},

  'summary': {
    help_text: html`
      NOTE: Text in the beta release post, the enterprise release notes, 
      and other external sources will be based on this text.

      Begin with one line explaining what the feature does. Add one or two 
      lines explaining how this feature helps developers. Avoid language such 
      as "a new feature". They all are or have been new features.

      Write it from a web developer's point of view.
      Follow the example link below for more guidance.<br>
      <a target="_blank" 
          href="https://github.com/GoogleChrome/chromium-dashboard/wiki/EditingHelp#summary-example">
        Guidelines and example</a>.`,
  },

  'owner': {
    help_text: html`
      Comma separated list of full email addresses. Prefer @chromium.org.`,
  },

  'unlisted': {
    help_text: html`
      Check this box for draft features that should not appear 
      in the feature list. Anyone with the link will be able to 
      view the feature on the detail page.`,
  },

  'blink_components': {
    help_text: html`
      Select the most specific component. If unsure, leave as "Blink".`,
  },

  'category': {
    help_text: html`
      Select the most specific category. If unsure, leave as "Miscellaneous".`,
  },

  'feature_type': {
    help_text: html`
      Select the feature type.`,
  },

  'intent_stage': {
    help_text: html`
      Select the appropriate process stage.`,
  },

  'search_tags': {
    help_text: html`
      Comma separated keywords used only in search.`,
  },

  'impl_status_chrome': {
    help_text: html`
      Implementation status in Chromium.`,
  },

  'bug_url': {
    help_text: html`
      Tracking bug url (https://bugs.chromium.org/...). This bug 
      should have "Type=Feature" set and be world readable. 
      Note: This field only accepts one URL.`,
  },

  'launch_bug_url': {
    help_text: html`
      Launch bug url (https://bugs.chromium.org/...) to track launch 
      approvals. 
      <a target="_blank" 
          href="https://bugs.chromium.org/p/chromium/issues/entry?template=Chrome+Launch+Feature">
        Create launch bug</a>.`,
  },

  'motivation': {
    help_text: html`
      Explain why the web needs this change. It may be useful 
      to describe what web developers are forced to do without 
      it. When possible, add links to your explainer 
      backing up your claims. 
      <a target="_blank" 
          href="https://github.com/GoogleChrome/chromium-dashboard/wiki/EditingHelp#motivation-example">
        Example</a>.`,
  },
};
