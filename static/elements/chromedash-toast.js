import {LitElement, html} from 'lit-element';
import style from '../css/elements/chromedash-toast.css';

// Keeps track of the toast currently opened.
let _currentToast = null;

class ChromedashToast extends LitElement {
  static styles = style;

  static get properties() {
    return {
      msg: {type: String},
      open: {type: Boolean, reflect: true},
      actionLabel: {attribute: false},
      duration: {attribute: false}, // The duration in milliseconds to show the toast. -1 or `Infinity`, to disable the toast auto-closing.
    };
  }

  constructor() {
    super();
    this.msg = '';
    this.actionLabel = '';
    this.duration = 7000;
    this.open = false;
  }

  /**
   * Shows a message in the toast.
   * @method showMessage
   * @param {string} msg Message to show.Notification (event) type.
   * @param {string} optAction Optional action link.
   * @param {function} optTapHandler Optional handler to execute when the
   *     toast action is tapped.
   * @param {Number} optDuration Optional duration to show the toast for.
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

    // Override duration just for this toast.
    const originalDuration = this.duration;
    if (typeof optDuration !== 'undefined') {
      this.duration = optDuration;
    }

    this.open = true;

    this.duration = originalDuration; // reset site-wide duration.
  }

  close() {
    this.open = false;
  }

  _openChanged() {
    clearTimeout(this._timerId);

    if (this.open) {
      // Close existing toast if one is showing.
      if (_currentToast && _currentToast !== this) {
        _currentToast.close();
      }
      _currentToast = this;

      if (this.duration >= 0) {
        this._timerId = setTimeout(() => this.close(), this.duration);
      }
    } else if (_currentToast === this) {
      _currentToast = null;
    }
  }

  render() {
    return html`
      <span id="msg">${this.msg}</span>
      <a href="#" id="action">${this.actionLabel}</a>
    `;
  }
}

customElements.define('chromedash-toast', ChromedashToast);
