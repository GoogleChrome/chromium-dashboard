import {LitElement, css, html} from 'lit-element';
import SHARED_STYLES from '../css/shared.css';

const DEFAULT_DURATION = 7000;

class ChromedashToast extends LitElement {
  static get properties() {
    return {
      msg: {type: String},
      open: {type: Boolean, reflect: true},
      actionLabel: {attribute: false},
    };
  }

  constructor() {
    super();
    this.msg = '';
    this.actionLabel = '';
    this.open = false;
  }

  static get styles() {
    return [
      SHARED_STYLES,
      css`
      :host {
        display: flex;
        justify-content: space-between;
        position: fixed;
        background: var(--toast-background);
        color: var(--toast-color);
        min-height: 48px;
        min-width: 288px;
        padding: var(--content-padding);
        box-sizing: border-box;
        box-shadow: var(--card-box-shadow);
        border-radius: var(--border-radius);
        margin: var(--content-padding);
        cursor: default;
        transition: transform 0.3s, opacity 0.3s;
        opacity: 0;
        will-change: opacity, transform;
        -webkit-transform: translateY(100px);
        transform: translateY(100px);
        z-index: 3;
        bottom: 0;
      }

      :host([open]) {
        opacity: 1;
        transform: translateY(0px);
      }

      #action {
        text-transform: uppercase;
        text-decoration: none;
        color: var(--toast-action-color);
        font-weight: bold;
      }

      #msg {
        margin-right: var(--content-padding);
      }
    `];
  }

  /**
   * Shows a message in the toast.
   * @method showMessage
   * @param {string} msg Message to show.Notification (event) type.
   * @param {string} optAction Optional action link.
   * @param {function} optTapHandler Optional handler to execute when the
   *     toast action is tapped.
   * @param {Number} optDuration Optional duration to show the toast for.
   *     Use -1 to keep the toast open indefinitely.
   */
  showMessage(msg, optAction, optTapHandler, optDuration) {
    this.msg = msg;
    this.actionLabel = optAction;
    this.shadowRoot.querySelector('#action').addEventListener('click', (e) => {
      e.preventDefault();
      if (optTapHandler) {
        optTapHandler();
      }
    }, {once: true});

    const duration = optDuration || DEFAULT_DURATION;
    if (duration > 0) {
      window.setTimeout(() => {
        this.open = false;
      }, duration);
    }

    this.open = true;
  }

  close() {
    this.open = false;
  }

  render() {
    return html`
      <span id="msg">${this.msg}</span>
      <a href="#" id="action">${this.actionLabel}</a>
    `;
  }
}

customElements.define('chromedash-toast', ChromedashToast);
