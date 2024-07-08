import {LitElement, css, html} from 'lit';
import {customElement, property} from 'lit/decorators.js';
import {ref} from 'lit/directives/ref.js';
import {FORM_STYLES} from '../css/forms-css.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {ALL_FIELDS} from './form-field-specs.js';
import {showToastMessage} from './utils.js';

let dialogEl;

export async function openPostIntentDialog(
  featureId: number,
  stageId: number,
  ownerEmails: Array<string>,
  gateId = 0
) {
  if (!dialogEl) {
    dialogEl = document.createElement('chromedash-post-intent-dialog');
    document.body.appendChild(dialogEl);
    dialogEl.featureId = featureId;
    dialogEl.stageId = stageId;
    dialogEl.gateId = gateId;
    dialogEl.ownerEmails = ownerEmails;
    await dialogEl.updateComplete;
  }
  dialogEl.show();
}

@customElement('chromedash-post-intent-dialog')
class ChromedashPostIntentDialog extends LitElement {
  @property({type: Number})
  featureId = 0;
  @property({type: Number})
  stageId = 0;
  @property({type: Number})
  gateId = 0;
  @property({type: Array<string>})
  ownerEmails = [];

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
    const defaultCCEmails = this.ownerEmails.join(',');

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
    console;
    // Make sure that the CC emails input is valid.
    const ccEmailsInput = this.shadowRoot!.querySelector('sl-input');
    if (!ccEmailsInput || ccEmailsInput.hasAttribute('data-user-invalid')) {
      return;
    }
    const submitButton = this.shadowRoot!.querySelector(
      '#submit-intent-button'
    );
    if (submitButton) {
      submitButton.setAttribute('disabled', '');
    }
    window.csClient
      .postIntentToBlinkDev(this.featureId, {
        stage_id: this.stageId,
        gate_id: this.gateId,
        intent_cc_emails: ccEmailsInput?.value?.split(','),
      })
      .then(() => {
        showToastMessage(
          'Intent submitted! Check for your thread on blink-dev shortly.'
        );
        setTimeout(() => {
          window.location.href = `/feature/${this.featureId}`;
        }, 3000);
      })
      .catch(() => {
        showToastMessage(
          'Some errors occurred. Please refresh the page or try again later.'
        );
        if (submitButton) {
          submitButton.removeAttribute('disabled');
        }
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
        id="submit-intent-button"
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
