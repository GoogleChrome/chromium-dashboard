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

import {html, nothing} from 'lit';
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
      summary: 'A summary of Feature X',
      explainer_links: ['https://example.com/explainer'],
      browsers: {
        chrome: {
          owners: ['owner@example.com'],
          bug: 'https://crbug.com/123456',
          blink_components: ['Blink>DOM'],
        },
        ff: {view: {}},
        safari: {view: {}},
        webdev: {view: {}},
        other: {view: {}},
      },
      standards: {
        spec: 'https://example.com/spec',
      },
      resources: {},
    } as unknown as Feature;
    const stage = {
      id: 20,
      stage_type: enums.STAGE_BLINK_SHIPPING,
      intent_thread_url: 'https://example.com/intent-thread',
    } as unknown as StageDict;
    const gate = {
      id: 99,
      gate_type: enums.GATE_TYPES.API_SHIP,
      state: enums.GATE_REVIEW_REQUESTED,
    } as unknown as GateDict;

    it('renders feature fields in northwest, northeast, and central grid sections when opened with context', async () => {
      const component = await fixture<ChromedashIntentDialog>(
        html`<chromedash-intent-dialog></chromedash-intent-dialog>`
      );
      assert.instanceOf(component, ChromedashIntentDialog);
      assert.equal(component.renderDialogContent(), nothing);

      component.openWithContext(feature, stage, gate);
      await component.updateComplete;

      assert.equal(parseRawQuery(window.location.search).dialog, 'intent');

      const dialog = component.shadowRoot!.querySelector('sl-dialog');
      assert.exists(dialog);
      assert.equal(dialog!.getAttribute('label'), 'Intent to Ship');
      assert.equal(dialog!.getAttribute('style'), '--width:fit-content');

      const northwest = dialog!.querySelector('#northwest');
      const northeast = dialog!.querySelector('#northeast');
      const central = dialog!.querySelector('#central');
      assert.exists(northwest);
      assert.exists(northeast);
      assert.exists(central);
      assert.isNull(dialog!.querySelector('dt sl-icon'));

      assert.exists(northwest!.querySelector('table.data-table'));
      assert.isNull(northwest!.querySelector('dl'));
      assert.include(northwest!.textContent, 'Feature X');
      assert.include(northwest!.textContent, 'owner@example.com');
      const explainerLink = northwest!.querySelector<HTMLAnchorElement>(
        'tr#explainer_links td:nth-child(2) a'
      );
      assert.exists(explainerLink);
      assert.equal(
        explainerLink!.getAttribute('href'),
        'https://example.com/explainer'
      );
      assert.equal(explainerLink!.textContent, 'https://example.com/explainer');
      const explainerList = northwest!.querySelector<HTMLElement>(
        'tr#explainer_links ul.inline-list'
      );
      assert.exists(explainerList);
      assert.equal(getComputedStyle(explainerList!).listStyleType, 'none');
      const specLink = northwest!.querySelector<HTMLAnchorElement>(
        'tr#spec_link td:nth-child(2) a'
      );
      assert.exists(specLink);
      assert.equal(specLink!.getAttribute('href'), 'https://example.com/spec');
      assert.equal(specLink!.textContent, 'https://example.com/spec');
      assert.equal(getComputedStyle(specLink!).textOverflow, 'ellipsis');
      const intentThreadLink = northwest!.querySelector<HTMLAnchorElement>(
        'tr#intent_thread_url td:nth-child(2) a'
      );
      assert.exists(intentThreadLink);
      assert.equal(
        intentThreadLink!.getAttribute('href'),
        'https://example.com/intent-thread'
      );
      assert.equal(
        intentThreadLink!.textContent,
        'https://example.com/intent-thread'
      );
      const webFeatureCell = northwest!.querySelector(
        'tr#web_feature td:nth-child(2)'
      );
      assert.exists(webFeatureCell);
      assert.exists(webFeatureCell!.querySelector('i'));
      assert.equal(webFeatureCell!.textContent, 'None');

      assert.exists(northeast!.querySelector('table.data-table'));
      assert.isNull(northeast!.querySelector('dl'));
      const bugLink = northeast!.querySelector<HTMLAnchorElement>(
        'tr#bug_url td:nth-child(2) a'
      );
      assert.exists(bugLink);
      assert.equal(bugLink!.getAttribute('href'), 'https://crbug.com/123456');
      assert.equal(bugLink!.textContent, 'https://crbug.com/123456');
      const dtDesktopCell = northeast!.querySelector(
        'tr#dt_milestone_desktop_start td:nth-child(2)'
      );
      assert.exists(dtDesktopCell);
      assert.exists(dtDesktopCell!.querySelector('i'));
      assert.equal(dtDesktopCell!.textContent, 'None');
      // Optional fields ending with '?' are omitted when undefined.
      assert.isNull(northeast!.querySelector('tr#launch_bug_url'));
      assert.isNull(northeast!.querySelector('tr#dt_milestone_android_start'));
      assert.isNull(central!.querySelector('dt#motivation'));
      assert.include(central!.textContent, 'A summary of Feature X');

      const detailsEls = Array.from(
        central!.querySelectorAll<HTMLElement>('sl-details')
      );
      const summaries = detailsEls.map(el => el.getAttribute('summary'));
      // 'Details' is omitted because all of its fields ('motivation?', 'dev_trial_instructions?') are undefined.
      assert.deepEqual(summaries, [
        'Spec and TAG',
        'Risks',
        'Signals',
        'Implementation',
        'Deployment and adoption',
      ]);
      for (const el of detailsEls) {
        assert.isTrue(el.hasAttribute('open'));
      }

      dialog!.dispatchEvent(new CustomEvent('sl-hide', {bubbles: true}));
      assert.isUndefined(parseRawQuery(window.location.search).dialog);
    });

    it('filters central groups by intent type and renders defined optional fields', async () => {
      const component = await fixture<ChromedashIntentDialog>(
        html`<chromedash-intent-dialog></chromedash-intent-dialog>`
      );
      const featureWithOptionals = {
        ...feature,
        motivation: 'Strong developer demand',
        launch_bug_url: 'https://crbug.com/999999',
      } as unknown as Feature;
      const prototypeStage = {
        id: 10,
        stage_type: enums.STAGE_BLINK_PROTOTYPE,
      } as unknown as StageDict;

      component.openWithContext(featureWithOptionals, prototypeStage, gate);
      await component.updateComplete;

      const northeast = component.shadowRoot!.querySelector('#northeast')!;
      const central = component.shadowRoot!.querySelector('#central')!;

      const launchBugLink = northeast.querySelector<HTMLAnchorElement>(
        'tr#launch_bug_url td:nth-child(2) a'
      );
      assert.exists(launchBugLink);
      assert.equal(
        launchBugLink!.getAttribute('href'),
        'https://crbug.com/999999'
      );

      const detailsEls = Array.from(
        central.querySelectorAll<HTMLElement>('sl-details')
      );
      assert.deepEqual(
        detailsEls.map(el => el.getAttribute('summary')),
        ['Details']
      );
      assert.exists(central.querySelector('dt#motivation'));
      assert.include(central.textContent, 'Strong developer demand');
    });

    it('switches to showing grid areas one after the other when content width is too narrow', async () => {
      const component = await fixture<ChromedashIntentDialog>(
        html`<chromedash-intent-dialog></chromedash-intent-dialog>`
      );
      component.openWithContext(feature, stage, gate);
      await component.updateComplete;
      await new Promise(resolve => requestAnimationFrame(resolve));

      const gridEl =
        component.shadowRoot!.querySelector<HTMLElement>('#content-grid')!;
      assert.exists(gridEl);

      // Constrain width so two columns cannot fit without horizontal overflow.
      gridEl.style.width = '200px';
      component.checkGridOverflow();

      assert.isTrue(gridEl.classList.contains('narrow'));
      const northwest = gridEl.querySelector<HTMLElement>('#northwest')!;
      const northeast = gridEl.querySelector<HTMLElement>('#northeast')!;
      const central = gridEl.querySelector<HTMLElement>('#central')!;
      assert.equal(getComputedStyle(northwest).gridColumnStart, '1');
      assert.equal(getComputedStyle(northeast).gridColumnStart, '1');
      assert.equal(getComputedStyle(central).gridColumnStart, '1');
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
