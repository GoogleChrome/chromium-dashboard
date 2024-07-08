import {LitElement, css, html} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';

let dialogEl;


export async function openPostIntentDialog() {
  if (!dialogEl) {
    dialogEl = document.createElement('chromedash-post-intent-dialog');
    document.body.appendChild(dialogEl);
    await dialogEl.updateComplete;
  }
  dialogEl.show();
}


class ChromedashPostIntentDialog extends LitElement {
  static get properties() {
    return {
    };
  }

  constructor() {
    super();
  }

  static get styles() {
    return [
      ...SHARED_STYLES,
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
      `,
    ];
  }

  show() {
    this.shadowRoot!.querySelector('sl-dialog')!.show();
  }

  renderDialog() {
    return html` <sl-dialog label="Post intent to blink-dev">
      <p>
        TODO(DanielRyanSmith): add confirmation plus CC email selection.
      </p>
    </sl-dialog>`;
  }

  render() {
    return this.renderDialog();
  }
}

customElements.define(
  'chromedash-post-intent-dialog',
  ChromedashPostIntentDialog
);
