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
import sinon from 'sinon';
import '@shoelace-style/shoelace/dist/components/dialog/dialog.js';
import {ChromedashChecklistSummary} from './chromedash-checklist-summary.js';
import {ChromedashPreflightDialog} from './chromedash-preflight-dialog.js';
import {
  GATE_NA_REQUESTED,
  GATE_PREPARING,
  GATE_REVIEW_REQUESTED,
  GATE_TYPES,
  PROGRESS_VOTE_STATE,
  VOTE_OPTIONS,
} from './form-field-enums.js';
import {
  ChromeStatusClient,
  Feature,
  StageDict,
  User,
} from '../js-src/cs-client.js';
import {GateDict} from './chromedash-gate-chip.js';
import {Process, ProcessStage, ProgressItem} from './chromedash-gate-column.js';

describe('chromedash-checklist-summary', () => {
  const feature = {
    id: 123456,
    stages: [{id: 20, stage_type: 160, intent_stage: 3}],
  } as unknown as Feature;

  const stage = {
    id: 20,
    stage_type: 160,
    intent_stage: 3,
  } as unknown as StageDict;

  const dqShipGate = {
    id: 99,
    stage_id: 20,
    gate_type: GATE_TYPES.DQ_SHIP,
    team_name: 'Data Quality',
    state: GATE_PREPARING,
  } as unknown as GateDict;

  const dqPlanGate = {
    id: 98,
    stage_id: 20,
    gate_type: GATE_TYPES.DQ_PLAN,
    team_name: 'Data Quality',
    state: GATE_PREPARING,
  } as unknown as GateDict;

  const nonDqGate = {
    id: 97,
    stage_id: 20,
    gate_type: GATE_TYPES.PRIVACY_SHIP,
    team_name: 'Privacy',
    state: GATE_PREPARING,
  } as unknown as GateDict;

  const action = {
    name: 'Review data quality',
    url: 'request review',
    prerequisites: [
      'Motivation',
      'Explainer',
      'Spec link',
      'Samples',
      'Doc links',
    ],
    gate_types: [GATE_TYPES.DQ_SHIP],
  };

  const processStage = {
    name: 'Prepare to ship',
    outgoing_stage: 3,
    stage_type: 160,
    actions: [action],
    progress_items: [
      {name: 'Motivation', field: 'motivation'},
      {name: 'Explainer', field: 'explainer_links'},
      {name: 'Spec link', field: 'spec_link'},
      {name: 'Samples', field: 'sample_links'},
      {name: 'Doc links', field: 'doc_links'},
    ],
  } as unknown as ProcessStage;

  const process = {
    name: 'Blink launch process',
    stages: [processStage],
  } as unknown as Process;

  let getGatesStub: sinon.SinonStub;

  beforeEach(() => {
    window.csClient = new ChromeStatusClient('fake_token', 1);
    getGatesStub = sinon.stub(window.csClient, 'getGates');
    getGatesStub.resolves({gates: [dqShipGate]});
  });

  afterEach(() => {
    getGatesStub.restore();
  });

  it('renders nothing while loading', async () => {
    const component = await fixture<ChromedashChecklistSummary>(
      html`<chromedash-checklist-summary
        .loading=${true}
        .feature=${feature}
        .stage=${stage}
        .gate=${dqShipGate}
        .process=${process}
        .featureGates=${[dqShipGate]}
      ></chromedash-checklist-summary>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashChecklistSummary);
    assert.isNull(component.shadowRoot!.querySelector('h2'));
    assert.isNull(component.shadowRoot!.querySelector('.bubble'));
  });

  it('fetches gates when featureGates is empty and renders once loaded', async () => {
    const component = await fixture<ChromedashChecklistSummary>(
      html`<chromedash-checklist-summary
        .loading=${false}
        .feature=${feature}
        .stage=${stage}
        .gate=${dqShipGate}
        .process=${process}
        .progress=${{} as ProgressItem}
        .featureGates=${[]}
      ></chromedash-checklist-summary>`
    );

    assert.isTrue(getGatesStub.calledOnceWithExactly(123456));
    await component.updateComplete;

    assert.isNotNull(component.shadowRoot!.querySelector('h2'));
    assert.isNotNull(component.shadowRoot!.querySelector('.bubble'));
  });

  it('renders nothing for non-DQ gates', async () => {
    const component = await fixture<ChromedashChecklistSummary>(
      html`<chromedash-checklist-summary
        .loading=${false}
        .feature=${feature}
        .stage=${stage}
        .gate=${nonDqGate}
        .process=${process}
        .progress=${{} as ProgressItem}
        .featureGates=${[nonDqGate]}
      ></chromedash-checklist-summary>`
    );

    assert.isNull(component.shadowRoot!.querySelector('h2'));
    assert.isNull(component.shadowRoot!.querySelector('.bubble'));
  });

  it('renders nothing when processStage has no matching actions for the gate type', async () => {
    const component = await fixture<ChromedashChecklistSummary>(
      html`<chromedash-checklist-summary
        .loading=${false}
        .feature=${feature}
        .stage=${stage}
        .gate=${dqPlanGate}
        .process=${process}
        .progress=${{} as ProgressItem}
        .featureGates=${[dqPlanGate]}
      ></chromedash-checklist-summary>`
    );

    assert.isNull(component.shadowRoot!.querySelector('h2'));
    assert.isNull(component.shadowRoot!.querySelector('.bubble'));
  });

  it('counts prerequisites and other gates and renders strip chart and legend', async () => {
    const progress = {
      Motivation: {
        state: PROGRESS_VOTE_STATE.VERIFIED,
        set_on: '2026-10-01T00:00:00',
        set_by: 'user@example.com',
      },
      Explainer: {
        state: PROGRESS_VOTE_STATE.NA,
        set_on: '2026-10-01T00:00:00',
        set_by: 'user@example.com',
      },
      'Spec link': {
        state: PROGRESS_VOTE_STATE.READY_FOR_REVIEW,
        set_on: '2026-10-01T00:00:00',
        set_by: 'user@example.com',
      },
      Samples: {
        state: PROGRESS_VOTE_STATE.NEEDS_WORK,
        set_on: '2026-10-01T00:00:00',
        set_by: 'reviewer@example.com',
      },
      // 'Doc links' is omitted, so it counts as NOT_STARTED (preparing).
    } as unknown as ProgressItem;

    const featureGates = [
      dqShipGate, // Ignored by findOtherGates ('Data Quality')
      {
        id: 101,
        stage_id: 20,
        team_name: 'API Owners', // Ignored by findOtherGates ('API Owners')
        state: VOTE_OPTIONS.APPROVED[0],
      },
      {
        id: 102,
        stage_id: 20,
        team_name: 'Privacy',
        state: VOTE_OPTIONS.APPROVED[0], // Verified
      },
      {
        id: 103,
        stage_id: 20,
        team_name: 'Security',
        state: GATE_REVIEW_REQUESTED, // Ready
      },
      {
        id: 104,
        stage_id: 20,
        team_name: 'Enterprise',
        state: GATE_NA_REQUESTED, // Ready
      },
      {
        id: 105,
        stage_id: 20,
        team_name: 'Debuggability',
        state: VOTE_OPTIONS.NEEDS_WORK[0], // Needs work
      },
      {
        id: 106,
        stage_id: 20,
        team_name: 'Testing',
        state: GATE_PREPARING, // Preparing
      },
      {
        id: 107,
        stage_id: 999, // Different stage, ignored
        team_name: 'Privacy',
        state: VOTE_OPTIONS.APPROVED[0],
      },
    ] as unknown as GateDict[];

    const component = await fixture<ChromedashChecklistSummary>(
      html`<chromedash-checklist-summary
        .loading=${false}
        .feature=${feature}
        .stage=${stage}
        .gate=${dqShipGate}
        .process=${process}
        .progress=${progress}
        .featureGates=${featureGates}
      ></chromedash-checklist-summary>`
    );

    // Expected counts:
    // Verified: 2 prereqs (Motivation, Explainer) + 1 gate (Privacy) = 3
    // Ready: 1 prereq (Spec link) + 2 gates (Security, Enterprise) = 3
    // Needs work: 1 prereq (Samples) + 1 gate (Debuggability) = 2
    // Preparing: 1 prereq (Doc links) + 1 gate (Testing) = 2
    const stripChart = component.shadowRoot!.querySelector('#strip-chart')!;
    assert.exists(stripChart);
    assert.equal(stripChart.querySelectorAll('.verified').length, 3);
    assert.equal(stripChart.querySelectorAll('.ready').length, 3);
    assert.equal(stripChart.querySelectorAll('.needs-work').length, 2);
    assert.equal(stripChart.querySelectorAll('.preparing').length, 2);

    const legendText = component
      .shadowRoot!.querySelector('#legend')!
      .textContent!.trim();
    assert.equal(
      legendText,
      '3 Verified. 3 Ready for review. 2 Needs work. 2 Not started.'
    );
  });

  it('omits zero-count categories in renderLegend', async () => {
    const component = await fixture<ChromedashChecklistSummary>(
      html`<chromedash-checklist-summary></chromedash-checklist-summary>`
    );

    const legendParts = component.renderLegend(2, 0, 1, 0);
    assert.deepEqual(legendParts, ['2 Verified. ', '1 Needs work. ']);
  });

  it('opens the preflight dialog when View checklist button is clicked', async () => {
    const user = {can_edit_all: true} as unknown as User;
    const component = await fixture<ChromedashChecklistSummary>(
      html`<chromedash-checklist-summary
        .loading=${false}
        .user=${user}
        .feature=${feature}
        .stage=${stage}
        .gate=${dqShipGate}
        .process=${process}
        .progress=${{} as ProgressItem}
        .featureGates=${[dqShipGate]}
      ></chromedash-checklist-summary>`
    );

    const handleSpy = sinon.spy(component, 'handleViewChecklist');
    const button = component.shadowRoot!.querySelector(
      'sl-button'
    ) as HTMLElement;
    assert.exists(button);
    assert.equal(button.textContent?.trim(), 'View checklist');

    button.click();
    assert.isTrue(handleSpy.calledOnceWithExactly(processStage, action));

    const dialogEl = document.querySelector(
      'chromedash-preflight-dialog'
    ) as ChromedashPreflightDialog;
    assert.exists(dialogEl);
    await dialogEl.updateComplete;
    assert.isTrue(dialogEl.userCanVote());
  });
});
