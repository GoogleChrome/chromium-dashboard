import {LitElement, css, html} from 'lit';
import {SHARED_STYLES} from '../sass/shared-css.js';

class ChromedashCallout extends LitElement {
  static get properties() {
    return {
      signedIn: {type: Boolean},
      targetId: {type: String},
      // TODO(jrobbins): Support sides other than "south".
      side: {type: String}, // "north", "south", "east", or "west"
      hidden: {type: Boolean},
      top: {type: Number},
      left: {type: Number},
      cue: {type: String}, // String to send to the server when dismissed.
      dismissedCues: {attribute: false, type: Object},
    };
  }

  constructor() {
    super();
    this.side = 'south';
    this.hidden = true;
    this.top = 0;
    this.left = 0;
    this.signedIn = false;
    this.dismissedCues = {};
  }

  connectedCallback() {
    super.connectedCallback();
    if (this.dismissedCues.includes(this.cue)) {
      // Don't show the cue because the user has already dismissed it.
      return;
    }
    try {
      this.attachToTarget(this.parentNode.querySelector('#' + this.targetId));
    } catch (error) {
      console.error('Failed to attach target', error);
    }
  }

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
      #bubble {
        position: absolute;
        display: inline-block;
        background: var(--callout-bg-color);
        border-radius: var(--large-border-radius);
        padding: var(--content-padding-half);
        max-width: 24em;
        color: var(--callout-text-color);
        font-weight: bold;
      }
      #bubble[hidden] {
        display: none;
      }
      #bubble:after {
        content: '';
        position: absolute;
        border: 20px solid transparent;
      }
      /* Bubble will be located on the south side of target element. */
      #bubble.south:after {
        top: -20px;
        left: 20px;
        width: 0;
        height: 0;
        border-bottom-color: var(--callout-bg-color);
        border-top: 0;
     }
     #closebox {
       float: right;
       margin-left: var(--content-padding-half);
       color: var(--light-icon-fill-color);
     }
     #cue-content-container {
       margin: var(--content-padding-quarter);
     }
    `];
  }

  // TODO(jrobbins): Consider using:
  // el.getBoundingClientRect().top + window.scrollY
  // and creating the bubble directly under the document.
  contentOffsetTop(el) {
    let offset = 0;
    while (el.offsetParent && el != this.offsetParent) {
      offset += el.offsetTop;
      el = el.offsetParent;
    }
    return offset;
  }

  contentOffsetLeft(el) {
    let offset = 0;
    while (el.offsetParent && el != this.offsetParent) {
      offset += el.offsetLeft;
      el = el.offsetParent;
    }
    return offset;
  }

  attachToTarget(el) {
    if (this.side == 'south') {
      const targetBottom = this.contentOffsetTop(el) + el.offsetHeight;
      this.top = targetBottom + 20;
      this.left = Math.max(this.contentOffsetLeft(el) - 20, 0);
    }
    /* TODO(jrobbins): Implement support for other sides. */
    this.hidden = false;
  }

  dismiss() {
    this.hidden = true;
    if (this.signedIn) {
      window.csClient.dismissCue(this.cue);
    }
    // Signed out users simply hide this element without storing
    // the fact that the cue was dismissed.
  }

  render() {
    return html`
      <div id="bubble" class="${this.side}" ?hidden=${this.hidden}
          style="top:${this.top}px; left:${this.left}px;">
        <iron-icon id="closebox"
          icon="chromestatus:close" @click=${this.dismiss}></iron-icon>
        <div id="cue-content-container">
          <slot></slot>
        </div>
      </div>
    `;
  }
}

customElements.define('chromedash-callout', ChromedashCallout);
