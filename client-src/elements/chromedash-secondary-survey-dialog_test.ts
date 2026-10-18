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
import {fixture, assert, expect, elementUpdated} from '@open-wc/testing';
import {SlTextarea} from '@shoelace-style/shoelace';
import '@shoelace-style/shoelace/dist/components/dialog/dialog.js';
import '@shoelace-style/shoelace/dist/components/input/input.js';
import '@shoelace-style/shoelace/dist/components/select/select.js';
import '@shoelace-style/shoelace/dist/components/option/option.js';
import sinon from 'sinon';
import './chromedash-secondary-survey-dialog.js';
import './chromedash-na-rationale-dialog.js';
import {
  isTestingGate,
  shouldShowSecondarySurveyDialog,
  ChromedashSecondarySurveyDialog,
} from './chromedash-secondary-survey-dialog.js';
import {openAddStageDialog} from './chromedash-add-stage-dialog.js';
import {
  dialogTypes,
  openFinalizeExtensionDialog,
  openPrereqsDialog,
} from './chromedash-ot-prereqs-dialog.js';
import {openPostIntentDialog} from './chromedash-post-intent-dialog.js';
import {ChromedashNaRationaleDialog} from './chromedash-na-rationale-dialog.js';
import {ChromeStatusClient} from '../js-src/cs-client.js';
import {GATE_TYPES} from './form-field-enums.js';

describe('chromedash-secondary-survey-dialog', () => {
  let component: ChromedashSecondarySurveyDialog;

  beforeEach(async () => {
    component = await fixture<ChromedashSecondarySurveyDialog>(html`
      <chromedash-secondary-survey-dialog></chromedash-secondary-survey-dialog>
    `);
    document.body.appendChild(component);
  });

  afterEach(() => {
    component.remove();
  });

  it('can detect the type of review gate', () => {
    assert.isTrue(isTestingGate({gate_type: GATE_TYPES.TESTING_PLAN}));
    assert.isTrue(isTestingGate({gate_type: GATE_TYPES.TESTING_SHIP}));
    assert.isFalse(isTestingGate({gate_type: GATE_TYPES.API_SHIP}));
    assert.isFalse(isTestingGate({gate_type: GATE_TYPES.PRIVACY_SHIP}));
  });

  it('can will show the dialog based on the type of review gate', () => {
    assert.isTrue(
      shouldShowSecondarySurveyDialog({gate_type: GATE_TYPES.TESTING_PLAN})
    );
    assert.isTrue(
      shouldShowSecondarySurveyDialog({gate_type: GATE_TYPES.TESTING_SHIP})
    );
    assert.isFalse(
      shouldShowSecondarySurveyDialog({gate_type: GATE_TYPES.API_SHIP})
    );
    assert.isFalse(
      shouldShowSecondarySurveyDialog({gate_type: GATE_TYPES.PRIVACY_SHIP})
    );
  });

  it('is an instance of ChromedashSecondarySurveyDialog', () => {
    assert.instanceOf(component, ChromedashSecondarySurveyDialog);
  });

  it('renders the testing form', async () => {
    component.gate = {gate_type: GATE_TYPES.TESTING_PLAN};
    await elementUpdated(component);
    const radios = component.shadowRoot?.querySelector('sl-radio-group');
    assert.isNotNull(radios, 'Testing form should contain radio groups');
    const button = component.shadowRoot?.querySelector('#generate_button');
    assert.isNotNull(button, 'Testing form should contain generate button');
  });

  it('generates comments that contain the text entered', async () => {
    component.gate = {gate_type: GATE_TYPES.TESTING_PLAN};
    let actual: string = '';
    component.resolve = (commentText?: string) => {
      actual = commentText || '';
    };
    await elementUpdated(component);
    const textarea =
      component.shadowRoot?.querySelector<SlTextarea>('sl-textarea');
    textarea!.value = 'This is a unique string';
    component.generateTestingComment();
    assert.include(actual, 'This is a unique string');
  });

  it('clears form fields when show() is called', async () => {
    component.gate = {gate_type: GATE_TYPES.TESTING_PLAN};
    await elementUpdated(component);
    const textarea =
      component.shadowRoot!.querySelector<SlTextarea>('#performance_tests')!;
    textarea.value = 'Previous value';
    component.show();
    assert.equal(textarea.value, '');
  });

  it('updates singleton add-stage-dialog properties and resets select on reopen', async () => {
    await openAddStageDialog(100, 0);
    const dialogEl = document.querySelector(
      'chromedash-add-stage-dialog'
    ) as any;
    assert.exists(dialogEl);
    assert.equal(dialogEl.featureId, 100);
    assert.equal(dialogEl.featureType, 0);

    dialogEl.stageCreateSelect.value = '160';
    dialogEl.checkCanSubmit();
    assert.isTrue(dialogEl.canSubmit);

    const handler = sinon.spy();
    await openAddStageDialog(200, 1, handler);
    assert.equal(dialogEl.featureId, 200);
    assert.equal(dialogEl.featureType, 1);
    assert.equal(dialogEl.onSubmitCustomHandler, handler);
    assert.isFalse(dialogEl.canSubmit);
    assert.equal(dialogEl.stageCreateSelect.value, '0');
    dialogEl.checkCanSubmit();
    assert.isFalse(dialogEl.canSubmit);
  });

  it('updates singleton ot-prereqs-dialog properties on reopen', async () => {
    await openPrereqsDialog(100, {id: 10}, dialogTypes.CREATION);
    const dialogEl = document.querySelector(
      'chromedash-ot-prereqs-dialog'
    ) as any;
    assert.exists(dialogEl);
    assert.equal(dialogEl.featureId, 100);
    assert.equal(dialogEl.stage.id, 10);
    assert.equal(dialogEl.dialogType, dialogTypes.CREATION);

    await openFinalizeExtensionDialog(
      200,
      {id: 20},
      135,
      dialogTypes.FINALIZE_EXTENSION
    );
    assert.equal(dialogEl.featureId, 200);
    assert.equal(dialogEl.stage.id, 20);
    assert.equal(dialogEl.milestone, 135);
    assert.equal(dialogEl.dialogType, dialogTypes.FINALIZE_EXTENSION);
    assert.include(
      dialogEl.shadowRoot.innerHTML,
      'no intent thread link has been detected'
    );
  });

  it('updates singleton post-intent-dialog properties and trims CC emails on submit', async () => {
    window.csClient = new ChromeStatusClient('fake_token', 1);
    const postStub = sinon
      .stub(window.csClient, 'postIntentToBlinkDev')
      .returns(new Promise(() => {}));

    await openPostIntentDialog(100, 10, ['a@example.com'], 1);
    const dialogEl = document.querySelector(
      'chromedash-post-intent-dialog'
    ) as any;
    assert.exists(dialogEl);
    assert.equal(dialogEl.featureId, 100);

    await openPostIntentDialog(200, 20, ['b@example.com', 'c@example.com'], 2);
    assert.equal(dialogEl.featureId, 200);
    assert.equal(dialogEl.stageId, 20);
    assert.equal(dialogEl.gateId, 2);

    const input = dialogEl.shadowRoot.querySelector('sl-input');
    input.value = ' b@example.com , c@example.com , ';
    dialogEl.submitIntent();

    assert.isTrue(
      postStub.calledOnceWithExactly(200, 20, {
        gate_id: 2,
        intent_cc_emails: ['b@example.com', 'c@example.com'],
      })
    );
    postStub.restore();
  });

  it('clears na-rationale-dialog textarea when openOn is called again', async () => {
    const naDialog = await fixture<ChromedashNaRationaleDialog>(html`
      <chromedash-na-rationale-dialog></chromedash-na-rationale-dialog>
    `);
    naDialog.openOn({team_name: 'Privacy'} as any, () => {});
    await elementUpdated(naDialog);
    naDialog.rationaleRef.value!.value = 'Old rationale';

    naDialog.openOn({team_name: 'Security'} as any, () => {});
    assert.equal(naDialog.rationaleRef.value!.value, '');
  });
});
