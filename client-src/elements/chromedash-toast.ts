import {LitElement, css, html} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';
import {customElement, state, property} from 'lit/decorators.js';

const DEFAULT_DURATION = 7000;

@customElement('chromedash-toast')
class ChromedashToast extends LitElement {
  @property({type: String})
  msg = '';

  @property({attribute: false})
  actionLabel = '';

  @state()
  currentTimeout: number | null = null;

  @property({type: Boolean})
  waitingForTransition = false;

 connectedCallback() {
    super.connectedCallback();
    // Initialize the element as a manual popover.
    // 'manual' prevents light-dismiss and Esc key interactions,
    // suitable for a toast that manages its own lifecycle.
    this.popover = 'manual';
  }

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
            opacity 0.3s,
            overlay 0.3s allow-discrete, /* For popover animation */
            display 0.3s allow-discrete; /* For popover animation */
          opacity: 0;
          will-change: opacity, transform;
          -webkit-transform: translateY(100px);
          transform: translateY(100px);
          /* z-index may no longer be needed as popovers are in the top layer,
             but keeping it doesn't harm if specific stacking order with other
             non-popover fixed elements is intended. For now, let's try removing.
             z-index: 3; */
          bottom: 0;
        }

        /* :host([open]) is replaced by :popover-open */
        :host(:popover-open) {
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
      // @starting-style is needed for entry animations of popovers.
      // It defines the style from which the :popover-open state will transition.
      css`
        @starting-style {
          :host(:popover-open) {
            opacity: 0;
            transform: translateY(100px);
          }
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

    if (this.matches(':popover-open')) {
      // triggers the previous toast to slide out
      this.hidePopover();
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
        this.hidePopover();
      }, duration);
    }
    this.showPopover();
  }

  render() {
    return html`
      <span id="msg">${this.msg}</span>
      <a href="#" id="action">${this.actionLabel}</a>
    `;
  }
}
