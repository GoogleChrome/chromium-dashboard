import {LitElement, css, html} from 'lit-element';
import '@polymer/iron-icon';

// This is a simplfied version of chops-dialog:
// https://source.chromium.org/chromium/infra/infra/+/main:appengine/monorail/static_src/elements/chops/chops-dialog/chops-dialog.js

class ChromedashDialog extends LitElement {
  static get properties() {
    return {
      heading: {type: String},
      opened: {type: Boolean, reflect: true},
    };
  }

  static get styles() {
    return css`
      :host {
        position: fixed;
        z-index: 9999;
        left: 0;
        top: 0;
        width: 100%;
        height: 100%;
        overflow: auto;
        background-color: rgba(0,0,0,0.4);
        display: flex;
        align-items: center;
        justify-content: center;
      }
      :host(:not([opened])) {
        display: none;
      }
      :host, .dialog::backdrop {
        /* TODO(zhangtiff): Deprecate custom backdrop in favor of native
        * browser backdrop.
        */
        cursor: pointer;
      }
      .dialog {
        background: none;
        border: 0;
        max-width: 90%;
      }
      #heading {
        margin-top: 0;
        font-weight: normal;
      }
      .dialog-content {
        /* This extra div is here because otherwise the browser can't
        * differentiate between a click event that hits the dialog element or
        * its backdrop pseudoelement.
        */
        box-sizing: border-box;
        background: white;
        padding: 1em 16px;
        cursor: default;
        box-shadow: 0px 3px 20px 0px hsla(0, 0%, 0%, 0.4);
        width: var(--dialog-width-param);
        max-width: var(--dialog-max-width-param, 100%);
      }
      #close-icon {
        background: transparent;
        border: 0;
        float: right;
        cursor: pointer;
      }

    `;
  }

  constructor() {
    super();
    this.heading = '';
    this.opened = false;
    this._boundKeydownHandler = this._keydownHandler.bind(this);
  }

  connectedCallback() {
    super.connectedCallback();
    this.addEventListener('click', (evt) => {
      if (!this.opened) return;
      // A click outside the dialog box will close the dialog.
      const clickIsOutsideDialog = !evt.composedPath().find(
        (node) => node.classList && node.classList.contains('dialog-content'),
      );
      if (clickIsOutsideDialog) {
        this.close();
      }
    });
    window.addEventListener('keydown', this._boundKeydownHandler, true);
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    window.removeEventListener('keydown', this._boundKeydownHandler,
      true);
  }

  updated(changedProperties) {
    if (changedProperties.has('opened')) {
      this._openedChanged(this.opened);
    }
  }

  _keydownHandler(event) {
    if (!this.opened) return;
    if (event.key === 'Escape') {
      this.close();
    }
  }

  close() {
    this.opened = false;
  }

  open() {
    this.opened = true;
  }

  _cancelHandler() {
    this.close();
  }

  _openedChanged(opened) {
    const dialog = this.shadowRoot.querySelector('dialog');
    if (!dialog) return;
    if (opened) {
      if (dialog.showModal) {
        dialog.showModal();
      } else {
        dialog.setAttribute('open', 'true');
      }
    } else {
      if (dialog.close) {
        dialog.close();
      } else {
        dialog.setAttribute('open', undefined);
      }
    }
  }

  render() {
    return html`
      <dialog class="dialog" role="dialog" @cancel=${this._cancelHandler}>
        <div class="dialog-content">
          <button id="close-icon" @click=${this.close}>
             <iron-icon icon="chromestatus:close"></iron-icon>
          </button>
          <h2 id="heading">${this.heading}</h2>
          <slot></slot>
        </div>
      </dialog>
    `;
  }
}


customElements.define('chromedash-dialog', ChromedashDialog);
