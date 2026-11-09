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

    // submit button exists
    const submitButton = component.renderRoot.querySelector(
      'input[type="submit"]'
    );
    assert.exists(submitButton);
  });

  it('handleFormSubmit redirects to feature page (non-enterprise)', async () => {
    const userEmail = 'user@gmail.com';
    const component = await fixture<ChromedashGuideNewPage>(
      html`<chromedash-guide-new-page .userEmail=${userEmail}>
      </chromedash-guide-new-page>`
    );
    await component.updateComplete;

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

    // Switch back to FEATURE_TYPE_CODE_CHANGE_ID and submit the form.
    component.handleFormFieldUpdate({
      detail: {
        value: FEATURE_TYPES.FEATURE_TYPE_CODE_CHANGE_ID[0],
        index: featureTypeIndex,
      },
    });

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
    assert.isTrue(createFeatureStub.calledOnce);
    assert.equal(
      createFeatureStub.firstCall.args[0].feature_type,
      FEATURE_TYPES.FEATURE_TYPE_CODE_CHANGE_ID[0]
    );
    assert.notProperty(createFeatureStub.firstCall.args[0], 'web_feature');

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

    const selectEl = component.shadowRoot?.querySelector(
      'sl-select[name="web_feature"]'
    );
    assert.exists(selectEl);

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

    const inputEl = component.shadowRoot?.querySelector(
      'sl-input[name="web_feature"]'
    );
    assert.exists(inputEl);

    // Explainer links should now be rendered below the input.
    const explainerField = component.shadowRoot?.querySelector(
      'chromedash-form-field[name="explainer_links"]'
    );
    assert.exists(explainerField);

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

    const createFeatureStub = sinon.stub(window.csClient, 'createFeature');
    createFeatureStub.returns(Promise.resolve({feature_id: 12345}));
    sinon.stub(component, 'navigate');

    const fakeEvent = {preventDefault: sinon.spy()};
    const hiddenTokenField = component.renderRoot.querySelector(
      'input[name="token"]'
    );
    component.handleFormSubmit(fakeEvent, hiddenTokenField);

    assert.isTrue(createFeatureStub.calledOnce);
    const submitArg = createFeatureStub.firstCall.args[0];
    assert.equal(submitArg.web_feature, 'proposed-feature-id');
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
});
