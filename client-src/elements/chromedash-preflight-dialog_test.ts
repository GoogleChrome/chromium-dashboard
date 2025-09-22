import {assert} from '@open-wc/testing';
import {Feature, StageDict} from '../js-src/cs-client';
import {VOTE_OPTIONS} from './form-field-enums';
import {GateDict} from './chromedash-gate-chip.js';
import {findPendingGates} from './chromedash-preflight-dialog';

describe('preflight functions', () => {
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
