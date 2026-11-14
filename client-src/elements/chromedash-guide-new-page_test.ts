/**
 * Copyright 2026 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashGuideNewPage} from './chromedash-guide-new-page.js';
import {FEATURE_TYPES} from './form-field-enums.js';
import {ChromeStatusClient} from '../js-src/cs-client.js';
import sinon from 'sinon';

describe('chromedash-guide-new-page', () => {
  beforeEach(async () => {
    window.csClient = new ChromeStatusClient('fake_token', 1);
    sinon.stub(window.csClient, 'getBlinkComponents');
    window.csClient.getBlinkComponents.returns(Promise.resolve({}));
    sinon.stub(window.csClient, 'getWebFeatureInfos');
    window.csClient.getWebFeatureInfos.returns(
      Promise.resolve({data: [{feature_id: 'grid', status: 'newly'}]})
    );
  });

  afterEach(() => {
    window.csClient.getBlinkComponents.restore();
    window.csClient.getWebFeatureInfos.restore();
  });

  function populateRequiredFields(component: ChromedashGuideNewPage) {
    const controls = component.shadowRoot?.querySelectorAll<
      HTMLElement & {
        value?: unknown;
        required?: boolean;
        checked?: boolean;
        input?: HTMLInputElement | HTMLTextAreaElement;
      }
    >(
      'sl-input, sl-select, sl-textarea, chromedash-textarea, input, select, textarea'
    );
    for (const control of controls || []) {
      if (
        control.tagName.toLowerCase() === 'input' &&
        (control as HTMLInputElement).type === 'radio'
      ) {
        const radio = control as HTMLInputElement;
        if (radio.value === '0') {
          radio.checked = true;
        }
      } else if (control.tagName.toLowerCase() === 'sl-select') {
        control.value = 'grid';
      } else if (
        (control.hasAttribute('required') || Boolean(control.required)) &&
        !control.value
      ) {
        control.value = 'dummy value';
        if (control.input) {
          control.input.value = 'dummy value';
        }
      }
    }
    for (const fv of component.fieldValues) {
      if (fv.value === '' || fv.value === undefined || fv.value === null) {
        fv.value = 'dummy value';
      }
    }
    component.selectedWebFeature = 'grid';
    component.proposedWebFeature = 'grid';
  }

  it('renders with fake data', async () => {
    const userEmail = 'user@gmail.com';
    const component = await fixture(
      html`<chromedash-guide-new-page .userEmail=${userEmail}>
      </chromedash-guide-new-page>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashGuideNewPage);

    const subheaderDiv = component.renderRoot.querySelector('div#subheader');
    assert.exists(subheaderDiv);
    // Process and UI feedback link is clickable
    assert.include(
      subheaderDiv.innerHTML,
      'href="https://github.com/GoogleChrome/chromium-dashboard/issues/new?labels=Feedback&amp;template=process-and-guide-ux-feedback.md"'
    );

    // overview form exists and is with action path
    const overviewForm = component.renderRoot.querySelector('form')!;
    assert.exists(overviewForm);

    // owner field filled with the user email
    assert.include(overviewForm.innerHTML, userEmail);

    // feature type chromedash-form-field exists and is with four options
    const featureTypeFormField = component.renderRoot.querySelector(
      'chromedash-form-field[name="feature_type_radio_group"]'
    )!;
    assert.include(featureTypeFormField.outerHTML, 'New or changed feature');
    assert.include(featureTypeFormField.outerHTML, 'Chromium catches up');
    assert.include(
      featureTypeFormField.outerHTML,
      'No developer-visible change'
    );
    assert.include(featureTypeFormField.outerHTML, 'Feature removal');

    // feature_type field value is initialized to 0
    const featureTypeFv = component.fieldValues.find(
      fv => fv.name === 'feature_type'
    );
    assert.exists(featureTypeFv);
    assert.equal(featureTypeFv!.value, 0);

    // submit button exists
    const submitButton = component.renderRoot.querySelector<HTMLInputElement>(
      'input[type="submit"]'
    );
    assert.exists(submitButton);
    assert.include(submitButton!.style.margin, 'var(--content-padding)');
  });

  it('handleFormSubmit redirects to feature page (non-enterprise)', async () => {
    const userEmail = 'user@gmail.com';
    const component = await fixture<ChromedashGuideNewPage>(
      html`<chromedash-guide-new-page .userEmail=${userEmail}>
      </chromedash-guide-new-page>`
    );
    await component.updateComplete;
    populateRequiredFields(component);

    const navigateStub = sinon.stub(component, 'navigate');
    const createFeatureStub = sinon.stub(window.csClient, 'createFeature');
    createFeatureStub.returns(Promise.resolve({feature_id: 12345}));

    const fakeEvent = {preventDefault: sinon.spy()};
    const hiddenTokenField = component.renderRoot.querySelector(
      'input[name="token"]'
    );
    component.handleFormSubmit(fakeEvent, hiddenTokenField);

    assert.isTrue(fakeEvent.preventDefault.calledOnce);
    assert.isTrue(createFeatureStub.calledOnce);

    // Default feature type should be 0 (Incubate)
    assert.equal(createFeatureStub.firstCall.args[0].feature_type, 0);

    await new Promise(resolve => setTimeout(resolve, 0));

    assert.isTrue(navigateStub.calledOnceWith('/feature/12345'));

    createFeatureStub.restore();
    navigateStub.restore();
  });

  it('handleFormSubmit redirects to feature page (enterprise)', async () => {
    const userEmail = 'user@gmail.com';
    const component = await fixture<ChromedashGuideNewPage>(
      html`<chromedash-guide-new-page
        .userEmail=${userEmail}
        .isEnterpriseFeature=${true}
      >
      </chromedash-guide-new-page>`
    );
    await component.updateComplete;
    populateRequiredFields(component);

    const navigateStub = sinon.stub(component, 'navigate');
    const createFeatureStub = sinon.stub(window.csClient, 'createFeature');
    createFeatureStub.returns(Promise.resolve({feature_id: 54321}));

    const fakeEvent = {preventDefault: sinon.spy()};
    const hiddenTokenField = component.renderRoot.querySelector(
      'input[name="token"]'
    );
    component.handleFormSubmit(fakeEvent, hiddenTokenField);

    assert.isTrue(fakeEvent.preventDefault.calledOnce);
    assert.isTrue(createFeatureStub.calledOnce);

    // Feature type should be 4 (Enterprise)
    assert.equal(createFeatureStub.firstCall.args[0].feature_type, 4);

    await new Promise(resolve => setTimeout(resolve, 0));

    assert.isTrue(
      navigateStub.calledOnceWith('/guide/editall/54321#id_rollout_milestone')
    );

    createFeatureStub.restore();
    navigateStub.restore();
  });

  it('maybeMakeWebFeatureRequired hides web_feature for code change features and filters it on submit', async () => {
    const component = await fixture<ChromedashGuideNewPage>(
      html`<chromedash-guide-new-page .userEmail=${'user@gmail.com'}>
      </chromedash-guide-new-page>`
    );
    await component.updateComplete;

    const webFeatureRow =
      component.shadowRoot!.querySelector<HTMLElement>('#web_feature_row');
    assert.exists(webFeatureRow);

    const featureTypeIndex = component.fieldValues.findIndex(
      fv => fv.name === 'feature_type'
    );
    const webFeatureIndex = component.fieldValues.findIndex(
      fv => fv.name === 'web_feature'
    );
    assert.notEqual(featureTypeIndex, -1);
    assert.notEqual(webFeatureIndex, -1);

    // Simulate user choosing a web_feature value.
    component.setWebFeatureValue('grid');
    assert.equal(component.fieldValues[webFeatureIndex].value, 'grid');

    // Switch feature_type to FEATURE_TYPE_CODE_CHANGE_ID.
    component.handleFormFieldUpdate({
      detail: {
        value: FEATURE_TYPES.FEATURE_TYPE_CODE_CHANGE_ID[0],
        index: featureTypeIndex,
      },
    });

    assert.equal(webFeatureRow.style.display, 'none');
    // Value remains in fieldValues while editing in case user unhides the field.
    assert.equal(component.fieldValues[webFeatureIndex].value, 'grid');

    // Switch feature_type to FEATURE_TYPE_INCUBATE_ID and verify restoration.
    component.handleFormFieldUpdate({
      detail: {
        value: FEATURE_TYPES.FEATURE_TYPE_INCUBATE_ID[0],
        index: featureTypeIndex,
      },
    });

    assert.equal(webFeatureRow.style.display, '');
    assert.equal(component.fieldValues[webFeatureIndex].value, 'grid');

    // Switch back to FEATURE_TYPE_CODE_CHANGE_ID in propose mode and submit the form.
    component.handleWebFeatureModeChange('propose');
    await component.updateComplete;

    component.handleFormFieldUpdate({
      detail: {
        value: FEATURE_TYPES.FEATURE_TYPE_CODE_CHANGE_ID[0],
        index: featureTypeIndex,
      },
    });
    await component.updateComplete;

    const explainerField = component.shadowRoot!.querySelector<HTMLElement>(
      'chromedash-form-field[name="explainer_links"]'
    );
    assert.exists(explainerField);
    assert.equal(explainerField!.style.display, 'none');

    populateRequiredFields(component);
    // Leave proposed web_feature and explainer_links empty while in code-change mode.
    component.proposedWebFeature = '';
    const explainerIndex = component.fieldValues.findIndex(
      fv => fv.name === 'explainer_links'
    );
    if (explainerIndex !== -1) {
      component.fieldValues[explainerIndex].value = '';
    }
    const explainerTextarea =
      explainerField!.querySelector<HTMLTextAreaElement>('chromedash-textarea');
    if (explainerTextarea) {
      explainerTextarea.value = '';
    }

    const navigateStub = sinon.stub(component, 'navigate');
    const createFeatureStub = sinon.stub(window.csClient, 'createFeature');
    createFeatureStub.returns(Promise.resolve({feature_id: 12345}));

    const fakeEvent = {preventDefault: sinon.spy()};
    const hiddenTokenField = component.renderRoot.querySelector(
      'input[name="token"]'
    );
    component.handleFormSubmit(fakeEvent, hiddenTokenField);

    assert.equal(
      component.fieldValues.findIndex(fv => fv.name === 'web_feature'),
      -1
    );
    assert.equal(
      component.fieldValues.findIndex(fv => fv.name === 'explainer_links'),
      -1
    );
    assert.isTrue(createFeatureStub.calledOnce);
    assert.equal(
      createFeatureStub.firstCall.args[0].feature_type,
      FEATURE_TYPES.FEATURE_TYPE_CODE_CHANGE_ID[0]
    );
    assert.notProperty(createFeatureStub.firstCall.args[0], 'web_feature');
    assert.notProperty(createFeatureStub.firstCall.args[0], 'explainer_links');

    await new Promise(resolve => setTimeout(resolve, 0));

    assert.isTrue(navigateStub.calledOnceWith('/feature/12345'));

    createFeatureStub.restore();
    navigateStub.restore();
  });

  it('renders web-feature radio buttons and selects existing web-feature', async () => {
    const component = await fixture<ChromedashGuideNewPage>(
      html`<chromedash-guide-new-page .userEmail=${'user@gmail.com'}>
      </chromedash-guide-new-page>`
    );
    await component.updateComplete;

    const existingRadio = component.shadowRoot!.querySelector<HTMLInputElement>(
      '#web_feature_mode_existing'
    );
    const proposeRadio = component.shadowRoot!.querySelector<HTMLInputElement>(
      '#web_feature_mode_propose'
    );
    assert.exists(existingRadio);
    assert.exists(proposeRadio);
    assert.isTrue(existingRadio!.checked);
    assert.isFalse(proposeRadio!.checked);

    const selectEl = component.shadowRoot?.querySelector<HTMLElement>(
      'sl-select[name="web_feature"]'
    );
    assert.exists(selectEl);
    assert.isTrue(selectEl!.hasAttribute('required'));

    // Explainer links field should not be present in existing mode.
    const explainerField = component.shadowRoot?.querySelector(
      'chromedash-form-field[name="explainer_links"]'
    );
    assert.isNull(explainerField);

    // Simulate selecting a feature.
    component.handleSelectWebFeature({
      target: {value: 'grid'},
    } as unknown as Event);
    await component.updateComplete;

    const webFeatureFv = component.fieldValues.find(
      fv => fv.name === 'web_feature'
    );
    assert.exists(webFeatureFv);
    assert.equal(webFeatureFv?.value, 'grid');

    // Link to webstatus.dev should be rendered.
    const webstatusLink = component.shadowRoot?.querySelector(
      'a[href="https://webstatus.dev/features/grid"]'
    );
    assert.exists(webstatusLink);
    assert.include(webstatusLink!.textContent!, 'grid');

    const helpTextEl = component.shadowRoot?.querySelector(
      '#web_feature_row .helptext'
    );
    assert.exists(helpTextEl);
    assert.include(helpTextEl!.textContent!, 'web-features project');
  });

  it('switches to propose web-feature mode and submits proposed value and explainer links', async () => {
    const component = await fixture<ChromedashGuideNewPage>(
      html`<chromedash-guide-new-page .userEmail=${'user@gmail.com'}>
      </chromedash-guide-new-page>`
    );
    await component.updateComplete;

    // Switch to propose mode.
    component.handleWebFeatureModeChange('propose');
    await component.updateComplete;

    const helpTextEl = component.shadowRoot?.querySelector(
      '#web_feature_row .helptext'
    );
    assert.exists(helpTextEl);
    assert.include(
      helpTextEl!.textContent!,
      'Enter a proposed web-feature ID consisting of lowercase letters and dashes.'
    );

    const inputEl = component.shadowRoot?.querySelector<HTMLElement>(
      'sl-input[name="web_feature"]'
    );
    assert.exists(inputEl);
    assert.isTrue(inputEl!.hasAttribute('required'));
    assert.equal(inputEl!.previousElementSibling?.textContent, 'proposed/');

    // Explainer links should now be rendered across the full table rather than inside the td.
    const explainerField = component.shadowRoot?.querySelector(
      'chromedash-form-field[name="explainer_links"]'
    );
    assert.exists(explainerField);
    assert.notEqual(explainerField!.parentElement?.tagName.toLowerCase(), 'td');
    assert.isTrue(explainerField!.hasAttribute('forcerequired'));

    // Webstatus link should NOT be present.
    const webstatusLink = component.shadowRoot?.querySelector(
      'a[href*="webstatus.dev"]'
    );
    assert.isNull(webstatusLink);

    // Simulate typing a proposed web_feature.
    component.handleInputWebFeature({
      target: {value: 'proposed-feature-id'},
    } as unknown as Event);

    const webFeatureFv = component.fieldValues.find(
      fv => fv.name === 'web_feature'
    );
    assert.exists(webFeatureFv);
    assert.equal(webFeatureFv?.value, 'proposed-feature-id');

    // Simulate filling out explainer links.
    const explainerIndex = component.fieldValues.findIndex(
      fv => fv.name === 'explainer_links'
    );
    assert.notEqual(explainerIndex, -1);
    component.handleFormFieldUpdate({
      detail: {
        value: 'https://github.com/example/explainer',
        index: explainerIndex,
      },
    });

    populateRequiredFields(component);
    component.proposedWebFeature = 'proposed-feature-id';
    component.setWebFeatureValue('proposed-feature-id');
    const webFeatureInput =
      component.shadowRoot?.querySelector<HTMLInputElement>(
        'sl-input[name="web_feature"]'
      );
    if (webFeatureInput) {
      webFeatureInput.value = 'proposed-feature-id';
    }
    component.fieldValues[explainerIndex].value =
      'https://github.com/example/explainer';
    const explainerControl = component.shadowRoot?.querySelector(
      'chromedash-form-field[name="explainer_links"]'
    );
    const textarea = explainerControl?.querySelector<HTMLTextAreaElement>(
      'chromedash-textarea'
    );
    if (textarea) {
      textarea.value = 'https://github.com/example/explainer';
    }

    const createFeatureStub = sinon.stub(window.csClient, 'createFeature');
    createFeatureStub.returns(Promise.resolve({feature_id: 12345}));
    sinon.stub(component, 'navigate');

    const form = component.shadowRoot!.querySelector('form')!;
    form.dispatchEvent(new Event('submit', {bubbles: true, cancelable: true}));

    assert.isTrue(createFeatureStub.calledOnce);
    const submitArg = createFeatureStub.firstCall.args[0];
    assert.equal(submitArg.web_feature, 'proposed/proposed-feature-id');
    assert.equal(
      submitArg.explainer_links,
      'https://github.com/example/explainer'
    );

    createFeatureStub.restore();
  });

  it('does not render web_feature for enterprise features', async () => {
    const component = await fixture<ChromedashGuideNewPage>(
      html`<chromedash-guide-new-page
        .userEmail=${'user@gmail.com'}
        .isEnterpriseFeature=${true}
      >
      </chromedash-guide-new-page>`
    );
    await component.updateComplete;

    const webFeatureRow =
      component.shadowRoot?.querySelector('#web_feature_row');
    assert.isNull(webFeatureRow);
  });

  it('renders widely supported warning in existing mode when feature_type is incubate', async () => {
    const component = await fixture<ChromedashGuideNewPage>(
      html`<chromedash-guide-new-page .userEmail=${'user@gmail.com'}>
      </chromedash-guide-new-page>`
    );
    await component.updateComplete;

    component.webFeatureInfos = [
      {feature_id: 'grid', status: 'widely'},
      {feature_id: 'subgrid', status: 'limited'},
    ];
    component.webFeatureChoices = {
      grid: ['grid', 'grid'],
      subgrid: ['subgrid', 'subgrid'],
    };
    await component.updateComplete;

    // Select 'subgrid' (not widely supported)
    component.handleSelectWebFeature({
      target: {value: 'subgrid'},
    } as unknown as Event);
    await component.updateComplete;

    assert.isFalse(component.shouldDisplayWidelySupportedWarning());
    assert.notInclude(
      component.shadowRoot?.innerHTML || '',
      'This web feature is already widely supported'
    );

    // Select 'grid' (widely supported) while feature_type is 0 (New or changed feature)
    component.handleSelectWebFeature({
      target: {value: 'grid'},
    } as unknown as Event);
    await component.updateComplete;

    assert.isTrue(component.shouldDisplayWidelySupportedWarning());
    assert.include(
      component.shadowRoot?.innerHTML || '',
      'This web feature is already widely supported, are you sure that you are incubating a change to it?'
    );

    // Change feature_type to 1 (Existing feature implementation)
    const featureTypeIndex = component.fieldValues.findIndex(
      fv => fv.name === 'feature_type'
    );
    assert.notEqual(featureTypeIndex, -1);
    component.handleFormFieldUpdate({
      detail: {value: 1, index: featureTypeIndex},
    });
    await component.updateComplete;

    assert.isFalse(component.shouldDisplayWidelySupportedWarning());
    assert.notInclude(
      component.shadowRoot?.innerHTML || '',
      'This web feature is already widely supported'
    );
  });

  it('blocks submission when in existing mode and web_feature is empty', async () => {
    const component = await fixture<ChromedashGuideNewPage>(
      html`<chromedash-guide-new-page .userEmail=${'user@gmail.com'}>
      </chromedash-guide-new-page>`
    );
    await component.updateComplete;

    populateRequiredFields(component);
    // Explicitly clear web_feature in existing mode
    component.selectedWebFeature = '';
    component.setWebFeatureValue('');
    const selectEl = component.shadowRoot?.querySelector<HTMLSelectElement>(
      'sl-select[name="web_feature"]'
    );
    if (selectEl) {
      selectEl.value = '';
    }

    const createFeatureStub = sinon.stub(window.csClient, 'createFeature');
    const reportValiditySpy = sinon.spy(component, 'reportControlValidity');
    const fakeEvent = {preventDefault: sinon.spy()};
    const hiddenTokenField = component.renderRoot.querySelector(
      'input[name="token"]'
    );
    component.handleFormSubmit(fakeEvent, hiddenTokenField);

    assert.isFalse(createFeatureStub.called);
    assert.isTrue(reportValiditySpy.called);
    createFeatureStub.restore();
  });

  it('blocks submission when in propose mode and explainer_links is empty', async () => {
    const component = await fixture<ChromedashGuideNewPage>(
      html`<chromedash-guide-new-page .userEmail=${'user@gmail.com'}>
      </chromedash-guide-new-page>`
    );
    await component.updateComplete;

    populateRequiredFields(component);
    component.handleWebFeatureModeChange('propose');
    await component.updateComplete;

    component.proposedWebFeature = 'proposed-id';
    component.setWebFeatureValue('proposed-id');
    const explainerIdx = component.fieldValues.findIndex(
      fv => fv.name === 'explainer_links'
    );
    if (explainerIdx !== -1) {
      component.fieldValues[explainerIdx].value = '';
    }

    const createFeatureStub = sinon.stub(window.csClient, 'createFeature');
    const reportValiditySpy = sinon.spy(component, 'reportControlValidity');
    const fakeEvent = {preventDefault: sinon.spy()};
    const hiddenTokenField = component.renderRoot.querySelector(
      'input[name="token"]'
    );
    component.handleFormSubmit(fakeEvent, hiddenTokenField);

    assert.isFalse(createFeatureStub.called);
    assert.isTrue(reportValiditySpy.called);
    createFeatureStub.restore();
  });

  it('blocks submission when a required field like name is empty', async () => {
    const component = await fixture<ChromedashGuideNewPage>(
      html`<chromedash-guide-new-page .userEmail=${'user@gmail.com'}>
      </chromedash-guide-new-page>`
    );
    await component.updateComplete;

    populateRequiredFields(component);
    const nameInput = component.shadowRoot?.querySelector<HTMLInputElement>(
      'sl-input[name="name"]'
    );
    if (nameInput) {
      nameInput.value = '';
    }

    const createFeatureStub = sinon.stub(window.csClient, 'createFeature');
    const fakeEvent = {preventDefault: sinon.spy()};
    const hiddenTokenField = component.renderRoot.querySelector(
      'input[name="token"]'
    );
    component.handleFormSubmit(fakeEvent, hiddenTokenField);

    assert.isFalse(createFeatureStub.called);
    createFeatureStub.restore();
  });

  it('resets submitting on error and does not duplicate fieldValues on re-render', async () => {
    const userEmail = 'user@gmail.com';
    const component = await fixture<ChromedashGuideNewPage>(
      html`<chromedash-guide-new-page .userEmail=${userEmail}>
      </chromedash-guide-new-page>`
    );
    await component.updateComplete;

    populateRequiredFields(component);
    const initialLength = component.fieldValues.length;
    const createFeatureStub = sinon
      .stub(window.csClient, 'createFeature')
      .returns(Promise.reject(new Error('Create failed')));

    const fakeEvent = {preventDefault: sinon.spy()};
    const hiddenTokenField = component.renderRoot.querySelector(
      'input[name="token"]'
    );
    component.handleFormSubmit(fakeEvent, hiddenTokenField);
    await component.updateComplete;
    assert.equal(component.fieldValues.length, initialLength);

    await new Promise(resolve => setTimeout(resolve, 0));
    assert.isFalse(component.submitting);

    createFeatureStub.restore();
  });

  it('populates owner when userEmail arrives after initial render and updates fieldValues when isEnterpriseFeature changes', async () => {
    const component = await fixture<ChromedashGuideNewPage>(
      html`<chromedash-guide-new-page></chromedash-guide-new-page>`
    );
    await component.updateComplete;

    const ownerFieldBefore = component.fieldValues.find(
      fv => fv.name === 'owner_emails'
    );
    assert.exists(ownerFieldBefore);
    assert.isEmpty(ownerFieldBefore.value);

    // Simulate userEmail arriving asynchronously
    component.userEmail = 'late-user@chromium.org';
    await component.updateComplete;

    const ownerFieldAfter = component.fieldValues.find(
      fv => fv.name === 'owner_emails'
    );
    assert.equal(ownerFieldAfter?.value, 'late-user@chromium.org');

    // Switching to enterprise feature should re-align and truncate fieldValues
    const nonEnterpriseLength = component.fieldValues.length;
    component.isEnterpriseFeature = true;
    await component.updateComplete;

    assert.isBelow(component.fieldValues.length, nonEnterpriseLength);
    assert.isUndefined(
      component.fieldValues.find(fv => fv.name === 'feature_type')
    );
  });
});
