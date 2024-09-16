import {LitElement, html} from 'lit';
import {customElement} from 'lit/decorators.js';

@customElement('chromedash-login-required-page')
export class ChromedashLoginRequiredPage extends LitElement {
  render() {
    return html` <div>Please login to see the content of this page.</div> `;
  }
}
