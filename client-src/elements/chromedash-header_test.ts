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
import {ChromedashHeader} from './chromedash-header.js';
import './chromedash-toast.js';
import {ChromeStatusClient} from '../js-src/cs-client.js';
import sinon from 'sinon';

describe('chromedash-header', () => {
  /* window.csClient and <chromedash-toast> are initialized at _base.html
   * which are not available here, so we initialize them before each test.
   * We also stub out the API calls here so that they return test data. */
  beforeEach(async () => {
    await fixture(html`<chromedash-toast></chromedash-toast>`);
    window.csClient = new ChromeStatusClient('fake_token', 1);
    sinon.stub(window.csClient, 'getPermissions');
  });

  afterEach(() => {
    window.csClient.getPermissions.restore();
  });

  it('invalid server response', async () => {
    const invalidResponse = Promise.reject(
      new Error('Got error response from server')
    );
    window.csClient.getPermissions.returns(invalidResponse);
    const component = await fixture(
      html`<chromedash-header appTitle="Fake Title"></chromedash-header>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashHeader);

    // invalid feature requests would trigger the toast to show message
    const toastEl = document.querySelector('chromedash-toast');
    const toastMsgSpan = toastEl?.shadowRoot?.querySelector('span#msg');
    assert.include(
      toastMsgSpan?.innerHTML,
      'Some errors occurred. Please refresh the page or try again later.'
    );
  });

  it('user is not signed in', async () => {
    window.csClient.getPermissions.returns(Promise.resolve(null));
    const component = await fixture(
      html`<chromedash-header appTitle="Fake Title"></chromedash-header>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashHeader);
    const header = component.renderRoot.querySelector('header');
    assert.exists(header);

    // aside and title exist
    const aside = component.renderRoot.querySelector('aside');
    assert.exists(aside);
    assert.include(aside.innerHTML, 'Fake Title');

    // nav bar exists
    const nav = component.renderRoot.querySelector('nav');
    assert.exists(nav);

    const navInnerHTML = nav.innerHTML;
    // anon has the (slotted in) google sign-in button
    assert.include(navInnerHTML, '<slot>');
  });

  it('user is signed in', async () => {
    window.csClient.getPermissions.returns(
      Promise.resolve({
        can_create_feature: true,
        can_edit: true,
        is_admin: false,
        email: 'example@google.com',
      })
    );
    const component = await fixture(
      html`<chromedash-header appTitle="Fake Title"></chromedash-header>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashHeader);
    const header = component.renderRoot.querySelector('header');
    assert.exists(header);

    // aside and title exist
    const aside = component.renderRoot.querySelector('aside');
    assert.exists(aside);
    assert.include(aside.innerHTML, 'Fake Title');

    // nav bar exists
    const nav = component.renderRoot.querySelector('nav');
    assert.exists(nav);

    const navInnerHTML = nav.innerHTML;
    // logged in users have Settings and Sign Out options
    assert.include(navInnerHTML, 'Settings');
    assert.include(navInnerHTML, 'Sign out');
  });
});
