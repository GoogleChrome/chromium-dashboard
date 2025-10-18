import {assert, fixture} from '@open-wc/testing';
import {html} from 'lit';
import sinon from 'sinon';
import {ChromeStatusClient} from '../js-src/cs-client';
import {ChromedashGuideEditallPage} from './chromedash-guide-editall-page';
import './chromedash-toast';

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
        id: 4,
        stage_type: 1061,
        intent_stage: 1,
      },
      {
        id: 5,
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

  const validChannelsPromise = Promise.resolve({
    stable: {
      "branch_point": "2025-09-01T00:00:00",
      "earliest_beta": "2025-09-03T00:00:00",
      "earliest_beta_chromeos": "2025-09-16T00:00:00",
      "earliest_beta_ios": "2025-09-03T00:00:00",
      "early_stable": "2025-09-24T00:00:00",
      "early_stable_ios": "2025-09-17T00:00:00",
      "final_beta": "2025-09-24T00:00:00",
      "final_beta_cut": "2025-09-23T00:00:00",
      "late_stable_date": "2025-10-14T00:00:00",
      "latest_beta": "2025-09-18T00:00:00",
      "mstone": 141,
      "next_late_stable_refresh": "2025-10-28T00:00:00",
      "next_stable_refresh": "2025-10-14T00:00:00",
      "stable_cut": "2025-09-23T00:00:00",
      "stable_cut_ios": "2025-09-16T00:00:00",
      "stable_date": "2025-09-30T00:00:00",
      "stable_refresh_first": "2025-10-14T00:00:00",
      "version": 141
    },
    beta: {
      "branch_point": "2025-09-29T00:00:00",
      "earliest_beta": "2025-10-01T00:00:00",
      "earliest_beta_chromeos": "2025-10-14T00:00:00",
      "earliest_beta_ios": "2025-10-01T00:00:00",
      "early_stable": "2025-10-22T00:00:00",
      "early_stable_ios": "2025-10-22T00:00:00",
      "final_beta": "2025-10-22T00:00:00",
      "final_beta_cut": "2025-10-21T00:00:00",
      "late_stable_date": "2025-11-11T00:00:00",
      "latest_beta": "2025-10-16T00:00:00",
      "mstone": 142,
      "stable_cut": "2025-10-21T00:00:00",
      "stable_cut_ios": "2025-10-21T00:00:00",
      "stable_date": "2025-10-28T00:00:00",
      "stable_refresh_first": "2025-11-11T00:00:00",
      "stable_refresh_second": "2025-12-02T00:00:00",
      "stable_refresh_third": "2025-12-16T00:00:00",
      "version": 142
    },
    dev: {
      "branch_point": "2025-10-27T00:00:00",
      "earliest_beta": "2025-10-29T00:00:00",
      "earliest_beta_chromeos": "2025-11-11T00:00:00",
      "earliest_beta_ios": "2025-10-29T00:00:00",
      "early_stable": "2025-11-19T00:00:00",
      "early_stable_ios": "2025-11-19T00:00:00",
      "final_beta": "2025-11-19T00:00:00",
      "final_beta_cut": "2025-11-18T00:00:00",
      "late_stable_date": "2025-12-16T00:00:00",
      "latest_beta": "2025-11-13T00:00:00",
      "mstone": 143,
      "stable_cut": "2025-11-18T00:00:00",
      "stable_cut_ios": "2025-11-18T00:00:00",
      "stable_date": "2025-12-02T00:00:00",
      "version": 143
    }
  });

  /* window.csClient and <chromedash-toast> are initialized at spa.html
   * which are not available here, so we initialize them before each test.
   * We also stub out the API calls here so that they return test data. */
  beforeEach(async () => {
    await fixture(html`<chromedash-toast></chromedash-toast>`);
    window.csClient = new ChromeStatusClient('fake_token', 1);
    sinon.stub(window.csClient, 'getFeature');
    sinon.stub(window.csClient, 'getChannels');
    sinon.stub(window.csClient, 'getBlinkComponents');
    window.csClient.getBlinkComponents.returns(Promise.resolve({}));
  });

  afterEach(() => {
    window.csClient.getFeature.restore();
    window.csClient.getBlinkComponents.restore();
    window.csClient.getChannels.restore();
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
    const toastMsgSpan = toastEl?.shadowRoot?.querySelector('span#msg');
    assert.include(
      toastMsgSpan?.innerHTML,
      'Some errors occurred. Please refresh the page or try again later.'
    );
  });

  it('renders with fake data', async () => {
    const featureId = 123456;
    window.csClient.getFeature.withArgs(featureId).returns(validFeaturePromise);
    window.csClient.getChannels.returns(validChannelsPromise);

    const component = await fixture<ChromedashGuideEditallPage>(
      html`<chromedash-guide-editall-page .featureId=${featureId}>
      </chromedash-guide-editall-page>`
    );

    await component.updateComplete;

    assert.exists(component, 'component exists.');
    assert.instanceOf(component, ChromedashGuideEditallPage);

    const subheaderDiv = component.renderRoot.querySelector('div#subheader');
    assert.exists(subheaderDiv, 'Subheader exists.');
    // subheader title is correct and clickable
    assert.include(subheaderDiv.innerHTML, 'href="/feature/123456"');
    assert.include(subheaderDiv.innerHTML, 'Edit feature:');

    // feature form, hidden token field, and submit/cancel buttons exist
    const featureForm = component.renderRoot.querySelector(
      'form[name="feature_form"]'
    );
    assert.exists(featureForm, 'Feature form exists.');
    assert.include(featureForm.innerHTML, '<input type="hidden" name="token">');
    assert.include(featureForm.innerHTML, '<section class="final_buttons">');

    const formTable = component.renderRoot.querySelector(
      'chromedash-form-table'
    );
    assert.exists(formTable, 'Form table exists.');

    // delete button shown on rollout steps only
    const deleteButtons = formTable.querySelectorAll('sl-button[stage="1061"]');
    assert.equal(deleteButtons.length, 2);
  });

  it('avoids duplicating feature-level fields in stages of the same type', async () => {
    const featureId = 123456;
    // The mock feature has two stages of type 160 (ids 2 and 3).
    window.csClient.getFeature.withArgs(featureId).returns(validFeaturePromise);
    window.csClient.getChannels.returns(validChannelsPromise);

    const component = await fixture<ChromedashGuideEditallPage>(
      html`<chromedash-guide-editall-page .featureId=${featureId}>
      </chromedash-guide-editall-page>`
    );

    await component.updateComplete;

    // Find all the sections for the duplicated stage type.
    const sections = component.renderRoot.querySelectorAll(
      'section[stage="160"]'
    );
    assert.equal(
      sections.length,
      2,
      'Should render a section for each stage of type 160'
    );

    // Get all the form fields within each section.
    const firstSectionFields = sections[0].querySelectorAll(
      'chromedash-form-field'
    );
    const secondSectionFields = sections[1].querySelectorAll(
      'chromedash-form-field'
    );

    assert.isAbove(
      firstSectionFields.length,
      0,
      'First section should have fields'
    );

    assert.isBelow(
      secondSectionFields.length,
      firstSectionFields.length,
      'Second section of same stage type should have fewer fields due to de-duplication'
    );

    // 'tag_review_status' is a feature-level field that should appear in the first section.
    const featureFieldInFirstSection = sections[0].querySelector(
      'chromedash-form-field[name="tag_review_status"]'
    );
    assert.exists(
      featureFieldInFirstSection,
      'Feature-level field should be in the first section'
    );

    // It should NOT appear in the second section.
    const featureFieldInSecondSection = sections[1].querySelector(
      'chromedash-form-field[name="tag_review_status"]'
    );
    assert.isNull(
      featureFieldInSecondSection,
      'Feature-level field should NOT be in the second section'
    );
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
