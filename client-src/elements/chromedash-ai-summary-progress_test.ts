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
import {ChromeStatusClient} from '../js-src/cs-client.js';
import {
  SummaryProgressStep as ProgressStep,
  SummaryProgressStepStatusEnum,
  SummaryProgressStepStepEnum,
} from 'chromestatus-openapi';

describe('chromedash-ai-summary-progress', () => {
  let sandbox: sinon.SinonSandbox;

  beforeEach(() => {
    sandbox = sinon.createSandbox();
    window.csClient = {
      triggerSummaryGeneration: sandbox.stub().resolves({
        message: 'Task enqueued',
      }),
    } as Partial<ChromeStatusClient> as ChromeStatusClient;
  });

  afterEach(() => {
    sandbox.restore();
  });

  it('renders nothing when empty with no steps, not loading, and no error', async () => {
    const el = await fixture<ChromedashAiSummaryProgress>(
      html`<chromedash-ai-summary-progress></chromedash-ai-summary-progress>`
    );

    expect(el.shadowRoot!.children.length).to.equal(0);
  });

  it('renders progress steps with correct labels, accessibility roles, and icons', async () => {
    const steps: ProgressStep[] = [
      {
        step: SummaryProgressStepStepEnum.READ_SPEC,
        status: SummaryProgressStepStatusEnum.SUCCESS,
        message: 'Found spec link',
        start_timestamp: new Date(),
      },
      {
        step: SummaryProgressStepStepEnum.SEARCH_MDN,
        status: SummaryProgressStepStatusEnum.IN_PROGRESS,
        message: 'Searching web docs',
        start_timestamp: new Date(),
      },
      {
        step: SummaryProgressStepStepEnum.VERIFY_DOC_LINK,
        status: SummaryProgressStepStatusEnum.FAILED,
        message: '404 not found',
        start_timestamp: new Date(),
      },
      {
        step: SummaryProgressStepStepEnum.READ_EXPLAINER,
        status: SummaryProgressStepStatusEnum.RETRYING,
        message: 'Retrying explainer',
        start_timestamp: new Date(),
      },
    ];

    const el = await fixture<ChromedashAiSummaryProgress>(
      html`<chromedash-ai-summary-progress
        .progressSteps=${steps}
      ></chromedash-ai-summary-progress>`
    );

    const stepsList = el.shadowRoot!.querySelector('.steps-list');
    expect(stepsList).to.exist;
    expect(stepsList!.getAttribute('role')).to.equal('list');

    const stepItems = el.shadowRoot!.querySelectorAll('.step-item');
    expect(stepItems.length).to.equal(4);

    expect(stepItems[0].getAttribute('role')).to.equal('listitem');
    expect(stepItems[0].classList.contains('success')).to.be.true;
    expect(stepItems[0].textContent).to.contain('Reading specification');
    expect(stepItems[0].textContent).to.contain('Found spec link');
    expect(
      stepItems[0].querySelector('.visually-hidden')!.textContent
    ).to.contain('Status: Succeeded');
    const successIcon = stepItems[0].querySelector('sl-icon');
    expect(successIcon).to.exist;
    expect(successIcon!.getAttribute('name')).to.equal('check-lg');
    expect(successIcon!.getAttribute('aria-hidden')).to.equal('true');

    expect(stepItems[1].classList.contains('in-progress')).to.be.true;
    expect(stepItems[1].textContent).to.contain('Searching MDN documentation');
    expect(
      stepItems[1].querySelector('.visually-hidden')!.textContent
    ).to.contain('Status: In progress');
    expect(stepItems[1].querySelector('sl-spinner')).to.exist;

    expect(stepItems[2].classList.contains('failed')).to.be.true;
    expect(stepItems[2].textContent).to.contain(
      'Verifying documentation links'
    );
    expect(
      stepItems[2].querySelector('.visually-hidden')!.textContent
    ).to.contain('Status: Failed');
    const failedIcon = stepItems[2].querySelector('sl-icon');
    expect(failedIcon).to.exist;
    expect(failedIcon!.getAttribute('name')).to.equal('x-circle-fill');

    expect(stepItems[3].classList.contains('retrying')).to.be.true;
    expect(
      stepItems[3].querySelector('.visually-hidden')!.textContent
    ).to.contain('Status: Retrying');
    const retryIcon = stepItems[3].querySelector('sl-icon');
    expect(retryIcon).to.exist;
    expect(retryIcon!.getAttribute('name')).to.equal('exclamation-circle-fill');
  });

  it('renders default fallback label and renders no icon for unknown step/status', async () => {
    const steps: ProgressStep[] = [
      {
        step: 'FUTURE_CUSTOM_STEP' as SummaryProgressStepStepEnum,
        status: 'UNKNOWN_STATUS' as SummaryProgressStepStatusEnum,
        start_timestamp: new Date(),
      },
    ];

    const el = await fixture<ChromedashAiSummaryProgress>(
      html`<chromedash-ai-summary-progress
        .progressSteps=${steps}
      ></chromedash-ai-summary-progress>`
    );

    const stepItem = el.shadowRoot!.querySelector('.step-item');
    expect(stepItem).to.exist;
    expect(stepItem!.textContent).to.contain('FUTURE_CUSTOM_STEP');
    expect(stepItem!.querySelector('.visually-hidden')!.textContent).to.contain(
      'Status: UNKNOWN_STATUS'
    );
    expect(stepItem!.querySelector('sl-icon')).to.not.exist;
    expect(stepItem!.querySelector('sl-spinner')).to.not.exist;
  });

  it('truncates step message longer than MAX_STEP_MESSAGE_LENGTH (300 chars)', async () => {
    const longMessage = 'A'.repeat(400);
    const steps: ProgressStep[] = [
      {
        step: SummaryProgressStepStepEnum.READ_SPEC,
        status: SummaryProgressStepStatusEnum.SUCCESS,
        message: longMessage,
        start_timestamp: new Date(),
      },
    ];

    const el = await fixture<ChromedashAiSummaryProgress>(
      html`<chromedash-ai-summary-progress
        .progressSteps=${steps}
      ></chromedash-ai-summary-progress>`
    );

    const stepMessage = el.shadowRoot!.querySelector('.step-message');
    expect(stepMessage).to.exist;
    expect(stepMessage!.textContent).to.contain('A'.repeat(300) + '...');
    expect(stepMessage!.textContent).to.not.contain('A'.repeat(301));
  });

  it('renders header spinner and Running badge in loading-only state when progressSteps is empty', async () => {
    const el = await fixture<ChromedashAiSummaryProgress>(
      html`<chromedash-ai-summary-progress
        .loading=${true}
      ></chromedash-ai-summary-progress>`
    );

    const container = el.shadowRoot!.querySelector('.container');
    expect(container).to.exist;

    const header = el.shadowRoot!.querySelector('.header');
    expect(header).to.exist;
    expect(header!.querySelector('sl-spinner')).to.exist;
    expect(header!.textContent).to.contain('Running');

    const stepsList = el.shadowRoot!.querySelector('.steps-list');
    expect(stepsList).to.not.exist;
  });

  it('does not call triggerSummaryGeneration and warns when featureId is invalid (0)', async () => {
    const warnSpy = sandbox.spy(console, 'warn');
    const el = await fixture<ChromedashAiSummaryProgress>(
      html`<chromedash-ai-summary-progress
        .featureId=${0}
      ></chromedash-ai-summary-progress>`
    );

    await el.handleTrigger();

    expect(warnSpy.calledOnce).to.be.true;
    expect((window.csClient.triggerSummaryGeneration as sinon.SinonStub).called)
      .to.be.false;
  });

  it('does not re-trigger when loading is already true', async () => {
    const el = await fixture<ChromedashAiSummaryProgress>(
      html`<chromedash-ai-summary-progress
        .featureId=${101}
        .loading=${true}
      ></chromedash-ai-summary-progress>`
    );

    await el.handleTrigger();

    expect((window.csClient.triggerSummaryGeneration as sinon.SinonStub).called)
      .to.be.false;
  });

  it('resets loading flag unconditionally even if disconnected during execution', async () => {
    let resolveTrigger: (value?: unknown) => void;
    (window.csClient.triggerSummaryGeneration as sinon.SinonStub).returns(
      new Promise(resolve => {
        resolveTrigger = resolve;
      })
    );

    const el = await fixture<ChromedashAiSummaryProgress>(
      html`<chromedash-ai-summary-progress
        .featureId=${101}
      ></chromedash-ai-summary-progress>`
    );

    const triggerPromise = el.handleTrigger();
    expect(el.loading).to.be.true;

    // Disconnect element while in-flight
    el.remove();
    resolveTrigger!();
    await triggerPromise;

    expect(el.loading).to.be.false;
  });

  it('renders error banner and calls handleTrigger on Retry click', async () => {
    const el = await fixture<ChromedashAiSummaryProgress>(
      html`<chromedash-ai-summary-progress
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
        .featureId=${101}
      ></chromedash-ai-summary-progress>`
    );

    let eventFired = false;
    el.addEventListener('summary-generation-started', ((
      e: CustomEvent<{featureId: number; force: boolean}>
    ) => {
      eventFired = true;
      expect(e.detail.featureId).to.equal(101);
      expect(e.detail.force).to.be.true;
    }) as EventListener);

    await el.handleTrigger(true);
    expect(eventFired).to.be.true;
    expect(
      (
        window.csClient.triggerSummaryGeneration as sinon.SinonStub
      ).calledOnceWith(101, true)
    ).to.be.true;
  });

  it('applies compact styling when compact is true', async () => {
    const steps: ProgressStep[] = [
      {
        step: SummaryProgressStepStepEnum.READ_SPEC,
        status: SummaryProgressStepStatusEnum.SUCCESS,
        message: 'Done',
        start_timestamp: new Date(),
      },
    ];

    const el = await fixture<ChromedashAiSummaryProgress>(
      html`<chromedash-ai-summary-progress
        .compact=${true}
        .progressSteps=${steps}
      ></chromedash-ai-summary-progress>`
    );

    const container = el.shadowRoot!.querySelector('.container');
    expect(container).to.exist;
    expect(container!.classList.contains('compact')).to.be.true;
  });
});
