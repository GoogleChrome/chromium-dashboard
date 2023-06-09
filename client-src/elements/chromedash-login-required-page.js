import {LitElement, html} from 'lit';

export class ChromedashLoginRequiredPage extends LitElement {
  render() {
    return html`
    <div>
        Please login to see the content of this page.
    </div>
    `;
  }
}

customElements.define('chromedash-login-required-page', ChromedashLoginRequiredPage);
