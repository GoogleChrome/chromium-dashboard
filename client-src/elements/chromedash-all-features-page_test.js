import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashAllFeaturesPage} from './chromedash-all-features-page';
import './chromedash-toast';
import {ChromeStatusClient} from '../js-src/cs-client';
import sinon from 'sinon';

describe('chromedash-all-features-page', () => {
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
      html`<chromedash-all-features-page></chromedash-all-features-page>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashAllFeaturesPage);

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
          summary: 'detailed sum',
          new_crbug_url: 'fake crbug link',
          browsers: {
            chrome: {
              blink_components: ['Blink'],
              owners: ['fake chrome owner one', 'fake chrome owner two'],
              status: {text: 'fake chrome status text'},
            },
            ff: {view: {text: 'fake ff view text'}},
            safari: {view: {text: 'fake safari view text'}},
            webdev: {view: {text: 'fake webdev view text'}},
          },
          resources: {
            samples: ['fake sample link one', 'fake sample link two'],
            docs: ['fake doc link one', 'fake doc link two'],
          },
          standards: {
            spec: 'fake spec link',
            maturity: {
              text: 'Unknown standards status - check spec link for status',
            },
          },
          tags: ['tag_one'],
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
      html`<chromedash-all-features-page .user=${user}>
      </chromedash-all-features-page>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashAllFeaturesPage);

    // feature table exists
    const featureTableEl = component.shadowRoot.querySelector(
      'chromedash-feature-table'
    );
    assert.exists(featureTableEl);

    // title exists
    const titleEl = component.shadowRoot.querySelector('div#content-title');
    assert.include(titleEl.innerHTML, '<h2>');
    assert.include(titleEl.innerHTML, 'Features</h2>');
  });
});
