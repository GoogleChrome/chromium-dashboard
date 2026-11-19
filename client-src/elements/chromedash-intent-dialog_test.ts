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
import '@shoelace-style/shoelace/dist/components/details/details.js';
import '@shoelace-style/shoelace/dist/components/dialog/dialog.js';
import sinon from 'sinon';
import {
  ChromeStatusClient,
  Feature,
  FeatureLink,
  StageDict,
} from '../js-src/cs-client.js';
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
          owners: ['owner@example.com', 'owner2@example.com'],
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

      // When viewport is not narrow (> 860px), sl-dialog::part(base) right inset is --sidebar-space (410px)
      // so the panel centers over the drawer and #content-component-wrapper and does not overlap #content-sidebar-space.
      const basePart =
        dialog!.shadowRoot?.querySelector<HTMLElement>('[part~="base"]');
      const panelPart =
        dialog!.shadowRoot?.querySelector<HTMLElement>('[part~="panel"]');
      assert.exists(basePart);
      assert.exists(panelPart);
      if (window.innerWidth > 860) {
        const expectedRightOpen =
          410 + Math.max(0, (window.innerWidth - 210 - 860 - 410) / 2);
        assert.equal(
          getComputedStyle(basePart!).right,
          `${expectedRightOpen}px`
        );
        const rect = panelPart!.getBoundingClientRect();
        assert.isAtMost(rect.right, window.innerWidth - expectedRightOpen);

        // When the nav drawer is closed (--content-margin-left: 20px),
        // the right inset shifts left to keep clear of #content-sidebar-space.
        component.style.setProperty('--content-margin-left', '20px');
        const expectedRightClosed =
          410 + Math.max(0, (window.innerWidth - 20 - 860 - 410) / 2);
        assert.equal(
          getComputedStyle(basePart!).right,
          `${expectedRightClosed}px`
        );
        const closedRect = panelPart!.getBoundingClientRect();
        assert.isAtMost(
          closedRect.right,
          window.innerWidth - expectedRightClosed
        );
        component.style.removeProperty('--content-margin-left');
      } else {
        assert.equal(getComputedStyle(basePart!).right, '0px');
      }

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
      const ownerCell = northwest!.querySelector('tr#owner td:nth-child(2)');
      assert.exists(ownerCell);
      assert.equal(
        ownerCell!.textContent?.trim(),
        'owner@example.com, owner2@example.com'
      );
      const explainerLink = northwest!.querySelector(
        'tr#explainer_links td:nth-child(2) chromedash-link'
      );
      assert.exists(explainerLink);
      assert.equal(
        explainerLink!.getAttribute('href'),
        'https://example.com/explainer'
      );
      const explainerList = northwest!.querySelector<HTMLElement>(
        'tr#explainer_links ul.inline-list'
      );
      assert.exists(explainerList);
      assert.equal(getComputedStyle(explainerList!).listStyleType, 'none');
      const specLink = northwest!.querySelector(
        'tr#spec_link td:nth-child(2) chromedash-link'
      );
      assert.exists(specLink);
      assert.equal(specLink!.getAttribute('href'), 'https://example.com/spec');
      const intentThreadLink = northwest!.querySelector(
        'tr#intent_thread_url td:nth-child(2) chromedash-link'
      );
      assert.exists(intentThreadLink);
      assert.equal(
        intentThreadLink!.getAttribute('href'),
        'https://example.com/intent-thread'
      );
      const webFeatureCell = northwest!.querySelector(
        'tr#web_feature td:nth-child(2)'
      );
      assert.exists(webFeatureCell);
      assert.exists(webFeatureCell!.querySelector('i'));
      assert.equal(
        webFeatureCell!.textContent?.trim(),
        'No information provided yet'
      );

      assert.exists(northeast!.querySelector('table.data-table'));
      assert.isNull(northeast!.querySelector('dl'));
      const bugLink = northeast!.querySelector(
        'tr#bug_url td:nth-child(2) chromedash-link'
      );
      assert.exists(bugLink);
      assert.equal(bugLink!.getAttribute('href'), 'https://crbug.com/123456');
      const dtDesktopCell = northeast!.querySelector(
        'tr#dt_milestone_desktop_start td:nth-child(2)'
      );
      assert.exists(dtDesktopCell);
      assert.exists(dtDesktopCell!.querySelector('i'));
      assert.equal(
        dtDesktopCell!.textContent?.trim(),
        'No information provided yet'
      );
      // Optional fields ending with '?' are omitted when undefined.
      assert.isNull(northeast!.querySelector('tr#launch_bug_url'));
      assert.isNull(northeast!.querySelector('tr#dt_milestone_android_start'));
      assert.isNull(central!.querySelector('dt#motivation'));
      assert.include(central!.textContent, 'A summary of Feature X');

      const detailsEls = Array.from(
        central!.querySelectorAll<HTMLElement>('sl-details')
      );
      const summaries = detailsEls.map(el => el.getAttribute('summary'));
      // 'Details' is omitted because all of its fields ('motivation?', 'devtrial_instructions?') are undefined.
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

      // Bubbling sl-hide from a child <sl-details> should not clear ?dialog=intent.
      detailsEls[0].dispatchEvent(new CustomEvent('sl-hide', {bubbles: true}));
      assert.equal(parseRawQuery(window.location.search).dialog, 'intent');

      // sl-hide originating on <sl-dialog> itself clears ?dialog=intent.
      dialog!.dispatchEvent(new CustomEvent('sl-hide', {bubbles: true}));
      assert.isUndefined(parseRawQuery(window.location.search).dialog);

      component.hide();
    });

    it('filters central groups by intent type and renders defined optional fields', async () => {
      const component = await fixture<ChromedashIntentDialog>(
        html`<chromedash-intent-dialog></chromedash-intent-dialog>`
      );
      const featureWithOptionals = {
        ...feature,
        motivation: 'Strong developer demand',
        devtrial_instructions: 'https://example.com/devtrial-howto',
        launch_bug_url: 'https://crbug.com/999999',
        initial_public_proposal_url: 'javascript:alert(1)',
        explainer_links: ['https://example.com/explainer', 'N/A', null],
      } as unknown as Feature;
      const prototypeStage = {
        id: 10,
        stage_type: enums.STAGE_BLINK_PROTOTYPE,
      } as unknown as StageDict;

      component.openWithContext(featureWithOptionals, prototypeStage, gate);
      await component.updateComplete;

      const northwest = component.shadowRoot!.querySelector('#northwest')!;
      const northeast = component.shadowRoot!.querySelector('#northeast')!;
      const central = component.shadowRoot!.querySelector('#central')!;

      const launchBugLink = northeast.querySelector(
        'tr#launch_bug_url td:nth-child(2) chromedash-link'
      );
      assert.exists(launchBugLink);
      assert.equal(
        launchBugLink!.getAttribute('href'),
        'https://crbug.com/999999'
      );

      // Non-http(s) URLs render as plain text rather than clickable links.
      const proposalCell = northeast.querySelector(
        'tr#initial_public_proposal_url td:nth-child(2)'
      );
      assert.exists(proposalCell);
      assert.isNull(proposalCell!.querySelector('chromedash-link'));
      assert.isNull(proposalCell!.querySelector('a'));
      assert.equal(proposalCell!.textContent?.trim(), 'javascript:alert(1)');

      const explainerItems = Array.from(
        northwest.querySelectorAll('tr#explainer_links ul.inline-list li')
      );
      assert.equal(explainerItems.length, 2);
      assert.exists(explainerItems[0].querySelector('chromedash-link'));
      assert.isNull(explainerItems[1].querySelector('chromedash-link'));
      assert.equal(explainerItems[1].textContent, 'N/A');

      const detailsEls = Array.from(
        central.querySelectorAll<HTMLElement>('sl-details')
      );
      assert.deepEqual(
        detailsEls.map(el => el.getAttribute('summary')),
        ['Details']
      );
      assert.exists(central.querySelector('dt#motivation'));
      assert.include(central.textContent, 'Strong developer demand');
      assert.exists(central.querySelector('dt#devtrial_instructions'));
      const devtrialLink = central.querySelector('chromedash-link');
      assert.exists(devtrialLink);
      assert.equal(
        devtrialLink!.getAttribute('href'),
        'https://example.com/devtrial-howto'
      );

      component.hide();
    });

    it('resolves stage-specific milestone and origin trial fields from their owning stages', async () => {
      const component = await fixture<ChromedashIntentDialog>(
        html`<chromedash-intent-dialog></chromedash-intent-dialog>`
      );
      const dtStage = {
        id: 11,
        stage_type: enums.STAGE_BLINK_DEV_TRIAL,
        desktop_first: 130,
      } as unknown as StageDict;
      const otExtStage = {
        id: 16,
        stage_type: enums.STAGE_BLINK_EXTEND_ORIGIN_TRIAL,
        ot_stage_id: 15,
        desktop_last: 136,
        intent_thread_url: 'https://example.com/extend-thread',
      } as unknown as StageDict;
      const otStage = {
        id: 15,
        stage_type: enums.STAGE_BLINK_ORIGIN_TRIAL,
        desktop_first: 132,
        desktop_last: 134,
        experiment_goals: 'Validate API ergonomics',
        experiment_risks: 'Potential API surface changes',
        extensions: [otExtStage],
      } as unknown as StageDict;
      const earlierShipStage = {
        id: 19,
        stage_type: enums.STAGE_BLINK_SHIPPING,
        desktop_first: 133,
      } as unknown as StageDict;
      const shipStage = {
        id: 20,
        stage_type: enums.STAGE_BLINK_SHIPPING,
        desktop_first: 137,
        intent_thread_url: 'https://example.com/ship-thread',
      } as unknown as StageDict;
      const rolloutStage = {
        id: 25,
        stage_type: enums.STAGE_ENT_ROLLOUT,
        desktop_first: 138,
      } as unknown as StageDict;

      const multiStageFeature = {
        ...feature,
        stages: [dtStage, otStage, earlierShipStage, shipStage, rolloutStage],
      } as unknown as Feature;

      // 1. Open Intent to Ship: each milestone row reads from its own stage.
      component.openWithContext(multiStageFeature, shipStage, gate);
      await component.updateComplete;

      const northeast = component.shadowRoot!.querySelector('#northeast')!;
      assert.equal(
        northeast
          .querySelector('tr#dt_milestone_desktop_start td:nth-child(2)')
          ?.textContent?.trim(),
        '130'
      );
      assert.equal(
        northeast
          .querySelector('tr#ot_milestone_desktop_start td:nth-child(2)')
          ?.textContent?.trim(),
        '132'
      );
      assert.equal(
        northeast
          .querySelector('tr#ot_milestone_desktop_end td:nth-child(2)')
          ?.textContent?.trim(),
        '136 (extended from 134)'
      );
      assert.equal(
        northeast
          .querySelector('tr#shipped_milestone td:nth-child(2)')
          ?.textContent?.trim(),
        '137'
      );
      assert.equal(
        northeast
          .querySelector('tr#rollout_milestone td:nth-child(2)')
          ?.textContent?.trim(),
        '138'
      );

      // 2. Open Intent to Extend Experiment: experiment_goals and experiment_risks read from parent OT stage,
      // while intent_thread_url reads from the extension stage itself.
      const extendGate = {
        id: 100,
        gate_type: enums.GATE_TYPES.API_EXTEND_ORIGIN_TRIAL,
        state: enums.GATE_REVIEW_REQUESTED,
      } as unknown as GateDict;
      component.openWithContext(multiStageFeature, otExtStage, extendGate);
      await component.updateComplete;

      const northwest = component.shadowRoot!.querySelector('#northwest')!;
      const central = component.shadowRoot!.querySelector('#central')!;
      const extThreadLink = northwest.querySelector(
        'tr#intent_thread_url td:nth-child(2) chromedash-link'
      );
      assert.exists(extThreadLink);
      assert.equal(
        extThreadLink!.getAttribute('href'),
        'https://example.com/extend-thread'
      );
      assert.include(central.textContent, 'Validate API ergonomics');
      assert.include(central.textContent, 'Potential API surface changes');
      // Picks the latest matching shipping stage (137, not 133).
      assert.equal(
        northeast
          .querySelector('tr#shipped_milestone td:nth-child(2)')
          ?.textContent?.trim(),
        '137'
      );

      component.hide();
    });

    it('wraps northwest and northeast vertically when content width is too narrow', async () => {
      const component = await fixture<ChromedashIntentDialog>(
        html`<chromedash-intent-dialog></chromedash-intent-dialog>`
      );

      // At laptop dialog content width, #northwest and #northeast fit side-by-side even with long URLs.
      const featureWithLongUrls = {
        ...feature,
        explainer_links: [
          'https://docs.google.com/document/d/1234567890abcdefghijklmnopqrstuvwxyz/edit',
        ],
        browsers: {
          ...feature.browsers,
          chrome: {
            ...feature.browsers.chrome,
            bug: 'https://issues.chromium.org/issues/401234567890/something-very-long',
          },
        },
      } as unknown as Feature;
      component.openWithContext(featureWithLongUrls, stage, gate);
      await component.updateComplete;
      await new Promise(resolve => requestAnimationFrame(resolve));

      const gridEl =
        component.shadowRoot!.querySelector<HTMLElement>('#content-grid')!;
      assert.exists(gridEl);
      const northwest = gridEl.querySelector<HTMLElement>('#northwest')!;
      const northeast = gridEl.querySelector<HTMLElement>('#northeast')!;
      const central = gridEl.querySelector<HTMLElement>('#central')!;

      // Simulate laptop dialog content width (~1000px).
      gridEl.style.width = '1000px';

      const nwWideRect = northwest.getBoundingClientRect();
      const neWideRect = northeast.getBoundingClientRect();
      const centralWideRect = central.getBoundingClientRect();
      assert.equal(nwWideRect.top, neWideRect.top);
      assert.isAbove(neWideRect.left, nwWideRect.left);
      assert.isAtLeast(centralWideRect.top, nwWideRect.bottom);

      // Constrain width so two columns wrap one after the other in pure CSS.
      gridEl.style.width = '500px';

      const nwNarrowRect = northwest.getBoundingClientRect();
      const neNarrowRect = northeast.getBoundingClientRect();
      const centralNarrowRect = central.getBoundingClientRect();
      assert.equal(nwNarrowRect.left, neNarrowRect.left);
      assert.equal(nwNarrowRect.left, centralNarrowRect.left);
      assert.isAtLeast(neNarrowRect.top, nwNarrowRect.bottom);
      assert.isAtLeast(centralNarrowRect.top, neNarrowRect.bottom);

      component.hide();
    });

    it('openIntentDialog mounts dialog and opens with context', async () => {
      const featureLinks = [
        {url: 'https://example.com/spec', type: 'spec', information: {}},
      ] as unknown as FeatureLink[];
      await openIntentDialog(feature, stage, gate, featureLinks);

      const dialogEl = document.querySelector(
        'chromedash-intent-dialog'
      ) as ChromedashIntentDialog;
      assert.exists(dialogEl);
      await dialogEl.updateComplete;

      assert.deepEqual(dialogEl.feature, feature);
      assert.deepEqual(dialogEl.stage, stage);
      assert.deepEqual(dialogEl.gate, gate);
      assert.deepEqual(dialogEl.featureLinks, featureLinks);
      const specLink = dialogEl.shadowRoot!.querySelector(
        'tr#spec_link td:nth-child(2) chromedash-link'
      ) as HTMLElement & {featureLinks?: FeatureLink[]};
      assert.exists(specLink);
      assert.deepEqual(specLink.featureLinks, featureLinks);
      assert.equal(parseRawQuery(window.location.search).dialog, 'intent');

      dialogEl.hide();
      assert.isUndefined(parseRawQuery(window.location.search).dialog);
    });
  });
});
