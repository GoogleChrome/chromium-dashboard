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
import '@shoelace-style/shoelace/dist/components/dialog/dialog.js';
import {
  Action,
  ChromedashGateColumn,
  Process,
  ProcessStage,
  ProgressItem,
} from './chromedash-gate-column.js';
import {ChromedashPreflightDialog} from './chromedash-preflight-dialog.js';
import {PROGRESS_VOTE_STATE} from './form-field-enums.js';
import {ChromeStatusClient, Feature, StageDict} from '../js-src/cs-client.js';
import {GateDict} from './chromedash-gate-chip.js';
import sinon from 'sinon';

describe('chromedash-gate-column', () => {
  /* window.csClient is initialized in spa.html
   * which is not available here, so we initialize it before each test.
   * We also stub out the API calls here so that they return test data. */
  beforeEach(async () => {
    window.csClient = new ChromeStatusClient('fake_token', 1);
    sinon.stub(window.csClient, 'getFeatureProcess');
    sinon.stub(window.csClient, 'getVotes');
    sinon.stub(window.csClient, 'getComments');
  });

  afterEach(() => {
    window.csClient.getFeatureProcess.restore();
    window.csClient.getVotes.restore();
    window.csClient.getComments.restore();
  });

  it('can be added to the page before being opened', async () => {
    const component = await fixture(
      html`<chromedash-gate-column></chromedash-gate-column>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashGateColumn);
  });

  describe('executeAction', () => {
    it('calls handleFullReviewRequest when url is "request review"', async () => {
      const component = await fixture<ChromedashGateColumn>(
        html`<chromedash-gate-column></chromedash-gate-column>`
      );
      const reviewReqStub = sinon.stub(component, 'handleFullReviewRequest');
      const windowOpenStub = sinon.stub(window, 'open');

      try {
        component.executeAction('request review');
        assert.isTrue(reviewReqStub.calledOnce);
        assert.isFalse(windowOpenStub.called);
      } finally {
        reviewReqStub.restore();
        windowOpenStub.restore();
      }
    });

    it('opens a new window and focuses it for other URLs', async () => {
      const component = await fixture<ChromedashGateColumn>(
        html`<chromedash-gate-column></chromedash-gate-column>`
      );
      const reviewReqStub = sinon.stub(component, 'handleFullReviewRequest');
      const focusStub = sinon.stub();
      const windowOpenStub = sinon
        .stub(window, 'open')
        .returns({focus: focusStub} as unknown as Window);

      try {
        component.executeAction('/feature/123456/gate/99/intent');
        await new Promise(resolve => setTimeout(resolve, 0));

        assert.isFalse(reviewReqStub.called);
        assert.isTrue(
          windowOpenStub.calledOnceWithExactly(
            '/feature/123456/gate/99/intent',
            '_blank'
          )
        );
        assert.isTrue(focusStub.calledOnce);
      } finally {
        reviewReqStub.restore();
        windowOpenStub.restore();
      }
    });
  });

  describe('renderAction', () => {
    const feature = {id: 123456, stages: []} as unknown as Feature;
    const stage = {id: 20, stage_type: 160} as unknown as StageDict;
    const gate = {id: 99, stage_id: 20} as unknown as GateDict;
    const processStage = {
      name: 'Prepare to ship',
      outgoing_stage: 3,
      progress_items: [{name: 'Explainer', field: 'explainer_links'}],
    } as unknown as ProcessStage;
    const process = {
      name: 'Blink process',
      stages: [processStage],
    } as unknown as Process;
    const action: Action = {
      name: 'Review data quality',
      url: 'request review',
      prerequisites: ['Explainer'],
    };

    it('executes action directly when prerequisites and gates are satisfied', async () => {
      const component = await fixture<ChromedashGateColumn>(
        html`<chromedash-gate-column></chromedash-gate-column>`
      );
      component.feature = feature;
      component.stage = stage;
      component.gate = gate;
      component.process = process;
      component.progress = {
        Explainer: {
          state: PROGRESS_VOTE_STATE.VERIFIED,
          set_on: '2026-09-23T00:00:00',
          set_by: 'ChromeStatus',
        },
      } as unknown as ProgressItem;

      const getGatesStub = sinon
        .stub(window.csClient, 'getGates')
        .resolves({gates: []});
      const executeActionStub = sinon.stub(component, 'executeAction');

      try {
        const actionBtn = await fixture<HTMLElement>(
          component.renderAction(processStage, action)
        );
        actionBtn.click();
        await new Promise(resolve => setTimeout(resolve, 0));

        assert.isTrue(getGatesStub.calledOnceWithExactly(123456));
        assert.isTrue(
          executeActionStub.calledOnceWithExactly('request review')
        );
      } finally {
        getGatesStub.restore();
        executeActionStub.restore();
      }
    });

    it('opens preflight dialog when prerequisites are pending and executes action on proceed', async () => {
      const component = await fixture<ChromedashGateColumn>(
        html`<chromedash-gate-column></chromedash-gate-column>`
      );
      component.feature = feature;
      component.stage = stage;
      component.gate = gate;
      component.process = process;
      component.progress = {} as unknown as ProgressItem;

      const getGatesStub = sinon
        .stub(window.csClient, 'getGates')
        .resolves({gates: []});
      const executeActionStub = sinon.stub(component, 'executeAction');

      try {
        const actionBtn = await fixture<HTMLElement>(
          component.renderAction(processStage, action)
        );
        actionBtn.click();
        await new Promise(resolve => setTimeout(resolve, 0));

        assert.isFalse(executeActionStub.called);

        const dialogEl = document.querySelector(
          'chromedash-preflight-dialog'
        ) as ChromedashPreflightDialog;
        assert.exists(dialogEl);
        await dialogEl.updateComplete;

        dialogEl.handleProceed();
        await new Promise(resolve => setTimeout(resolve, 0));

        assert.isTrue(
          executeActionStub.calledOnceWithExactly('request review')
        );
      } finally {
        getGatesStub.restore();
        executeActionStub.restore();
      }
    });

    it('opens preflight dialog when prerequisites are pending and does not execute action on cancel', async () => {
      const component = await fixture<ChromedashGateColumn>(
        html`<chromedash-gate-column></chromedash-gate-column>`
      );
      component.feature = feature;
      component.stage = stage;
      component.gate = gate;
      component.process = process;
      component.progress = {} as unknown as ProgressItem;

      const getGatesStub = sinon
        .stub(window.csClient, 'getGates')
        .resolves({gates: []});
      const executeActionStub = sinon.stub(component, 'executeAction');

      try {
        const actionBtn = await fixture<HTMLElement>(
          component.renderAction(processStage, action)
        );
        actionBtn.click();
        await new Promise(resolve => setTimeout(resolve, 0));

        const dialogEl = document.querySelector(
          'chromedash-preflight-dialog'
        ) as ChromedashPreflightDialog;
        assert.exists(dialogEl);
        await dialogEl.updateComplete;

        dialogEl.handleCancel();
        await new Promise(resolve => setTimeout(resolve, 0));

        assert.isFalse(executeActionStub.called);
      } finally {
        getGatesStub.restore();
        executeActionStub.restore();
      }
    });
  });
});
