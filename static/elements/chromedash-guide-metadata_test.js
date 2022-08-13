import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashGuideMetadata} from './chromedash-guide-metadata';
import './chromedash-toast';
import '../js-src/cs-client';
import sinon from 'sinon';

describe('chromedash-guide-metadata', () => {
  const permissionsPromise = Promise.resolve({
    can_approve: false,
    can_create_feature: true,
    can_edit_all: true,
    is_admin: false,
    email: 'example@google.com',
  });
  const adminPermissionsPromise = Promise.resolve({
    can_approve: false,
    can_create_feature: true,
    can_edit_all: true,
    is_admin: true,
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

  /* window.csClient and <chromedash-toast> are initialized at _base.html
   * which are not available here, so we initialize them before each test.
   * We also stub out the API calls here so that they return test data. */
  beforeEach(async () => {
    await fixture(html`<chromedash-toast></chromedash-toast>`);
    window.csClient = new ChromeStatusClient('fake_token', 1);
    sinon.stub(window.csClient, 'getPermissions');
    sinon.stub(window.csClient, 'getFeature');
  });

  afterEach(() => {
    window.csClient.getPermissions.restore();
    window.csClient.getFeature.restore();
  });

  it('renders with no data', async () => {
    window.csClient.getPermissions.returns(permissionsPromise);
    const invalidFeaturePromise = Promise.reject(new Error('Got error response from server'));
    window.csClient.getFeature.withArgs(0).returns(invalidFeaturePromise);

    const component = await fixture(
      html`<chromedash-guide-metadata></chromedash-guide-metadata>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashGuideMetadata);

    // invalid feature requests would trigger the toast to show message
    const toastEl = document.querySelector('chromedash-toast');
    const toastMsgSpan = toastEl.shadowRoot.querySelector('span#msg');
    assert.include(toastMsgSpan.innerHTML,
      'Some errors occurred. Please refresh the page or try again later.');
  });

  it('renders with fake data', async () => {
    const featureId = 123456;
    window.csClient.getPermissions.returns(permissionsPromise);
    window.csClient.getFeature.withArgs(featureId).returns(validFeaturePromise);

    const component = await fixture(
      html`<chromedash-guide-metadata
             .featureId=${featureId}>
           </chromedash-guide-metadata>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashGuideMetadata);

    const metadataDiv = component.shadowRoot.querySelector('div#metadata-readonly');
    assert.exists(metadataDiv);
    // edit button exists
    assert.include(metadataDiv.innerHTML, 'id="open-metadata"');
    // feature summary is listed
    assert.include(metadataDiv.innerHTML, 'fake detailed summary');
    // feature owners are listed
    assert.include(metadataDiv.innerHTML, 'href="mailto:fake chrome owner one"');
    assert.include(metadataDiv.innerHTML, 'href="mailto:fake chrome owner two"');
    // feature category is listed
    assert.include(metadataDiv.innerHTML, 'fake category');
    // feature feature type is listed
    assert.include(metadataDiv.innerHTML, 'fake feature type');
    // feature intent stage is listed
    assert.include(metadataDiv.innerHTML, 'fake intent stage');
    // feature tag is listed
    assert.include(metadataDiv.innerHTML, 'tag_one');
    // feature status is listed
    assert.include(metadataDiv.innerHTML, 'fake chrome status text');
    // feature blink component is listed
    assert.include(metadataDiv.innerHTML, 'Blink');
  });

  it('user is an admin', async () => {
    const featureId = 123456;
    window.csClient.getPermissions.returns(adminPermissionsPromise);
    window.csClient.getFeature.withArgs(featureId).returns(validFeaturePromise);

    const component = await fixture(
      html`<chromedash-guide-metadata
             .featureId=${featureId}>
           </chromedash-guide-metadata>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashGuideMetadata);

    const metadataDiv = component.shadowRoot.querySelector('div#metadata-readonly');
    assert.exists(metadataDiv);
    // delete button exists
    assert.include(metadataDiv.innerHTML, 'class="delete-button"');
  });
});
