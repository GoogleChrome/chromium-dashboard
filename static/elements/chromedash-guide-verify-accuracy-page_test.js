import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashGuideVerifyAccuracyPage} from './chromedash-guide-verify-accuracy-page';
import './chromedash-toast';
import '../js-src/cs-client';
import sinon from 'sinon';

describe('chromedash-guide-verify-accuracy-page', () => {
  const validFeaturePromise = Promise.resolve({
    id: 123456,
    name: 'feature one',
    summary: 'fake detailed summary',
    category: 'fake category',
    feature_type: 'fake feature type',
    intent_stage: 'fake intent stage',
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
      maturity: {text: 'Unknown standards status - check spec link for status'},
    },
    tags: ['tag_one'],
  });
  /* TODO: create a proper fake data once the form generation is migrated to frontend */
  const forms = '[["fake section name", ""]]';

  /* window.csClient and <chromedash-toast> are initialized at _base.html
   * which are not available here, so we initialize them before each test.
   * We also stub out the API calls here so that they return test data. */
  beforeEach(async () => {
    await fixture(html`<chromedash-toast></chromedash-toast>`);
    window.csClient = new ChromeStatusClient('fake_token', 1);
    sinon.stub(window.csClient, 'getFeature');
  });

  afterEach(() => {
    window.csClient.getFeature.restore();
  });

  it('renders with no data', async () => {
    const invalidFeaturePromise = Promise.reject(new Error('Got error response from server'));
    window.csClient.getFeature.withArgs(0).returns(invalidFeaturePromise);

    const component = await fixture(
      html`<chromedash-guide-verify-accuracy-page></chromedash-guide-verify-accuracy-page>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashGuideVerifyAccuracyPage);

    // invalid feature requests would trigger the toast to show message
    const toastEl = document.querySelector('chromedash-toast');
    const toastMsgSpan = toastEl.shadowRoot.querySelector('span#msg');
    assert.include(toastMsgSpan.innerHTML,
      'Some errors occurred. Please refresh the page or try again later.');
  });

  it('renders with fake data', async () => {
    const featureId = 123456;
    window.csClient.getFeature.withArgs(featureId).returns(validFeaturePromise);

    const component = await fixture(
      html`<chromedash-guide-verify-accuracy-page
             .featureId=${featureId}
             .forms=${forms}>
           </chromedash-guide-verify-accuracy-page>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashGuideVerifyAccuracyPage);

    const subheaderDiv = component.shadowRoot.querySelector('div#subheader');
    assert.exists(subheaderDiv);
    // subheader title is correct and clickable
    assert.include(subheaderDiv.innerHTML, 'href="/guide/edit/123456"');
    assert.include(subheaderDiv.innerHTML, 'Verify feature data for');

    // feature form, hidden token field, and submit/cancel buttons exist
    const featureForm = component.shadowRoot.querySelector('form[name="feature_form"]');
    assert.exists(featureForm);
    assert.include(featureForm.innerHTML, '<input type="hidden" name="token">');
    assert.include(featureForm.innerHTML, '<section class="final_buttons">');
  });
});
