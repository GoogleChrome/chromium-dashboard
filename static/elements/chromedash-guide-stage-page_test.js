import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashGuideStagePage} from './chromedash-guide-stage-page';
import './chromedash-toast';
import '../js-src/cs-client';
import sinon from 'sinon';

describe('chromedash-guide-stage-page', () => {
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
  const processPromise = Promise.resolve({
    stages: [{
      name: 'stage one',
      description: 'a description',
      progress_items: [],
      outgoing_stage: 1,
      actions: [],
    }],
  });
  const implStatusName = 'fake implStatusName';
  /* TODO: create a proper fake data once the form generation is migrated to frontend */
  const featureForm = '["", ["fake feature field 1", "fake feature field 2"]]';
  const implStatusForm = '["", ["fake implStatus field 1", "fake implStatus field 2"]]';

  /* window.csClient and <chromedash-toast> are initialized at _base.html
   * which are not available here, so we initialize them before each test.
   * We also stub out the API calls here so that they return test data. */
  beforeEach(async () => {
    await fixture(html`<chromedash-toast></chromedash-toast>`);
    window.csClient = new ChromeStatusClient('fake_token', 1);
    sinon.stub(window.csClient, 'getFeature');
    sinon.stub(window.csClient, 'getFeatureProcess');
    window.csClient.getFeatureProcess.returns(processPromise);
  });

  afterEach(() => {
    window.csClient.getFeature.restore();
    window.csClient.getFeatureProcess.restore();
  });

  it('renders with no data', async () => {
    const invalidFeaturePromise = Promise.reject(new Error('Got error response from server'));
    window.csClient.getFeature.withArgs(0).returns(invalidFeaturePromise);

    const component = await fixture(
      html`<chromedash-guide-stage-page></chromedash-guide-stage-page>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashGuideStagePage);

    // invalid feature requests would trigger the toast to show message
    const toastEl = document.querySelector('chromedash-toast');
    const toastMsgSpan = toastEl.shadowRoot.querySelector('span#msg');
    assert.include(toastMsgSpan.innerHTML,
      'Some errors occurred. Please refresh the page or try again later.');
  });

  it('renders with fake data (with implStatusForm and implStatusName)', async () => {
    const stageId = 1;
    const featureId = 123456;
    window.csClient.getFeature.withArgs(featureId).returns(validFeaturePromise);

    const component = await fixture(
      html`<chromedash-guide-stage-page
             .stageId=${stageId}
             .featureId=${featureId}
             .featureForm=${featureForm}
             .implStatusForm=${implStatusForm}
             .implStatusName=${implStatusName}>
           </chromedash-guide-stage-page>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashGuideStagePage);

    const subheaderDiv = component.shadowRoot.querySelector('div#subheader');
    assert.exists(subheaderDiv);
    // subheader title is correct and clickable
    assert.include(subheaderDiv.innerHTML, 'href="/guide/edit/123456"');
    assert.include(subheaderDiv.innerHTML, 'Edit feature:');

    // feature form, hidden token field, and submit/cancel buttons exist
    const form = component.shadowRoot.querySelector('form[name="feature_form"]');
    assert.exists(form);
    assert.include(form.innerHTML, '<input type="hidden" name="token">');
    assert.include(form.innerHTML,
      '<input type="hidden" name="form_fields" value="fake feature field 1,'+
      'fake feature field 2,fake implStatus field 1,fake implStatus field 2">');
    assert.include(form.innerHTML, '<div class="final_buttons">');

    // Implementation section renders correct title and fields
    assert.include(form.innerHTML, 'Implementation in Chromium');
    assert.include(form.innerHTML, 'fake implStatusName');
    assert.include(form.innerHTML, 'type="hidden" name="impl_status_offered"');
    assert.include(form.innerHTML, 'type="checkbox" name="set_impl_status"');
    assert.notInclude(form.innerHTML, 'This feature already has implementation status');
  });

  it('renders with fake data (without implStatusForm and implStatusName)', async () => {
    const stageId = 1;
    const featureId = 123456;
    window.csClient.getFeature.withArgs(featureId).returns(validFeaturePromise);

    const component = await fixture(
      html`<chromedash-guide-stage-page
             .stageId=${stageId}
             .featureId=${featureId}
             .featureForm=${featureForm}>
           </chromedash-guide-stage-page>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashGuideStagePage);

    const form = component.shadowRoot.querySelector('form[name="feature_form"]');
    assert.exists(form);

    // Implementation section renders correct title and fields
    assert.notInclude(form.innerHTML, 'Implementation in Chromium');
    assert.notInclude(form.innerHTML, 'This feature already has implementation status');
    assert.notInclude(form.innerHTML, 'fake implStatusName');
    assert.notInclude(form.innerHTML, 'type="hidden" name="impl_status_offered"');
    assert.notInclude(form.innerHTML, 'type="checkbox" name="set_impl_status"');
  });
});
