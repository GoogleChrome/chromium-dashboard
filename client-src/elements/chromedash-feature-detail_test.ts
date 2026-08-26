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

  it('renders AI summary progress and review dialog when user has edit permissions', async () => {
    const component = await fixture<ChromedashFeatureDetail>(
      html`<chromedash-feature-detail
        .feature=${feature}
        .canEdit=${true}
      ></chromedash-feature-detail>`
    );
    const progressEl = component.shadowRoot?.querySelector(
      'chromedash-ai-summary-progress'
    );
    assert.exists(progressEl);

    const reviewDialog = component.shadowRoot?.querySelector(
      'chromedash-summary-review-dialog'
    );
    assert.exists(reviewDialog);
  });

  it('does not render AI summary progress when user lacks edit permissions', async () => {
    const component = await fixture<ChromedashFeatureDetail>(
      html`<chromedash-feature-detail
        .feature=${feature}
        .canEdit=${false}
      ></chromedash-feature-detail>`
    );
    const progressEl = component.shadowRoot?.querySelector(
      'chromedash-ai-summary-progress'
    );
    assert.isNull(progressEl);
  });

  it('handles summary completion and opens review dialog with active suggestion', async () => {
    const component = await fixture<ChromedashFeatureDetail>(
      html`<chromedash-feature-detail
        .feature=${feature}
        .canEdit=${true}
      ></chromedash-feature-detail>`
    );
    const mockSuggestion = {
      feature_id: 123456789,
      suggested_summary: 'Suggested AI summary.',
      version_token: 1,
    } as any;

    component.handleSummaryCompleted(
      new CustomEvent('summary-generation-completed', {
        detail: {
          featureId: 123456789,
          suggestion: mockSuggestion,
        },
      })
    );

    assert.deepEqual(component.activeSuggestion, mockSuggestion);
  });

  it('updates feature summary and dispatches refetch-needed on suggestion applied', async () => {
    const component = await fixture<ChromedashFeatureDetail>(
      html`<chromedash-feature-detail
        .feature=${{...feature, summary: 'Old summary'}}
        .canEdit=${true}
      ></chromedash-feature-detail>`
    );

    let refetchDispatched = false;
    component.addEventListener('refetch-needed', () => {
      refetchDispatched = true;
    });

    component.handleSummarySuggestionApplied(
      new CustomEvent('summary-suggestion-applied', {
        detail: {
          featureId: 123456789,
          summary: 'New applied AI summary',
        },
      })
    );

    assert.equal(component.feature.summary, 'New applied AI summary');
    assert.isTrue(refetchDispatched);
  });
});
