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

import {assert, fixture} from '@open-wc/testing';
import {html} from 'lit';
import {ChromedashActivityPage} from './chromedash-activity-page.js';
import {ChromeStatusClient} from '../js-src/cs-client.js';
import sinon from 'sinon';

describe('chromedash-settings-page', () => {
  let getCommentsStub: sinon.SinonStub;
  /* window.csClient is initialized in spa.html
   * which is not available here, so we initialize it before each test.
   * We also stub out the API calls here so that they return test data. */
  beforeEach(async () => {
    window.csClient = new ChromeStatusClient('fake_token', 1);
    getCommentsStub = sinon.stub(window.csClient, 'getComments');
  });

  afterEach(() => {
    getCommentsStub.restore();
  });

  it('can be added to the page before being opened', async () => {
    const component = await fixture(
      html`<chromedash-activity-page></chromedash-activity-page>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashActivityPage);
  });
});
