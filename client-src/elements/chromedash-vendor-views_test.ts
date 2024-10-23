import {expect, fixture} from '@open-wc/testing';
import {html} from 'lit';
import './chromedash-vendor-views';

it('shows content if no link', async () => {
  const el = await fixture(
    html`<chromedash-vendor-views href="" .featureLinks=${[]}
      >Content</chromedash-vendor-views
    >`
  );
  expect(el).shadowDom.to.equal('<slot></slot>');
});

it('asks for a label if link not standards position', async () => {
  const el = await fixture(
    html`<chromedash-vendor-views
      href="https://bugzilla.mozilla.org/show_bug.cgi?id=1"
      .featureLinks=${[]}
      >Content</chromedash-vendor-views
    >`
  );
  expect(el).shadowDom.to.equal(`<chromedash-link showcontentaslabel
    href="https://bugzilla.mozilla.org/show_bug.cgi?id=1">
      <slot></slot>
    </chromedash-link>`);
});

it('does not request a label for standards positions', async () => {
  const elMozilla = await fixture(
    html`<chromedash-vendor-views
      href="https://github.com/mozilla/standards-positions/issues/766"
      .featureLinks=${[]}
      >Content</chromedash-vendor-views
    >`
  );
  expect(elMozilla).shadowDom.to.equal(`<chromedash-link
    href="https://github.com/mozilla/standards-positions/issues/766">
      <slot></slot>
    </chromedash-link>`);

  const elWebKit = await fixture(
    html`<chromedash-vendor-views
      href="https://github.com/WebKit/standards-positions/issues/294"
      .featureLinks=${[]}
      >Content</chromedash-vendor-views
    >`
  );
  expect(elWebKit).shadowDom.to.equal(`<chromedash-link
    href="https://github.com/WebKit/standards-positions/issues/294">
      <slot></slot>
    </chromedash-link>`);
});
