import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashDrawer} from './chromedash-drawer';
import './chromedash-toast';
import {ChromeStatusClient} from '../js-src/cs-client';
import sinon, {SinonStub} from 'sinon';

describe('chromedash-drawer', () => {
  /* window.csClient and <chromedash-toast> are initialized at _base.html
   * which are not available here, so we initialize them before each test.
   * We also stub out the API calls here so that they return test data. */
  let getPermissionsStub: SinonStub;
  beforeEach(async () => {
    await fixture(html`<chromedash-toast></chromedash-toast>`);
    window.csClient = new ChromeStatusClient('fake_token', 1);
    getPermissionsStub = sinon.stub(window.csClient, 'getPermissions');
  });

  afterEach(() => {
    getPermissionsStub.restore();
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
});
