import {html, fixture, expect, nextFrame} from '@open-wc/testing';
import sinon from 'sinon';
import './chromedash-wpt-eval-page.js';
import {ChromedashWPTEvalPage} from './chromedash-wpt-eval-page.js';
import {FeatureNotFoundError} from '../js-src/cs-client.js';

describe('chromedash-wpt-eval-page', () => {
  let csClientStub: {getFeature: sinon.SinonStub};

  // Sample feature data for testing
  const mockFeatureV1 = {
    id: 12345,
    name: 'Test Feature',
    summary: 'A summary of the feature',
    spec_link: 'https://spec.example.com',
    wpt_descr: 'Tests are here: https://wpt.fyi/results/feature/test.html',
    ai_test_eval_report: '# Report Title\n\nReport content goes here.',
  };

  beforeEach(() => {
    // Mock the global csClient before each test
    csClientStub = {
      getFeature: sinon.stub(),
    };
    (window as any).csClient = csClientStub;
  });

  afterEach(() => {
    sinon.restore();
  });

  it('renders the basic page structure', async () => {
    // Mock a never-resolving promise to keep it in loading state if needed,
    // or just let it resolve quickly to standard empty state.
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

    // Wait for initial fetch to complete
    await nextFrame(); // sometimes needed for state updates to propagate
    await el.updateComplete;

    expect(csClientStub.getFeature).to.have.been.calledWith(123);
    expect(el.loading).to.be.false;
    expect(el.feature).to.deep.equal(mockFeatureV1);

    // Check Report Rendering (markdown parsing)
    const reportSection = el.shadowRoot!.querySelector('.report-section');
    expect(reportSection).to.exist;
    expect(reportSection!.querySelector('h1')!.textContent).to.equal(
      'Report Title'
    );
    expect(reportSection!.innerHTML).to.contain('Report content goes here.');

    // Check Prerequisites rendered
    const prereqs = el.shadowRoot!.querySelector('.requirements-list');
    expect(prereqs).to.exist;
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
      expect(items.length).to.equal(3); // Spec, Desc, Valid URLs

      // Check for success icons
      items.forEach(item => {
        expect(item.querySelector('sl-icon')!.classList.contains('success')).to
          .be.true;
        expect(item.querySelector('sl-icon')!.getAttribute('name')).to.equal(
          'check_circle_20px'
        );
      });
    });

    it('shows checks as danger when data is missing', async () => {
      csClientStub.getFeature.resolves({
        ...mockFeatureV1,
        spec_link: '', // Missing
        wpt_descr: '', // Missing
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
        expect(item.querySelector('sl-icon')!.getAttribute('name')).to.equal(
          'x-circle-fill'
        );
      });

      expect(el.shadowRoot!.textContent).to.contain('Missing Spec URL');
      expect(el.shadowRoot!.textContent).to.contain('Missing WPT description');
    });

    it('correctly identifies and lists valid WPT URLs', async () => {
      csClientStub.getFeature.resolves({
        ...mockFeatureV1,
        wpt_descr:
          'Check https://wpt.fyi/results/foo.html and also https://wpt.fyi/results/bar/',
      });
      const el = await fixture<ChromedashWPTEvalPage>(
        html`<chromedash-wpt-eval-page
          .featureId=${3}
        ></chromedash-wpt-eval-page>`
      );
      await el.updateComplete;

      // The 3rd requirement item (Valid URLs) should be success
      const items = el.shadowRoot!.querySelectorAll('.requirement-item');
      expect(items[2].querySelector('.success')).to.exist;

      // Check the rendered list of URLs
      const urlList = el.shadowRoot!.querySelector('.url-list');
      expect(urlList).to.exist;
      const links = urlList!.querySelectorAll('li a');
      expect(links.length).to.equal(2);
      expect(links[0].getAttribute('href')).to.equal(
        'https://wpt.fyi/results/foo.html'
      );
      expect(links[1].getAttribute('href')).to.equal(
        'https://wpt.fyi/results/bar/'
      );
    });

    it('fails the "Valid URLs" check if wpt_descr has text but no valid links', async () => {
      csClientStub.getFeature.resolves({
        ...mockFeatureV1,
        wpt_descr:
          'Tests are available at github.com/web-platform-tests (invalid for this check)',
      });
      const el = await fixture<ChromedashWPTEvalPage>(
        html`<chromedash-wpt-eval-page
          .featureId=${4}
        ></chromedash-wpt-eval-page>`
      );
      await el.updateComplete;

      const items = el.shadowRoot!.querySelectorAll('.requirement-item');
      // Item 1 (Desc) should be success because text exists
      expect(items[1].querySelector('.success')).to.exist;
      // Item 2 (Valid URLs) should fail because the specific regex didn't match
      expect(items[2].querySelector('.danger')).to.exist;
      expect(el.shadowRoot!.querySelector('.url-list')).to.not.exist;
    });
  });

  describe('Error Handling', () => {
    it('handles FeatureNotFoundError gracefully by stopping loading', async () => {
      // Simulate a 404 from the client
      csClientStub.getFeature.rejects(new FeatureNotFoundError(123));

      const el = await fixture<ChromedashWPTEvalPage>(
        html`<chromedash-wpt-eval-page
          .featureId=${999}
        ></chromedash-wpt-eval-page>`
      );
      await el.updateComplete;

      expect(el.loading).to.be.false;
      expect(el.feature).to.be.null;
      // Should not see reports or checklists.
      expect(el.shadowRoot!.querySelector('.requirements-list')).to.not.exist;
      expect(el.shadowRoot!.querySelector('.report-section')).to.not.exist;
    });

    it('handles generic errors', async () => {
      csClientStub.getFeature.rejects(new Error('Network Boom'));

      const el = await fixture<ChromedashWPTEvalPage>(
        html`<chromedash-wpt-eval-page
          .featureId=${500}
        ></chromedash-wpt-eval-page>`
      );
      await el.updateComplete;

      expect(el.loading).to.be.true;

      expect(el.shadowRoot!.querySelector('sl-skeleton')).to.exist;
    });
  });
});
