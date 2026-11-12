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
import {ChromedashGuideMetadataPage} from './chromedash-guide-metadata-page.js';
import './chromedash-toast.js';

describe('chromedash-guide-metadata-page', () => {
  const validFeaturePromise = Promise.resolve({
    id: 123456,
    name: 'feature one',
    summary: 'fake detailed summary',
    category: 'fake category',
    feature_type: 'fake feature type',
    feature_type_int: 0,
    intent_stage: 'fake intent stage',
    new_crbug_url: 'fake crbug link',
    stages: [],
    browsers: {
      chrome: {
        blink_components: ['Blink'],
        owners: ['owner@chromium.org'],
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
      samples: [],
      docs: [],
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
    stable: {mstone: 141},
    beta: {mstone: 142},
    dev: {mstone: 143},
  });

  beforeEach(async () => {
    await fixture(html`<chromedash-toast></chromedash-toast>`);
    window.csClient = new ChromeStatusClient('fake_token', 1);
    sinon.stub(window.csClient, 'getFeature');
    sinon.stub(window.csClient, 'getChannels').returns(validChannelsPromise);
    sinon
      .stub(window.csClient, 'getBlinkComponents')
      .returns(Promise.resolve({}));
  });

  afterEach(() => {
    (window.csClient.getFeature as any).restore();
    (window.csClient.getChannels as any).restore();
    (window.csClient.getBlinkComponents as any).restore();
  });

  it('populates fieldValues and preserves length and edits across re-renders', async () => {
    const featureId = 123456;
    (window.csClient.getFeature as any)
      .withArgs(featureId)
      .returns(validFeaturePromise);

    const component = await fixture<ChromedashGuideMetadataPage>(
      html`<chromedash-guide-metadata-page .featureId=${featureId}>
      </chromedash-guide-metadata-page>`
    );
    assert.instanceOf(component, ChromedashGuideMetadataPage);
    await component.updateComplete;

    const initialLength = component.fieldValues.length;
    assert.isAbove(initialLength, 0);

    // 'owner' has featureJSONKey 'owner_emails', populated from formattedFeature['owner']
    const ownerField = component.fieldValues.find(
      fv => fv.name === 'owner_emails'
    );
    assert.exists(ownerField);
    assert.equal(ownerField.value, 'owner@chromium.org');

    // Simulate field update and trigger a re-render
    component.handleFormFieldUpdate({
      detail: {index: 0, value: 'updated name', isMarkdown: false},
    });
    assert.isTrue(component.fieldValues[0].touched);
    assert.equal(component.fieldValues[0].value, 'updated name');

    component.currentBetaMilestone = 143;
    await component.updateComplete;

    assert.equal(component.fieldValues.length, initialLength);
    assert.equal(component.fieldValues[0].value, 'updated name');
  });
});
