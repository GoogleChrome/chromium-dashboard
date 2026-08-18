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

import {html, fixture, expect} from '@open-wc/testing';
import sinon from 'sinon';
import './chromedash-ai-summary-progress.js';
import {ChromedashAiSummaryProgress} from './chromedash-ai-summary-progress.js';
import {ProgressStep, SummarySuggestion} from '../js-src/cs-client.js';

describe('chromedash-ai-summary-progress', () => {
  let sandbox: sinon.SinonSandbox;

  beforeEach(() => {
    sandbox = sinon.createSandbox();
    window.csClient = {
      getSummarySuggestion: sandbox.stub().resolves({
        suggestion: {
          feature_id: 101,
          status: 'PENDING',
          suggested_summary: 'AI summary',
          suggested_doc_links: [],
          version_token: 1,
          created: new Date(),
          updated: new Date(),
        } as SummarySuggestion,
        progress_steps: [
          {
            step: 'READ_SPEC',
            status: 'SUCCESS',
            message: 'Read 120 lines',
            start_timestamp: new Date(),
          },
          {
            step: 'SEARCH_MDN',
            status: 'IN_PROGRESS',
            message: 'Querying MDN',
            start_timestamp: new Date(),
          },
        ] as ProgressStep[],
      }),
      triggerSummaryGeneration: sandbox.stub().resolves({
        message: 'Task enqueued',
      }),
    } as any;
  });

  afterEach(() => {
    sandbox.restore();
  });

  it('renders nothing when empty with no steps, not loading, and no error', async () => {
    const el = await fixture<ChromedashAiSummaryProgress>(
      html`<chromedash-ai-summary-progress
        .autoPoll=${false}
      ></chromedash-ai-summary-progress>`
    );

    expect(el.shadowRoot!.children.length).to.equal(0);
  });

  it('renders progress steps with correct labels and Material icons', async () => {
    const steps: ProgressStep[] = [
      {
        step: 'READ_SPEC',
        status: 'SUCCESS',
        message: 'Found spec link',
        start_timestamp: new Date(),
      },
      {
        step: 'SEARCH_MDN',
        status: 'IN_PROGRESS',
        message: 'Searching web docs',
        start_timestamp: new Date(),
      },
      {
        step: 'VERIFY_DOC_LINK',
        status: 'FAILED',
        message: '404 not found',
        start_timestamp: new Date(),
      },
      {
        step: 'READ_EXPLAINER',
        status: 'RETRYING',
        message: 'Retrying explainer',
        start_timestamp: new Date(),
      },
    ];

    const el = await fixture<ChromedashAiSummaryProgress>(
      html`<chromedash-ai-summary-progress
        .autoPoll=${false}
        .progressSteps=${steps}
      ></chromedash-ai-summary-progress>`
    );

    const stepItems = el.shadowRoot!.querySelectorAll('.step-item');
    expect(stepItems.length).to.equal(4);

    expect(stepItems[0].classList.contains('success')).to.be.true;
    expect(stepItems[0].textContent).to.contain('Reading specification');
    expect(stepItems[0].textContent).to.contain('Found spec link');
    const successIcon = stepItems[0].querySelector('sl-icon');
    expect(successIcon).to.exist;
    expect(successIcon!.getAttribute('name')).to.equal('check-lg');

    expect(stepItems[1].classList.contains('in-progress')).to.be.true;
    expect(stepItems[1].textContent).to.contain('Searching MDN documentation');
    expect(stepItems[1].querySelector('sl-spinner')).to.exist;

    expect(stepItems[2].classList.contains('failed')).to.be.true;
    expect(stepItems[2].textContent).to.contain(
      'Verifying documentation links'
    );
    const failedIcon = stepItems[2].querySelector('sl-icon');
    expect(failedIcon).to.exist;
    expect(failedIcon!.getAttribute('name')).to.equal('x-circle-fill');

    expect(stepItems[3].classList.contains('retrying')).to.be.true;
    const retryIcon = stepItems[3].querySelector('sl-icon');
    expect(retryIcon).to.exist;
    expect(retryIcon!.getAttribute('name')).to.equal('exclamation-circle-fill');
  });

  it('renders error banner and calls handleTrigger on Retry click', async () => {
    const el = await fixture<ChromedashAiSummaryProgress>(
      html`<chromedash-ai-summary-progress
        .autoPoll=${false}
        .featureId=${101}
      ></chromedash-ai-summary-progress>`
    );
    el.error = 'Failed to generate summary';
    await el.updateComplete;

    const errorBanner = el.shadowRoot!.querySelector('.error-banner');
    expect(errorBanner).to.exist;
    expect(errorBanner!.textContent).to.contain('Failed to generate summary');

    const retryButton = errorBanner!.querySelector('sl-button');
    expect(retryButton).to.exist;

    const triggerSpy = sandbox.spy(el, 'handleTrigger');
    retryButton!.click();
    expect(triggerSpy.calledOnceWith(true)).to.be.true;
  });

  it('dispatches summary-generation-started event when triggered', async () => {
    const el = await fixture<ChromedashAiSummaryProgress>(
      html`<chromedash-ai-summary-progress
        .autoPoll=${false}
        .featureId=${101}
      ></chromedash-ai-summary-progress>`
    );

    let eventFired = false;
    el.addEventListener('summary-generation-started', (e: any) => {
      eventFired = true;
      expect(e.detail.featureId).to.equal(101);
      expect(e.detail.force).to.be.true;
    });

    await el.handleTrigger(true);
    expect(eventFired).to.be.true;
    expect(
      (
        window.csClient.triggerSummaryGeneration as sinon.SinonStub
      ).calledOnceWith(101, true)
    ).to.be.true;
  });

  it('dispatches summary-generation-completed when all steps succeed', async () => {
    (window.csClient.getSummarySuggestion as sinon.SinonStub).resolves({
      suggestion: {
        feature_id: 101,
        status: 'PENDING',
        suggested_summary: 'AI summary',
        suggested_doc_links: [],
        version_token: 1,
        created: new Date(),
        updated: new Date(),
      },
      progress_steps: [
        {
          step: 'READ_SPEC',
          status: 'SUCCESS',
          message: 'Done',
          start_timestamp: new Date(),
        },
      ],
    });

    const el = await fixture<ChromedashAiSummaryProgress>(
      html`<chromedash-ai-summary-progress
        .autoPoll=${false}
        .featureId=${101}
      ></chromedash-ai-summary-progress>`
    );

    let completedFired = false;
    el.addEventListener('summary-generation-completed', (e: any) => {
      completedFired = true;
      expect(e.detail.featureId).to.equal(101);
    });

    await el.fetchStatus();
    expect(completedFired).to.be.true;
  });

  it('dispatches summary-generation-failed when a step fails', async () => {
    (window.csClient.getSummarySuggestion as sinon.SinonStub).resolves({
      suggestion: null,
      progress_steps: [
        {
          step: 'READ_SPEC',
          status: 'FAILED',
          message: 'Error reading spec',
          start_timestamp: new Date(),
        },
      ],
    });

    const el = await fixture<ChromedashAiSummaryProgress>(
      html`<chromedash-ai-summary-progress
        .autoPoll=${false}
        .featureId=${101}
      ></chromedash-ai-summary-progress>`
    );

    let failedFired = false;
    el.addEventListener('summary-generation-failed', (e: any) => {
      failedFired = true;
      expect(e.detail.featureId).to.equal(101);
    });

    await el.fetchStatus();
    expect(failedFired).to.be.true;
  });

  it('applies compact styling when compact is true', async () => {
    const steps: ProgressStep[] = [
      {
        step: 'READ_SPEC',
        status: 'SUCCESS',
        message: 'Done',
        start_timestamp: new Date(),
      },
    ];

    const el = await fixture<ChromedashAiSummaryProgress>(
      html`<chromedash-ai-summary-progress
        .autoPoll=${false}
        .compact=${true}
        .progressSteps=${steps}
      ></chromedash-ai-summary-progress>`
    );

    const container = el.shadowRoot!.querySelector('.container');
    expect(container).to.exist;
    expect(container!.classList.contains('compact')).to.be.true;
  });

  it('cleans up polling timer on disconnectedCallback', async () => {
    const el = await fixture<ChromedashAiSummaryProgress>(
      html`<chromedash-ai-summary-progress
        .autoPoll=${false}
        .featureId=${101}
      ></chromedash-ai-summary-progress>`
    );

    el.startPolling();
    expect(el.polling).to.be.true;

    el.disconnectedCallback();
    expect(el.polling).to.be.false;
  });

  it('resets state and refetches when featureId changes dynamically', async () => {
    const el = await fixture<ChromedashAiSummaryProgress>(
      html`<chromedash-ai-summary-progress
        .autoPoll=${true}
        .featureId=${101}
      ></chromedash-ai-summary-progress>`
    );

    el.startPolling();
    expect(el.polling).to.be.true;

    (window.csClient.getSummarySuggestion as sinon.SinonStub)
      .withArgs(202)
      .resolves({
        suggestion: {
          feature_id: 202,
          status: 'PENDING',
          suggested_summary: 'New summary for 202',
          suggested_doc_links: [],
          version_token: 1,
          created: new Date(),
          updated: new Date(),
        },
        progress_steps: [
          {
            step: 'READ_SPEC',
            status: 'SUCCESS',
            message: 'Read spec for 202',
            start_timestamp: new Date(),
          },
        ],
      });

    el.featureId = 202;
    await el.updateComplete;
    await el.updateComplete;

    expect(
      (window.csClient.getSummarySuggestion as sinon.SinonStub).calledWith(202)
    ).to.be.true;
    expect(el.suggestion?.feature_id).to.equal(202);
  });

  it('sets error and stops polling after max 404 retries', async () => {
    (window.csClient.getSummarySuggestion as sinon.SinonStub).rejects({
      status: 404,
      message: 'Not found',
    });

    const el = await fixture<ChromedashAiSummaryProgress>(
      html`<chromedash-ai-summary-progress
        .autoPoll=${false}
        .featureId=${101}
      ></chromedash-ai-summary-progress>`
    );

    let failedFired = false;
    el.addEventListener('summary-generation-failed', (e: any) => {
      failedFired = true;
      expect(e.detail.featureId).to.equal(101);
    });

    el.startPolling();
    for (let i = 0; i < 5; i++) {
      await el.fetchStatus();
    }

    expect(el.polling).to.be.false;
    expect(el.error).to.contain('not start or expired');
    expect(failedFired).to.be.true;
  });
});
