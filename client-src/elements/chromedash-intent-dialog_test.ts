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
import sinon from 'sinon';
import {ChromeStatusClient, Feature, StageDict} from '../js-src/cs-client.js';
import {GateDict} from './chromedash-gate-chip.js';
import * as enums from './form-field-enums.js';
import {
  ChromedashIntentDialog,
  openIntentDialog,
  shouldOfferIntentDialog,
  stageTypeToIntentSubject,
} from './chromedash-intent-dialog.js';
import {clearURLParams, parseRawQuery} from './utils.js';

describe('chromedash-intent-dialog', () => {
  beforeEach(() => {
    window.csClient = new ChromeStatusClient('fake_token', 1);
    clearURLParams('dialog');
  });

  afterEach(() => {
    clearURLParams('dialog');
    sinon.restore();
  });

  describe('stageTypeToIntentSubject', () => {
    it('maps prototype stage types to Intent to Prototype', () => {
      assert.equal(
        stageTypeToIntentSubject(enums.STAGE_BLINK_PROTOTYPE),
        'Intent to Prototype'
      );
      assert.equal(
        stageTypeToIntentSubject(enums.STAGE_FAST_PROTOTYPE),
        'Intent to Prototype'
      );
    });

    it('maps dev trial stage types to Ready for Developer Testing', () => {
      assert.equal(
        stageTypeToIntentSubject(enums.STAGE_BLINK_DEV_TRIAL),
        'Ready for Developer Testing'
      );
      assert.equal(
        stageTypeToIntentSubject(enums.STAGE_FAST_DEV_TRIAL),
        'Ready for Developer Testing'
      );
      assert.equal(
        stageTypeToIntentSubject(enums.STAGE_PSA_DEV_TRIAL),
        'Ready for Developer Testing'
      );
      assert.equal(
        stageTypeToIntentSubject(enums.STAGE_DEP_DEV_TRIAL),
        'Ready for Developer Testing'
      );
    });

    it('maps origin and deprecation trial stage types to Intent to Experiment', () => {
      assert.equal(
        stageTypeToIntentSubject(enums.STAGE_BLINK_ORIGIN_TRIAL),
        'Intent to Experiment'
      );
      assert.equal(
        stageTypeToIntentSubject(enums.STAGE_FAST_ORIGIN_TRIAL),
        'Intent to Experiment'
      );
      assert.equal(
        stageTypeToIntentSubject(enums.STAGE_DEP_DEPRECATION_TRIAL),
        'Intent to Experiment'
      );
    });

    it('maps extension stage types to Intent to Extend Experiment', () => {
      assert.equal(
        stageTypeToIntentSubject(enums.STAGE_BLINK_EXTEND_ORIGIN_TRIAL),
        'Intent to Extend Experiment'
      );
      assert.equal(
        stageTypeToIntentSubject(enums.STAGE_FAST_EXTEND_ORIGIN_TRIAL),
        'Intent to Extend Experiment'
      );
      assert.equal(
        stageTypeToIntentSubject(enums.STAGE_DEP_EXTEND_DEPRECATION_TRIAL),
        'Intent to Extend Experiment'
      );
    });

    it('maps shipping, PSA, and deprecation plan stage types to their subjects', () => {
      assert.equal(
        stageTypeToIntentSubject(enums.STAGE_BLINK_SHIPPING),
        'Intent to Ship'
      );
      assert.equal(
        stageTypeToIntentSubject(enums.STAGE_FAST_SHIPPING),
        'Intent to Ship'
      );
      assert.equal(
        stageTypeToIntentSubject(enums.STAGE_DEP_SHIPPING),
        'Intent to Ship'
      );
      assert.equal(
        stageTypeToIntentSubject(enums.STAGE_PSA_SHIPPING),
        'Web-Facing Change PSA'
      );
      assert.equal(
        stageTypeToIntentSubject(enums.STAGE_DEP_PLAN),
        'Intent to Deprecate and Remove'
      );
    });

    it('returns Unknown intent for unmapped stage types', () => {
      assert.equal(
        stageTypeToIntentSubject(enums.STAGE_BLINK_INCUBATE),
        'Unknown intent'
      );
      assert.equal(stageTypeToIntentSubject(999), 'Unknown intent');
    });
  });

  describe('shouldOfferIntentDialog', () => {
    it('returns true for API intent gates that are not in PREPARING state', () => {
      const intentGateTypes = [
        enums.GATE_TYPES.API_PROTOTYPE,
        enums.GATE_TYPES.API_ORIGIN_TRIAL,
        enums.GATE_TYPES.API_EXTEND_ORIGIN_TRIAL,
        enums.GATE_TYPES.API_SHIP,
        enums.GATE_TYPES.API_PLAN,
      ];
      for (const gateType of intentGateTypes) {
        assert.isTrue(
          shouldOfferIntentDialog({
            gate_type: gateType,
            state: enums.GATE_REVIEW_REQUESTED,
          })
        );
        assert.isTrue(
          shouldOfferIntentDialog({
            gate_type: gateType,
            state: enums.VOTE_OPTIONS.APPROVED[0],
          })
        );
      }
    });

    it('returns false when gate state is GATE_PREPARING', () => {
      assert.isFalse(
        shouldOfferIntentDialog({
          gate_type: enums.GATE_TYPES.API_SHIP,
          state: enums.GATE_PREPARING,
        })
      );
    });

    it('returns false for non-intent gate types', () => {
      assert.isFalse(
        shouldOfferIntentDialog({
          gate_type: enums.GATE_TYPES.PRIVACY_SHIP,
          state: enums.GATE_REVIEW_REQUESTED,
        })
      );
      assert.isFalse(
        shouldOfferIntentDialog({
          gate_type: enums.GATE_TYPES.ENTERPRISE_SHIP,
          state: enums.VOTE_OPTIONS.APPROVED[0],
        })
      );
    });
  });

  describe('ChromedashIntentDialog', () => {
    const feature = {
      id: 123456,
      name: 'Feature X',
    } as unknown as Feature;
    const stage = {
      id: 20,
      stage_type: enums.STAGE_BLINK_SHIPPING,
    } as unknown as StageDict;
    const gate = {
      id: 99,
      gate_type: enums.GATE_TYPES.API_SHIP,
      state: enums.GATE_REVIEW_REQUESTED,
    } as unknown as GateDict;

    it('sets dialog label from stage type and updates URL param when opened and closed', async () => {
      const component = await fixture<ChromedashIntentDialog>(
        html`<chromedash-intent-dialog></chromedash-intent-dialog>`
      );
      assert.instanceOf(component, ChromedashIntentDialog);

      component.openWithContext(feature, stage, gate);
      await component.updateComplete;

      assert.equal(parseRawQuery(window.location.search).dialog, 'intent');

      const dialog = component.shadowRoot!.querySelector('sl-dialog');
      assert.exists(dialog);
      assert.equal(dialog!.getAttribute('label'), 'Intent to Ship');

      dialog!.dispatchEvent(new CustomEvent('sl-hide', {bubbles: true}));
      assert.isUndefined(parseRawQuery(window.location.search).dialog);
    });

    it('openIntentDialog mounts dialog and opens with context', async () => {
      await openIntentDialog(feature, stage, gate);

      const dialogEl = document.querySelector(
        'chromedash-intent-dialog'
      ) as ChromedashIntentDialog;
      assert.exists(dialogEl);
      await dialogEl.updateComplete;

      assert.deepEqual(dialogEl.feature, feature);
      assert.deepEqual(dialogEl.stage, stage);
      assert.deepEqual(dialogEl.gate, gate);
      assert.equal(parseRawQuery(window.location.search).dialog, 'intent');

      dialogEl.hide();
      assert.isUndefined(parseRawQuery(window.location.search).dialog);
    });
  });
});
