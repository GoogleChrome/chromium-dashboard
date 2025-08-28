import {assert} from '@open-wc/testing';
import {Feature, StageDict} from '../js-src/cs-client';
import {VOTE_OPTIONS} from './form-field-enums';
import {GateDict} from './chromedash-gate-chip.js';
import {
  findMissingFields,
  shouldShowPrevoteDialog,
} from './chromedash-prevote-dialog';

describe('prevote functions', () => {
  describe('findMissingFields', () => {
    const goodFeature = {web_feature: 'array'} as Feature;
    const badFeature = {} as Feature;
    const expectedMissing = {name: 'Web feature', field: 'web_feature'};
    it('detects having now web feature', () => {
      assert.deepEqual([expectedMissing], findMissingFields({} as Feature));
    });
    it('detects an explictly missing web feature', () => {
      assert.deepEqual(
        [expectedMissing],
        findMissingFields({web_feature: 'Missing feature'} as Feature)
      );
    });
    it('detects accepts any other value for  web feature', () => {
      assert.deepEqual(
        [],
        findMissingFields({web_feature: 'array'} as Feature)
      );
    });
  });

  describe('shouldShowPrevoteDialog', () => {
    const goodFeature = {web_feature: 'array'} as Feature;
    const badFeature = {} as Feature;
    const pendingGates = [] as GateDict[];
    const gate = {team_name: 'API Owners'} as GateDict;
    const vote = VOTE_OPTIONS.APPROVED[0];

    it('does not show criteria are met', () => {
      assert.isFalse(
        shouldShowPrevoteDialog(goodFeature, pendingGates, gate, vote)
      );
    });

    it('shows when web feature is undefined', () => {
      assert.isTrue(
        shouldShowPrevoteDialog({} as Feature, pendingGates, gate, vote)
      );
    });

    it('shows when web feature is explicitly missing', () => {
      assert.isTrue(
        shouldShowPrevoteDialog(badFeature, pendingGates, gate, vote)
      );
    });

    it('does not show for other teams', () => {
      assert.isFalse(
        shouldShowPrevoteDialog(
          badFeature,
          pendingGates,
          {team_name: 'Enterprise'} as GateDict,
          vote
        )
      );
    });

    it('does not show for votes other than approval', () => {
      assert.isFalse(
        shouldShowPrevoteDialog(
          badFeature,
          pendingGates,
          gate,
          VOTE_OPTIONS.NEEDS_WORK[0]
        )
      );
    });

    it('shows when there are pending gates', () => {
      assert.isTrue(
        shouldShowPrevoteDialog(goodFeature, [{}] as GateDict[], gate, vote)
      );
    });
  });
});
