import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashGuideStagePage} from './chromedash-guide-stage-page';
import {STAGE_FORMS, IMPL_STATUS_FORMS} from './form-definition';
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
    feature_type_int: 1,
    intent_stage: 'fake intent stage',
    new_crbug_url: 'fake crbug link',
    browsers: {
      chrome: {
        blink_components: ['Blink'],
        owners: ['fake chrome owner one', 'fake chrome owner two'],
        status: {
          milestone_str: 'No active development',
          text: 'No active development',
          val: 1},
      },
      ff: {view: {text: 'No signal', val: 5}},
      safari: {view: {text: 'No signal', val: 5}},
      webdev: {view: {text: 'No signal', val: 4}},
      other: {view: {}},
    },
    resources: {
      samples: ['fake sample link one', 'fake sample link two'],
      docs: ['fake doc link one', 'fake doc link two'],
    },
    standards: {
      maturity: {
        short_text: 'Incubation',
        text: 'Specification being incubated in a Community Group',
        val: 3,
      },
      status: {text: 'Editor\'s Draft', val: 4},
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

  /* window.csClient and <chromedash-toast> are initialized at _base.html
   * which are not available here, so we initialize them before each test.
   * We also stub out the API calls here so that they return test data. */
  beforeEach(async () => {
    await fixture(html`<chromedash-toast></chromedash-toast>`);
    window.csClient = new ChromeStatusClient('fake_token', 1);
    sinon.stub(window.csClient, 'getFeature');
    sinon.stub(window.csClient, 'getFeatureProcess');
    sinon.stub(window.csClient, 'getBlinkComponents');
    window.csClient.getFeatureProcess.returns(processPromise);
    window.csClient.getBlinkComponents.returns(Promise.resolve({}));
  });

  afterEach(() => {
    window.csClient.getFeature.restore();
    window.csClient.getFeatureProcess.restore();
    window.csClient.getBlinkComponents.restore();
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
    const stageId = 2;
    const featureId = 123456;
    window.csClient.getFeature.withArgs(featureId).returns(validFeaturePromise);

    const component = await fixture(
      html`<chromedash-guide-stage-page
             .stageId=${stageId}
             .featureId=${featureId}>
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
    assert.include(form.innerHTML, '<input type="hidden" name="form_fields"');
    assert.include(form.innerHTML, `${STAGE_FORMS[1][stageId].join()}`);
    assert.include(form.innerHTML, `${IMPL_STATUS_FORMS[stageId][1].join()}`);
    assert.include(form.innerHTML, '<div class="final_buttons">');

    // Implementation section renders correct title and fields
    assert.include(form.innerHTML, 'Implementation in Chromium');
    assert.include(form.innerHTML, '4');
    assert.include(form.innerHTML, 'type="hidden" name="impl_status_offered"');
    assert.include(form.innerHTML, 'sl-checkbox name="set_impl_status"');
    assert.notInclude(form.innerHTML, 'This feature already has implementation status');
  });

  it('renders with fake data (without implStatusForm and implStatusName)', async () => {
    const stageId = 1;
    const featureId = 123456;
    window.csClient.getFeature.withArgs(featureId).returns(validFeaturePromise);

    const component = await fixture(
      html`<chromedash-guide-stage-page
             .stageId=${stageId}
             .featureId=${featureId}>
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
    assert.notInclude(form.innerHTML, 'sl-checkbox name="set_impl_status"');
  });
});
