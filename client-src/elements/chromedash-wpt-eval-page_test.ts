import {html, fixture, expect, nextFrame} from '@open-wc/testing';
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
    confidential: false,
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
      'AI-powered WPT coverage analysis'
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

    // Check Header Structure
    const header = reportSection!.querySelector('.report-header');
    expect(header).to.exist;
    expect(header!.querySelector('h2')!.textContent).to.equal(
      'Analysis Results'
    );

    // Check Content
    const content = reportSection!.querySelector('.report-content');
    expect(content!.querySelector('h1')!.textContent).to.equal('Report Title');
  });

  it('sanitizes HTML in the report to prevent XSS', async () => {
    const maliciousContent = `# Safe Title
     <script>window.alert("XSS")</script>
     <img src="x" onerror="window.alert('img XSS')">
     <a href="javascript:alert('link XSS')">Bad Link</a>
    `;

    csClientStub.getFeature.resolves({
      ...mockFeatureV1,
      ai_test_eval_report: maliciousContent,
    });

    const el = await fixture<ChromedashWPTEvalPage>(
      html`<chromedash-wpt-eval-page
        .featureId=${123}
      ></chromedash-wpt-eval-page>`
    );
    await el.updateComplete;

    const content = el.shadowRoot!.querySelector('.report-content');
    expect(content).to.exist;

    // The title should still exist
    expect(content!.querySelector('h1')!.textContent).to.equal('Safe Title');

    // The script tag should be completely removed
    expect(content!.querySelector('script')).to.not.exist;

    // The img tag might exist (depending on config), but the onerror attribute must be gone
    const img = content!.querySelector('img');
    if (img) {
      expect(img.hasAttribute('onerror')).to.be.false;
    }

    // The link should not have a javascript: href
    const link = content!.querySelector('a');
    if (link) {
      expect(link.href).to.not.contain('javascript:');
    }
  });

  describe('Report Copy Functionality', () => {
    // Mock the clipboard API
    const mockWriteText = sinon.stub();

    beforeEach(() => {
      // Define a mock clipboard on the navigator instance
      Object.defineProperty(navigator, 'clipboard', {
        value: {
          writeText: mockWriteText,
        },
        configurable: true,
        writable: true,
      });

      mockWriteText.reset();
    });

    it('renders the copy button with correct text', async () => {
      csClientStub.getFeature.resolves(mockFeatureV1);
      const el = await fixture<ChromedashWPTEvalPage>(
        html`<chromedash-wpt-eval-page
          .featureId=${1}
        ></chromedash-wpt-eval-page>`
      );
      await el.updateComplete;

      const copyButton = el.shadowRoot!.querySelector(
        '.report-header sl-button'
      );
      expect(copyButton).to.exist;
      expect(copyButton!.textContent).to.contain('Copy Report');
      expect(copyButton!.getAttribute('title')).to.equal(
        'Copy report to clipboard'
      );
    });

    it('copies report content to clipboard when clicked', async () => {
      csClientStub.getFeature.resolves(mockFeatureV1);
      const el = await fixture<ChromedashWPTEvalPage>(
        html`<chromedash-wpt-eval-page
          .featureId=${1}
        ></chromedash-wpt-eval-page>`
      );
      await el.updateComplete;

      const copyButton = el.shadowRoot!.querySelector(
        '.report-header sl-button'
      ) as HTMLElement;
      copyButton.click();

      expect(mockWriteText).to.have.been.calledWith(
        mockFeatureV1.ai_test_eval_report
      );
    });

    it('does not render copy button if no report exists', async () => {
      csClientStub.getFeature.resolves({
        ...mockFeatureV1,
        ai_test_eval_report: null,
      });
      const el = await fixture<ChromedashWPTEvalPage>(
        html`<chromedash-wpt-eval-page
          .featureId=${1}
        ></chromedash-wpt-eval-page>`
      );
      await el.updateComplete;

      const reportSection = el.shadowRoot!.querySelector('.report-section');
      expect(reportSection).to.not.exist;
    });
  });

  describe('Prerequisites Checklist', () => {
    it('shows all checks as success and displays all values when all data is present', async () => {
      const specLink = 'https://valid.spec';
      const wptDescr = 'Description text https://wpt.fyi/results/a';
      const featureName = 'Test Feature Name';
      const featureSummary = 'Test Feature Summary';

      csClientStub.getFeature.resolves({
        ...mockFeatureV1,
        name: featureName,
        summary: featureSummary,
        spec_link: specLink,
        wpt_descr: wptDescr,
      });
      const el = await fixture<ChromedashWPTEvalPage>(
        html`<chromedash-wpt-eval-page
          .featureId=${1}
        ></chromedash-wpt-eval-page>`
      );
      await el.updateComplete;

      // Check requirement items (Total 5: Name, Summary, Spec, Descr, Valid URLs)
      const items = el.shadowRoot!.querySelectorAll('.requirement-item');
      expect(items.length).to.equal(5);
      items.forEach(item => {
        expect(item.querySelector('sl-icon')!.classList.contains('success')).to
          .be.true;
      });

      // Check displayed data containers (Total 5)
      const dataContainers = el.shadowRoot!.querySelectorAll(
        '.url-list-container'
      );
      expect(dataContainers.length).to.equal(5);

      // Verify Feature Name (Index 0)
      expect(dataContainers[0].textContent).to.contain(featureName);

      // Verify Feature Summary (Index 1)
      expect(dataContainers[1].textContent).to.contain(featureSummary);

      // Verify Spec URL (Index 2)
      const specAnchor = dataContainers[2].querySelector('a');
      expect(specAnchor).to.exist;
      expect(specAnchor!.href).to.contain(specLink);

      // Verify WPT Description (Index 3)
      expect(dataContainers[3].textContent).to.contain(wptDescr);

      // Verify Valid URLs (Index 4)
      expect(dataContainers[4].querySelector('ul')).to.exist;
    });
    it('annotates directory WPT URLs but not individual test file URLs', async () => {
      const dirUrl = 'https://wpt.fyi/results/css';
      const fileUrl = 'https://wpt.fyi/results/dom/historical.html';

      csClientStub.getFeature.resolves({
        ...mockFeatureV1,
        wpt_descr: `Relevant tests:\n${dirUrl}\n${fileUrl}`,
      });

      const el = await fixture<ChromedashWPTEvalPage>(
        html`<chromedash-wpt-eval-page
          .featureId=${1}
        ></chromedash-wpt-eval-page>`
      );

      await el.updateComplete;

      // Get all URL list items
      const listItems = Array.from(
        el.shadowRoot!.querySelectorAll<HTMLLIElement>(
          '.url-list-container ul.url-list li'
        )
      );

      // Find the list items by URL text
      const dirItem = listItems.find(li => li.textContent?.includes(dirUrl));
      const fileItem = listItems.find(li => li.textContent?.includes(fileUrl));

      expect(dirItem, 'directory URL item should exist').to.exist;
      expect(fileItem, 'file URL item should exist').to.exist;

      // Directory URL should be annotated
      expect(
        dirItem!.querySelector('.dir-note'),
        'directory URL should show annotation'
      ).to.exist;
      expect(dirItem!.textContent).to.contain('(all tests in directory)');

      // File URL should NOT be annotated
      expect(
        fileItem!.querySelector('.dir-note'),
        'file URL should not show annotation'
      ).to.not.exist;
      expect(fileItem!.textContent).to.not.contain('(all tests in directory)');
    });

    it('shows Name/Summary as success, but other checks as danger when optional data is missing', async () => {
      // Feature has name/summary (default mock), but missing spec and wpt_descr
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
      expect(items.length).to.equal(5);

      // Name (0) and Summary (1) should be SUCCESS
      expect(items[0].querySelector('.success')).to.exist;
      expect(items[1].querySelector('.success')).to.exist;

      // Spec (2), Descr (3), Valid URLs (4) should be DANGER
      expect(items[2].querySelector('.danger')).to.exist;
      expect(items[3].querySelector('.danger')).to.exist;
      expect(items[4].querySelector('.danger')).to.exist;

      // Check displayed data containers
      const dataContainers = el.shadowRoot!.querySelectorAll(
        '.url-list-container'
      );
      // Should only show 2 containers (Name and Summary)
      expect(dataContainers.length).to.equal(2);
      expect(dataContainers[0].textContent).to.contain(mockFeatureV1.name);
      expect(dataContainers[1].textContent).to.contain(mockFeatureV1.summary);
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

    it('renders primary evaluate button when no report exists', async () => {
      // Feature has no report yet
      csClientStub.getFeature.resolves({
        ...mockFeatureV1,
        ai_test_eval_report: null,
        ai_test_eval_run_status: null,
      });

      const el = await fixture<ChromedashWPTEvalPage>(
        html`<chromedash-wpt-eval-page
          .featureId=${1}
        ></chromedash-wpt-eval-page>`
      );
      await el.updateComplete;

      const button = el.shadowRoot!.querySelector('.generate-button');

      expect(button).to.have.attribute('variant', 'primary');
      expect(button!.textContent?.trim()).to.equal('Evaluate test coverage');
    });

    it('renders danger re-evaluate button when a report already exists', async () => {
      // Feature already has a report
      csClientStub.getFeature.resolves({
        ...mockFeatureV1,
        ai_test_eval_report: 'Existing report content',
        ai_test_eval_run_status: null,
      });

      const el = await fixture<ChromedashWPTEvalPage>(
        html`<chromedash-wpt-eval-page
          .featureId=${1}
        ></chromedash-wpt-eval-page>`
      );
      await el.updateComplete;

      const button = el.shadowRoot!.querySelector('.generate-button');

      expect(button).to.have.attribute('variant', 'danger');
      expect(button!.textContent?.trim()).to.equal(
        'Discard this report and reevaluate test coverage'
      );
    });

    it('starts analysis, enters IN_PROGRESS state, and starts polling on click', async () => {
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
      expect(successMsg!.textContent).to.contain('Analysis complete!');

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
      expect(alert!.textContent).to.contain('previous analysis run failed');

      // Button should still be visible to try again
      expect(el.shadowRoot!.querySelector('.generate-button')).to.exist;
    });

    it('shows retry button and help text if IN_PROGRESS but hanging (> 60 mins)', async () => {
      // Set timestamp to 61 minutes ago
      const sixtyOneMinutesAgo = new Date(
        Date.now() - 61 * 60 * 1000
      ).toISOString();

      csClientStub.getFeature.resolves({
        ...mockFeatureV1,
        ai_test_eval_run_status: AITestEvaluationStatus.IN_PROGRESS,
        ai_test_eval_status_timestamp: sixtyOneMinutesAgo,
      });

      const el = await fixture<ChromedashWPTEvalPage>(
        html`<chromedash-wpt-eval-page
          .featureId=${1}
        ></chromedash-wpt-eval-page>`
      );
      await el.updateComplete;

      // Spinner should NOT exist
      expect(el.shadowRoot!.querySelector('.status-in-progress')).to.not.exist;
      expect(el.shadowRoot!.querySelector('sl-spinner')).to.not.exist;

      // Button SHOULD exist and have specific text
      const button = el.shadowRoot!.querySelector('.generate-button');
      expect(button).to.exist;
      expect(button).to.not.have.attribute('disabled');
      expect(button!.textContent?.trim()).to.equal(
        'Retry analysis (Process timed out)'
      );

      // Help text should exist
      const helpText = el.shadowRoot!.querySelector('.help-text');
      expect(helpText).to.exist;
      expect(helpText!.textContent).to.contain('seems to be stuck');
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

  describe('Confidentiality Logic', () => {
    it('disables button and shows specific message if feature is confidential', async () => {
      csClientStub.getFeature.resolves({
        ...mockFeatureV1,
        confidential: true,
      });

      const el = await fixture<ChromedashWPTEvalPage>(
        html`<chromedash-wpt-eval-page
          .featureId=${1}
        ></chromedash-wpt-eval-page>`
      );
      await el.updateComplete;

      const button = el.shadowRoot!.querySelector('.generate-button');
      const helpText = el.shadowRoot!.querySelector('.help-text');
      const cooldownMsg = el.shadowRoot!.querySelector('.cooldown-message');

      expect(button).to.exist;
      expect(button).to.have.attribute('disabled');

      expect(helpText).to.exist;
      expect(helpText!.textContent).to.contain(
        'This feature is set to "confidential"'
      );
      expect(helpText!.textContent).to.contain(
        'cannot be sent to Gemini for evaluation'
      );

      // Cooldown message should NOT be shown even if no cooldown exists.
      expect(cooldownMsg).to.not.exist;
    });
  });
});
