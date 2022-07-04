import {LitElement, html} from 'lit';


class ChromedashFooter extends LitElement {
  render() {
    // TODO: Create a precomiled main css file and import it instead of inlining it here
    return html`
      <link rel="stylesheet" href="/static/css/main.css">
      <footer>
        <div>
          <a href="https://github.com/GoogleChrome/chromium-dashboard/wiki/"
            target="_blank" rel="noopener">Help</a>
          <a href="https://groups.google.com/a/chromium.org/forum/#!newtopic/blink-dev"
            target="_blank" rel="noopener">Discuss</a>
          <a href="https://github.com/GoogleChrome/chromium-dashboard/issues"
            target="_blank" rel="noopener">File an issue</a>
          <a href="https://policies.google.com/privacy"
            target="_blank" rel="noopener">Privacy</a>
        </div>
      </footer>
    `;
  }
}

customElements.define('chromedash-footer', ChromedashFooter);
