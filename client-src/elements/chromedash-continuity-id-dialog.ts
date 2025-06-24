import {LitElement, css, html} from 'lit';
import {customElement, property, state, query} from 'lit/decorators.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import '@shoelace-style/shoelace/dist/components/button/button.js';
import '@shoelace-style/shoelace/dist/components/dialog/dialog.js';
import '@shoelace-style/shoelace/dist/components/input/input.js';
import '@shoelace-style/shoelace/dist/components/spinner/spinner.js';
import '@shoelace-style/shoelace/dist/components/icon/icon.js';
import {showToastMessage} from './utils.js';

/**
 * Opens the singleton dialog for ID verification.
 * @param featureId The ID of the feature on the page.
 * @param gateId The ID of the gate that the dialog was dispatched from.
 */
export async function openIdVerificationDialog(
  featureId: number,
  gateId: number
) {
  let idVerificationDialogEl = document.querySelector(
    'chromedash-continuity-id-dialog'
  ) as ChromedashIdVerificationDialog;
  // Create the dialog if it doesn't exist
  if (!idVerificationDialogEl) {
    idVerificationDialogEl = document.createElement(
      'chromedash-continuity-id-dialog'
    ) as ChromedashIdVerificationDialog;
    document.body.appendChild(idVerificationDialogEl);
    await idVerificationDialogEl.updateComplete;
  }

  // Configure the dialog with the provided parameters.
  idVerificationDialogEl.featureId = featureId;
  idVerificationDialogEl.gateId = gateId;
  idVerificationDialogEl.reset();

  idVerificationDialogEl.show();
}

type VerificationState = 'idle' | 'loading' | 'success' | 'error';

@customElement('chromedash-continuity-id-dialog')
export class ChromedashIdVerificationDialog extends LitElement {
  @query('sl-dialog')
  dialog;

  @state()
  _idValue = '';

  @state()
  _verificationState: VerificationState = 'idle';

  @state()
  _verificationMessage: string = '';

  @state()
  _canCheck: boolean = false;

  @state()
  _reload = () => location.reload();

  @property({type: Number})
  featureId = 0;

  @property({type: Number})
  gateId = 0;

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        sl-dialog::part(panel) {
          max-width: 720px;
          width: 90vw;
        }

        p {
          line-height: 1.6;
          margin: 0 0 20px 0;
        }
        p a {
          text-decoration: none;
          font-weight: 500;
        }
        p a:hover {
          text-decoration: underline;
        }

        .controls {
          display: flex;
          gap: 16px;
          align-items: anchor-center;
          margin-bottom: 4px;
        }
        sl-input {
          flex-grow: 1;
        }
        sl-input::part(form-control-help-text) {
          transition: all 0.3s ease;
          /* Prevents layout shift when text appears */
          min-height: 1.2rem;
        }
        .success-message::part(form-control-help-text) {
          color: var(--md-green-600);
        }
        .error-message::part(form-control-help-text) {
          color: var(--md-red-600);
        }

        .footer-actions {
          display: flex;
          justify-content: space-between;
          align-items: center;
          width: 100%;
          border-top: 1px solid var(--md-gray-300);
          padding-top: 12px;
          margin-top: 24px;
        }
      `,
    ];
  }

  connectedCallback() {
    super.connectedCallback();
    this.reset();
  }

  /** Resets the component to its initial state. */
  reset() {
    this._idValue = '';
    this._verificationState = 'idle';
    this._verificationMessage = 'Please enter an existing Continuity ID.';
    this._canCheck = false;
  }

  show() {
    this.reset();
    this.dialog.show();
  }

  hide() {
    this.dialog.hide();
  }

  async onSubmit(usingContinuityId: boolean) {
    if (usingContinuityId && isNaN(Number(this._idValue))) {
      this._verificationState = 'error';
      this._verificationMessage = 'Continuity ID must be a valid number.';
      return;
    }
    this._verificationState = 'loading';
    this._verificationMessage = 'Verifying...';
    let continuityId: number | null = null;
    if (usingContinuityId) {
      continuityId = parseInt(this._idValue);
    }
    try {
      const resp = await window.csClient.createSecurityLaunchIssue(
        this.featureId,
        this.gateId,
        continuityId
      );
      if (resp.failed_reason) {
        this._verificationState = 'error';
        this._verificationMessage = resp.failed_reason;
      } else {
        // TODO(DanielRyanSmith): Add a more specific success message here.
        // Maybe navigate to the new launch issue?
        showToastMessage('Success!');
        this._verificationState = 'success';
        this._verificationMessage = 'Verification success!';
        setTimeout(() => {
          this.dialog.hide();
          this._reload();
        }, 3000);
      }
    } catch (error) {
      console.error(error);
      this._verificationState = 'error';
      this._verificationMessage =
        'Some errors occurred. Please refresh the page or try again later.';
      showToastMessage(
        'Some errors occurred. Please refresh the page or try again later.'
      );
    }
  }

  private _handleInput(e: Event) {
    const newValue = (e.target as HTMLInputElement).value;
    // If user types, reset previous success/error states.
    if (
      this._verificationState === 'success' ||
      this._verificationState === 'error'
    ) {
      this._verificationState = 'idle';
      this._verificationMessage = 'Please enter a Continuity ID.';
    }
    this._idValue = newValue;
    this._canCheck = this._idValue.trim().length > 0; // Simple validation: not empty
  }

  private async _handleSubmitClick() {
    await this.onSubmit(true);
  }

  private async _handleSubmitClickNoContinuityId() {
    await this.onSubmit(false);
  }

  private _renderSuffixIcon() {
    switch (this._verificationState) {
      case 'loading':
        return html`<sl-spinner slot="suffix"></sl-spinner>`;
      case 'success':
        return html`<sl-icon
          library="material"
          slot="suffix"
          name="check_circle_outline"
          style="color: var(--md-green-600);"
        ></sl-icon>`;
      case 'error':
        return html`<sl-icon
          library="material"
          slot="suffix"
          name="highlight_off"
          style="color: var(--md-red-600);"
        ></sl-icon>`;
      default:
        return html``;
    }
  }

  render() {
    const isVerifying = this._verificationState === 'loading';
    const isVerified = this._verificationState === 'success';

    let helpTextClass = '';
    if (this._verificationState === 'success') {
      helpTextClass = 'success-message';
    } else if (this._verificationState === 'error') {
      helpTextClass = 'error-message';
    }

    let verificationButtonText = 'Verify and Submit';
    if (isVerifying) {
      verificationButtonText = 'Verifying...';
    }
    if (isVerified) {
      verificationButtonText = 'Verified!';
    }

    return html`
      <sl-dialog
        label="Does Chrome Security already know about this specific feature?"
        class="dialog"
        @sl-hide=${this.reset}
      >
        <p>
          If so, we can assign it to the same folks who you've already been
          chatting with! Please provide the 'Continuity ID' if you have one. If
          you're not sure, please check
          <a
            href="https://g-issues.chromium.org/issues?q=componentid:1542395%20status:open"
            target="_blank"
            rel="noopener"
            >go/chrome-security-tracking-bugs</a
          >
          to look for your project by title! If you sent a PRD to PRD-reviews or
          reached out for consultation, you surely have one! If you don't have
          one, no worries - leave this field blank and we'll create one for you!
        </p>

        <div class="controls">
          <sl-input
            label="Continuity ID"
            .value=${this._idValue}
            @sl-input=${this._handleInput}
            .helpText=${this._verificationMessage}
            class=${helpTextClass}
            ?disabled=${isVerifying || isVerified}
            aria-describedby="helper-text"
          >
            ${this._renderSuffixIcon()}
          </sl-input>
          <sl-button
            variant="primary"
            outline
            @click=${this._handleSubmitClick}
            ?disabled=${!this._canCheck || isVerifying || isVerified}
            ?loading=${isVerifying}
          >
            ${verificationButtonText}
          </sl-button>
        </div>

        <div class="footer-actions">
          <sl-button
            class="no-id-btn"
            variant="default"
            @click=${this._handleSubmitClickNoContinuityId}
            ?disabled=${this._canCheck}
          >
            I don't have a Continuity ID
          </sl-button>
        </div>
      </sl-dialog>
    `;
  }
}
