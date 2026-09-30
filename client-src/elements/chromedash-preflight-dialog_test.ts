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
import '@shoelace-style/shoelace/dist/components/dialog/dialog.js';
import {Feature, StageDict} from '../js-src/cs-client.js';
import {PROGRESS_VOTE_STATE, VOTE_OPTIONS} from './form-field-enums.js';
import {GateDict} from './chromedash-gate-chip.js';
import {
  ChromedashPreflightDialog,
  findPendingGates,
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

    it('returns true when a prerequisite is NEEDS_WORK or NEEDS_REVIEW', () => {
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

      const progressNeedsReview = {
        Explainer: {
          state: PROGRESS_VOTE_STATE.NEEDS_REVIEW,
          set_on: '2026-09-23T00:00:00',
          set_by: 'reviewer@example.com',
        },
        'Spec link': {
          state: PROGRESS_VOTE_STATE.VERIFIED,
          set_on: '2026-09-23T00:00:00',
          set_by: 'ChromeStatus',
        },
      };
      assert.isTrue(somePendingPrereqs(action, progressNeedsReview));
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

    it('renders 3-column tables per stage with rows and Other gates table below', async () => {
      const component = await fixture<ChromedashPreflightDialog>(
        html`<chromedash-preflight-dialog></chromedash-preflight-dialog>`
      );
      const progress = {
        Motivation: 'true',
        'Spec link': 'https://example.com/spec',
      } as unknown as ProgressItem;
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
        '/feature/123456/gate/99/intent'
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
      assert.equal(row0Cells.length, 3);
      assert.equal(row0Cells[0].textContent?.trim(), 'Verified');
      assert.isNotNull(row0Cells[0].querySelector('.status.approved'));
      assert.equal(row0Cells[1].textContent?.trim(), 'Motivation');
      assert.equal(
        row0Cells[2].querySelector('a')?.getAttribute('href'),
        '/guide/stage/123456/1/10#id_motivation'
      );

      const row1Cells = stage1Rows[1].querySelectorAll('td');
      assert.equal(row1Cells[0].textContent?.trim(), 'Not started');
      assert.isNotNull(row1Cells[0].querySelector('.status.preparing'));
      assert.equal(row1Cells[1].textContent?.trim(), 'Explainer');
      assert.equal(
        row1Cells[2].querySelector('a')?.getAttribute('href'),
        '/guide/stage/123456/1/10#id_explainer_links'
      );

      const row2Cells = stage1Rows[2].querySelectorAll('td');
      assert.equal(row2Cells[0].textContent?.trim(), 'Not started');
      assert.equal(row2Cells[1].textContent?.trim(), 'Tracking bug URL');
      assert.equal(
        row2Cells[2].querySelector('a')?.getAttribute('href'),
        '/guide/stage/123456/metadata#id_bug_url'
      );

      // Table 1: Start prototyping (Spec link=Verified with edit link, Draft API spec=Pending with no edit link)
      const stage2Rows = tables[1].querySelectorAll('tr');
      assert.equal(stage2Rows.length, 2);
      assert.equal(
        stage2Rows[0].querySelectorAll('td')[0].textContent?.trim(),
        'Verified'
      );
      assert.equal(
        stage2Rows[0].querySelectorAll('td')[1].textContent?.trim(),
        'Spec link'
      );
      assert.isNotNull(
        stage2Rows[0].querySelectorAll('td')[2].querySelector('a')
      );
      assert.isNull(stage2Rows[1].querySelectorAll('td')[2].querySelector('a'));

      // Table 2: Other gates
      const gateRows = tables[2].querySelectorAll('tr');
      assert.equal(gateRows.length, 1);
      const gateCells = gateRows[0].querySelectorAll('td');
      assert.equal(gateCells.length, 3);
      assert.equal(gateCells[0].textContent?.trim(), 'Needs work');
      assert.equal(gateCells[1].textContent?.trim(), 'Privacy');
      assert.equal(
        gateCells[2].querySelector('a')?.textContent?.trim(),
        'View'
      );
      assert.equal(
        gateCells[2].querySelector('a')?.getAttribute('href'),
        '/feature/123456?gate=501'
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
        '/feature/123456/gate/99/intent'
      );
      await component.updateComplete;

      const headers = Array.from(
        component.shadowRoot!.querySelectorAll('h3')
      ).map(h => h.textContent?.trim());
      assert.deepEqual(headers, ['Start incubating', 'Start prototyping']);
    });
  });
});
