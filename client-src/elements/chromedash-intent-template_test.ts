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
import {ChromedashIntentContent} from './chromedash-intent-content.js';

describe('chromedash-intent-content', () => {
  it('renders with fake data', async () => {
    const component = await fixture(
      html`<chromedash-intent-content
        appTitle="Chrome Status Test"
        subject="A fake subject"
        intentBody="<div>A basic intent body</div>"
      >
      </chromedash-intent-content>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashIntentContent);

    const subject = component.renderRoot.querySelector(
      '#email-subject-content'
    ) as HTMLElement;
    const body = component.renderRoot.querySelector(
      '#email-body-content'
    ) as HTMLElement;

    assert.equal(body.innerText, 'A basic intent body');
    assert.equal(subject.innerText, 'A fake subject');
  });
});
