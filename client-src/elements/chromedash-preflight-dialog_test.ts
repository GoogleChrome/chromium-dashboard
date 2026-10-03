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
import '@shoelace-style/shoelace/dist/components/dialog/dialog.js';
import {Feature, StageDict} from '../js-src/cs-client.js';
import {PROGRESS_VOTE_STATE, VOTE_OPTIONS} from './form-field-enums.js';
import {GateDict} from './chromedash-gate-chip.js';
import {
  ChromedashPreflightDialog,
  findOtherGates,
  findPendingGates,
  openPreflightDialog,
  somePendingPrereqs,
} from './chromedash-preflight-dialog.js';
import {Action, Process, ProgressItem} from './chromedash-gate-column.js';

describe('preflight functions', () => {
  describe('somePendingPrereqs', () => {
    const action: Action = {
      name: 'Draft Intent to Ship email',
      url: '/intent',
      prerequisites: ['Explainer', 'Spec link'],
    };

    it('returns false when all prerequisites are VERIFIED or NA', () => {
      const progress = {
        Explainer: {
          state: PROGRESS_VOTE_STATE.VERIFIED,
          set_on: '2026-09-23T00:00:00',
          set_by: 'ChromeStatus',
        },
        'Spec link': {
          state: PROGRESS_VOTE_STATE.NA,
          set_on: '2026-09-23T00:00:00',
          set_by: 'reviewer@example.com',
        },
      };
      assert.isFalse(somePendingPrereqs(action, progress));
    });

    it('returns true when a prerequisite is NEEDS_WORK or READY_FOR_REVIEW', () => {
      const progressNeedsWork = {
        Explainer: {
          state: PROGRESS_VOTE_STATE.VERIFIED,
          set_on: '2026-09-23T00:00:00',
          set_by: 'ChromeStatus',
        },
        'Spec link': {
          state: PROGRESS_VOTE_STATE.NEEDS_WORK,
          feedback: 'Broken link',
          set_on: '2026-09-23T00:00:00',
          set_by: 'reviewer@example.com',
        },
      };
      assert.isTrue(somePendingPrereqs(action, progressNeedsWork));

      const progressReadyForReview = {
        Explainer: {
          state: PROGRESS_VOTE_STATE.READY_FOR_REVIEW,
          set_on: '2026-09-23T00:00:00',
          set_by: 'reviewer@example.com',
        },
        'Spec link': {
          state: PROGRESS_VOTE_STATE.VERIFIED,
          set_on: '2026-09-23T00:00:00',
          set_by: 'ChromeStatus',
        },
      };
      assert.isTrue(somePendingPrereqs(action, progressReadyForReview));
    });

    it('returns true when a prerequisite is missing from progress', () => {
      const progress = {
        Explainer: {
          state: PROGRESS_VOTE_STATE.VERIFIED,
          set_on: '2026-09-23T00:00:00',
          set_by: 'ChromeStatus',
        },
      };
      assert.isTrue(somePendingPrereqs(action, progress));
    });
  });

  describe('findOtherGates', () => {
    const stage = {id: 123} as StageDict;

    it('handles stages without gates', () => {
      const actual = findOtherGates([], stage);
      assert.deepEqual([], actual);
    });

    it('ignores gates on other stages', () => {
      const offTopicGate = {
        team_name: 'Enterprise',
        state: VOTE_OPTIONS.NEEDS_WORK[0],
        stage_id: stage.id + 1,
      } as GateDict;
      const actual = findOtherGates([offTopicGate], stage);
      assert.deepEqual([], actual);
    });

    it('finds other gates (excluding API Owners and Data Quality) and sorts them', () => {
      const enterpriseGate = {
        team_name: 'Enterprise',
        state: VOTE_OPTIONS.NEEDS_WORK[0],
        stage_id: stage.id,
      } as GateDict;
      const privacyGate = {
        team_name: 'Privacy',
        state: VOTE_OPTIONS.APPROVED[0],
        stage_id: stage.id,
      } as GateDict;
      const apiGate = {
        team_name: 'API Owners',
        state: VOTE_OPTIONS.NEEDS_WORK[0],
        stage_id: stage.id,
      } as GateDict;
      const dqGate = {
        team_name: 'Data Quality',
        state: VOTE_OPTIONS.NEEDS_WORK[0],
        stage_id: stage.id,
      } as GateDict;
      const actual = findOtherGates(
        [enterpriseGate, apiGate, dqGate, privacyGate],
        stage
      );
      const expected = [privacyGate, enterpriseGate];
      assert.deepEqual(expected, actual);
    });
  });

  describe('findPendingGates', () => {
    const stage = {id: 123} as StageDict;

    it('handles stages without gates', () => {
      const actual = findPendingGates([], stage);
      const expected = [];
      assert.deepEqual(expected, actual);
    });

    it('ignores gates on other stages', () => {
      const offTopicGate = {
        team_name: 'Enterprise',
        state: VOTE_OPTIONS.NEEDS_WORK[0],
        stage_id: stage.id + 1,
      } as GateDict;
      const actual = findPendingGates([offTopicGate], stage);
      const expected = [];
      assert.deepEqual(expected, actual);
    });

    it('finds pending gates (other than API Owners) and sorts them', () => {
      const enterpriseGate = {
        team_name: 'Enterprise',
        state: VOTE_OPTIONS.NEEDS_WORK[0],
        stage_id: stage.id,
      } as GateDict;
      const privacyGate = {
        team_name: 'Privacy',
        state: VOTE_OPTIONS.NEEDS_WORK[0],
        stage_id: stage.id,
      } as GateDict;
      const approvedSecurityGate = {
        team_name: 'WP Security',
        state: VOTE_OPTIONS.APPROVED[0],
        stage_id: stage.id,
      } as GateDict;
      const apiGate = {
        team_name: 'API Owners',
        state: VOTE_OPTIONS.NEEDS_WORK[0],
        stage_id: stage.id,
      } as GateDict;
      const actual = findPendingGates(
        [enterpriseGate, apiGate, approvedSecurityGate, privacyGate],
        stage
      );
      const expected = [privacyGate, enterpriseGate];
      assert.deepEqual(expected, actual);
    });
  });

  describe('ChromedashPreflightDialog', () => {
    const feature = {
      id: 123456,
      stages: [
        {id: 10, stage_type: 110, intent_stage: 1},
        {id: 20, stage_type: 120, intent_stage: 2},
      ],
    } as unknown as Feature;

    const process = {
      name: 'New feature incubation',
      stages: [
        {
          name: 'Start incubating',
          outgoing_stage: 1,
          progress_items: [
            {name: 'Motivation', field: 'motivation'},
            {name: 'Explainer', field: 'explainer_links'},
            {name: 'Tracking bug URL', field: 'bug_url'},
          ],
        },
        {
          name: 'Start prototyping',
          outgoing_stage: 2,
          progress_items: [
            {name: 'Spec link', field: 'spec_link'},
            {name: 'Draft API spec'},
          ],
        },
        {
          name: 'Evaluate readiness to ship',
          outgoing_stage: 3,
          progress_items: [{name: 'Doc links', field: 'doc_links'}],
        },
      ],
    } as unknown as Process;

    const action = {
      name: 'Draft Intent to Ship email',
      url: '/feature/123456/gate/99/intent',
      prerequisites: [
        'Motivation',
        'Explainer',
        'Tracking bug URL',
        'Spec link',
        'Draft API spec',
      ],
    } as Action;

    const feStage = {id: 20, stage_type: 120, intent_stage: 2} as StageDict;

    it('renders 4-column tables per stage with rows and Other gates table below', async () => {
      const component = await fixture<ChromedashPreflightDialog>(
        html`<chromedash-preflight-dialog></chromedash-preflight-dialog>`
      );
      const progress = {
        Motivation: {
          state: PROGRESS_VOTE_STATE.VERIFIED,
          set_on: '2026-09-23T00:00:00',
          set_by: 'ChromeStatus',
        },
        'Spec link': {
          state: PROGRESS_VOTE_STATE.VERIFIED,
          set_on: '2026-09-23T00:00:00',
          set_by: 'ChromeStatus',
        },
      };
      const privacyGate = {
        id: 501,
        team_name: 'Privacy',
        state: VOTE_OPTIONS.NEEDS_WORK[0],
        stage_id: feStage.id,
      } as GateDict;

      component.openWithContext(
        feature,
        progress,
        process,
        action,
        feStage,
        feStage,
        [privacyGate],
        () => {}
      );
      await component.updateComplete;

      const headers = Array.from(
        component.shadowRoot!.querySelectorAll('h3')
      ).map(h => h.textContent?.trim());
      // "Evaluate readiness to ship" has no matching prerequisites, so it is omitted.
      assert.deepEqual(headers, [
        'Start incubating',
        'Start prototyping',
        'Other gates',
      ]);

      const tables = component.shadowRoot!.querySelectorAll('table.data-table');
      assert.equal(tables.length, 3);

      // Table 0: Start incubating (Motivation=Approved, Explainer=Pending, Tracking bug URL=Pending)
      const stage1Rows = tables[0].querySelectorAll('tr');
      assert.equal(stage1Rows.length, 3);

      const row0Cells = stage1Rows[0].querySelectorAll('td');
      assert.equal(row0Cells.length, 4);
      assert.isNotNull(
        row0Cells[0].querySelector('sl-icon[name="caret-right-fill"]')
      );
      assert.equal(row0Cells[1].textContent?.trim(), 'Verified');
      assert.isNotNull(row0Cells[1].querySelector('.status.approved'));
      assert.equal(row0Cells[2].textContent?.trim(), 'Motivation');
      assert.equal(
        row0Cells[3].querySelector('a')?.getAttribute('href'),
        '/guide/stage/123456/1/10#id_motivation'
      );

      const row1Cells = stage1Rows[1].querySelectorAll('td');
      assert.isNotNull(
        row1Cells[0].querySelector('sl-icon[name="caret-right-fill"]')
      );
      assert.equal(row1Cells[1].textContent?.trim(), 'Not started');
      assert.isNotNull(row1Cells[1].querySelector('.status.preparing'));
      assert.equal(row1Cells[2].textContent?.trim(), 'Explainer');
      assert.equal(
        row1Cells[3].querySelector('a')?.getAttribute('href'),
        '/guide/stage/123456/1/10#id_explainer_links'
      );

      const row2Cells = stage1Rows[2].querySelectorAll('td');
      assert.isNotNull(
        row2Cells[0].querySelector('sl-icon[name="caret-right-fill"]')
      );
      assert.equal(row2Cells[1].textContent?.trim(), 'Not started');
      assert.equal(row2Cells[2].textContent?.trim(), 'Tracking bug URL');
      assert.equal(
        row2Cells[3].querySelector('a')?.getAttribute('href'),
        '/guide/stage/123456/metadata#id_bug_url'
      );

      // Table 1: Start prototyping (Spec link=Verified with edit link, Draft API spec=Pending with no edit link)
      const stage2Rows = tables[1].querySelectorAll('tr');
      assert.equal(stage2Rows.length, 2);
      assert.equal(
        stage2Rows[0].querySelectorAll('td')[1].textContent?.trim(),
        'Verified'
      );
      assert.equal(
        stage2Rows[0].querySelectorAll('td')[2].textContent?.trim(),
        'Spec link'
      );
      assert.isNotNull(
        stage2Rows[0].querySelectorAll('td')[3].querySelector('a')
      );
      assert.isNull(stage2Rows[1].querySelectorAll('td')[3].querySelector('a'));

      // Table 2: Other gates
      const gateRows = tables[2].querySelectorAll('tr');
      assert.equal(gateRows.length, 1);
      const gateCells = gateRows[0].querySelectorAll('td');
      assert.equal(gateCells.length, 4);
      assert.equal(gateCells[0].textContent?.trim(), '');
      assert.equal(gateCells[1].textContent?.trim(), 'Needs work');
      assert.equal(gateCells[2].textContent?.trim(), 'Privacy');
      assert.equal(
        gateCells[3].querySelector('a')?.textContent?.trim(),
        'View'
      );
      assert.equal(
        gateCells[3].querySelector('a')?.getAttribute('href'),
        '/feature/123456?gate=501'
      );
    });

    it('initially expands items with feedback and toggles expansion on caret click', async () => {
      const component = await fixture<ChromedashPreflightDialog>(
        html`<chromedash-preflight-dialog></chromedash-preflight-dialog>`
      );
      const processWithCriteria = {
        ...process,
        stages: [
          {
            name: 'Start incubating',
            outgoing_stage: 1,
            progress_items: [
              {
                name: 'Motivation',
                field: 'motivation',
                criteria: 'Summarizes the reasons.',
              },
              {
                name: 'Explainer',
                field: 'explainer_links',
                criteria: 'Must include use cases and sample code.',
              },
              {name: 'Tracking bug URL', field: 'bug_url'},
            ],
          },
        ],
      } as unknown as Process;
      const progress = {
        Explainer: {
          state: PROGRESS_VOTE_STATE.NEEDS_WORK,
          feedback: 'Please add more details about the API.',
          set_on: '2026-09-23T00:00:00',
          set_by: 'reviewer@example.com',
        },
      };

      component.openWithContext(
        feature,
        progress,
        processWithCriteria,
        action,
        feStage,
        feStage,
        [],
        () => {}
      );
      await component.updateComplete;

      const tables = component.shadowRoot!.querySelectorAll('table.data-table');
      let stage1Rows = tables[0].querySelectorAll('tr');
      // Motivation has no feedback so its criteria row is hidden.
      // Explainer has feedback so its feedback and criteria rows are visible.
      // 3 items + 1 feedback row + 1 criteria row for Explainer = 5 rows.
      assert.equal(stage1Rows.length, 5);

      const motivationCaret = stage1Rows[0].querySelector(
        'sl-icon'
      ) as HTMLElement;
      assert.isFalse(motivationCaret.classList.contains('expanded'));

      const explainerRowCells = stage1Rows[1].querySelectorAll('td');
      const explainerCaret = explainerRowCells[0].querySelector(
        'sl-icon'
      ) as HTMLElement;
      assert.isTrue(explainerCaret.classList.contains('expanded'));
      assert.equal(explainerRowCells[1].textContent?.trim(), 'Needs work');
      assert.isNotNull(
        explainerRowCells[1].querySelector('.status.needs_work')
      );
      assert.equal(explainerRowCells[2].textContent?.trim(), 'Explainer');

      const feedbackRow = stage1Rows[2];
      assert.isTrue(feedbackRow.classList.contains('feedback'));
      const feedbackCells = feedbackRow.querySelectorAll('td');
      assert.equal(feedbackCells.length, 4);
      assert.equal(feedbackCells[0].textContent?.trim(), '');
      assert.equal(feedbackCells[1].textContent?.trim(), 'Feedback:');
      assert.equal(
        feedbackCells[2].textContent?.trim(),
        'Please add more details about the API.'
      );
      assert.equal(feedbackCells[3].textContent?.trim(), '');
      assert.equal(getComputedStyle(feedbackCells[0]).borderTopStyle, 'none');

      const criteriaRow = stage1Rows[3];
      assert.isTrue(criteriaRow.classList.contains('criteria'));
      const criteriaCells = criteriaRow.querySelectorAll('td');
      assert.equal(criteriaCells.length, 4);
      assert.equal(criteriaCells[0].textContent?.trim(), '');
      assert.equal(criteriaCells[1].textContent?.trim(), 'Criteria:');
      assert.equal(
        criteriaCells[2].textContent?.trim(),
        'Must include use cases and sample code.'
      );
      assert.equal(criteriaCells[3].textContent?.trim(), '');
      assert.equal(getComputedStyle(criteriaCells[0]).borderTopStyle, 'none');

      // Click Explainer caret to collapse it.
      explainerCaret.click();
      await component.updateComplete;
      stage1Rows = tables[0].querySelectorAll('tr');
      assert.equal(stage1Rows.length, 3);
      assert.isFalse(
        stage1Rows[1].querySelector('sl-icon')!.classList.contains('expanded')
      );

      // Click Motivation caret to expand it.
      motivationCaret.click();
      await component.updateComplete;
      stage1Rows = tables[0].querySelectorAll('tr');
      assert.equal(stage1Rows.length, 4);
      assert.isTrue(
        stage1Rows[0].querySelector('sl-icon')!.classList.contains('expanded')
      );
      assert.isTrue(stage1Rows[1].classList.contains('criteria'));
      assert.equal(
        stage1Rows[1].querySelectorAll('td')[2].textContent?.trim(),
        'Summarizes the reasons.'
      );
    });

    it('omits other gates table when there are no other gates', async () => {
      const component = await fixture<ChromedashPreflightDialog>(
        html`<chromedash-preflight-dialog></chromedash-preflight-dialog>`
      );
      const progress = {} as ProgressItem;

      component.openWithContext(
        feature,
        progress,
        process,
        action,
        feStage,
        feStage,
        [],
        () => {}
      );
      await component.updateComplete;

      const headers = Array.from(
        component.shadowRoot!.querySelectorAll('h3')
      ).map(h => h.textContent?.trim());
      assert.deepEqual(headers, ['Start incubating', 'Start prototyping']);
    });

    it('resolves with true and hides dialog when Proceed is clicked', async () => {
      const component = await fixture<ChromedashPreflightDialog>(
        html`<chromedash-preflight-dialog></chromedash-preflight-dialog>`
      );
      const progress = {} as ProgressItem;
      const resolveStub = sinon.stub();
      const hideSpy = sinon.spy(component, 'hide');

      component.openWithContext(
        feature,
        progress,
        process,
        action,
        feStage,
        feStage,
        [],
        resolveStub
      );
      await component.updateComplete;

      const buttons = component.shadowRoot!.querySelectorAll('sl-button');
      const proceedButton = buttons[0] as HTMLElement;
      assert.include(proceedButton.textContent, 'Proceed');

      proceedButton.click();
      assert.isTrue(hideSpy.calledOnce);
      assert.isTrue(resolveStub.calledOnceWithExactly(true));
    });

    it('resolves with false and hides dialog when Cancel is clicked', async () => {
      const component = await fixture<ChromedashPreflightDialog>(
        html`<chromedash-preflight-dialog></chromedash-preflight-dialog>`
      );
      const progress = {} as ProgressItem;
      const resolveStub = sinon.stub();
      const hideSpy = sinon.spy(component, 'hide');

      component.openWithContext(
        feature,
        progress,
        process,
        action,
        feStage,
        feStage,
        [],
        resolveStub
      );
      await component.updateComplete;

      const buttons = component.shadowRoot!.querySelectorAll('sl-button');
      const cancelButton = buttons[1] as HTMLElement;
      assert.include(cancelButton.textContent, 'Cancel');

      cancelButton.click();
      assert.isTrue(hideSpy.calledOnce);
      assert.isTrue(resolveStub.calledOnceWithExactly(false));
    });

    it('openPreflightDialog returns a promise that resolves when user acts', async () => {
      const progress = {} as ProgressItem;
      const dialogPromise = openPreflightDialog(
        feature,
        progress,
        process,
        action,
        feStage,
        feStage,
        []
      );

      const dialogEl = document.querySelector(
        'chromedash-preflight-dialog'
      ) as ChromedashPreflightDialog;
      assert.exists(dialogEl);
      await dialogEl.updateComplete;

      dialogEl.handleProceed();
      const result = await dialogPromise;
      assert.isTrue(result);
    });
  });
});
