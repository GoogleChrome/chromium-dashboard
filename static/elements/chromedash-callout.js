import {LitElement, css, html} from 'lit-element';

class ChromedashCallout extends LitElement {
  static get properties() {
    return {
      targetEl: {type: Element},
      // TODO(jrobbins): Support sides other than "south".
      side: {type: String}, // "north", "south", "east", or "west"
      hidden: {type: Boolean},
    };
  }

  constructor() {
    super();
    this.side = 'south';
    this.hidden = false;
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
        position: relative;
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
      /* Bubble will be located on the south side of targetEl. */
      #bubble.south:after {
        top: 0;
        left: 50%;
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

  close() {
    this.hidden = true;
  }

  render() {
    return html`
      <div id="bubble" class="${this.side}" ?hidden=${this.hidden}>
        <iron-icon id="closebox"
          icon="chromestatus:close" @click=${this.close}></iron-icon>
        <div style="margin: 4px">
          <slot></slot>
        </div>
      </div>
    `;
  }
}

customElements.define('chromedash-callout', ChromedashCallout);
