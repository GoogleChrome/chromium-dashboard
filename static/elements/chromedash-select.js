
import SlSelect from '@shoelace-style/shoelace/dist/components/select/select.js';

export class ChromedashSelect extends SlSelect {
  resizeMenu() {
    this.menu.style.width = `${this.control.clientWidth}px`;
    requestAnimationFrame(() => this.dropdown.reposition());
  }
}

customElements.define('chromedash-select', ChromedashSelect);
