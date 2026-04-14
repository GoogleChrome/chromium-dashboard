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

import './chromedash-toast.js';
import {html} from 'lit';
import {ChromedashAdminBlinkPage} from './chromedash-admin-blink-page.js';
import {assert, fixture} from '@open-wc/testing';
import sinon, {SinonStubbedInstance} from 'sinon';
import {ComponentsUsersResponse, DefaultApi} from 'chromestatus-openapi';
describe('chromedash-admin-blink-page', () => {
  let csOpenApiClientStub: SinonStubbedInstance<DefaultApi>;
  beforeEach(async () => {
    await fixture(html`<chromedash-toast></chromedash-toast>`);
  });
  it('render with no data', async () => {
    csOpenApiClientStub = sinon.createStubInstance(DefaultApi);
    csOpenApiClientStub.listComponentUsers.rejects(
      new Error('Got error response from server')
    );
    window.csOpenApiClient = csOpenApiClientStub;

    const component = await fixture(
      html`<chromedash-admin-blink-page></chromedash-admin-blink-page>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashAdminBlinkPage);

    // error response would trigger the toast to show message
    const toastEl = document.querySelector('chromedash-toast');
    const toastMsgSpan = toastEl!.shadowRoot!.querySelector('span#msg');
    assert.include(
      toastMsgSpan!.innerHTML,
      'Some errors occurred. Please refresh the page or try again later.'
    );
  });

  it('render with fake data', async () => {
    /** @type {import('chromestatus-openapi').ComponentsUsersResponse} */
    const response: ComponentsUsersResponse = {
      users: [{id: 0, name: 'user0', email: 'user0@example.com'}],
      components: [
        {id: '0', name: 'component0', subscriber_ids: [0], owner_ids: [0]},
      ],
    };
    csOpenApiClientStub = sinon.createStubInstance(DefaultApi);
    csOpenApiClientStub.listComponentUsers.resolves(response);
    window.csOpenApiClient = csOpenApiClientStub;

    const component = await fixture(
      html`<chromedash-admin-blink-page></chromedash-admin-blink-page>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashAdminBlinkPage);

    // subheader exists
    const subheaderCountEl =
      component.shadowRoot!.querySelector('#component-count');
    assert.exists(subheaderCountEl);
  });
});
