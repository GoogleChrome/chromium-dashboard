import {html, fixture, assert} from '@open-wc/testing';
import sinon from 'sinon';
import page from 'page';
import {ChromedashApp} from './chromedash-app.js';
import './chromedash-app.js';
import {User, ChromeStatusClient} from '../js-src/cs-client.js';

describe('chromedash-app', () => {
  const user = {
    can_create_feature: true,
    can_edit: true,
    is_admin: true,
    can_review_release_notes: true,
    email: 'editor@google.com',
  } as unknown as User;

  beforeEach(() => {
    // Stub csClient permissions and count APIs
    window.csClient = new ChromeStatusClient('fake_token', 1);
    sinon.stub(window.csClient, 'getPermissions').resolves(user);
    sinon.stub(window.csClient, 'getPendingReviewsCount').resolves({count: 2});

    // Stub page.js router methods to prevent real routing side-effects
    sinon.stub(page, 'start');
    sinon.stub(page, 'strict');
    sinon.stub(page, 'show');
    sinon.stub(page, 'redirect');
  });

  afterEach(() => {
    sinon.restore();
  });

  it('catches refetch-needed event bubbled from child and triggers drawer count refresh', async () => {
    const component = (await fixture(
      html`<chromedash-app></chromedash-app>`
    )) as ChromedashApp;

    await component.updateComplete;

    // Locate the drawer component in the shadow DOM
    const drawer = component.renderRoot.querySelector('chromedash-drawer') as any;
    assert.exists(drawer);

    // Spy on the drawer's fetchPendingReviewsCount method
    const fetchCountSpy = sinon.spy(drawer, 'fetchPendingReviewsCount');

    // Dispatch the 'refetch-needed' event on the page component wrapper (simulating child bubble)
    const wrapper = component.renderRoot.querySelector('#content-component-wrapper');
    assert.exists(wrapper);
    
    wrapper.dispatchEvent(
      new CustomEvent('refetch-needed', {
        bubbles: true,
        composed: true,
      })
    );

    // Verify that the app container caught the event and successfully invoked the drawer refresh!
    assert.isTrue(fetchCountSpy.calledOnce);
  });
});
