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

import {html, fixture, expect, oneEvent} from '@open-wc/testing';
import sinon from 'sinon';
import './chromedash-ai-summary-progress.js';
import {ChromedashAiSummaryProgress} from './chromedash-ai-summary-progress.js';
import {ChromeStatusClient} from '../js-src/cs-client.js';
import {
  SummaryProgressStep as ProgressStep,
  SummaryProgressStepStatusEnum,
  SummaryProgressStepStepEnum,
  SummarySuggestion,
} from 'chromestatus-openapi';

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
            step: SummaryProgressStepStepEnum.READ_SPEC,
            status: SummaryProgressStepStatusEnum.SUCCESS,
            message: 'Read 120 lines',
            start_timestamp: new Date(),
          },
          {
            step: SummaryProgressStepStepEnum.SEARCH_MDN,
            status: SummaryProgressStepStatusEnum.IN_PROGRESS,
            message: 'Querying MDN',
            start_timestamp: new Date(),
          },
        ] as ProgressStep[],
      }),
      triggerSummaryGeneration: sandbox.stub().resolves({
        message: 'Task enqueued',
      }),
    } as Partial<ChromeStatusClient> as ChromeStatusClient;
  });

  afterEach(() => {
    sandbox.restore();
  });

  it('renders trigger button when empty with no steps, not loading, and no error', async () => {
    const el = await fixture<ChromedashAiSummaryProgress>(
      html`<chromedash-ai-summary-progress
        .autoPoll=${false}
      ></chromedash-ai-summary-progress>`
    );

    const button = el.shadowRoot!.querySelector(
      'sl-button[data-testid="generate-ai-summary-button"]'
    );
    expect(button).to.exist;
  });

  it('renders nothing when hideIdleTrigger is true and empty', async () => {
    const el = await fixture<ChromedashAiSummaryProgress>(
      html`<chromedash-ai-summary-progress
        .autoPoll=${false}
        .hideIdleTrigger=${true}
      ></chromedash-ai-summary-progress>`
    );

    expect(el.shadowRoot!.children.length).to.equal(0);
  });

  it('renders review button when suggestion is pending and not running', async () => {
    const el = await fixture<ChromedashAiSummaryProgress>(
      html`<chromedash-ai-summary-progress
        .autoPoll=${false}
        .suggestion=${
          {
            status: 'PENDING',
            suggested_summary: 'Pending test',
          } as SummarySuggestion
        }
      ></chromedash-ai-summary-progress>`
    );

    const reviewButton = el.shadowRoot!.querySelector(
      'sl-button[data-testid="review-ai-summary-button"]'
    );
    expect(reviewButton).to.exist;
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
        .autoPoll=${false}
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
        .autoPoll=${false}
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
        .autoPoll=${false}
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
        .autoPoll=${false}
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
        .autoPoll=${false}
        .featureId=${0}
      ></chromedash-ai-summary-progress>`
    );

    await el.handleTrigger();

    expect(warnSpy.calledOnce).to.be.true;
    expect((window.csClient.triggerSummaryGeneration as sinon.SinonStub).called)
      .to.be.false;
  });

  it('clears suggestion and progressSteps when handleTrigger is invoked', async () => {
    const el = await fixture<ChromedashAiSummaryProgress>(
      html`<chromedash-ai-summary-progress
        .autoPoll=${false}
        .featureId=${101}
      ></chromedash-ai-summary-progress>`
    );
    el.suggestion = {
      feature_id: 101,
      status: 'PENDING',
      suggested_summary: 'Old summary',
      suggested_doc_links: [],
      version_token: 1,
      created: new Date(),
      updated: new Date(),
    };
    el.progressSteps = [
      {
        step: SummaryProgressStepStepEnum.READ_SPEC,
        status: SummaryProgressStepStatusEnum.SUCCESS,
        start_timestamp: new Date(),
      },
    ];

    const triggerPromise = el.handleTrigger(true);
    expect(el.suggestion).to.be.null;
    expect(el.progressSteps).to.deep.equal([]);
    await triggerPromise;
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

    const startedPromise = oneEvent(el, 'summary-generation-started');
    await el.handleTrigger(true);
    const event = (await startedPromise) as CustomEvent<{
      featureId: number;
      force: boolean;
    }>;

    expect(event.detail.featureId).to.equal(101);
    expect(event.detail.force).to.be.true;
    expect(
      (
        window.csClient.triggerSummaryGeneration as sinon.SinonStub
      ).calledOnceWith(101, true)
    ).to.be.true;
  });

  it('polls status and emits summary-generation-completed when finished', async () => {
    (window.csClient.getSummarySuggestion as sinon.SinonStub).resolves({
      suggestion: {
        feature_id: 101,
        status: 'PENDING',
        suggested_summary: 'Completed AI summary',
        suggested_doc_links: [],
        version_token: 1,
        created: new Date(),
        updated: new Date(),
      },
      progress_steps: [
        {
          step: SummaryProgressStepStepEnum.READ_SPEC,
          status: SummaryProgressStepStatusEnum.SUCCESS,
          message: 'Done',
          start_timestamp: new Date(),
        },
      ],
    });

    let resolveCompleted: (e: CustomEvent) => void;
    const completedPromise = new Promise<CustomEvent>(resolve => {
      resolveCompleted = resolve;
    });

    const el = await fixture<ChromedashAiSummaryProgress>(
      html`<chromedash-ai-summary-progress
        .autoPoll=${true}
        .featureId=${101}
        @summary-generation-completed=${(e: CustomEvent) => resolveCompleted(e)}
      ></chromedash-ai-summary-progress>`
    );

    const event = (await completedPromise) as CustomEvent<{
      featureId: number;
      suggestion: SummarySuggestion | null;
    }>;

    expect(event.detail.featureId).to.equal(101);
    expect(event.detail.suggestion?.suggested_summary).to.equal(
      'Completed AI summary'
    );
    expect(el.suggestion?.suggested_summary).to.equal('Completed AI summary');
  });

  it('emits summary-generation-failed event when a step fails', async () => {
    (window.csClient.getSummarySuggestion as sinon.SinonStub).resolves({
      suggestion: null,
      progress_steps: [
        {
          step: SummaryProgressStepStepEnum.READ_SPEC,
          status: SummaryProgressStepStatusEnum.FAILED,
          message: 'Error reading spec',
          start_timestamp: new Date(),
        },
      ],
    });

    let resolveFailed: (e: CustomEvent) => void;
    const failedPromise = new Promise<CustomEvent>(resolve => {
      resolveFailed = resolve;
    });

    const el = await fixture<ChromedashAiSummaryProgress>(
      html`<chromedash-ai-summary-progress
        .autoPoll=${true}
        .featureId=${101}
        @summary-generation-failed=${(e: CustomEvent) => resolveFailed(e)}
      ></chromedash-ai-summary-progress>`
    );

    const event = (await failedPromise) as CustomEvent<{
      featureId: number;
    }>;

    expect(event.detail.featureId).to.equal(101);
  });

  it('stops in-flight monitor and does not emit failure event when featureId changes rapidly', async () => {
    let resolveDelay: (value: unknown) => void;
    (window.csClient.getSummarySuggestion as sinon.SinonStub)
      .withArgs(101)
      .returns(
        new Promise(resolve => {
          resolveDelay = resolve;
        })
      );

    let failedEventFired = false;
    const el = await fixture<ChromedashAiSummaryProgress>(
      html`<chromedash-ai-summary-progress
        .autoPoll=${true}
        .featureId=${101}
        @summary-generation-failed=${() => {
          failedEventFired = true;
        }}
      ></chromedash-ai-summary-progress>`
    );

    // Rapidly switch featureId while 101 is pending
    el.featureId = 202;
    await el.updateComplete;

    // Resolve the old 101 promise
    resolveDelay!({
      suggestion: null,
      progress_steps: [],
    });

    expect(failedEventFired).to.be.false;
  });

  it('stops in-flight monitor and emits no events when disconnected', async () => {
    let failedEventFired = false;
    (window.csClient.getSummarySuggestion as sinon.SinonStub)
      .withArgs(101)
      .returns(new Promise(() => {}));

    const el = await fixture<ChromedashAiSummaryProgress>(
      html`<chromedash-ai-summary-progress
        .autoPoll=${true}
        .featureId=${101}
        @summary-generation-failed=${() => {
          failedEventFired = true;
        }}
      ></chromedash-ai-summary-progress>`
    );

    el.remove();
    expect(failedEventFired).to.be.false;
  });

  it('truncates error messages exceeding 200 characters with ellipsis at exact boundary', async () => {
    const msg200 = 'E'.repeat(200);
    const msg201 = 'F'.repeat(201);

    (window.csClient.getSummarySuggestion as sinon.SinonStub)
      .withArgs(101)
      .rejects(new Error(msg200));

    (window.csClient.getSummarySuggestion as sinon.SinonStub)
      .withArgs(202)
      .rejects(new Error(msg201));

    let resolveFailed1: (e: CustomEvent) => void;
    const failedPromise1 = new Promise<CustomEvent>(resolve => {
      resolveFailed1 = resolve;
    });

    const el1 = await fixture<ChromedashAiSummaryProgress>(
      html`<chromedash-ai-summary-progress
        .autoPoll=${true}
        .featureId=${101}
        @summary-generation-failed=${(e: CustomEvent) => resolveFailed1(e)}
      ></chromedash-ai-summary-progress>`
    );

    await failedPromise1;
    await el1.updateComplete;

    expect(el1.error).to.equal(msg200);
    expect(el1.error!.endsWith('...')).to.be.false;

    let resolveFailed2: (e: CustomEvent) => void;
    const failedPromise2 = new Promise<CustomEvent>(resolve => {
      resolveFailed2 = resolve;
    });

    const el2 = await fixture<ChromedashAiSummaryProgress>(
      html`<chromedash-ai-summary-progress
        .autoPoll=${true}
        .featureId=${202}
        @summary-generation-failed=${(e: CustomEvent) => resolveFailed2(e)}
      ></chromedash-ai-summary-progress>`
    );

    await failedPromise2;
    await el2.updateComplete;

    expect(el2.error).to.equal('F'.repeat(200) + '...');
  });

  it('falls back to default fetch error message when error message is empty or whitespace', async () => {
    (window.csClient.getSummarySuggestion as sinon.SinonStub)
      .withArgs(101)
      .rejects(new Error('   '));

    let resolveFailed: (e: CustomEvent) => void;
    const failedPromise = new Promise<CustomEvent>(resolve => {
      resolveFailed = resolve;
    });

    const el = await fixture<ChromedashAiSummaryProgress>(
      html`<chromedash-ai-summary-progress
        .autoPoll=${true}
        .featureId=${101}
        @summary-generation-failed=${(e: CustomEvent) => resolveFailed(e)}
      ></chromedash-ai-summary-progress>`
    );

    await failedPromise;
    await el.updateComplete;

    expect(el.error).to.equal('Failed to fetch summary generation status');
  });

  it('renders fixed-geometry button and avoids expanding container in compact mode', async () => {
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
        .autoPoll=${false}
        .compact=${true}
        .progressSteps=${steps}
      ></chromedash-ai-summary-progress>`
    );

    const container = el.shadowRoot!.querySelector('.container');
    expect(container).to.not.exist;

    const button = el.shadowRoot!.querySelector('sl-button');
    expect(button).to.exist;
    expect(button!.getAttribute('size')).to.equal('small');
  });

  it('dispatches summary-dialog-requested when clicked during running in compact mode', async () => {
    const el = await fixture<ChromedashAiSummaryProgress>(
      html`<chromedash-ai-summary-progress
        .autoPoll=${false}
        .compact=${true}
        .loading=${true}
      ></chromedash-ai-summary-progress>`
    );

    const dialogRequestedPromise = oneEvent(el, 'summary-dialog-requested');
    const generatingButton = el.shadowRoot!.querySelector(
      'sl-button[data-testid="ai-summary-generating-button"]'
    );
    expect(generatingButton).to.exist;
    (generatingButton as HTMLElement).click();

    const event = await dialogRequestedPromise;
    expect(event).to.exist;
  });

  it('resets state and refetches when featureId changes dynamically', async () => {
    (window.csClient.getSummarySuggestion as sinon.SinonStub)
      .withArgs(101)
      .resolves({
        suggestion: {
          feature_id: 101,
          status: 'PENDING',
          suggested_summary: 'AI summary 101',
          suggested_doc_links: [],
          version_token: 1,
          created: new Date(),
          updated: new Date(),
        },
        progress_steps: [
          {
            step: SummaryProgressStepStepEnum.READ_SPEC,
            status: SummaryProgressStepStatusEnum.SUCCESS,
            message: 'Done 101',
            start_timestamp: new Date(),
          },
        ],
      });

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
            step: SummaryProgressStepStepEnum.READ_SPEC,
            status: SummaryProgressStepStatusEnum.SUCCESS,
            message: 'Read spec for 202',
            start_timestamp: new Date(),
          },
        ],
      });

    let resolveFirst: (e: CustomEvent) => void;
    const firstPromise = new Promise<CustomEvent>(resolve => {
      resolveFirst = resolve;
    });
    let resolveSecond: (e: CustomEvent) => void;
    const secondPromise = new Promise<CustomEvent>(resolve => {
      resolveSecond = resolve;
    });

    let completedCount = 0;
    const el = await fixture<ChromedashAiSummaryProgress>(
      html`<chromedash-ai-summary-progress
        .autoPoll=${true}
        .featureId=${101}
        @summary-generation-completed=${(e: CustomEvent) => {
          completedCount++;
          if (completedCount === 1) resolveFirst(e);
          else resolveSecond(e);
        }}
      ></chromedash-ai-summary-progress>`
    );

    await firstPromise;
    expect(el.suggestion?.feature_id).to.equal(101);

    el.featureId = 202;
    await secondPromise;

    expect(
      (window.csClient.getSummarySuggestion as sinon.SinonStub).calledWith(202)
    ).to.be.true;
    expect(el.suggestion?.feature_id).to.equal(202);
  });

  it('triggers polling automatically when autoPoll is dynamically toggled to true', async () => {
    (window.csClient.getSummarySuggestion as sinon.SinonStub)
      .withArgs(303)
      .resolves({
        suggestion: {
          feature_id: 303,
          status: 'PENDING',
          suggested_summary: 'AI summary 303',
          suggested_doc_links: [],
          version_token: 1,
          created: new Date(),
          updated: new Date(),
        },
        progress_steps: [
          {
            step: SummaryProgressStepStepEnum.READ_SPEC,
            status: SummaryProgressStepStatusEnum.SUCCESS,
            message: 'Done 303',
            start_timestamp: new Date(),
          },
        ],
      });

    let resolveCompleted: (e: CustomEvent) => void;
    const completedPromise = new Promise<CustomEvent>(resolve => {
      resolveCompleted = resolve;
    });

    const el = await fixture<ChromedashAiSummaryProgress>(
      html`<chromedash-ai-summary-progress
        .autoPoll=${false}
        .featureId=${303}
        @summary-generation-completed=${(e: CustomEvent) => {
          resolveCompleted(e);
        }}
      ></chromedash-ai-summary-progress>`
    );

    // Initial state: autoPoll is false, so getSummarySuggestion(303) should not have been called
    expect(
      (window.csClient.getSummarySuggestion as sinon.SinonStub).calledWith(303)
    ).to.be.false;

    // Dynamically toggle autoPoll to true
    el.autoPoll = true;
    await completedPromise;

    expect(
      (window.csClient.getSummarySuggestion as sinon.SinonStub).calledWith(303)
    ).to.be.true;
    expect(el.suggestion?.feature_id).to.equal(303);
  });

  describe('retry cooldown and error rate limiting', () => {
    let clock: sinon.SinonFakeTimers;

    beforeEach(() => {
      clock = sinon.useFakeTimers();
    });

    afterEach(() => {
      clock.restore();
    });

    it('sets 30s cooldown when error mentions 429, quota, or rate limit', async () => {
      (window.csClient.triggerSummaryGeneration as sinon.SinonStub)
        .withArgs(401, false)
        .rejects(new Error('HTTP 429: ResourceExhausted Quota Exceeded'));

      const el = await fixture<ChromedashAiSummaryProgress>(
        html`<chromedash-ai-summary-progress
          .autoPoll=${false}
          .featureId=${401}
        ></chromedash-ai-summary-progress>`
      );

      await el.handleTrigger(false);
      expect(el.retryCooldownSeconds).to.equal(30);
    });

    it('sets 5s cooldown for general network or server errors', async () => {
      (window.csClient.triggerSummaryGeneration as sinon.SinonStub)
        .withArgs(402, false)
        .rejects(new Error('Internal Server Error 500'));

      const el = await fixture<ChromedashAiSummaryProgress>(
        html`<chromedash-ai-summary-progress
          .autoPoll=${false}
          .featureId=${402}
        ></chromedash-ai-summary-progress>`
      );

      await el.handleTrigger(false);
      expect(el.retryCooldownSeconds).to.equal(5);
    });

    it('renders disabled cooldown button in compact mode and enables retry button when countdown hits 0', async () => {
      const el = await fixture<ChromedashAiSummaryProgress>(
        html`<chromedash-ai-summary-progress
          .autoPoll=${false}
          .compact=${true}
          .featureId=${403}
        ></chromedash-ai-summary-progress>`
      );

      el.error = 'Rate limit reached';
      el._startCooldown(3);
      await el.updateComplete;

      let cooldownBtn = el.shadowRoot!.querySelector(
        'sl-button[data-testid="ai-summary-cooldown-button"]'
      );
      expect(cooldownBtn).to.exist;
      expect(cooldownBtn!.hasAttribute('disabled')).to.be.true;
      expect(cooldownBtn!.textContent).to.contain('Retry in 3s');

      // Advance clock by 1 second
      clock.tick(1000);
      await el.updateComplete;
      expect(el.retryCooldownSeconds).to.equal(2);
      cooldownBtn = el.shadowRoot!.querySelector(
        'sl-button[data-testid="ai-summary-cooldown-button"]'
      );
      expect(cooldownBtn!.textContent).to.contain('Retry in 2s');

      // Advance clock by 2 more seconds -> cooldown expires
      clock.tick(2000);
      await el.updateComplete;
      expect(el.retryCooldownSeconds).to.equal(0);

      const retryBtn = el.shadowRoot!.querySelector(
        'sl-button[data-testid="ai-summary-retry-button"]'
      );
      expect(retryBtn).to.exist;
      expect(retryBtn!.textContent).to.contain('Failed · Retry');
    });

    it('disables retry button with countdown in full error banner during cooldown', async () => {
      const el = await fixture<ChromedashAiSummaryProgress>(
        html`<chromedash-ai-summary-progress
          .autoPoll=${false}
          .compact=${false}
          .featureId=${404}
        ></chromedash-ai-summary-progress>`
      );

      el.error = 'Temporary service failure';
      el._startCooldown(4);
      await el.updateComplete;

      const bannerRetryBtn = el.shadowRoot!.querySelector(
        'sl-button[data-testid="ai-summary-banner-retry-button"]'
      );
      expect(bannerRetryBtn).to.exist;
      expect(bannerRetryBtn!.hasAttribute('disabled')).to.be.true;
      expect(bannerRetryBtn!.textContent).to.contain('Retry in 4s');

      clock.tick(4000);
      await el.updateComplete;
      expect(bannerRetryBtn!.hasAttribute('disabled')).to.be.false;
      expect(bannerRetryBtn!.textContent).to.contain('Retry');
    });

    it('prevents handleTrigger execution while cooldown is active', async () => {
      const el = await fixture<ChromedashAiSummaryProgress>(
        html`<chromedash-ai-summary-progress
          .autoPoll=${false}
          .featureId=${405}
        ></chromedash-ai-summary-progress>`
      );

      el._startCooldown(15);
      await el.handleTrigger(true);

      expect(
        (
          window.csClient.triggerSummaryGeneration as sinon.SinonStub
        ).calledWith(405)
      ).to.be.false;
    });

    it('clears cooldown timer and interval on disconnectedCallback', async () => {
      const el = await fixture<ChromedashAiSummaryProgress>(
        html`<chromedash-ai-summary-progress
          .autoPoll=${false}
          .featureId=${406}
        ></chromedash-ai-summary-progress>`
      );

      el._startCooldown(10);
      expect(el.retryCooldownSeconds).to.equal(10);

      el.disconnectedCallback();
      clock.tick(5000);

      // Interval should have been cleared, so timer doesn't tick after disconnect
      expect(el.retryCooldownSeconds).to.equal(10);
    });
  });

  describe('stale step handling and null summary recovery', () => {
    it('returns isTaskRunning = false when latest step is FAILED despite older IN_PROGRESS steps', async () => {
      const el = await fixture<ChromedashAiSummaryProgress>(
        html`<chromedash-ai-summary-progress
          .autoPoll=${false}
          .compact=${true}
          .featureId=${501}
        ></chromedash-ai-summary-progress>`
      );

      el.progressSteps = [
        {
          step: SummaryProgressStepStepEnum.UNKNOWN,
          status: SummaryProgressStepStatusEnum.FAILED,
          message: 'JSON Parsing Error: Failed to parse LLM structured output',
          start_timestamp: new Date(),
        },
        {
          step: SummaryProgressStepStepEnum.UNKNOWN,
          status: SummaryProgressStepStatusEnum.IN_PROGRESS,
          message: 'Invoking gemini-3.1-pro-preview with ADK Runner',
          start_timestamp: new Date(Date.now() - 3600000),
        },
      ];
      await el.updateComplete;

      expect(el.isTaskRunning).to.be.false;
      expect(el.error).to.contain('JSON Parsing Error');

      const retryBtn = el.shadowRoot!.querySelector(
        'sl-button[data-testid="ai-summary-retry-button"]'
      );
      expect(retryBtn).to.exist;
      expect(retryBtn!.textContent).to.contain('Failed · Retry');
    });

    it('expires IN_PROGRESS steps older than 5 minutes as stale', async () => {
      const el = await fixture<ChromedashAiSummaryProgress>(
        html`<chromedash-ai-summary-progress
          .autoPoll=${false}
          .compact=${true}
          .featureId=${502}
        ></chromedash-ai-summary-progress>`
      );

      // Step started 10 minutes ago
      el.progressSteps = [
        {
          step: SummaryProgressStepStepEnum.UNKNOWN,
          status: SummaryProgressStepStatusEnum.IN_PROGRESS,
          message: 'Invoking gemini',
          start_timestamp: new Date(Date.now() - 10 * 60 * 1000),
        },
      ];
      await el.updateComplete;

      expect(el.isTaskRunning).to.be.false;
    });

    it('does not render Review button when suggestion.suggested_summary is null', async () => {
      const el = await fixture<ChromedashAiSummaryProgress>(
        html`<chromedash-ai-summary-progress
          .autoPoll=${false}
          .compact=${true}
          .featureId=${503}
          .suggestion=${{
            feature_id: 503,
            suggested_summary: null as unknown as string,
            status: 'PENDING',
            version_token: 1,
          }}
        ></chromedash-ai-summary-progress>`
      );

      const reviewBtn = el.shadowRoot!.querySelector(
        'sl-button[data-testid="review-ai-summary-button"]'
      );
      expect(reviewBtn).to.not.exist;

      const generateBtn = el.shadowRoot!.querySelector(
        'sl-button[data-testid="generate-ai-summary-button"]'
      );
      expect(generateBtn).to.exist;
    });

    it('tolerates initial empty steps while loading=true within grace period', async () => {
      const el = await fixture<ChromedashAiSummaryProgress>(
        html`<chromedash-ai-summary-progress
          .autoPoll=${false}
          .compact=${true}
          .featureId=${504}
        ></chromedash-ai-summary-progress>`
      );

      el.loading = true;
      // First poll with empty steps returns true (still active)
      expect(el['_isStepsActive']([])).to.be.true;
      // Subsequent poll with empty steps still returns true during grace period
      expect(el['_isStepsActive']([])).to.be.true;
    });

    it('emits failure event and sets error if task finishes without suggested_summary', async () => {
      let failedEventFired = false;
      const el = await fixture<ChromedashAiSummaryProgress>(
        html`<chromedash-ai-summary-progress
          .autoPoll=${true}
          .compact=${true}
          .featureId=${505}
          @summary-generation-failed=${() => {
            failedEventFired = true;
          }}
        ></chromedash-ai-summary-progress>`
      );

      (window.csClient.getSummarySuggestion as sinon.SinonStub)
        .withArgs(505)
        .resolves({
          suggestion: {
            feature_id: 505,
            suggested_summary: null as unknown as string,
            status: 'PENDING',
            version_token: 1,
          },
          progress_steps: [
            {
              step: SummaryProgressStepStepEnum.UNKNOWN,
              status: SummaryProgressStepStatusEnum.SUCCESS,
              message: 'Finished without summary',
              start_timestamp: new Date(),
            },
          ],
        });

      await el._statusTask.run();
      expect(failedEventFired).to.be.true;
      expect(el.error).to.contain(
        'did not produce any candidate summary or documentation links'
      );
    });

    it('successfully completes when suggestion has suggested_doc_links even without suggested_summary', async () => {
      let completedEventFired = false;
      const el = await fixture<ChromedashAiSummaryProgress>(
        html`<chromedash-ai-summary-progress
          .autoPoll=${true}
          .compact=${true}
          .featureId=${506}
          @summary-generation-completed=${() => {
            completedEventFired = true;
          }}
        ></chromedash-ai-summary-progress>`
      );

      (window.csClient.getSummarySuggestion as sinon.SinonStub)
        .withArgs(506)
        .resolves({
          suggestion: {
            feature_id: 506,
            suggested_summary: null as unknown as string,
            suggested_doc_links: [
              'https://developer.mozilla.org/en-US/docs/Web/CSS/masonry',
            ],
            status: 'PENDING',
            version_token: 1,
          },
          progress_steps: [
            {
              step: SummaryProgressStepStepEnum.UNKNOWN,
              status: SummaryProgressStepStatusEnum.SUCCESS,
              message: 'Finished with doc links',
              start_timestamp: new Date(),
            },
          ],
        });

      await el._statusTask.run();
      expect(completedEventFired).to.be.true;
      expect(el.error).to.be.null;
    });

    it('marks task as not running and renders retry button when steps contains FAILED as latest step even with older IN_PROGRESS steps', async () => {
      const featureId = 5980625432215552;
      const recentTimestamp = new Date();
      const olderTimestamp = new Date(recentTimestamp.getTime() - 1000);

      const el = await fixture<ChromedashAiSummaryProgress>(
        html`<chromedash-ai-summary-progress
          .autoPoll=${false}
          .compact=${true}
          .featureId=${featureId}
        ></chromedash-ai-summary-progress>`
      );

      el.progressSteps = [
        {
          step: SummaryProgressStepStepEnum.UNKNOWN,
          status: SummaryProgressStepStatusEnum.FAILED,
          message: 'Generation Error: Model returned an empty response.',
          start_timestamp: recentTimestamp,
          end_timestamp: recentTimestamp,
        },
        {
          step: SummaryProgressStepStepEnum.UNKNOWN,
          status: SummaryProgressStepStatusEnum.FAILED,
          message: 'Generation Error: Model returned an empty response.',
          start_timestamp: olderTimestamp,
          end_timestamp: olderTimestamp,
        },
        {
          step: SummaryProgressStepStepEnum.UNKNOWN,
          status: SummaryProgressStepStatusEnum.IN_PROGRESS,
          message: 'Invoking gemini-3.1-pro-preview with ADK Runner',
          start_timestamp: olderTimestamp,
          end_timestamp: olderTimestamp,
        },
        {
          step: SummaryProgressStepStepEnum.UNKNOWN,
          status: SummaryProgressStepStatusEnum.SUCCESS,
          message: 'Rendered prompt template for feature',
          start_timestamp: olderTimestamp,
          end_timestamp: olderTimestamp,
        },
      ];

      await el.updateComplete;

      expect(el.isTaskRunning).to.be.false;
      expect(el.error).to.be.a('string').and.not.empty;
      const retryBtn = el.shadowRoot!.querySelector(
        'sl-button[data-testid="ai-summary-retry-button"]'
      );
      expect(retryBtn).to.exist;
      expect(retryBtn!.textContent).to.contain('Failed · Retry');
    });
  });
});
