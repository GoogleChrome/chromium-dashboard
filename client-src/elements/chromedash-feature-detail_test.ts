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
import {ChromedashFeatureDetail} from './chromedash-feature-detail.js';
import {
  FEATURE_TYPES,
  GATE_PREPARING,
  GATE_REVIEW_REQUESTED,
  GATE_TYPES,
  STAGE_BLINK_ORIGIN_TRIAL,
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

  it('shows only actions without gate types at the stage level', async () => {
    const component: ChromedashFeatureDetail = (await fixture(
      html`<chromedash-feature-detail
        .feature=${feature}
        .gates=${[]}
      ></chromedash-feature-detail>`
    )) as ChromedashFeatureDetail;

    const reviewDataQuality = {
      name: 'Review data quality',
      url: 'request review',
      gate_types: [GATE_TYPES.DQ_SHIP],
    };
    const intentToShip = {
      name: 'Draft Intent to Ship email',
      url: '/feature/{feature_id}/gate/{gate_id}/intent',
      gate_types: [GATE_TYPES.API_SHIP],
    };
    const devTrialEmail = {
      name: 'Draft Ready for Developer Testing email',
      url: '/feature/{feature_id}/stage/{outgoing_stage}/intent',
      gate_types: [],
    };

    // Actions tied to a gate are shown on that gate, not on the stage.
    const stageWithGatedActions = {actions: [reviewDataQuality, intentToShip]};
    assert.isEmpty(component.getStageLevelActions(stageWithGatedActions));
    assert.isFalse(
      component.hasStageActions(stageWithGatedActions, {id: 10} as any)
    );

    const stageWithUngatedAction = {
      actions: [reviewDataQuality, intentToShip, devTrialEmail],
    };
    assert.deepEqual(component.getStageLevelActions(stageWithUngatedAction), [
      devTrialEmail,
    ]);
    assert.isTrue(
      component.hasStageActions(stageWithUngatedAction, {id: 10} as any)
    );
  });

  it('does not show Review data quality on PSA shipping stages', async () => {
    const psaFeature = {
      ...feature,
      feature_type_int: FEATURE_TYPES.FEATURE_TYPE_CODE_CHANGE_ID[0],
    };
    const component: ChromedashFeatureDetail = (await fixture(
      html`<chromedash-feature-detail
        .feature=${psaFeature}
        .gates=${[]}
      ></chromedash-feature-detail>`
    )) as ChromedashFeatureDetail;

    const psaShippingStage = {
      actions: [
        {
          name: 'Review data quality',
          url: 'request review',
          gate_types: [GATE_TYPES.DQ_SHIP],
        },
        {
          name: 'Draft Web-Facing Change PSA email',
          url: '/feature/{feature_id}/stage/{outgoing_stage}/intent',
          gate_types: [],
        },
      ],
    };
    assert.deepEqual(
      component.getStageLevelActions(psaShippingStage).map(a => a.name),
      ['Draft Web-Facing Change PSA email']
    );
  });

  describe('origin trial buttons', () => {
    const googler = {email: 'someone@google.com'} as any;
    const otStage = {
      id: 20,
      stage_type: STAGE_BLINK_ORIGIN_TRIAL,
      extensions: [],
    } as any;
    const createdOtStage = {...otStage, origin_trial_id: '-123'} as any;
    const approvedExtension = {id: 21, ot_action_requested: true};
    const otStageWithApprovedExtension = {
      ...createdOtStage,
      extensions: [approvedExtension],
    } as any;
    const approvedGates = [
      {stage_id: otStage.id, state: VOTE_OPTIONS.APPROVED[0]},
      {stage_id: approvedExtension.id, state: VOTE_OPTIONS.APPROVED[0]},
    ];

    async function renderDetail(canEdit: boolean) {
      return (await fixture(
        html`<chromedash-feature-detail
          .feature=${feature}
          .gates=${approvedGates}
          .user=${googler}
          ?canEdit=${canEdit}
        ></chromedash-feature-detail>`
      )) as ChromedashFeatureDetail;
    }

    async function buttonLabels(template): Promise<string[]> {
      const el = await fixture(html`<div>${template}</div>`);
      return [...el.querySelectorAll('sl-button')].map(b =>
        b.textContent!.trim()
      );
    }

    it('lets a Google account without edit access request a trial', async () => {
      const component = await renderDetail(false);
      assert.deepEqual(
        await buttonLabels(component.renderOriginTrialButton(otStage)),
        ['Request Trial Creation']
      );
    });

    it('lets a Google account without edit access request an extension', async () => {
      const component = await renderDetail(false);
      assert.deepEqual(
        await buttonLabels(component.renderExtensionButton(createdOtStage)),
        ['Request a trial extension']
      );
    });

    it('only lets editors finalize an approved extension', async () => {
      const nonEditor = await renderDetail(false);
      assert.deepEqual(
        await buttonLabels(
          nonEditor.renderExtensionButton(otStageWithApprovedExtension)
        ),
        ['Trial Extension Pending']
      );

      const editor = await renderDetail(true);
      assert.deepEqual(
        await buttonLabels(
          editor.renderExtensionButton(otStageWithApprovedExtension)
        ),
        ['Finalize Extension']
      );
    });
  });

  it('scrolls the stage <sl-details> into view in initializeGateColumn', async () => {
    const originalSearch = window.location.search;
    window.history.replaceState({}, '', '?gate=99');
    const scrollSpy = sinon.spy(Element.prototype, 'scrollIntoView');

    try {
      const featureWithStages = {
        id: 123456789,
        is_enterprise_feature: false,
        stages: [
          {id: 10, stage_type: 110, extensions: []},
          {id: 20, stage_type: 160, extensions: []},
        ],
      };
      const process = {
        stages: [
          {
            stage_type: 110,
            name: 'Start incubating',
            description: 'desc 1',
            actions: [],
          },
          {
            stage_type: 160,
            name: 'Prepare to ship',
            description: 'desc 2',
            actions: [],
          },
        ],
      };
      const testGates = [
        {
          id: 99,
          stage_id: 20,
          state: GATE_REVIEW_REQUESTED,
          team_name: 'API Owners',
        },
      ];

      const component: ChromedashFeatureDetail = (await fixture(
        html`<chromedash-feature-detail
          .feature=${featureWithStages}
          .process=${process}
          .gates=${testGates}
        ></chromedash-feature-detail>`
      )) as ChromedashFeatureDetail;

      await component.updateComplete;

      const stageDetails = component.renderRoot.querySelector('#stage-20');
      assert.exists(stageDetails);
      assert.isTrue(scrollSpy.calledOnce);
      assert.strictEqual(scrollSpy.firstCall.thisValue, stageDetails);
    } finally {
      scrollSpy.restore();
      window.history.replaceState(
        {},
        '',
        originalSearch || window.location.pathname
      );
    }
  });
});
