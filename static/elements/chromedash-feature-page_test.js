import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashFeaturePage} from './chromedash-feature-page';
import './chromedash-toast';
import '../js-src/cs-client';
import sinon from 'sinon';

describe('chromedash-feature-page', () => {
  const processPromise = Promise.resolve({
    name: 'fake process',
    stages: [{name: 'fake stage name', outgoing_stage: 1}],
  });
  const fieldDefsPromise = Promise.resolve({
    1: ['fake field one', 'fake field two', 'fake field three'],
  });
  const dismissedCuesPromise = Promise.resolve(['progress-checkmarks']);

  /* window.csClient and <chromedash-toast> are initialized at _base.html
   * which are not available here, so we initialize them before each test.
   * We also stub out the API calls here so that they return test data. */
  beforeEach(async () => {
    await fixture(html`<chromedash-toast></chromedash-toast>`);
    window.csClient = new ChromeStatusClient('fake_token', 1);
    sinon.stub(window.csClient, 'getFeature');
    sinon.stub(window.csClient, 'getFeatureProcess');
    sinon.stub(window.csClient, 'getFieldDefs');
    sinon.stub(window.csClient, 'getDismissedCues');
    window.csClient.getFeatureProcess.returns(processPromise);
    window.csClient.getFieldDefs.returns(fieldDefsPromise);
    window.csClient.getDismissedCues.returns(dismissedCuesPromise);
  });

  afterEach(() => {
    window.csClient.getFeature.restore();
    window.csClient.getFeatureProcess.restore();
    window.csClient.getFieldDefs.restore();
    window.csClient.getDismissedCues.restore();
  });

  it('renders with no data', async () => {
    const invalidFeaturePromise = Promise.reject(new Error('Got error response from server'));
    window.csClient.getFeature.withArgs(0).returns(invalidFeaturePromise);

    const component = await fixture(
      html`<chromedash-feature-page></chromedash-feature-page>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashFeaturePage);

    // invalid feature requests would trigger the toast to show message
    const toastEl = document.querySelector('chromedash-toast');
    const toastMsgSpan = toastEl.shadowRoot.querySelector('span#msg');
    assert.include(toastMsgSpan.innerHTML,
      'Some errors occurred. Please refresh the page or try again later.');
  });

  it('renders with fake data', async () => {
    const featureId = 123456;
    const validFeaturePromise = Promise.resolve({
      id: 123456,
      browsers: {
        chrome: {
          blink_component: ['Blink'],
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
    window.csClient.getFeature.withArgs(featureId).returns(validFeaturePromise);

    const component = await fixture(
      html`<chromedash-feature-page
              .featureId=${featureId}
             ></chromedash-feature-page>`);
    assert.exists(component);

    const sampleSection = component.shadowRoot.querySelector('section#demo');
    assert.exists(sampleSection);
    assert.include(sampleSection.innerHTML, 'href="fake sample link one"');
    assert.include(sampleSection.innerHTML, 'href="fake sample link two"');

    const docSection = component.shadowRoot.querySelector('section#documentation');
    assert.exists(docSection);
    assert.include(docSection.innerHTML, 'href="fake doc link one"');
    assert.include(docSection.innerHTML, 'href="fake doc link two"');

    const specSection = component.shadowRoot.querySelector('section#specification');
    assert.exists(specSection);
    assert.include(specSection.innerHTML, 'href="fake spec link"');

    const tagSection = component.shadowRoot.querySelector('section#tags');
    assert.exists(tagSection);
    assert.include(tagSection.innerHTML, 'href="/features#tags:tag_one"');
  });
});
