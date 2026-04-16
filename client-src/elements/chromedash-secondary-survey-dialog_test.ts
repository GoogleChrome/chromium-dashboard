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
import sinon from 'sinon';
import './chromedash-secondary-survey-dialog.js';
import {
  isTestingGate,
  shouldShowSecondarySurveyDialog,
  ChromedashSecondarySurveyDialog,
} from './chromedash-secondary-survey-dialog.js';
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
});
