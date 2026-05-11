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
    deleteWPTCoverageEvaluation: sinon.SinonStub;
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
      deleteWPTCoverageEvaluation: sinon.stub(),
    };
    (window as any).csClient = csClientStub;
    sinon.stub(ChromedashWPTEvalPage.prototype, 'managePolling');
    sinon.stub(ChromedashWPTEvalPage.prototype, 'updateCooldown');
    sinon.stub(window, 'setInterval').returns(123 as any);
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
    expect(
      el.shadowRoot!.querySelector('.description')!.textContent
    ).to.contain('Explainers (Optional)');
  });

  it('shows skeletons while loading data', async () => {
    let resolveFeature: (value: any) => void;
    const featurePromise = new Promise(resolve => {
      resolveFeature = resolve;
    });
    // Return a promise that doesn't resolve immediately to test loading state
    csClientStub.getFeature.returns(featurePromise);
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

    // Resolve the promise so the component can finish its lifecycle cleanly
    resolveFeature!(mockFeatureV1);
    await el.updateComplete;
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
        'sl-button[title="Copy report to clipboard"]'
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
        'sl-button[title="Copy report to clipboard"]'
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

      // Check requirement items (Total 6: Name, Summary, Spec, Descr, Valid URLs, Explainers)
      const items = el.shadowRoot!.querySelectorAll('.requirement-item');
      expect(items.length).to.equal(6);
      items.forEach((item, index) => {
        if (index === 5) {
          // Explainers is the 6th item and is info by default
          expect(item.querySelector('sl-icon[name="info_20px"]')).to.exist;
        } else {
          expect(item.querySelector('sl-icon')!.classList.contains('success'))
            .to.be.true;
        }
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

    it('renders explainer links row correctly when links are present', async () => {
      const explainerLinks = ['https://example.com/explainer.md'];
      csClientStub.getFeature.resolves({
        ...mockFeatureV1,
        explainer_links: explainerLinks,
      });

      const el = await fixture<ChromedashWPTEvalPage>(
        html`<chromedash-wpt-eval-page
          .featureId=${1}
        ></chromedash-wpt-eval-page>`
      );
      await el.updateComplete;

      const items = el.shadowRoot!.querySelectorAll('.requirement-item');
      // Total 6 now: Name, Summary, Spec, Descr, Valid URLs, Explainers
      expect(items.length).to.equal(6);

      const explainerItem = items[5];
      // Note: By default includeExplainer is false, so it will show info icon initially unless checked
      expect(explainerItem.querySelector('sl-icon[name="info_20px"]')).to.exist;
      expect(explainerItem.querySelector('sl-checkbox')).to.exist;
      expect(
        explainerItem.querySelector('sl-checkbox')!.textContent
      ).to.contain('Include feature explainers');
      expect(explainerItem.querySelector('sl-badge')).to.not.exist;

      // The list is NOT rendered if includeExplainer is false
      const urlListContainer = el.shadowRoot!.querySelectorAll(
        '.url-list-container'
      );
      expect(urlListContainer.length).to.equal(5);
    });

    it('renders explainer links row correctly with Optional badge and info icon when links are missing and unchecked', async () => {
      csClientStub.getFeature.resolves({
        ...mockFeatureV1,
        explainer_links: [],
      });

      const el = await fixture<ChromedashWPTEvalPage>(
        html`<chromedash-wpt-eval-page
          .featureId=${1}
        ></chromedash-wpt-eval-page>`
      );
      await el.updateComplete;

      const items = el.shadowRoot!.querySelectorAll('.requirement-item');
      expect(items.length).to.equal(6);

      const explainerItem = items[5];
      // includeExplainer defaults to false, so it should show info icon if missing
      expect(explainerItem.querySelector('.success')).to.not.exist;
      expect(explainerItem.querySelector('sl-icon[name="info_20px"]')).to.exist;
      expect(explainerItem.querySelector('sl-badge[variant="neutral"]')).to
        .exist;
      expect(explainerItem.querySelector('sl-badge')!.textContent).to.contain(
        'Optional'
      );

      // Since includeExplainer is false, the list should not be rendered
      const urlList = el.shadowRoot!.querySelectorAll('.url-list');
      // Index 4 is WPT URLs. Index 5 (Explainers) should not exist.
      expect(urlList.length).to.equal(5);
    });

    it('toggling the includeExplainer checkbox updates state and icons', async () => {
      csClientStub.getFeature.resolves({
        ...mockFeatureV1,
        explainer_links: [],
      });
      const el = await fixture<ChromedashWPTEvalPage>(
        html`<chromedash-wpt-eval-page
          .featureId=${1}
        ></chromedash-wpt-eval-page>`
      );
      await el.updateComplete;

      expect(el.includeExplainer).to.be.false;
      const items = el.shadowRoot!.querySelectorAll('.requirement-item');
      expect(items[5].querySelector('sl-icon[name="info_20px"]')).to.exist;

      const checkbox = el.shadowRoot!.querySelector('sl-checkbox') as any;
      checkbox.checked = true;
      checkbox.dispatchEvent(new Event('sl-change'));
      await el.updateComplete;
      await new Promise(resolve => setTimeout(resolve, 0));

      expect(el.includeExplainer).to.be.true;
      expect(
        el
          .shadowRoot!.querySelectorAll('.requirement-item')[5]
          .querySelector('sl-icon[name="cancel_20px"].danger')
      ).to.exist;
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
      expect(items.length).to.equal(6); // 5 items + 1 explainer

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
      // Should only show 2 containers (Name and Summary) since others are missing
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
      ).to.have.been.calledWith(99, false); // Default is false

      // UI entered IN_PROGRESS state immediately (optimistic update)
      expect(el.feature?.ai_test_eval_run_status).to.equal(
        AITestEvaluationStatus.IN_PROGRESS
      );
      expect(el.shadowRoot!.querySelector('.status-in-progress')).to.exist;
      expect(el.shadowRoot!.querySelector('sl-spinner')).to.exist;

      // Polling started
      expect((ChromedashWPTEvalPage.prototype.managePolling as any).called).to
        .be.true;
    });

    it('passes includeExplainer=true to API when checkbox is checked', async () => {
      csClientStub.getFeature.resolves(mockFeatureV1);
      csClientStub.generateWPTCoverageEvaluation.resolves({});

      const el = await fixture<ChromedashWPTEvalPage>(
        html`<chromedash-wpt-eval-page
          .featureId=${99}
        ></chromedash-wpt-eval-page>`
      );
      await el.updateComplete;

      // Check the checkbox
      const checkbox = el.shadowRoot!.querySelector('sl-checkbox') as any;
      checkbox.checked = true;
      checkbox.dispatchEvent(new Event('sl-change'));
      await el.updateComplete;

      const button = el.shadowRoot!.querySelector(
        '.generate-button'
      ) as HTMLElement;
      button.click();
      await el.updateComplete;

      expect(
        csClientStub.generateWPTCoverageEvaluation
      ).to.have.been.calledWith(99, true);
    });

    it('renders IN_PROGRESS state when loaded from server', async () => {
      csClientStub.getFeature.resolves({
        ...mockFeatureV1,
        ai_test_eval_run_status: AITestEvaluationStatus.IN_PROGRESS,
      });

      const el = await fixture<ChromedashWPTEvalPage>(
        html`<chromedash-wpt-eval-page
          .featureId=${1}
        ></chromedash-wpt-eval-page>`
      );
      await el.updateComplete;

      expect(el.shadowRoot!.querySelector('.status-in-progress')).to.exist;
      // Should automatically start polling if loaded in progress
      expect((ChromedashWPTEvalPage.prototype.managePolling as any).called).to
        .be.true;
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
      expect((ChromedashWPTEvalPage.prototype.managePolling as any).called).to
        .be.true;

      // Restore managePolling to test its real behavior
      (ChromedashWPTEvalPage.prototype.managePolling as any).restore();
      // Simulate that it was polling by setting a fake interval ID
      (el as any)._pollIntervalId = 123;

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
      expect((el as any)._pollIntervalId).to.be.null;
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

      // Manually set cooldown remaining to simulate active cooldown
      (el as any)._cooldownRemaining = 1500000;

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

    it('persists cooldown even after deleting a report within the cooldown window', async () => {
      const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000).toISOString();
      const featureInCooldown = {
        ...mockFeatureV1,
        ai_test_eval_run_status: AITestEvaluationStatus.COMPLETE,
        ai_test_eval_status_timestamp: fiveMinutesAgo,
      };

      // 1. Initial load is in cooldown.
      csClientStub.getFeature.resolves(featureInCooldown);
      const el = await fixture<ChromedashWPTEvalPage>(
        html`<chromedash-wpt-eval-page
          .featureId=${1}
        ></chromedash-wpt-eval-page>`
      );

      // Manually set cooldown remaining to simulate active cooldown
      (el as any)._cooldownRemaining = 1500000;

      await el.updateComplete;

      // Verify cooldown is active.
      let button = el.shadowRoot!.querySelector('.generate-button');
      let message = el.shadowRoot!.querySelector('.cooldown-message');
      expect(button, 'Button should initially be disabled').to.have.attribute(
        'disabled'
      );
      expect(message, 'Cooldown message should initially be visible').to.exist;

      // 2. User deletes the report.
      const confirmStub = sinon.stub(window, 'confirm').returns(true);
      csClientStub.deleteWPTCoverageEvaluation.resolves({});
      // Subsequent fetchData call will get the same data, but we'll pretend the report is gone.
      csClientStub.getFeature.resolves({
        ...featureInCooldown,
        ai_test_eval_report: null,
      });

      const deleteButton = el.shadowRoot!.querySelector(
        'sl-button[title="Delete report"]'
      ) as HTMLElement;
      deleteButton.click();
      await nextFrame(); // Let delete operation process
      await el.updateComplete; // Let UI update after fetchData

      // 3. Verify cooldown is STILL active.
      button = el.shadowRoot!.querySelector('.generate-button');
      message = el.shadowRoot!.querySelector('.cooldown-message');
      expect(
        button,
        'Button should still be disabled after deletion'
      ).to.have.attribute('disabled');
      expect(message, 'Cooldown message should still be visible after deletion')
        .to.exist;
      expect(message!.textContent).to.contain('Available in');

      confirmStub.restore();
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

  describe('Report Deletion Functionality', () => {
    let confirmStub: sinon.SinonStub;

    beforeEach(() => {
      confirmStub = sinon.stub(window, 'confirm');
    });

    it('renders the delete button when a report is present', async () => {
      csClientStub.getFeature.resolves(mockFeatureV1); // Has a report by default.
      const el = await fixture<ChromedashWPTEvalPage>(
        html`<chromedash-wpt-eval-page
          .featureId=${1}
        ></chromedash-wpt-eval-page>`
      );
      await el.updateComplete;

      const deleteButton = el.shadowRoot!.querySelector(
        'sl-button[title="Delete report"]'
      );
      expect(deleteButton).to.exist;
      expect(deleteButton!.textContent).to.contain('Delete Report');
    });

    it('does not render the delete button if no report exists', async () => {
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

      const deleteButton = el.shadowRoot!.querySelector(
        'sl-button[title="Delete report"]'
      );
      expect(deleteButton).to.not.exist;
    });

    it('calls delete API and refetches data when user confirms', async () => {
      csClientStub.getFeature.resolves(mockFeatureV1);
      csClientStub.deleteWPTCoverageEvaluation.resolves({});
      confirmStub.returns(true); // User clicks "OK"

      const el = await fixture<ChromedashWPTEvalPage>(
        html`<chromedash-wpt-eval-page
          .featureId=${12345}
        ></chromedash-wpt-eval-page>`
      );
      await el.updateComplete;

      const deleteButton = el.shadowRoot!.querySelector(
        'sl-button[title="Delete report"]'
      ) as HTMLElement;
      deleteButton.click();

      // Give time for the async operation to complete.
      await nextFrame();

      expect(confirmStub).to.have.been.calledOnce;
      expect(csClientStub.deleteWPTCoverageEvaluation).to.have.been.calledWith(
        12345
      );

      // It should call getFeature again to refresh the data.
      // Called once on load, and a second time after deletion.
      expect(csClientStub.getFeature).to.have.been.calledTwice;
    });
  });
});
