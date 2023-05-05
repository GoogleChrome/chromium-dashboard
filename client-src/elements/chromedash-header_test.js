import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashHeader} from './chromedash-header';
import './chromedash-toast';
import '../js-src/cs-client';
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
    const invalidResponse = Promise.reject(new Error('Got error response from server'));
    window.csClient.getPermissions.returns(invalidResponse);
    const component = await fixture(
      html`<chromedash-header appTitle="Fake Title"></chromedash-header>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashHeader);

    // invalid feature requests would trigger the toast to show message
    const toastEl = document.querySelector('chromedash-toast');
    const toastMsgSpan = toastEl.shadowRoot.querySelector('span#msg');
    assert.include(toastMsgSpan.innerHTML,
      'Some errors occurred. Please refresh the page or try again later.');
  });

  it('user is not signed in', async () => {
    window.csClient.getPermissions.returns(Promise.resolve(null));
    const component = await fixture(
      html`<chromedash-header appTitle="Fake Title"></chromedash-header>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashHeader);
    const header = component.shadowRoot.querySelector('header');
    assert.exists(header);

    // aside and title exist
    const aside = component.shadowRoot.querySelector('aside');
    assert.exists(aside);
    assert.include(aside.innerHTML, 'Fake Title');

    // nav bar exists
    const nav = component.shadowRoot.querySelector('nav');
    assert.exists(nav);

    // nav bar has correct tabs
    const navInnerHTML = nav.innerHTML;
    assert.include(navInnerHTML, 'href="/roadmap"');
    assert.include(navInnerHTML, 'href="/features"');
    assert.include(navInnerHTML, 'href="/metrics/css/popularity"');
    assert.include(navInnerHTML, 'href="/metrics/feature/popularity"');

    // anon shouldn't have the myfeatures tab
    assert.notInclude(navInnerHTML, 'href="/myfeatures');

    // anon has the (slotted in) google sign-in button
    assert.include(navInnerHTML, '<slot>');
  });

  it('user is signed in', async () => {
    window.csClient.getPermissions.returns(Promise.resolve({
      can_create_feature: true,
      can_edit: true,
      is_admin: false,
      email: 'example@google.com',
    }));
    const component = await fixture(
      html`<chromedash-header appTitle="Fake Title"></chromedash-header>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashHeader);
    const header = component.shadowRoot.querySelector('header');
    assert.exists(header);

    // aside and title exist
    const aside = component.shadowRoot.querySelector('aside');
    assert.exists(aside);
    assert.include(aside.innerHTML, 'Fake Title');

    // nav bar exists
    const nav = component.shadowRoot.querySelector('nav');
    assert.exists(nav);

    // nav bar has correct tabs
    const navInnerHTML = nav.innerHTML;
    assert.include(navInnerHTML, 'href="/roadmap"');
    assert.include(navInnerHTML, 'href="/features"');
    assert.include(navInnerHTML, 'href="/metrics/css/popularity"');
    assert.include(navInnerHTML, 'href="/metrics/feature/popularity"');
    assert.include(navInnerHTML, 'href="/myfeatures');

    // logged in users have Settings and Sign Out options
    assert.include(navInnerHTML, 'Settings');
    assert.include(navInnerHTML, 'Sign out');
  });
});
