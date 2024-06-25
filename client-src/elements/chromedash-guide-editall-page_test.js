import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashGuideEditallPage} from './chromedash-guide-editall-page';
import './chromedash-toast';
import {ChromeStatusClient} from '../js-src/cs-client';
import sinon from 'sinon';

describe('chromedash-guide-editall-page', () => {
  const validFeaturePromise = Promise.resolve({
    id: 123456,
    name: 'feature one',
    summary: 'fake detailed summary',
    category: 'fake category',
    feature_type: 'fake feature type',
    feature_type_int: 0,
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
        stage_type: 160,
        intent_stage: 2,
      },
      {
        id: 3,
        stage_type: 160,
        intent_stage: 2,
      },
      {
        id: 3,
        stage_type: 1061,
        intent_stage: 1,
      },
      {
        id: 4,
        stage_type: 1061,
        intent_stage: 1,
      },
    ],
    browsers: {
      chrome: {
        blink_components: ['Blink'],
        owners: ['fake chrome owner one', 'fake chrome owner two'],
        status: {
          milestone_str: 'No active development',
          text: 'No active development',
          val: 1,
        },
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
      status: {text: "Editor's Draft", val: 4},
    },
    tags: ['tag_one'],
  });

  /* window.csClient and <chromedash-toast> are initialized at spa.html
   * which are not available here, so we initialize them before each test.
   * We also stub out the API calls here so that they return test data. */
  beforeEach(async () => {
    await fixture(html`<chromedash-toast></chromedash-toast>`);
    window.csClient = new ChromeStatusClient('fake_token', 1);
    sinon.stub(window.csClient, 'getFeature');
    sinon.stub(window.csClient, 'getBlinkComponents');
    window.csClient.getBlinkComponents.returns(Promise.resolve({}));
  });

  afterEach(() => {
    window.csClient.getFeature.restore();
    window.csClient.getBlinkComponents.restore();
  });

  it('renders with no data', async () => {
    const invalidFeaturePromise = Promise.reject(
      new Error('Got error response from server')
    );
    window.csClient.getFeature.withArgs(0).returns(invalidFeaturePromise);

    const component = await fixture(
      html`<chromedash-guide-editall-page></chromedash-guide-editall-page>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashGuideEditallPage);

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
    window.csClient.getFeature.withArgs(featureId).returns(validFeaturePromise);

    const component = await fixture(
      html`<chromedash-guide-editall-page .featureId=${featureId}>
      </chromedash-guide-editall-page>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashGuideEditallPage);

    const subheaderDiv = component.shadowRoot.querySelector('div#subheader');
    assert.exists(subheaderDiv);
    // subheader title is correct and clickable
    assert.include(subheaderDiv.innerHTML, 'href="/feature/123456"');
    assert.include(subheaderDiv.innerHTML, 'Edit feature:');

    // feature form, hidden token field, and submit/cancel buttons exist
    const featureForm = component.shadowRoot.querySelector(
      'form[name="feature_form"]'
    );
    assert.exists(featureForm);
    assert.include(featureForm.innerHTML, '<input type="hidden" name="token">');
    assert.include(featureForm.innerHTML, '<section class="final_buttons">');

    const formTable = component.shadowRoot.querySelector(
      'chromedash-form-table'
    );
    assert.exists(formTable);

    // delete button shown on rollout steps only
    const deleteButtons = formTable.querySelectorAll('sl-button[stage="1061"]');
    assert.equal(deleteButtons.length, 2);
  });

  it('avoids duplicating fields', async () => {
    const featureId = 123456;
    window.csClient.getFeature.withArgs(featureId).returns(validFeaturePromise);

    const component = await fixture(
      html`<chromedash-guide-editall-page .featureId=${featureId}>
      </chromedash-guide-editall-page>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashGuideEditallPage);

    // There are two shipping stage types, but 'tag_review_status' is not a stage-specific field,
    // so only one field should display and it should not display for the second stage.
    const measurementFields = component.shadowRoot.querySelectorAll(
      'sl-select[name="tag_review_status"]'
    );
    assert.exists(measurementFields);
    assert.isTrue(measurementFields.length === 1);
  });

  // TODO: make this work
  // it('calls milestone range pair checks', async () => {
  //   const featureId = 123456;
  //   window.csClient.getFeature.withArgs(featureId).returns(validFeaturePromise);

  //   const component = await fixture(
  //     html`<chromedash-guide-editall-page
  //            .featureId=${featureId}>
  //          </chromedash-guide-editall-page>`);
  //   assert.exists(component);
  //   assert.instanceOf(component, ChromedashGuideEditallPage);

  //   const milestoneFieldStart = component.shadowRoot.querySelector(
  //     'chromedash-form-field[name="ot_milestone_desktop_start"]');
  //   assert.exists(milestoneFieldStart);

  //   assert.exists(milestoneField);
  //   // Get the milestone fields
  //   const milestoneFieldStartInput =
  //     component.shadowRoot.querySelector(
  //       'chromedash-form-field[name="ot_milestone_desktop_start"] sl-input');
  //   const milestoneFieldEnd =
  //     component.shadowRoot.querySelector(
  //       'chromedash-form-field[name="ot_milestone_desktop_end"] sl-input');

  //   assert.exists(milestoneFieldStart);
  //   assert.exists(milestoneFieldEnd);

  //   // Set an invalid milestone values
  //   milestoneFieldStartInput.value = '100';
  //   milestoneFieldEnd.value = '99';

  //   // Trigger the change event on the milestone field
  //   milestoneFieldStartInput.dispatchEvent(new Event('sl-change'));

  //   // The error messages should be displayed
  //   const errorMessageStart = milestoneFieldStartInput.shadowRoot.querySelector('.check-error');
  //   assert.exists(errorMessageStart);

  //   const errorMessageEnd = milestoneFieldEnd.shadowRoot.querySelector('.check-error');
  //   assert.exists(errorMessageEnd);

  //   // Set a valid milestone value
  //   milestoneFieldStartInput.value = '42';
  //   milestoneFieldEnd.value = '43';

  //   // Trigger the change event on the milestone field
  //   milestoneField.dispatchEvent(new Event('sl-change'));

  //   // The error messages should not be displayed
  //   assert.notExists(errorMessageStart);
  //   assert.notExists(errorMessageEnd);
  // });
});
