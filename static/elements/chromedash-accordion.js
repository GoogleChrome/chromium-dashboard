import {LitElement, css, html} from 'lit-element';
import '@polymer/iron-icon';
import '@polymer/iron-collapse';

import SHARED_STYLES from '../css/shared.css';

// This implements one section of an accordion widget.  In other words, it is
// just a header that controls one secton on content.

class ChromedashAccordion extends LitElement {
  static get properties() {
    return {
      title: {type: String},
      opened: {type: Boolean, reflect: true},
      focus: {type: Boolean, reflect: false},
    };
  }

  static get styles() {
    return [
      SHARED_STYLES,
      css`
      h3 {
       margin: var(--content-padding-half) 0 0 0;
       background: var(--accordion-background);
       color: var(--accordion-color);
       border-radius: var(--accordion-border-radius);
       padding: var(--content-padding-quarter);
       width: var(--max-content-width);
       cursor: pointer;
      }
    `];
  }

  constructor() {
    super();
    this.opened = false;
    this.addEventListener('focus', ()=>this.focus = true);
    this.addEventListener('focusout', ()=>this.focus = false);
    this.addEventListener('keyup', (e)=>{
      // If the element is not in focus then simply return otherwise toggle
      if (!this.focus) return;
      // Open accordion should happen only by Space and Enter key as mentioned in web.dev
      if (e.code == 'Space' || e.code == 'Enter') this.toggle();
    });
  }

  toggle() {
    this.opened = !this.opened;
    if (this.id) {
      const anchor = this.opened ? this.id : '';
      history.replaceState(null, null, '#' + anchor);
    }
  }

  render() {
    return html`
     <h3 @click=${this.toggle} title="Click to expand" tabindex="0" role="region" aria-expanded=${this.opened}>
       <iron-icon
          icon="chromestatus:${this.opened ? 'expand-less' : 'expand-more'}">
       </iron-icon>
       ${this.title}
     </h3>

     <iron-collapse ?opened=${this.opened}>
       <slot></slot>
     </iron-collapse>
    `;
  }
}

customElements.define(
  'chromedash-accordion', ChromedashAccordion);
