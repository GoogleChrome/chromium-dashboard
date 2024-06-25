import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashGuideEditPage} from './chromedash-guide-edit-page';
import './chromedash-toast';
import {ChromeStatusClient} from '../js-src/cs-client';
import sinon from 'sinon';

describe('chromedash-guide-edit-page', () => {
  const permissionsPromise = Promise.resolve({
    can_create_feature: true,
    can_edit_all: true,
    is_admin: false,
    email: 'example@google.com',
  });
  const validFeaturePromise = Promise.resolve({
    id: 123456,
    name: 'feature one',
    summary: 'fake detailed summary',
    category: 'fake category',
    feature_type: 'fake feature type',
    intent_stage: 'fake intent stage',
    new_crbug_url: 'fake crbug link',
    stages: [
      {
        id: 1,
        stage_type: 110,
        intent_stage: 1,
      },
      {
        id: 2,
        stage_type: 120,
        intent_stage: 2,
      },
    ],
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
  const validGatesPromise = Promise.resolve({
    gates: [],
  });
  const processPromise = Promise.resolve({
    stages: [
      {
        name: 'stage one',
        description: 'a description',
        progress_items: [],
        outgoing_stage: 1,
        actions: [],
      },
    ],
  });
  const progressPromise = Promise.resolve({
    'Code in Chromium': 'True',
    'Draft API spec': 'fake spec link',
    'Estimated target milestone': 'True',
    'Final target milestone': 'True',
    'Intent to Experiment email': 'fake intent to experiment url',
    'Ready for Developer Testing email': 'fake ready for dev test url',
    'Spec link': 'fake spec link',
    'Web developer signals': 'True',
  });
  const dismissedCuesPromise = Promise.resolve(['progress-checkmarks']);

  /* window.csClient and <chromedash-toast> are initialized at spa.html
   * which are not available here, so we initialize them before each test.
   * We also stub out the API calls here so that they return test data. */
  beforeEach(async () => {
    await fixture(html`<chromedash-toast></chromedash-toast>`);
    window.csClient = new ChromeStatusClient('fake_token', 1);
    sinon.stub(window.csClient, 'getPermissions');
    sinon.stub(window.csClient, 'getFeature');
    sinon.stub(window.csClient, 'getGates');
    sinon.stub(window.csClient, 'getFeatureProcess');
    sinon.stub(window.csClient, 'getFeatureProgress');
    sinon.stub(window.csClient, 'getDismissedCues');
    window.csClient.getPermissions.returns(permissionsPromise);
    window.csClient.getFeatureProcess.returns(processPromise);
    window.csClient.getFeatureProgress.returns(progressPromise);
    window.csClient.getDismissedCues.returns(dismissedCuesPromise);
  });

  afterEach(() => {
    window.csClient.getPermissions.restore();
    window.csClient.getFeature.restore();
    window.csClient.getGates.restore();
    window.csClient.getFeatureProcess.restore();
    window.csClient.getFeatureProgress.restore();
    window.csClient.getDismissedCues.restore();
  });

  it('renders with no data', async () => {
    const invalidFeaturePromise = Promise.reject(
      new Error('Got error response from server')
    );
    window.csClient.getFeature.withArgs(0).returns(invalidFeaturePromise);

    const component = await fixture(
      html`<chromedash-guide-edit-page></chromedash-guide-edit-page>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashGuideEditPage);

    // invalid feature requests would trigger the toast to show message
    const toastEl = document.querySelector('chromedash-toast');
    const toastMsgSpan = toastEl.shadowRoot.querySelector('span#msg');
    assert.include(
      toastMsgSpan.innerHTML,
      'Some errors occurred. Please refresh the page or try again later.'
    );
  });

  it('renders with fake data', async () => {
    const featureId = 123456;
    window.csClient.getPermissions.returns(permissionsPromise);
    window.csClient.getFeature.withArgs(featureId).returns(validFeaturePromise);
    window.csClient.getGates.withArgs(featureId).returns(validGatesPromise);

    const component = await fixture(
      html`<chromedash-guide-edit-page .featureId=${featureId}>
      </chromedash-guide-edit-page>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashGuideEditPage);

    const subheaderDiv = component.shadowRoot.querySelector('div#subheader');
    assert.exists(subheaderDiv);
    // subheader title is correct and clickable
    assert.include(subheaderDiv.innerHTML, 'href="/feature/123456"');
    assert.include(subheaderDiv.innerHTML, 'feature one');
    // "Edit all fields" link exists and clickable
    assert.include(subheaderDiv.innerHTML, 'href="/guide/editall/123456');
    assert.include(subheaderDiv.innerHTML, 'Edit all fields');

    // chromedash-guide-metadata is rendered
    const metadata = component.shadowRoot.querySelector(
      'chromedash-guide-metadata'
    );
    assert.exists(metadata);

    // chromedash-process-overview is rendered
    const processOverview = component.shadowRoot.querySelector(
      'chromedash-process-overview'
    );
    assert.exists(processOverview);

    // footnote section is rendered and with the correct link
    const footnoteSection =
      component.shadowRoot.querySelector('section#footnote');
    assert.exists(footnoteSection);
    assert.include(
      footnoteSection.innerHTML,
      'href="https://www.chromium.org/blink/launching-features"'
    );
  });
});
