import {LitElement, css, html} from 'lit-element';

class ChromedashCallout extends LitElement {
  static get properties() {
    return {
      signedin: {type: Boolean},
      targetid: {type: String},
      // TODO(jrobbins): Support sides other than "south".
      side: {type: String}, // "north", "south", "east", or "west"
      hidden: {type: Boolean},
      top: {type: Number},
      left: {type: Number},
      cue: {type: String}, // String to send to the server when dismissed.
      dismissedcues: {attribute: false},
    };
  }

  constructor() {
    super();
    this.side = 'south';
    this.hidden = true;
    this.top = 0;
    this.left = 0;
    this.signedin = false;
    this.dismissedcues = [];
  }

  connectedCallback() {
    super.connectedCallback();
    if (this.dismissedcues.includes(this.cue)) {
      // Don't show the cue because the user has already dismissed it.
      return;
    }
    let targetEl = this.parentNode.querySelector('#' + this.targetid);
    if (targetEl) {
      this.attach(targetEl);
    } else {
      console.log('Callout target not found: #' + this.targetid);
    }
  }

  static get styles() {
    return css`
      :host {
        /* TODO(jrobins): Put this into a global theme.css file. */
        --blue-900: #174EA6;

        --callout-bg-color: var(--blue-900);
        --callout-text-color: white;
      }
      #bubble {
        position: absolute;
        display: inline-block;
        background: var(--callout-bg-color);
        border-radius: 8px;
        padding: 8px;
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
        top: 0;
        left: 40px;
        width: 0;
        height: 0;
        border-bottom-color: var(--callout-bg-color);
        border-top: 0;
        margin-left: -20px;
        margin-top: -20px;
     }
     #closebox {
       float: right;
       margin-left: 8px;
     }
    `;
  }

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

  attach(el) {
    if (this.side == 'south') {
      let targetBot = this.contentOffsetTop(el) + el.offsetHeight;
      this.top = targetBot + 20;
      this.left = Math.max(this.contentOffsetLeft(el) - 20, 0);
    }
    /* TODO(jrobbins): Implement support for other sides. */
    this.hidden = false;
  }

  dismiss() {
    this.hidden = true;
    if (this.signedin) {
      window.CuesService.dismissCue(this.cue);
    }
  }

  render() {
    return html`
      <div id="bubble" class="${this.side}" ?hidden=${this.hidden}
          style="top:${this.top}px; left:${this.left}px;">
        <iron-icon id="closebox"
          icon="chromestatus:close" @click=${this.dismiss}></iron-icon>
        <div style="margin: 4px">
          <slot></slot>
        </div>
      </div>
    `;
  }
}

customElements.define('chromedash-callout', ChromedashCallout);
