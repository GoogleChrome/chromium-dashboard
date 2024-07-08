import {LitElement, css, html} from 'lit';
import {ref} from 'lit/directives/ref.js';
import {FORM_STYLES} from '../css/forms-css.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {ALL_FIELDS} from './form-field-specs.js';
import {showToastMessage} from './utils.js';

let dialogEl;
let currentFeature;
let currentStage;
let currentGate;

export async function openPostIntentDialog(feature, stage, gate) {
  if (!dialogEl) {
    dialogEl = document.createElement('chromedash-post-intent-dialog');
    document.body.appendChild(dialogEl);
    currentFeature = feature;
    currentStage = stage;
    currentGate = gate;
    await dialogEl.updateComplete;
  }
  currentFeature = feature;
  currentStage = stage;
  currentGate = gate;
  dialogEl.show();
}

class ChromedashPostIntentDialog extends LitElement {
  static get properties() {
    return {};
  }

  constructor() {
    super();
  }

  static get styles() {
    return [
      ...SHARED_STYLES,
      ...FORM_STYLES,
      css`
        #prereqs-list li {
          margin-left: 8px;
          margin-bottom: 8px;
          list-style: circle;
        }
        #prereqs-header {
          margin-bottom: 8px;
        }
        #update-button {
          margin-right: 8px;
        }
        .float-right {
          float: right;
        }
        sl-input[data-user-invalid]::part(base) {
          border-color: red;
        }
      `,
    ];
  }

  show() {
    this.shadowRoot!.querySelector('sl-dialog')!.show();
  }

  updateAttributes(el) {
    if (!el) return;

    const attrs = ALL_FIELDS.intent_cc_emails.attrs || {};
    Object.keys(attrs).map(attr => {
      el.setAttribute(attr, attrs[attr]);
    });
  }

  renderIntentCCEmailOption() {
    const fieldInfo = ALL_FIELDS.intent_cc_emails;
    const defaultCCEmails = currentFeature.owner_emails.join(',');
    return html`${fieldInfo.help_text}
      <sl-input
        ${ref(this.updateAttributes)}
        id="id_${fieldInfo.name}"
        size="small"
        autocomplete="off"
        .value=${defaultCCEmails}
        ?required=${fieldInfo.required}
      >
      </sl-input>`;
  }

  submitIntent() {
    // Make sure that the CC emails input is valid.
    const ccEmailsInput = this.shadowRoot!.querySelector('sl-input');
    if (!ccEmailsInput || ccEmailsInput.hasAttribute('data-user-invalid')) {
      return;
    }

    window.csClient
      .postIntentToBlinkDev(currentFeature.id, {
        stage_id: currentStage?.id,
        gate_id: currentGate?.id,
        intent_cc_emails: ccEmailsInput?.value?.split(','),
      })
      .catch(() => {
        showToastMessage(
          'Some errors occurred. Please refresh the page or try again later.'
        );
      });
  }

  renderDialog() {
    return html`<sl-dialog label="Post intent to blink-dev">
      <p>
        This intent will be sent directly to
        <a
          href="https://groups.google.com/a/chromium.org/g/blink-dev"
          target="_blank"
          rel="noopener noreferrer"
          >blink-dev</a
        >.
      </p>
      <br /><br />
      ${this.renderIntentCCEmailOption()}
      <br /><br />
      <sl-button
        class="float-right"
        variant="primary"
        size="small"
        @click=${() => this.submitIntent()}
        >Submit intent</sl-button
      >
    </sl-dialog>`;
  }

  render() {
    return this.renderDialog();
  }
}

customElements.define(
  'chromedash-post-intent-dialog',
  ChromedashPostIntentDialog
);
