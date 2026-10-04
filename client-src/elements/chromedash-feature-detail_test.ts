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
import {Feature, StageDict} from '../js-src/cs-client.js';
import {
  ChromedashFeatureDetail,
  renderValue,
} from './chromedash-feature-detail.js';
import {
  GATE_PREPARING,
  GATE_REVIEW_REQUESTED,
  VOTE_OPTIONS,
} from './form-field-enums.js';

describe('chromedash-feature-detail', () => {
  const stageNoGates = {id: 1} as any;
  const stagePreparing = {id: 2} as any;
  const stageActive = {id: 3} as any;
  const stageMixed = {id: 4} as any;
  const stageResolved = {id: 5} as any;

  const gates = [
    {stage_id: stagePreparing.id, state: GATE_PREPARING},
    {stage_id: stageActive.id, state: GATE_PREPARING},
    {stage_id: stageActive.id, state: GATE_REVIEW_REQUESTED},
    {stage_id: stageMixed.id, state: GATE_PREPARING},
    {stage_id: stageMixed.id, state: VOTE_OPTIONS.APPROVED[0]},
    {stage_id: stageResolved.id, state: VOTE_OPTIONS.APPROVED[0]},
  ];

  const feature = {
    id: 123456789,
    is_enterprise_feature: false,
    stages: [],
  };

  it('renders with mimial data', async () => {
    const component = await fixture(
      html`<chromedash-feature-detail
        .feature=${feature}
      ></chromedash-feature-detail>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashFeatureDetail);
  });

  it('can identify active gates', async () => {
    const component: ChromedashFeatureDetail = (await fixture(
      html`<chromedash-feature-detail
        .feature=${feature}
        .gates=${gates}
      ></chromedash-feature-detail>`
    )) as ChromedashFeatureDetail;
    assert.isFalse(component.hasActiveGates(stageNoGates));
    assert.isFalse(component.hasActiveGates(stagePreparing));
    assert.isTrue(component.hasActiveGates(stageActive));
    assert.isFalse(component.hasActiveGates(stageMixed));
    assert.isFalse(component.hasActiveGates(stageResolved));
  });

  it('can identify mixed gates', async () => {
    const component: ChromedashFeatureDetail = (await fixture(
      html`<chromedash-feature-detail
        .feature=${feature}
        .gates=${gates}
      ></chromedash-feature-detail>`
    )) as ChromedashFeatureDetail;
    assert.isFalse(component.hasMixedGates(stageNoGates));
    assert.isFalse(component.hasMixedGates(stagePreparing));
    assert.isFalse(component.hasMixedGates(stageActive));
    assert.isTrue(component.hasMixedGates(stageMixed));
    assert.isFalse(component.hasMixedGates(stageResolved));
  });

  it('scrolls the stage <sl-details> into view in initializeGateColumn', async () => {
    const originalSearch = window.location.search;
    window.history.replaceState({}, '', '?gate=99');
    const scrollSpy = sinon.spy(Element.prototype, 'scrollIntoView');

    try {
      const featureWithStages = {
        id: 123456789,
        is_enterprise_feature: false,
        stages: [
          {id: 10, stage_type: 110, extensions: []},
          {id: 20, stage_type: 160, extensions: []},
        ],
      };
      const process = {
        stages: [
          {
            stage_type: 110,
            name: 'Start incubating',
            description: 'desc 1',
            actions: [],
          },
          {
            stage_type: 160,
            name: 'Prepare to ship',
            description: 'desc 2',
            actions: [],
          },
        ],
      };
      const testGates = [
        {
          id: 99,
          stage_id: 20,
          state: GATE_REVIEW_REQUESTED,
          team_name: 'API Owners',
        },
      ];

      const component: ChromedashFeatureDetail = (await fixture(
        html`<chromedash-feature-detail
          .feature=${featureWithStages}
          .process=${process}
          .gates=${testGates}
        ></chromedash-feature-detail>`
      )) as ChromedashFeatureDetail;

      await component.updateComplete;

      const stageDetails = component.renderRoot.querySelector('#stage-20');
      assert.exists(stageDetails);
      assert.isTrue(scrollSpy.calledOnce);
      assert.strictEqual(scrollSpy.firstCall.thisValue, stageDetails);
    } finally {
      scrollSpy.restore();
      window.history.replaceState(
        {},
        '',
        originalSearch || window.location.pathname
      );
    }
  });

  describe('renderValue', () => {
    const feStage = {id: 10} as StageDict;

    it('renders placeholder when field value is not defined', async () => {
      const el = await fixture<HTMLElement>(
        html`<div>
          ${renderValue(feStage, feature as unknown as Feature, 'motivation')}
        </div>`
      );
      assert.isNotNull(el.querySelector('i'));
      assert.equal(el.textContent?.trim(), 'No information provided yet');
    });

    it('renders checkbox values as True or False', async () => {
      const featureWithCheckbox = {
        ...feature,
        browsers: {chrome: {prefixed: true}},
      } as unknown as Feature;
      const el = await fixture<HTMLElement>(
        html`<div>
          ${renderValue(feStage, featureWithCheckbox, 'prefixed')}
        </div>`
      );
      assert.equal(el.querySelector('span.text')?.textContent?.trim(), 'True');
    });

    it('renders url and multi-url fields as chromedash-link elements', async () => {
      const featureWithUrls = {
        ...feature,
        standards: {spec: 'https://example.com/spec'},
        explainer_links: [
          'https://example.com/explainer-1',
          'https://example.com/explainer-2',
        ],
      } as unknown as Feature;

      const specEl = await fixture<HTMLElement>(
        html`<div>${renderValue(feStage, featureWithUrls, 'spec_link')}</div>`
      );
      const specLink = specEl.querySelector('chromedash-link');
      assert.isNotNull(specLink);
      assert.equal(specLink!.getAttribute('href'), 'https://example.com/spec');

      const explainersEl = await fixture<HTMLElement>(
        html`<div>
          ${renderValue(feStage, featureWithUrls, 'explainer_links')}
        </div>`
      );
      const listItems = explainersEl.querySelectorAll(
        'ul.inline-list li chromedash-link'
      );
      assert.equal(listItems.length, 2);
      assert.equal(
        listItems[0].getAttribute('href'),
        'https://example.com/explainer-1'
      );
      assert.equal(
        listItems[1].getAttribute('href'),
        'https://example.com/explainer-2'
      );
    });

    it('renders text and markdown fields appropriately', async () => {
      const featureWithText = {
        ...feature,
        motivation: 'Short text',
        summary: '**Bold summary**',
        markdown_fields: ['summary'],
      } as unknown as Feature;

      const textEl = await fixture<HTMLElement>(
        html`<div>${renderValue(feStage, featureWithText, 'motivation')}</div>`
      );
      assert.equal(
        textEl.querySelector('span.text')?.textContent?.trim(),
        'Short text'
      );

      const mdEl = await fixture<HTMLElement>(
        html`<div>${renderValue(feStage, featureWithText, 'summary')}</div>`
      );
      assert.equal(mdEl.querySelector('strong')?.textContent, 'Bold summary');
    });
  });
});
