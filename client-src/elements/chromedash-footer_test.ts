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

import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashFooter} from './chromedash-footer.js';

describe('chromedash-footer', () => {
  it('renders with no data', async () => {
    const component = await fixture(
      html`<chromedash-footer></chromedash-footer>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashFooter);
    const footer = component.renderRoot.querySelector('footer');
    assert.exists(footer);

    const links = [
      'https://github.com/GoogleChrome/chromium-dashboard/wiki/',
      'https://groups.google.com/a/chromium.org/forum/#!newtopic/blink-dev',
      'https://github.com/GoogleChrome/chromium-dashboard/issues',
      'https://policies.google.com/privacy',
    ];

    // all footer links exist and are clickable
    links.map(link => assert.include(footer.innerHTML, `href="${link}"`));
  });
});
