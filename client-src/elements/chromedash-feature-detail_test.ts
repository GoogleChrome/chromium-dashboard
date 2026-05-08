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
import {ChromedashFeatureDetail} from './chromedash-feature-detail.js';
import {
  GATE_PREPARING,
  GATE_REVIEW_REQUESTED,
  VOTE_OPTIONS,
} from './form-field-enums.js';

describe('chromedash-feature-detail', () => {
  const stageNoGates = {id: 1} as any;
  const stagePreparing = {id: 2} as any;
  const stageActive = {id: 3} as any;
  const stageMixed = {id: 4} as any;
  const stageResolved = {id: 5} as any;

  const gates = [
    {stage_id: stagePreparing.id, state: GATE_PREPARING},
    {stage_id: stageActive.id, state: GATE_PREPARING},
    {stage_id: stageActive.id, state: GATE_REVIEW_REQUESTED},
    {stage_id: stageMixed.id, state: GATE_PREPARING},
    {stage_id: stageMixed.id, state: VOTE_OPTIONS.APPROVED[0]},
    {stage_id: stageResolved.id, state: VOTE_OPTIONS.APPROVED[0]},
  ];

  const feature = {
    id: 123456789,
    is_enterprise_feature: false,
    stages: [],
  };

  it('renders with mimial data', async () => {
    const component = await fixture(
      html`<chromedash-feature-detail
        .feature=${feature}
      ></chromedash-feature-detail>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashFeatureDetail);
  });

  it('can identify active gates', async () => {
    const component: ChromedashFeatureDetail = (await fixture(
      html`<chromedash-feature-detail
        .feature=${feature}
        .gates=${gates}
      ></chromedash-feature-detail>`
    )) as ChromedashFeatureDetail;
    assert.isFalse(component.hasActiveGates(stageNoGates));
    assert.isFalse(component.hasActiveGates(stagePreparing));
    assert.isTrue(component.hasActiveGates(stageActive));
    assert.isFalse(component.hasActiveGates(stageMixed));
    assert.isFalse(component.hasActiveGates(stageResolved));
  });

  it('can identify mixed gates', async () => {
    const component: ChromedashFeatureDetail = (await fixture(
      html`<chromedash-feature-detail
        .feature=${feature}
        .gates=${gates}
      ></chromedash-feature-detail>`
    )) as ChromedashFeatureDetail;
    assert.isFalse(component.hasMixedGates(stageNoGates));
    assert.isFalse(component.hasMixedGates(stagePreparing));
    assert.isFalse(component.hasMixedGates(stageActive));
    assert.isTrue(component.hasMixedGates(stageMixed));
    assert.isFalse(component.hasMixedGates(stageResolved));
  });
});
