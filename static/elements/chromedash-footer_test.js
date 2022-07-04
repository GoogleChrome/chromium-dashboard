import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashFooter} from './chromedash-footer';

describe('chromedash-footer', () => {
  it('renders with no data', async () => {
    const component = await fixture(
      html`<chromedash-footer></chromedash-footer>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashFooter);
    const footer = component.shadowRoot.querySelector('footer');
    assert.exists(footer);

    const links = [
      'https://github.com/GoogleChrome/chromium-dashboard/wiki/',
      'https://groups.google.com/a/chromium.org/forum/#!newtopic/blink-dev',
      'https://github.com/GoogleChrome/chromium-dashboard/issues',
      'https://policies.google.com/privacy',
    ];

    // all footer links exist and are clickable
    links.map((link) => assert.include(footer.innerHTML, `href="${link}"`));
  });
});
