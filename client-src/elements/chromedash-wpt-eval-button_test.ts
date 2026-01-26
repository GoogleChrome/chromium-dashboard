import {html, fixture, expect} from '@open-wc/testing';
import './chromedash-wpt-eval-button.js';
import {ChromedashWPTEvalButton} from './chromedash-wpt-eval-button.js';

describe('chromedash-wpt-eval-button', () => {
  it('renders with default featureId', async () => {
    const el = await fixture<ChromedashWPTEvalButton>(
      html`<chromedash-wpt-eval-button></chromedash-wpt-eval-button>`
    );

    const button = el.shadowRoot!.querySelector('sl-button');
    expect(button).to.exist;
    expect(button!.getAttribute('href')).to.equal(
      '/feature/0/ai-coverage-analysis'
    );
    expect(el.shadowRoot!.textContent).to.contain('Evaluate test coverage');
  });

  it('renders with a specific featureId', async () => {
    const featureId = 12345;
    const el = await fixture<ChromedashWPTEvalButton>(
      html`<chromedash-wpt-eval-button
        .featureId=${featureId}
      ></chromedash-wpt-eval-button>`
    );

    const button = el.shadowRoot!.querySelector('sl-button');
    expect(button).to.exist;
    // Verify the href is constructed correctly with the passed ID
    expect(button!.getAttribute('href')).to.equal(
      `/feature/${featureId}/ai-coverage-analysis`
    );
  });

  it('contains the Gemini icon with correct styling class', async () => {
    const el = await fixture<ChromedashWPTEvalButton>(
      html`<chromedash-wpt-eval-button></chromedash-wpt-eval-button>`
    );

    const icon = el.shadowRoot!.querySelector('img.gemini-icon');
    expect(icon).to.exist;
    expect(icon!.getAttribute('slot')).to.equal('prefix');
    expect(icon!.getAttribute('alt')).to.equal('Gemini AI Logo');
    expect(icon!.getAttribute('src')).to.contain('gemini_2025');
  });
});
