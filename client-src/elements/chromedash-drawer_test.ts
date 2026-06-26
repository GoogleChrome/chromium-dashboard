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
import {ChromedashDrawer} from './chromedash-drawer.js';
import './chromedash-toast.js';
import {ChromeStatusClient} from '../js-src/cs-client.js';
import sinon, {SinonStub} from 'sinon';

describe('chromedash-drawer', () => {
  /* window.csClient and <chromedash-toast> are initialized at _base.html
   * which are not available here, so we initialize them before each test.
   * We also stub out the API calls here so that they return test data. */
  let getPermissionsStub: SinonStub;
  let getChannelsStub: SinonStub;
  beforeEach(async () => {
    await fixture(html`<chromedash-toast></chromedash-toast>`);
    window.csClient = new ChromeStatusClient('fake_token', 1);
    getPermissionsStub = sinon.stub(window.csClient, 'getPermissions');
    getChannelsStub = sinon.stub(window.csClient, 'getChannels').resolves({
      stable: {version: 125},
      beta: {version: 126},
      dev: {version: 127},
    });
  });

  afterEach(() => {
    getPermissionsStub.restore();
    getChannelsStub.restore();
  });

  it('user is not signed in', async () => {
    getPermissionsStub.returns(Promise.resolve(null));
    const component = await fixture(
      html`<chromedash-drawer appTitle="Fake Title"></chromedash-drawer>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashDrawer);
    const nav = component.shadowRoot!.querySelector('nav');
    assert.exists(nav);

    // nav bar has correct tabs
    const navInnerHTML = nav.innerHTML;
    assert.include(navInnerHTML, 'href="/roadmap"');
    assert.include(navInnerHTML, 'href="/features"');
    assert.include(navInnerHTML, 'href="/metrics/css/popularity"');
    assert.include(navInnerHTML, 'href="/metrics/feature/popularity"');

    // anon shouldn't have the myfeatures tab
    assert.notInclude(navInnerHTML, 'href="/myfeatures');
  });

  it('user is signed in', async () => {
    getPermissionsStub.returns(
      Promise.resolve({
        can_create_feature: true,
        can_edit: true,
        is_admin: false,
        email: 'example@google.com',
      })
    );
    const component = await fixture(
      html`<chromedash-drawer appTitle="Fake Title"></chromedash-drawer>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashDrawer);

    // nav bar exists
    const nav = component.shadowRoot!.querySelector('nav');
    assert.exists(nav);

    const navInnerHTML = nav.innerHTML;
    assert.include(navInnerHTML, 'href="/roadmap"');
    assert.include(navInnerHTML, 'href="/features"');
    assert.include(navInnerHTML, 'href="/metrics/css/popularity"');
    assert.include(navInnerHTML, 'href="/metrics/feature/popularity"');
    assert.include(navInnerHTML, 'href="/myfeatures');
  });

  it('renders release reviews pending badge for editors', async () => {
    getPermissionsStub.returns(
      Promise.resolve({
        can_create_feature: true,
        can_edit: true,
        is_admin: true,
        can_review_release_notes: true,
        email: 'editor@google.com',
      })
    );
    const getCountStub = sinon
      .stub(window.csClient, 'getPendingReviewsCount')
      .resolves({count: 3});

    const component = (await fixture(
      html`<chromedash-drawer appTitle="Fake Title"></chromedash-drawer>`
    )) as ChromedashDrawer;
    assert.exists(component);
    assert.instanceOf(component, ChromedashDrawer);

    // Wait for async calls and rendering
    await component.updateComplete;

    const nav = component.shadowRoot!.querySelector('nav');
    assert.exists(nav);

    const navInnerHTML = nav.innerHTML;
    assert.include(navInnerHTML, 'href="/review-release-notes"');
    assert.include(navInnerHTML, 'Review Release Notes');
    assert.include(navInnerHTML, '<sl-badge variant="danger" pill');
    assert.include(navInnerHTML, '>3</sl-badge>');

    getCountStub.restore();
  });

  it('renders dynamic channel badges for release notes when channels are loaded', async () => {
    getPermissionsStub.returns(Promise.resolve(null)); // Anonymous user
    const component = (await fixture(
      html`<chromedash-drawer appTitle="Fake Title"></chromedash-drawer>`
    )) as ChromedashDrawer;
    assert.exists(component);
    
    // Wait for async connectedCallback calls to resolve and update
    await component.updateComplete;

    const nav = component.shadowRoot!.querySelector('nav');
    assert.exists(nav);

    // Assert the main Release Notes link is rendered
    const releaseNotesLink = nav.querySelector('a[href="/release-notes"]');
    assert.exists(releaseNotesLink);
    assert.include(releaseNotesLink.textContent, 'Release Notes');

    // Assert the badge elements are rendered with correct versions
    const stableBadge = nav.querySelector('a[href="/release-notes/125"] sl-badge[variant="success"]');
    assert.exists(stableBadge);
    assert.include(stableBadge.textContent, '125');

    const betaBadge = nav.querySelector('a[href="/release-notes/126"] sl-badge[variant="warning"]');
    assert.exists(betaBadge);
    assert.include(betaBadge.textContent, '126');

    const devBadge = nav.querySelector('a[href="/release-notes/127"] sl-badge[variant="primary"]');
    assert.exists(devBadge);
    assert.include(devBadge.textContent, '127');
  });
});
