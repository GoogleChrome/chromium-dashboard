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
import {ChromedashOTExtensionPage} from './chromedash-ot-extension-page.js';
import './chromedash-toast.js';

describe('chromedash-ot-extension-page', () => {
  const validFeature = {
    id: 123456,
    name: 'feature one',
    stages: [],
  };

  const validStage = {
    id: 10,
    feature_id: 123456,
    stage_type: 150,
  };

  let fetchStub: sinon.SinonStub;

  beforeEach(async () => {
    await fixture(html`<chromedash-toast></chromedash-toast>`);
    window.csClient = new ChromeStatusClient('fake_token', 1);
    sinon.stub(window.csClient, 'getFeature').resolves(validFeature as any);
    sinon.stub(window.csClient, 'getStage').resolves(validStage as any);
    sinon.stub(window.csClient, 'getBlinkComponents').resolves({});
    fetchStub = sinon.stub(window, 'fetch').resolves({
      json: () =>
        Promise.resolve({
          mstones: [{mstone: '130', stable_date: '2026-06-01T00:00:00'}],
        }),
    } as any);
  });

  afterEach(() => {
    sinon.restore();
  });

  it('initializes fieldValues once without duplicating on re-render and binds value/stageId/feature', async () => {
    const component = await fixture<ChromedashOTExtensionPage>(
      html`<chromedash-ot-extension-page
        .featureId=${123456}
        .stageId=${10}
        .userEmail=${'owner@chromium.org'}
      >
      </chromedash-ot-extension-page>`
    );
    assert.instanceOf(component, ChromedashOTExtensionPage);
    await component.updateComplete;

    const initialLength = component.fieldValues.length;
    assert.isAbove(initialLength, 0);

    // Update a field and trigger a re-render
    component.handleFormFieldUpdate({
      detail: {index: 0, value: 135},
    });
    assert.equal(component.fieldValues[0].value, 135);

    component.currentMilestone = 131;
    await component.updateComplete;

    // fieldValues should not grow on re-render, and the form field should receive the updated value
    assert.equal(component.fieldValues.length, initialLength);
    const firstFieldEl = component.renderRoot.querySelector(
      'chromedash-form-field[index="0"]'
    ) as any;
    assert.exists(firstFieldEl);
    assert.equal(Number(firstFieldEl.value), 135);
    assert.equal(firstFieldEl.stageId, 10);
    assert.deepEqual(firstFieldEl.feature, validFeature);
  });

  it('handles empty or failed milestone schedule fetches gracefully', async () => {
    fetchStub.onFirstCall().resolves({
      json: () => Promise.resolve({mstones: []}),
    } as any);
    fetchStub
      .withArgs(
        'https://chromiumdash.appspot.com/fetch_milestone_schedule?mstone=132'
      )
      .resolves({
        json: () => Promise.resolve({mstones: []}),
      } as any);

    const component = await fixture<ChromedashOTExtensionPage>(
      html`<chromedash-ot-extension-page
        .featureId=${123456}
        .stageId=${10}
        .userEmail=${'owner@chromium.org'}
      >
      </chromedash-ot-extension-page>`
    );
    assert.instanceOf(component, ChromedashOTExtensionPage);
    await component.updateComplete;

    // Should keep default currentMilestone (123) when mstones is empty
    assert.equal(component.currentMilestone, 123);

    // Should not throw when getChromeScheduleDate encounters empty mstones or network error
    await component.getChromeScheduleDate('130');
    assert.isUndefined(component.endMilestoneDateValues['130']);

    fetchStub
      .withArgs(
        'https://chromiumdash.appspot.com/fetch_milestone_schedule?mstone=134'
      )
      .rejects(new Error('Network failure'));
    await component.getChromeScheduleDate('132');
    assert.isUndefined(component.endMilestoneDateValues['132']);
  });
});
