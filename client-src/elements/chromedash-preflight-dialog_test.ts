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
import '@shoelace-style/shoelace/dist/components/input/input.js';
import '@shoelace-style/shoelace/dist/components/select/select.js';
import '@shoelace-style/shoelace/dist/components/option/option.js';
import {SlInput, SlSelect} from '@shoelace-style/shoelace';
import {
  ChromeStatusClient,
  Feature,
  StageDict,
  User,
} from '../js-src/cs-client.js';
import {PROGRESS_VOTE_STATE, VOTE_OPTIONS} from './form-field-enums.js';
import {GateDict} from './chromedash-gate-chip.js';
import {
  ChromedashPreflightDialog,
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
      const apiGate = {
        team_name: 'API Owners',
        state: VOTE_OPTIONS.NEEDS_WORK[0],
        stage_id: stage.id,
      } as GateDict;
      const actual = findPendingGates(
        [enterpriseGate, apiGate, privacyGate],
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

    const baseUser: User = {
      id: 1,
      can_create_feature: true,
      can_edit_all: false,
      can_review_release_notes: false,
      can_comment: true,
      is_admin: false,
      email: 'user@example.com',
      is_site_editor: false,
      approvable_gate_types: [],
      editable_features: [123456],
    };

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
        baseUser,
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
      assert.isNotNull(row0Cells[1].querySelector('.status.verified'));
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
      assert.isNotNull(row1Cells[1].querySelector('.status.not_started'));
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
        baseUser,
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
        baseUser,
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
        baseUser,
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
        baseUser,
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
        baseUser,
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

    describe('canVote', () => {
      const progress = {} as ProgressItem;

      it('returns false when user is undefined or lacks permissions', async () => {
        const component = await fixture<ChromedashPreflightDialog>(
          html`<chromedash-preflight-dialog></chromedash-preflight-dialog>`
        );
        assert.isFalse(component.canVote());

        component.openWithContext(
          baseUser,
          feature,
          progress,
          process,
          action,
          feStage,
          feStage,
          [],
          () => {}
        );
        assert.isFalse(component.canVote());
      });

      it('returns true when user can_edit_all is true', async () => {
        const component = await fixture<ChromedashPreflightDialog>(
          html`<chromedash-preflight-dialog></chromedash-preflight-dialog>`
        );
        component.openWithContext(
          {...baseUser, can_edit_all: true},
          feature,
          progress,
          process,
          action,
          feStage,
          feStage,
          [],
          () => {}
        );
        assert.isTrue(component.canVote());
      });

      it('returns true when user can_review_release_notes is true', async () => {
        const component = await fixture<ChromedashPreflightDialog>(
          html`<chromedash-preflight-dialog></chromedash-preflight-dialog>`
        );
        component.openWithContext(
          {...baseUser, can_review_release_notes: true},
          feature,
          progress,
          process,
          action,
          feStage,
          feStage,
          [],
          () => {}
        );
        assert.isTrue(component.canVote());
      });

      it('returns true when user has approvable_gate_types', async () => {
        const component = await fixture<ChromedashPreflightDialog>(
          html`<chromedash-preflight-dialog></chromedash-preflight-dialog>`
        );
        component.openWithContext(
          {...baseUser, approvable_gate_types: [1]},
          feature,
          progress,
          process,
          action,
          feStage,
          feStage,
          [],
          () => {}
        );
        assert.isTrue(component.canVote());
      });
    });

    describe('canEdit', () => {
      const progress = {} as ProgressItem;

      it('returns false and hides Edit links when user cannot edit the feature', async () => {
        const component = await fixture<ChromedashPreflightDialog>(
          html`<chromedash-preflight-dialog></chromedash-preflight-dialog>`
        );
        assert.isFalse(component.canEdit());

        component.openWithContext(
          {...baseUser, editable_features: []},
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

        assert.isFalse(component.canEdit());
        assert.isEmpty(
          component.shadowRoot!.querySelectorAll('a.edit-progress-item')
        );
      });

      it('returns true when user editable_features includes the feature id', async () => {
        const component = await fixture<ChromedashPreflightDialog>(
          html`<chromedash-preflight-dialog></chromedash-preflight-dialog>`
        );
        component.openWithContext(
          {...baseUser, editable_features: [123456]},
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

        assert.isTrue(component.canEdit());
        assert.isNotEmpty(
          component.shadowRoot!.querySelectorAll('a.edit-progress-item')
        );
      });

      it('returns true when user can_edit_all is true', async () => {
        const component = await fixture<ChromedashPreflightDialog>(
          html`<chromedash-preflight-dialog></chromedash-preflight-dialog>`
        );
        component.openWithContext(
          {...baseUser, editable_features: [], can_edit_all: true},
          feature,
          progress,
          process,
          action,
          feStage,
          feStage,
          [],
          () => {}
        );
        assert.isTrue(component.canEdit());
      });
    });

    describe('voting UI and saving', () => {
      const voterUser: User = {
        ...baseUser,
        can_edit_all: true,
      };

      beforeEach(() => {
        window.csClient = new ChromeStatusClient('fake_token', 1);
      });

      it('renders status chips for all vote states and hides Save button when user cannot vote', async () => {
        const component = await fixture<ChromedashPreflightDialog>(
          html`<chromedash-preflight-dialog></chromedash-preflight-dialog>`
        );
        const progress = {
          Motivation: {
            state: PROGRESS_VOTE_STATE.READY_FOR_REVIEW,
            set_on: '2026-09-23T00:00:00',
            set_by: 'ChromeStatus',
          },
          Explainer: {
            state: PROGRESS_VOTE_STATE.NA,
            set_on: '2026-09-23T00:00:00',
            set_by: 'reviewer@example.com',
          },
          'Tracking bug URL': {
            state: PROGRESS_VOTE_STATE.NEEDS_WORK,
            set_on: '2026-09-23T00:00:00',
            set_by: 'reviewer@example.com',
          },
          'Spec link': {
            state: PROGRESS_VOTE_STATE.VERIFIED,
            set_on: '2026-09-23T00:00:00',
            set_by: 'reviewer@example.com',
          },
        };

        component.openWithContext(
          baseUser,
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

        assert.isEmpty(component.shadowRoot!.querySelectorAll('sl-select'));

        const stage1Rows = component
          .shadowRoot!.querySelectorAll('table.data-table')[0]
          .querySelectorAll('tr');
        assert.equal(
          stage1Rows[0].querySelectorAll('td')[1].textContent?.trim(),
          'Ready for review'
        );
        assert.isNotNull(
          stage1Rows[0].querySelector('.status.ready_for_review')
        );
        assert.equal(
          stage1Rows[1].querySelectorAll('td')[1].textContent?.trim(),
          'N/A'
        );
        assert.isNotNull(stage1Rows[1].querySelector('.status.na'));
        assert.equal(
          stage1Rows[2].querySelectorAll('td')[1].textContent?.trim(),
          'Needs work'
        );
        assert.isNotNull(stage1Rows[2].querySelector('.status.needs_work'));

        const buttons = Array.from(
          component.shadowRoot!.querySelectorAll('sl-button')
        ).map(b => b.textContent?.trim());
        assert.deepEqual(buttons, ['Proceed', 'Cancel']);
      });

      it('renders sl-select menus and a disabled Save button when user can vote', async () => {
        const component = await fixture<ChromedashPreflightDialog>(
          html`<chromedash-preflight-dialog></chromedash-preflight-dialog>`
        );
        const progress = {
          Motivation: {
            state: PROGRESS_VOTE_STATE.VERIFIED,
            set_on: '2026-09-23T00:00:00',
            set_by: 'reviewer@example.com',
          },
          Explainer: {
            state: PROGRESS_VOTE_STATE.READY_FOR_REVIEW,
            set_on: '2026-09-23T00:00:00',
            set_by: 'ChromeStatus',
          },
        };

        component.openWithContext(
          voterUser,
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

        const selects =
          component.shadowRoot!.querySelectorAll<SlSelect>('sl-select');
        assert.equal(selects.length, 5);
        assert.equal(selects[0].dataset.pi, 'Motivation');
        assert.equal(Number(selects[0].value), PROGRESS_VOTE_STATE.VERIFIED);
        assert.equal(selects[1].dataset.pi, 'Explainer');
        assert.equal(
          Number(selects[1].value),
          PROGRESS_VOTE_STATE.READY_FOR_REVIEW
        );
        assert.equal(selects[2].dataset.pi, 'Tracking bug URL');
        assert.equal(Number(selects[2].value), PROGRESS_VOTE_STATE.NOT_STARTED);

        const options = selects[0].querySelectorAll('sl-option');
        assert.equal(options.length, 5);

        const buttons = component.shadowRoot!.querySelectorAll('sl-button');
        assert.equal(buttons.length, 3);
        const saveButton = buttons[2];
        assert.equal(saveButton.textContent?.trim(), 'Save');
        assert.isTrue(saveButton.hasAttribute('disabled'));
      });

      it('enables Save button when a status menu changes and resets when reopened', async () => {
        const component = await fixture<ChromedashPreflightDialog>(
          html`<chromedash-preflight-dialog></chromedash-preflight-dialog>`
        );
        const progress = {} as ProgressItem;

        component.openWithContext(
          voterUser,
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

        const explainerSelect = component.shadowRoot!.querySelector<SlSelect>(
          'sl-select[data-pi="Explainer"]'
        )!;
        const getSaveButton = () =>
          component.shadowRoot!.querySelectorAll('sl-button')[2];

        assert.isTrue(getSaveButton().hasAttribute('disabled'));

        explainerSelect.value = String(PROGRESS_VOTE_STATE.VERIFIED);
        explainerSelect.dispatchEvent(new CustomEvent('sl-change'));
        await component.updateComplete;

        assert.isFalse(getSaveButton().hasAttribute('disabled'));

        // Reopening resets dirty state and disables Save again.
        component.openWithContext(
          voterUser,
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
        assert.isTrue(getSaveButton().hasAttribute('disabled'));
      });

      it('renders feature-values row and feedback sl-input for voters when expanded', async () => {
        const component = await fixture<ChromedashPreflightDialog>(
          html`<chromedash-preflight-dialog></chromedash-preflight-dialog>`
        );
        const progress = {
          Explainer: {
            state: PROGRESS_VOTE_STATE.NEEDS_WORK,
            feedback: 'Existing feedback',
            set_on: '2026-09-23T00:00:00',
            set_by: 'reviewer@example.com',
          },
        };

        component.openWithContext(
          voterUser,
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

        // Explainer has existing feedback and field="explainer_links", so it starts expanded
        // with a feature-values row and a populated feedback sl-input.
        const valueRows =
          component.shadowRoot!.querySelectorAll('tr.feature-values');
        assert.equal(valueRows.length, 1);
        const valueCells = valueRows[0].querySelectorAll('td');
        assert.equal(valueCells.length, 4);
        assert.equal(valueCells[0].textContent?.trim(), '');
        assert.equal(valueCells[1].textContent?.trim(), 'explainer_links:');
        assert.equal(valueCells[2].textContent?.trim(), 'Value goes here');
        assert.equal(valueCells[3].textContent?.trim(), '');
        assert.equal(getComputedStyle(valueCells[0]).borderTopStyle, 'none');

        const explainerInput = component.shadowRoot!.querySelector<SlInput>(
          '.feedback-widget[data-pi="Explainer"]'
        );
        assert.isNotNull(explainerInput);
        assert.equal(explainerInput!.value, 'Existing feedback');

        // Motivation has no existing feedback and starts collapsed.
        assert.isNull(
          component.shadowRoot!.querySelector(
            '.feedback-widget[data-pi="Motivation"]'
          )
        );

        // Expanding Motivation renders its feature-values row and an empty feedback sl-input.
        const tables =
          component.shadowRoot!.querySelectorAll('table.data-table');
        const stage1Rows = tables[0].querySelectorAll('tr');
        const motivationCaret = stage1Rows[0].querySelector(
          'sl-icon'
        ) as HTMLElement;
        motivationCaret.click();
        await component.updateComplete;

        const motivationInput = component.shadowRoot!.querySelector<SlInput>(
          '.feedback-widget[data-pi="Motivation"]'
        );
        assert.isNotNull(motivationInput);
        assert.equal(motivationInput!.value, '');
        assert.equal(
          component.shadowRoot!.querySelectorAll('tr.feature-values').length,
          2
        );

        // Expanding "Draft API spec" (which has no field) renders feedback sl-input
        // without adding another feature-values row.
        const stage2Rows = tables[1].querySelectorAll('tr');
        const draftSpecCaret = stage2Rows[1].querySelector(
          'sl-icon'
        ) as HTMLElement;
        draftSpecCaret.click();
        await component.updateComplete;

        assert.isNotNull(
          component.shadowRoot!.querySelector(
            '.feedback-widget[data-pi="Draft API spec"]'
          )
        );
        assert.equal(
          component.shadowRoot!.querySelectorAll('tr.feature-values').length,
          2
        );
      });

      it('auto-expands item when status menu changes to NEEDS_WORK', async () => {
        const component = await fixture<ChromedashPreflightDialog>(
          html`<chromedash-preflight-dialog></chromedash-preflight-dialog>`
        );
        const progress = {} as ProgressItem;

        component.openWithContext(
          voterUser,
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

        const explainerSelect = component.shadowRoot!.querySelector<SlSelect>(
          '.state-widget[data-pi="Explainer"]'
        )!;
        assert.isNull(
          component.shadowRoot!.querySelector(
            '.feedback-widget[data-pi="Explainer"]'
          )
        );

        // Selecting VERIFIED does not auto-expand.
        explainerSelect.value = String(PROGRESS_VOTE_STATE.VERIFIED);
        explainerSelect.dispatchEvent(new CustomEvent('sl-change'));
        await component.updateComplete;
        assert.isNull(
          component.shadowRoot!.querySelector(
            '.feedback-widget[data-pi="Explainer"]'
          )
        );

        // Selecting NEEDS_WORK auto-expands the item and reveals the feedback input.
        explainerSelect.value = String(PROGRESS_VOTE_STATE.NEEDS_WORK);
        explainerSelect.dispatchEvent(new CustomEvent('sl-change'));
        await component.updateComplete;
        assert.isNotNull(
          component.shadowRoot!.querySelector(
            '.feedback-widget[data-pi="Explainer"]'
          )
        );

        // Dispatching NEEDS_WORK again when already expanded keeps it expanded.
        explainerSelect.dispatchEvent(new CustomEvent('sl-change'));
        await component.updateComplete;
        assert.isNotNull(
          component.shadowRoot!.querySelector(
            '.feedback-widget[data-pi="Explainer"]'
          )
        );
      });

      it('enables Save button and marks item touched when feedback input changes', async () => {
        const postStub = sinon
          .stub(window.csClient, 'postFeatureProgressVote')
          .resolves({message: 'Done'});

        const component = await fixture<ChromedashPreflightDialog>(
          html`<chromedash-preflight-dialog></chromedash-preflight-dialog>`
        );
        const progress = {
          Explainer: {
            state: PROGRESS_VOTE_STATE.NEEDS_WORK,
            feedback: 'Initial feedback',
            set_on: '2026-09-23T00:00:00',
            set_by: 'reviewer@example.com',
          },
        };

        component.openWithContext(
          voterUser,
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

        const getSaveButton = () =>
          component.shadowRoot!.querySelectorAll('sl-button')[2];
        assert.isTrue(getSaveButton().hasAttribute('disabled'));

        const explainerFeedback = component.shadowRoot!.querySelector<SlInput>(
          '.feedback-widget[data-pi="Explainer"]'
        )!;
        explainerFeedback.value = '  Updated feedback text  ';
        explainerFeedback.dispatchEvent(new CustomEvent('sl-change'));
        await component.updateComplete;

        assert.isFalse(getSaveButton().hasAttribute('disabled'));

        getSaveButton().click();
        await component.updateComplete;

        assert.isTrue(
          postStub.calledOnceWithExactly(
            123456,
            'Explainer',
            PROGRESS_VOTE_STATE.NEEDS_WORK,
            'Updated feedback text'
          )
        );
      });

      it('posts only touched votes, disables controls while saving, fires refetch-needed, and closes dialog on Save', async () => {
        let resolvePost!: (value?: unknown) => void;
        const postStub = sinon
          .stub(window.csClient, 'postFeatureProgressVote')
          .returns(
            new Promise(resolve => {
              resolvePost = resolve;
            })
          );

        const component = await fixture<ChromedashPreflightDialog>(
          html`<chromedash-preflight-dialog></chromedash-preflight-dialog>`
        );
        const progress = {
          Motivation: {
            state: PROGRESS_VOTE_STATE.READY_FOR_REVIEW,
            set_on: '2026-09-23T00:00:00',
            set_by: 'ChromeStatus',
          },
        };
        const resolveDialogStub = sinon.stub();
        const hideSpy = sinon.spy(component, 'hide');
        const refetchSpy = sinon.spy();
        component.addEventListener('refetch-needed', refetchSpy);

        component.openWithContext(
          voterUser,
          feature,
          progress,
          process,
          action,
          feStage,
          feStage,
          [],
          resolveDialogStub
        );
        await component.updateComplete;

        const explainerSelect = component.shadowRoot!.querySelector<SlSelect>(
          '.state-widget[data-pi="Explainer"]'
        )!;
        const specLinkSelect = component.shadowRoot!.querySelector<SlSelect>(
          '.state-widget[data-pi="Spec link"]'
        )!;

        explainerSelect.value = String(PROGRESS_VOTE_STATE.VERIFIED);
        explainerSelect.dispatchEvent(new CustomEvent('sl-change'));
        specLinkSelect.value = String(PROGRESS_VOTE_STATE.NEEDS_WORK);
        specLinkSelect.dispatchEvent(new CustomEvent('sl-change'));
        await component.updateComplete;

        // Spec link auto-expanded on NEEDS_WORK; enter feedback with whitespace.
        const specLinkFeedback = component.shadowRoot!.querySelector<SlInput>(
          '.feedback-widget[data-pi="Spec link"]'
        )!;
        specLinkFeedback.value = '  Please fix broken anchor  ';
        specLinkFeedback.dispatchEvent(new CustomEvent('sl-change'));
        await component.updateComplete;

        const getSaveButton = () =>
          component.shadowRoot!.querySelectorAll('sl-button')[2];
        getSaveButton().click();
        await component.updateComplete;

        // While saving, button shows Saving... and controls are disabled.
        assert.equal(getSaveButton().textContent?.trim(), 'Saving...');
        assert.isTrue(getSaveButton().hasAttribute('disabled'));
        assert.isTrue(explainerSelect.disabled);

        // Only the two touched items are posted.
        assert.isTrue(postStub.calledTwice);
        assert.isTrue(
          postStub.calledWithExactly(
            123456,
            'Explainer',
            PROGRESS_VOTE_STATE.VERIFIED,
            ''
          )
        );
        assert.isTrue(
          postStub.calledWithExactly(
            123456,
            'Spec link',
            PROGRESS_VOTE_STATE.NEEDS_WORK,
            'Please fix broken anchor'
          )
        );

        resolvePost({message: 'Done'});
        await new Promise(resolve => setTimeout(resolve, 0));
        await component.updateComplete;

        assert.isTrue(hideSpy.calledOnce);
        assert.isTrue(resolveDialogStub.calledOnceWithExactly(false));
        assert.isTrue(refetchSpy.calledOnce);
        assert.equal(getSaveButton().textContent?.trim(), 'Save');
      });
    });
  });
});
