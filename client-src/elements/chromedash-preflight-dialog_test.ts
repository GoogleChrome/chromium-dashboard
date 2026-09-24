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

import {assert} from '@open-wc/testing';
import {StageDict} from '../js-src/cs-client.js';
import {PROGRESS_VOTE_STATE, VOTE_OPTIONS} from './form-field-enums.js';
import {GateDict} from './chromedash-gate-chip.js';
import {Action} from './chromedash-gate-column.js';
import {
  findPendingGates,
  somePendingPrereqs,
} from './chromedash-preflight-dialog.js';

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
});
