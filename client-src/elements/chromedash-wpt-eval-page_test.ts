import {html, fixture, expect, nextFrame, oneEvent} from '@open-wc/testing';
import sinon from 'sinon';
import './chromedash-wpt-eval-page.js';
import {ChromedashWPTEvalPage} from './chromedash-wpt-eval-page.js';
import {FeatureNotFoundError} from '../js-src/cs-client.js';
import {AITestEvaluationStatus} from './form-field-enums.js';

describe('chromedash-wpt-eval-page', () => {
  let csClientStub: {
    getFeature: sinon.SinonStub;
    generateWPTCoverageEvaluation: sinon.SinonStub;
  };

  // Sample feature data for testing
  const mockFeatureV1 = {
    id: 12345,
    name: 'Test Feature',
    summary: 'A summary of the feature',
    spec_link: 'https://spec.example.com',
    wpt_descr: 'Tests are here: https://wpt.fyi/results/feature/test.html',
    ai_test_eval_report: '# Report Title\n\nReport content goes here.',
    ai_test_eval_run_status: null,
  };

  beforeEach(() => {
    // Mock the global csClient before each test
    csClientStub = {
      getFeature: sinon.stub(),
      generateWPTCoverageEvaluation: sinon.stub(),
    };
    (window as any).csClient = csClientStub;
  });

  afterEach(() => {
    sinon.restore();
  });

  it('renders the basic page structure', async () => {
    csClientStub.getFeature.resolves(mockFeatureV1);
    const el = await fixture<ChromedashWPTEvalPage>(
      html`<chromedash-wpt-eval-page></chromedash-wpt-eval-page>`
    );

    expect(el.shadowRoot!.querySelector('h1')).to.exist;
    expect(el.shadowRoot!.textContent).to.contain(
      'AI-powered WPT coverage evaluation'
    );
    expect(el.shadowRoot!.querySelector('.experimental-tag')).to.exist;
    expect(el.shadowRoot!.querySelector('sl-alert')).to.exist;
    expect(el.shadowRoot!.querySelector('.description')).to.exist;
  });

  it('shows skeletons while loading data', async () => {
    // Return a promise that doesn't resolve immediately to test loading state
    csClientStub.getFeature.returns(new Promise(() => {}));
    const el = await fixture<ChromedashWPTEvalPage>(
      html`<chromedash-wpt-eval-page
        .featureId=${123}
      ></chromedash-wpt-eval-page>`
    );

    expect(el.loading).to.be.true;
    // Look for sl-skeleton elements
    expect(
      el.shadowRoot!.querySelectorAll('sl-skeleton').length
    ).to.be.greaterThan(0);
    // Ensure main content hasn't rendered yet
    expect(el.shadowRoot!.querySelector('.report-section')).to.not.exist;
  });

  it('fetches data and renders full report on success', async () => {
    csClientStub.getFeature.withArgs(123).resolves(mockFeatureV1);
    const el = await fixture<ChromedashWPTEvalPage>(
      html`<chromedash-wpt-eval-page
        .featureId=${123}
      ></chromedash-wpt-eval-page>`
    );

    await nextFrame();
    await el.updateComplete;

    expect(csClientStub.getFeature).to.have.been.calledWith(123);
    expect(el.loading).to.be.false;
    expect(el.feature).to.deep.equal(mockFeatureV1);

    // Check Report Rendering
    const reportSection = el.shadowRoot!.querySelector('.report-section');
    expect(reportSection).to.exist;
    expect(reportSection!.querySelector('h1')!.textContent).to.equal(
      'Report Title'
    );
  });

  describe('Prerequisites Checklist', () => {
    it('shows all checks as success when all data is present', async () => {
      csClientStub.getFeature.resolves({
        ...mockFeatureV1,
        spec_link: 'https://valid.spec',
        wpt_descr: 'https://wpt.fyi/results/a',
      });
      const el = await fixture<ChromedashWPTEvalPage>(
        html`<chromedash-wpt-eval-page
          .featureId=${1}
        ></chromedash-wpt-eval-page>`
      );
      await el.updateComplete;

      const items = el.shadowRoot!.querySelectorAll('.requirement-item');
      expect(items.length).to.equal(3);
      items.forEach(item => {
        expect(item.querySelector('sl-icon')!.classList.contains('success')).to
          .be.true;
      });
    });

    it('shows checks as danger when data is missing', async () => {
      csClientStub.getFeature.resolves({
        ...mockFeatureV1,
        spec_link: '',
        wpt_descr: '',
      });
      const el = await fixture<ChromedashWPTEvalPage>(
        html`<chromedash-wpt-eval-page
          .featureId=${2}
        ></chromedash-wpt-eval-page>`
      );
      await el.updateComplete;

      const items = el.shadowRoot!.querySelectorAll('.requirement-item');
      // Check for danger icons
      items.forEach(item => {
        expect(item.querySelector('sl-icon')!.classList.contains('danger')).to
          .be.true;
      });
    });
  });

  describe('Action Section & Generation Flow', () => {
    it('disables generate button if prerequisites are not met', async () => {
      csClientStub.getFeature.resolves({
        ...mockFeatureV1,
        spec_link: '', // Missing spec
      });
      const el = await fixture<ChromedashWPTEvalPage>(
        html`<chromedash-wpt-eval-page
          .featureId=${1}
        ></chromedash-wpt-eval-page>`
      );
      await el.updateComplete;

      const button = el.shadowRoot!.querySelector('.generate-button');
      expect(button).to.exist;
      expect(button).to.have.attribute('disabled');
    });

    it('enables generate button if prerequisites are met', async () => {
      // mockFeatureV1 has all prerequisites met
      csClientStub.getFeature.resolves(mockFeatureV1);
      const el = await fixture<ChromedashWPTEvalPage>(
        html`<chromedash-wpt-eval-page
          .featureId=${1}
        ></chromedash-wpt-eval-page>`
      );
      await el.updateComplete;

      const button = el.shadowRoot!.querySelector('.generate-button');
      expect(button).to.exist;
      expect(button).to.not.have.attribute('disabled');
    });

    it('starts evaluation, enters IN_PROGRESS state, and starts polling on click', async () => {
      csClientStub.getFeature.resolves(mockFeatureV1);
      csClientStub.generateWPTCoverageEvaluation.resolves({});
      const setIntervalSpy = sinon.spy(window, 'setInterval');

      const el = await fixture<ChromedashWPTEvalPage>(
        html`<chromedash-wpt-eval-page
          .featureId=${99}
        ></chromedash-wpt-eval-page>`
      );
      await el.updateComplete;

      const button = el.shadowRoot!.querySelector(
        '.generate-button'
      ) as HTMLElement;
      button.click();
      await el.updateComplete;

      // API called
      expect(
        csClientStub.generateWPTCoverageEvaluation
      ).to.have.been.calledWith(99);

      // UI entered IN_PROGRESS state immediately (optimistic update)
      expect(el.feature?.ai_test_eval_run_status).to.equal(
        AITestEvaluationStatus.IN_PROGRESS
      );
      expect(el.shadowRoot!.querySelector('.status-in-progress')).to.exist;
      expect(el.shadowRoot!.querySelector('sl-spinner')).to.exist;

      // Polling started
      expect(setIntervalSpy).to.have.been.called;
    });

    it('renders IN_PROGRESS state when loaded from server', async () => {
      csClientStub.getFeature.resolves({
        ...mockFeatureV1,
        ai_test_eval_run_status: AITestEvaluationStatus.IN_PROGRESS,
      });
      const setIntervalSpy = sinon.spy(window, 'setInterval');

      const el = await fixture<ChromedashWPTEvalPage>(
        html`<chromedash-wpt-eval-page
          .featureId=${1}
        ></chromedash-wpt-eval-page>`
      );
      await el.updateComplete;

      expect(el.shadowRoot!.querySelector('.status-in-progress')).to.exist;
      // Should automatically start polling if loaded in progress
      expect(setIntervalSpy).to.have.been.called;
    });

    it('stops polling and shows success message when status becomes COMPLETE during session', async () => {
      // 1. Start in progress
      csClientStub.getFeature.onFirstCall().resolves({
        ...mockFeatureV1,
        ai_test_eval_run_status: AITestEvaluationStatus.IN_PROGRESS,
      });
      // 2. Subsequent call completes it
      csClientStub.getFeature.onSecondCall().resolves({
        ...mockFeatureV1,
        ai_test_eval_run_status: AITestEvaluationStatus.COMPLETE,
      });

      const clearIntervalSpy = sinon.spy(window, 'clearInterval');

      const el = await fixture<ChromedashWPTEvalPage>(
        html`<chromedash-wpt-eval-page
          .featureId=${1}
        ></chromedash-wpt-eval-page>`
      );
      await el.updateComplete;

      // Verify initially in progress
      expect(el.feature?.ai_test_eval_run_status).to.equal(
        AITestEvaluationStatus.IN_PROGRESS
      );

      // Manually trigger the next fetch (simulating the poll interval hitting)
      await el.fetchData();
      await el.updateComplete;

      // Verify it is now complete
      expect(el.feature?.ai_test_eval_run_status).to.equal(
        AITestEvaluationStatus.COMPLETE
      );
      expect(el.completedInThisSession).to.be.true;

      // Check UI for success message
      const successMsg = el.shadowRoot!.querySelector('.status-complete');
      expect(successMsg).to.exist;
      expect(successMsg!.textContent).to.contain('Evaluation complete!');

      // Verify polling stopped
      expect(clearIntervalSpy).to.have.been.called;
    });

    it('shows error alert if previous run FAILED', async () => {
      csClientStub.getFeature.resolves({
        ...mockFeatureV1,
        ai_test_eval_run_status: AITestEvaluationStatus.FAILED,
      });

      const el = await fixture<ChromedashWPTEvalPage>(
        html`<chromedash-wpt-eval-page
          .featureId=${1}
        ></chromedash-wpt-eval-page>`
      );
      await el.updateComplete;

      const alert = el.shadowRoot!.querySelector('sl-alert[variant="danger"]');
      expect(alert).to.exist;
      expect(alert!.textContent).to.contain('previous evaluation run failed');

      // Button should still be visible to try again
      expect(el.shadowRoot!.querySelector('.generate-button')).to.exist;
    });
  });

  describe('Error Handling', () => {
    it('handles FeatureNotFoundError by stopping loading', async () => {
      csClientStub.getFeature.rejects(new FeatureNotFoundError(123));
      const el = await fixture<ChromedashWPTEvalPage>(
        html`<chromedash-wpt-eval-page
          .featureId=${999}
        ></chromedash-wpt-eval-page>`
      );
      await el.updateComplete;

      expect(el.loading).to.be.false;
      expect(el.feature).to.be.null;
      expect(el.shadowRoot!.querySelector('.requirements-list')).to.not.exist;
    });

    it('handles generic errors by stopping loading (updated behavior)', async () => {
      csClientStub.getFeature.rejects(new Error('Network Boom'));
      const el = await fixture<ChromedashWPTEvalPage>(
        html`<chromedash-wpt-eval-page
          .featureId=${500}
        ></chromedash-wpt-eval-page>`
      );
      await el.updateComplete;

      // New behavior: finally block ensures loading is false even on generic error
      expect(el.loading).to.be.false;
      // Should NOT show skeletons anymore
      expect(el.shadowRoot!.querySelector('sl-skeleton')).to.not.exist;
    });
  });

  // NEW: Cooldown Logic Tests
  describe('Cooldown Logic', () => {
    it('disables button and shows cooldown message if last run was COMPLETE < 30 mins ago', async () => {
      const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000).toISOString();

      csClientStub.getFeature.resolves({
        ...mockFeatureV1,
        ai_test_eval_run_status: AITestEvaluationStatus.COMPLETE,
        ai_test_eval_status_timestamp: fiveMinutesAgo,
      });

      const el = await fixture<ChromedashWPTEvalPage>(
        html`<chromedash-wpt-eval-page
          .featureId=${1}
        ></chromedash-wpt-eval-page>`
      );
      await el.updateComplete;

      const button = el.shadowRoot!.querySelector('.generate-button');
      const message = el.shadowRoot!.querySelector('.cooldown-message');

      expect(button).to.exist;
      expect(button).to.have.attribute('disabled');
      expect(message).to.exist;
      expect(message!.textContent).to.contain('Available in');
    });

    it('enables button if last run was COMPLETE > 30 mins ago', async () => {
      const thirtyFiveMinutesAgo = new Date(
        Date.now() - 35 * 60 * 1000
      ).toISOString();

      csClientStub.getFeature.resolves({
        ...mockFeatureV1,
        ai_test_eval_run_status: AITestEvaluationStatus.COMPLETE,
        ai_test_eval_status_timestamp: thirtyFiveMinutesAgo,
      });

      const el = await fixture<ChromedashWPTEvalPage>(
        html`<chromedash-wpt-eval-page
          .featureId=${1}
        ></chromedash-wpt-eval-page>`
      );
      await el.updateComplete;

      const button = el.shadowRoot!.querySelector('.generate-button');
      const message = el.shadowRoot!.querySelector('.cooldown-message');

      expect(button).to.exist;
      expect(button).to.not.have.attribute('disabled');
      expect(message).to.not.exist;
    });

    it('enables button if last run was FAILED even if timestamp is recent', async () => {
      // If failed, we usually allow retrying immediately
      const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000).toISOString();

      csClientStub.getFeature.resolves({
        ...mockFeatureV1,
        ai_test_eval_run_status: AITestEvaluationStatus.FAILED,
        ai_test_eval_status_timestamp: fiveMinutesAgo,
      });

      const el = await fixture<ChromedashWPTEvalPage>(
        html`<chromedash-wpt-eval-page
          .featureId=${1}
        ></chromedash-wpt-eval-page>`
      );
      await el.updateComplete;

      const button = el.shadowRoot!.querySelector('.generate-button');
      const message = el.shadowRoot!.querySelector('.cooldown-message');

      expect(button).to.exist;
      expect(button).to.not.have.attribute('disabled');
      expect(message).to.not.exist;
    });
  });
});
