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
import sinon from 'sinon';
import {ChromedashTimelinePage} from './chromedash-timeline-page.js';
import './chromedash-toast.js';

describe('chromedash-timeline-page', () => {
  /* <chromedash-toast> are initialized at spa.html
   * which are not available here, so we initialize them before each test.
   * We also stub out the API calls here so that they return test data. */
  let fetchStub: sinon.SinonStub;
  beforeEach(async () => {
    await fixture(html`<chromedash-toast></chromedash-toast>`);
    fetchStub = sinon.stub(window, 'fetch');
    // hacky way to stub out google chart load method
    window.google = {
      charts: {
        load: () => {},
        setOnLoadCallback: f => f(),
      },
    };
  });

  afterEach(() => {
    fetchStub.restore();
  });

  it('invalid timeline fetch response', async () => {
    fetchStub.returns(Promise.reject(new Error('No results')));
    const component = await fixture(
      html`<chromedash-timeline-page></chromedash-timeline-page>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashTimelinePage);

    // error response would trigger the toast to show message
    const toastEl = document.querySelector('chromedash-toast');
    const toastMsgSpan = toastEl!.shadowRoot!.querySelector('span#msg');
    assert.include(
      toastMsgSpan!.innerHTML,
      'Some errors occurred. Please refresh the page or try again later.'
    );
  });

  it('valid timeline fetch response', async () => {
    const type = 'feature';
    const view = 'popularity';
    fetchStub.returns(Promise.resolve({}));
    const component = await fixture(
      html`<chromedash-timeline-page .type="${type}" .view="${view}">
      </chromedash-timeline-page>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashTimelinePage);

    // header exists and with the correct link and title
    const subheaderDiv = component.shadowRoot!.querySelector('div#subheader');
    assert.exists(subheaderDiv);
    assert.include(subheaderDiv.innerHTML, `href="/metrics/${type}/${view}"`);
    assert.include(
      subheaderDiv.innerHTML,
      'HTML &amp; JavaScript usage metrics &gt; all features &gt; timeline'
    );

    // chromedash-timeline exists
    const timelineEl = component.shadowRoot!.querySelector(
      'chromedash-timeline'
    );
    assert.exists(timelineEl);
  });
});
