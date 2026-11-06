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

import {assert, fixture} from '@open-wc/testing';
import {html} from 'lit';
import sinon from 'sinon';
import {ChromeStatusClient} from '../js-src/cs-client.js';
import {ChromedashOTCreationPage} from './chromedash-ot-creation-page.js';
import {
  OT_SETUP_STATUS_OPTIONS,
  USE_COUNTER_TYPE_WEBDXFEATURE,
} from './form-field-enums.js';
import './chromedash-toast.js';

describe('chromedash-ot-creation-page', () => {
  const validFeature = {
    id: 123456,
    name: 'feature one',
    stages: [],
  };

  const validStage = {
    id: 10,
    feature_id: 123456,
    stage_type: 150,
    ot_setup_status: OT_SETUP_STATUS_OPTIONS.OT_NOT_CREATED,
    ot_require_approvals: true,
    ot_approval_buganizer_component: 999888,
    ot_approval_buganizer_custom_field_id: 111222,
    ot_approval_group_email: 'approvers@chromium.org',
    ot_approval_criteria_url: 'https://example.com/criteria',
    ot_is_deprecation_trial: true,
  };

  const validGates = {
    gates: [{id: 1, stage_id: 10, state: 5}], // APPROVED = 5
    possible_owners: {},
  };

  beforeEach(async () => {
    await fixture(html`<chromedash-toast></chromedash-toast>`);
    window.csClient = new ChromeStatusClient('fake_token', 1);
    sinon.stub(window.csClient, 'getFeature').resolves(validFeature as any);
    sinon.stub(window.csClient, 'getStage').resolves(validStage as any);
    sinon.stub(window.csClient, 'getGates').resolves(validGates as any);
    sinon.stub(window.csClient, 'getBlinkComponents').resolves({});
  });

  afterEach(() => {
    sinon.restore();
  });

  it('populates existing approval field values, sets isDeprecationTrial, and passes stageId/feature to fields', async () => {
    const component = await fixture<ChromedashOTCreationPage>(
      html`<chromedash-ot-creation-page
        .featureId=${123456}
        .stageId=${10}
        .userEmail=${'owner@chromium.org'}
      >
      </chromedash-ot-creation-page>`
    );
    assert.instanceOf(component, ChromedashOTCreationPage);
    await component.updateComplete;

    assert.isTrue(component.showApprovalsFields);
    assert.isTrue(component.isDeprecationTrial);

    const buganizerComp = component.fieldValues.find(
      fv => fv.name === 'ot_approval_buganizer_component'
    );
    const customFieldId = component.fieldValues.find(
      fv => fv.name === 'ot_approval_buganizer_custom_field_id'
    );
    const groupEmail = component.fieldValues.find(
      fv => fv.name === 'ot_approval_group_email'
    );
    const criteriaUrl = component.fieldValues.find(
      fv => fv.name === 'ot_approval_criteria_url'
    );

    assert.equal(buganizerComp?.value, 999888);
    assert.equal(customFieldId?.value, 111222);
    assert.equal(groupEmail?.value, 'approvers@chromium.org');
    assert.equal(criteriaUrl?.value, 'https://example.com/criteria');

    const formFieldEl = component.renderRoot.querySelector(
      'chromedash-form-field[name="ot_display_name"]'
    ) as any;
    assert.exists(formFieldEl);
    assert.equal(formFieldEl.stageId, 10);
    assert.deepEqual(formFieldEl.feature, validFeature);
  });

  it('prefixes use counter without duplicating prefix and resets submitting on error', async () => {
    const nonDeprecationStage = {
      ...validStage,
      ot_is_deprecation_trial: false,
      ot_webfeature_use_counter: 'WebDXFeature::MyFeature',
    };
    (window.csClient.getStage as sinon.SinonStub).resolves(
      nonDeprecationStage as any
    );

    const createOTStub = sinon
      .stub(window.csClient, 'createOriginTrial')
      .rejects(new Error('Network error'));

    const component = await fixture<ChromedashOTCreationPage>(
      html`<chromedash-ot-creation-page .featureId=${123456} .stageId=${10}>
      </chromedash-ot-creation-page>`
    );
    await component.updateComplete;

    assert.isFalse(component.isDeprecationTrial);
    component.webfeatureUseCounterType = USE_COUNTER_TYPE_WEBDXFEATURE;

    const fakeEvent = {preventDefault: sinon.spy()};
    await component.handleFormSubmit(fakeEvent);
    await new Promise(resolve => setTimeout(resolve, 0));

    assert.isTrue(createOTStub.calledOnce);
    const submittedBody = createOTStub.firstCall.args[2];
    assert.equal(
      submittedBody.ot_webfeature_use_counter.value,
      'WebDXFeature::MyFeature'
    );
    assert.isFalse(component.submitting);
  });
});
