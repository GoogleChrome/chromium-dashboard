/**
 * Copyright 2026 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import {expect, fixture} from '@open-wc/testing';
import {html} from 'lit';
import './chromedash-vendor-views.js';

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
