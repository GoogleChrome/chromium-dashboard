import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashGuideVerifyAccuracyPage} from './chromedash-guide-verify-accuracy-page';
import './chromedash-toast';
import {ChromeStatusClient} from '../js-src/cs-client';
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
    ],
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

  /* window.csClient and <chromedash-toast> are initialized at _base.html
   * which are not available here, so we initialize them before each test.
   * We also stub out the API calls here so that they return test data. */
  let getFeatureStub;
  let updateFeatureStub;
  let ensureTokenStub;

  beforeEach(async () => {
    await fixture(html`<chromedash-toast></chromedash-toast>`);
    window.csClient = new ChromeStatusClient('fake_token', 1);
    getFeatureStub = sinon.stub(window.csClient, 'getFeature');
    updateFeatureStub = sinon
      .stub(window.csClient, 'updateFeature')
      .resolves({});
    ensureTokenStub = sinon
      .stub(window.csClient, 'ensureTokenIsValid')
      .resolves();
  });

  afterEach(() => {
    getFeatureStub.restore();
    updateFeatureStub.restore();
    ensureTokenStub.restore();
  });

  it('renders with no data', async () => {
    const invalidFeaturePromise = Promise.reject(
      new Error('Got error response from server')
    );
    getFeatureStub.withArgs(0).returns(invalidFeaturePromise);

    const component = await fixture<ChromedashGuideVerifyAccuracyPage>(
      html`<chromedash-guide-verify-accuracy-page></chromedash-guide-verify-accuracy-page>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashGuideVerifyAccuracyPage);

    // invalid feature requests would trigger the toast to show message
    const toastEl = document.querySelector('chromedash-toast');
    const toastMsgSpan = toastEl?.shadowRoot?.querySelector('span#msg');
    assert.include(
      toastMsgSpan?.innerHTML,
      'Some errors occurred. Please refresh the page or try again later.'
    );
  });

  it('renders skeletons while loading', async () => {
    const featureId = 123456;
    const neverResolves = new Promise(() => {});
    getFeatureStub.withArgs(featureId).returns(neverResolves);

    const component = await fixture<ChromedashGuideVerifyAccuracyPage>(
      html`<chromedash-guide-verify-accuracy-page
        .featureId=${featureId}
      ></chromedash-guide-verify-accuracy-page>`
    );
    await component.updateComplete;

    const skeleton = component.renderRoot.querySelector('sl-skeleton');
    assert.exists(skeleton);
    const form = component.renderRoot.querySelector(
      'form[name="feature_form"]'
    );
    assert.isNull(form);
  });

  it('renders with fake data', async () => {
    const featureId = 123456;
    getFeatureStub.withArgs(featureId).returns(validFeaturePromise);

    const component = await fixture(
      html`<chromedash-guide-verify-accuracy-page
        .featureId=${featureId}
      ></chromedash-guide-verify-accuracy-page>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashGuideVerifyAccuracyPage);

    await component.updateComplete;

    const subheaderDiv = component.renderRoot.querySelector('div#subheader');
    assert.exists(subheaderDiv);
    // subheader title is correct and clickable
    assert.include(subheaderDiv.innerHTML, 'href="/feature/123456"');
    assert.include(subheaderDiv.innerHTML, 'Verify feature data for');

    // feature form, hidden token field, and submit/cancel buttons exist
    const featureForm = component.renderRoot.querySelector(
      'form[name="feature_form"]'
    );
    assert.exists(featureForm);
    assert.include(featureForm.innerHTML, '<input type="hidden" name="token">');
    assert.include(featureForm.innerHTML, '<section class="final_buttons">');

    // Renders the correct "last verified" title
    const title = component.renderRoot.querySelector('h3');
    assert.isNotNull(title);
    assert.include(
      title.textContent,
      'Accuracy last verified at time of creation.'
    );
  });

  it('renders all form sections and handles duplicate stage types', async () => {
    const featureId = 123456;
    // This promise has stage types [110, 160, 160]
    getFeatureStub.withArgs(featureId).returns(validFeaturePromise);

    const component = await fixture<ChromedashGuideVerifyAccuracyPage>(
      html`<chromedash-guide-verify-accuracy-page
        .featureId=${featureId}
      ></chromedash-guide-verify-accuracy-page>`
    );
    await component.updateComplete;

    const formTable = component.renderRoot.querySelector(
      'chromedash-form-table'
    );
    assert.exists(formTable);
    const titles = formTable.querySelectorAll('h3');
    // Expect 4 sections: Metadata, Stage (160), Stage (160) #2, Confirmation
    assert.equal(titles.length, 4);

    // The 2nd section (index 1) should be the first stage 160.
    const firstOTHeader = titles[1];
    assert.notInclude(firstOTHeader.textContent, ' 2');

    // The 3rd section (index 2) should be the *duplicate* stage 160.
    const duplicateStageHeader = titles[2];
    // Its text content should be 'Some Name 2'
    assert.include(duplicateStageHeader.textContent, ' 2');

    // The 4th section (index 3) should be the confirmation.
    const confirmationHeader = titles[3];
    assert.include(confirmationHeader.textContent, 'Verify Accuracy');
  });

  it('handles form field updates', async () => {
    const featureId = 123456;
    getFeatureStub.withArgs(featureId).returns(validFeaturePromise);
    const component = await fixture<ChromedashGuideVerifyAccuracyPage>(
      html`<chromedash-guide-verify-accuracy-page
        .featureId=${featureId}
      ></chromedash-guide-verify-accuracy-page>`
    );
    await component.updateComplete;

    // The 'accurate_as_of' field is special (touched=true).
    const accurateAsOf = component.fieldValues.find(fv => fv.name === 'accurate_as_of');
    assert.exists(accurateAsOf);
    assert.isTrue(accurateAsOf.touched);

    // Find another form field (e.g., the second one)
    const field = component.renderRoot.querySelector(
      'chromedash-form-field[index="1"]'
    );
    assert.exists(field);
    const fieldInfo = component.fieldValues[1];
    assert.isFalse(fieldInfo.touched);

    // Simulate an update event
    const event = new CustomEvent('form-field-update', {
      detail: {
        index: 1,
        value: 'new value',
      },
    });
    field.dispatchEvent(event);

    // Check component state
    assert.equal(component.fieldValues[1].value, 'new value');
    assert.isTrue(component.fieldValues[1].touched);
  });
});
