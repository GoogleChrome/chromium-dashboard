// TODO Remove this once the shoelace fix is part of a new shoelace version.
// See https://github.com/shoelace-style/shoelace/commit/624a8bbe71e59ae6255730e34d71e0b13d5ecf90

import SlSelect from '@shoelace-style/shoelace/dist/components/select/select.js';

export class ChromedashSelect extends SlSelect {
  resizeMenu() {
    this.menu.style.width = `${this.control.clientWidth}px`;
    requestAnimationFrame(() => this.dropdown.reposition());
  }
}

customElements.define('chromedash-select', ChromedashSelect);
