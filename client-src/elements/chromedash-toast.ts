import {LitElement, css, html} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';
import {customElement, state, property} from 'lit/decorators.js';

const DEFAULT_DURATION = 7000;

@customElement('chromedash-toast')
class ChromedashToast extends LitElement {
  @property({type: String})
  msg = '';

  @property({type: Boolean, reflect: true})
  open = false;

  @property({attribute: false})
  actionLabel = '';

  @state()
  currentTimeout: number | null = null;

  @property({type: Boolean})
  waitingForTransition = false;

  static get styles() {
    return [
      ...SHARED_STYLES,
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
          transition:
            transform 0.3s,
            opacity 0.3s;
          opacity: 0;
          will-change: opacity, transform;
          -webkit-transform: translateY(100px);
          transform: translateY(100px);
          z-index: 3;
          bottom: 0;
        }

        :host([open]) {
          opacity: 1;
          transform: translateY(-32px);
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
      `,
    ];
  }

  showMessage(
    msg: string,
    optAction: string,
    optTapHandler: () => void,
    optDuration: number
  ) {
    if (this.waitingForTransition) return;

    this.msg = msg;
    this.actionLabel = optAction;

    if (optTapHandler) {
      const action = this.shadowRoot!.querySelector('#action');
      if (action) {
        action.addEventListener(
          'click',
          e => {
            e.preventDefault();
            optTapHandler();
          },
          {once: true}
        );
      }
    }

    if (this.open) {
      // triggers the previous toast to slide out
      this.open = false;
      this.waitingForTransition = true;
      if (this.currentTimeout !== null) {
        clearTimeout(this.currentTimeout);
      }
      // Don't show the new toast until the transition is over
      // (wait for the previous toast to be completely gone)
      this.addEventListener(
        'transitionend',
        () => {
          this.show(optDuration);
          this.waitingForTransition = false;
        },
        {once: true}
      );
    } else {
      this.show(optDuration);
    }
  }

  show(optDuration) {
    const duration = optDuration || DEFAULT_DURATION;
    if (duration > 0) {
      this.currentTimeout = window.setTimeout(() => {
        this.open = false;
      }, duration);
    }
    this.open = true;
  }

  render() {
    return html`
      <span id="msg">${this.msg}</span>
      <a href="#" id="action">${this.actionLabel}</a>
    `;
  }
}
