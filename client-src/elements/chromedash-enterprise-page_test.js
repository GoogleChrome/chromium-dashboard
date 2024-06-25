import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashEnterprisePage} from './chromedash-enterprise-page';
import './chromedash-toast';
import {ChromeStatusClient} from '../js-src/cs-client';
import sinon from 'sinon';

describe('chromedash-enterprise-page', () => {
  /* window.csClient and <chromedash-toast> are initialized at spa.html
   * which are not available here, so we initialize them before each test.
   * We also stub out the API calls here so that they return test data. */
  beforeEach(async () => {
    await fixture(html`<chromedash-toast></chromedash-toast>`);
    window.csClient = new ChromeStatusClient('fake_token', 1);
    sinon.stub(window.csClient, 'getStars');
    sinon.stub(window.csClient, 'searchFeatures');
    window.csClient.getStars.returns(Promise.resolve([123456]));
  });

  afterEach(() => {
    window.csClient.getStars.restore();
    window.csClient.searchFeatures.restore();
  });

  it('render with no data', async () => {
    const invalidFeaturePromise = Promise.reject(
      new Error('Got error response from server')
    );
    window.csClient.searchFeatures.returns(invalidFeaturePromise);
    const component = await fixture(
      html`<chromedash-enterprise-page></chromedash-enterprise-page>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashEnterprisePage);

    // error response would trigger the toast to show message
    const toastEl = document.querySelector('chromedash-toast');
    const toastMsgSpan = toastEl.shadowRoot.querySelector('span#msg');
    assert.include(
      toastMsgSpan.innerHTML,
      'Some errors occurred. Please refresh the page or try again later.'
    );
  });

  it('render with fake data', async () => {
    const validFeaturePromise = Promise.resolve({
      total_count: 1,
      features: [
        {
          id: 123456,
          name: 'feature one',
        },
      ],
    });
    const user = {
      can_create_feature: true,
      can_edit_all: true,
      is_admin: false,
      email: 'example@gmail.com',
      editable_features: [],
    };
    window.csClient.searchFeatures.returns(validFeaturePromise);
    const component = await fixture(
      html`<chromedash-enterprise-page .user=${user}>
      </chromedash-enterprise-page>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashEnterprisePage);

    // feature table exists
    const featureTableEl = component.shadowRoot.querySelector(
      'chromedash-feature-table'
    );
    assert.exists(featureTableEl);

    // title exists
    const titleEl = component.shadowRoot.querySelector('h2');
    assert.include(
      titleEl.innerHTML,
      'Enterprise features and breaking changes'
    );
  });
});
