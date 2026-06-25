import {assert, fixture} from '@open-wc/testing';
import {html} from 'lit';
import sinon from 'sinon';
import {ChromeStatusClient} from '../js-src/cs-client.js';
import {ChromedashAiSummaryProgress} from './chromedash-ai-summary-progress.js';
import './chromedash-ai-summary-progress.js';

describe('chromedash-ai-summary-progress', () => {
  const featureId = 12345;

  const mockProgressSteps = [
    {
      step_id: 'start',
      start_timestamp: '2026-06-01T12:00:00Z',
      end_timestamp: '2026-06-01T12:00:00.200Z',
      message: 'Initializing...',
      status: 'success' as const,
    },
    {
      step_id: 'tool_1',
      start_timestamp: '2026-06-01T12:00:00.200Z',
      end_timestamp: '2026-06-01T12:00:01.700Z',
      message: 'Searching MDN for css nesting...',
      status: 'success' as const,
    },
    {
      step_id: 'llm_generation',
      start_timestamp: '2026-06-01T12:00:01.700Z',
      end_timestamp: null,
      message: 'Executing AI generation loop...',
      status: 'in_progress' as const,
    },
  ];

  beforeEach(() => {
    window.csClient = new ChromeStatusClient('fake_token', 1);
    sinon.stub(window.csClient, 'getSummarySuggestion').resolves({
      status: 'in_progress',
      progress_steps: mockProgressSteps,
    });
  });

  afterEach(() => {
    window.csClient.getSummarySuggestion.restore();
  });

  it('renders skeleton loader initially', async () => {
    // Delay resolution to capture initial pending state
    let resolveSuggestion: (value: unknown) => void = () => {};
    const pendingPromise = new Promise(resolve => {
      resolveSuggestion = resolve;
    });
    window.csClient.getSummarySuggestion.restore();
    sinon.stub(window.csClient, 'getSummarySuggestion').returns(pendingPromise);

    const el = (await fixture(
      html`<chromedash-ai-summary-progress
        .featureId=${featureId}
      ></chromedash-ai-summary-progress>`
    )) as ChromedashAiSummaryProgress;

    // Renders skeleton
    const skeleton = el.shadowRoot!.querySelector('sl-skeleton');
    assert.exists(skeleton);

    // Resolve suggestion
    resolveSuggestion({
      status: 'in_progress',
      progress_steps: mockProgressSteps,
    });
    await new Promise(resolve => setTimeout(resolve, 0));
    await el.updateComplete;

    // Skeleton is gone
    assert.isNull(el.shadowRoot!.querySelector('sl-skeleton'));
  });

  it('renders collapsed progress row on successful load', async () => {
    const el = (await fixture(
      html`<chromedash-ai-summary-progress
        .featureId=${featureId}
      ></chromedash-ai-summary-progress>`
    )) as ChromedashAiSummaryProgress;

    await el.updateComplete;

    // Pulsing logo, badge, and latest step preview are rendered
    const logo = el.shadowRoot!.querySelector('.gemini-pulse-icon');
    assert.exists(logo);

    const tag = el.shadowRoot!.querySelector('sl-tag');
    assert.exists(tag);
    assert.include(tag.textContent, 'Generating');

    const preview = el.shadowRoot!.querySelector('.active-step-preview');
    assert.exists(preview);
    assert.include(preview.textContent, 'Executing AI generation loop...');

    // Chevron trigger is rendered
    const toggleBtn = el.shadowRoot!.querySelector(
      '.details-toggle-btn'
    ) as HTMLElement;
    assert.exists(toggleBtn);
    assert.include(toggleBtn.textContent, 'Show Details ▾');
  });

  it('toggles expanded DevOps console tray on click', async () => {
    const el = (await fixture(
      html`<chromedash-ai-summary-progress
        .featureId=${featureId}
      ></chromedash-ai-summary-progress>`
    )) as ChromedashAiSummaryProgress;

    await el.updateComplete;

    // Console tray is collapsed initially
    let tray = el.shadowRoot!.querySelector('.timeline-console-tray');
    assert.isNull(tray);

    // Click trigger to expand
    const toggleBtn = el.shadowRoot!.querySelector(
      '.details-toggle-btn'
    ) as HTMLElement;
    toggleBtn.click();
    await el.updateComplete;

    // Console tray is visible
    tray = el.shadowRoot!.querySelector('.timeline-console-tray');
    assert.exists(tray);

    // Renders 4 lines (1 pruned marker + 3 steps)
    const lines = el.shadowRoot!.querySelectorAll('.console-line');
    assert.equal(lines.length, 4);

    // Line 0: Pruned marker
    assert.include(
      lines[0].textContent,
      '[Older attempts pruned to save space]'
    );

    // Line 1: success, elapsed time (mock step 0)
    assert.include(lines[1].textContent, 'Initializing...');
    assert.include(lines[1].textContent, '+0.2s');

    // Line 2: success, elapsed time (mock step 1)
    assert.include(lines[2].textContent, 'Searching MDN for css nesting...');
    assert.include(lines[2].textContent, '+1.5s');

    // Line 3: active, showing 'active' status text instead of duration (mock step 2)
    assert.include(lines[3].textContent, 'Executing AI generation loop...');
    assert.include(lines[3].textContent, 'active');

    // Click trigger again to collapse
    toggleBtn.click();
    await el.updateComplete;
    assert.isNull(el.shadowRoot!.querySelector('.timeline-console-tray'));
  });

  it('polls every 3s in background and fires suggestion-finished on completion', async () => {
    let callCount = 0;
    window.csClient.getSummarySuggestion.restore();
    sinon.stub(window.csClient, 'getSummarySuggestion').callsFake(() => {
      callCount++;
      if (callCount === 1) {
        return Promise.resolve({
          status: 'in_progress',
          progress_steps: mockProgressSteps,
        });
      }
      return Promise.resolve({
        status: 'complete',
        suggested_summary: 'Done summary',
        suggested_doc_links: [],
      });
    });

    const clock = sinon.useFakeTimers();

    const el = (await fixture(
      html`<chromedash-ai-summary-progress
        .featureId=${featureId}
      ></chromedash-ai-summary-progress>`
    )) as ChromedashAiSummaryProgress;

    await el.updateComplete;
    assert.equal(callCount, 1);

    // Set up finished event listener
    const finishedPromise = new Promise<CustomEvent>(resolve => {
      el.addEventListener('suggestion-finished', e =>
        resolve(e as CustomEvent)
      );
    });

    // Fast-forward 3 seconds to trigger background poll
    await clock.tickAsync(3000);
    await el.updateComplete;

    assert.equal(callCount, 2);

    // Verify finished event was fired and contains the complete suggestion details
    const event = await finishedPromise;
    assert.equal(event.detail.suggestion.status, 'complete');
    assert.equal(event.detail.suggestion.suggested_summary, 'Done summary');

    clock.restore();
  });

  it('renders pruned history marker when older runs are pruned', async () => {
    // 1. First step is Attempt #2 (should show marker)
    window.csClient.getSummarySuggestion.restore();
    sinon.stub(window.csClient, 'getSummarySuggestion').resolves({
      status: 'in_progress',
      progress_steps: [
        {
          step_id: 'separator_123',
          start_timestamp: '2026-06-01T12:00:00Z',
          end_timestamp: '2026-06-01T12:00:00.200Z',
          message: '--- New Generation Attempt #2 (Model: gemini) ---',
          status: 'success' as const,
        },
      ],
    });

    const el1 = (await fixture(
      html`<chromedash-ai-summary-progress
        .featureId=${featureId}
      ></chromedash-ai-summary-progress>`
    )) as ChromedashAiSummaryProgress;
    await el1.updateComplete;

    // Expand tray
    const toggleBtn1 = el1.shadowRoot!.querySelector(
      '.details-toggle-btn'
    ) as HTMLElement;
    toggleBtn1.click();
    await el1.updateComplete;

    // Verify pruned marker is rendered
    const marker1 = el1.shadowRoot!.querySelector('.pruned-marker-line');
    assert.exists(marker1);
    assert.include(
      marker1.textContent,
      '[Older attempts pruned to save space]'
    );

    // 2. First step is Attempt #1 (should NOT show marker)
    window.csClient.getSummarySuggestion.restore();
    sinon.stub(window.csClient, 'getSummarySuggestion').resolves({
      status: 'in_progress',
      progress_steps: [
        {
          step_id: 'separator_123',
          start_timestamp: '2026-06-01T12:00:00Z',
          end_timestamp: '2026-06-01T12:00:00.200Z',
          message: '--- New Generation Attempt #1 (Model: gemini) ---',
          status: 'success' as const,
        },
      ],
    });

    const el2 = (await fixture(
      html`<chromedash-ai-summary-progress
        .featureId=${featureId}
      ></chromedash-ai-summary-progress>`
    )) as ChromedashAiSummaryProgress;
    await el2.updateComplete;

    const toggleBtn2 = el2.shadowRoot!.querySelector(
      '.details-toggle-btn'
    ) as HTMLElement;
    toggleBtn2.click();
    await el2.updateComplete;

    // Verify pruned marker does NOT exist
    assert.isNull(el2.shadowRoot!.querySelector('.pruned-marker-line'));

    // 3. First step is a tool call (no separator, meaning older separators were pruned)
    window.csClient.getSummarySuggestion.restore();
    sinon.stub(window.csClient, 'getSummarySuggestion').resolves({
      status: 'in_progress',
      progress_steps: [
        {
          step_id: 'tool_123',
          start_timestamp: '2026-06-01T12:00:00Z',
          end_timestamp: '2026-06-01T12:00:00.200Z',
          message: 'Searching MDN...',
          status: 'success' as const,
        },
      ],
    });

    const el3 = (await fixture(
      html`<chromedash-ai-summary-progress
        .featureId=${featureId}
      ></chromedash-ai-summary-progress>`
    )) as ChromedashAiSummaryProgress;
    await el3.updateComplete;

    const toggleBtn3 = el3.shadowRoot!.querySelector(
      '.details-toggle-btn'
    ) as HTMLElement;
    toggleBtn3.click();
    await el3.updateComplete;

    // Verify pruned marker is rendered
    const marker3 = el3.shadowRoot!.querySelector('.pruned-marker-line');
    assert.exists(marker3);
  });
});
