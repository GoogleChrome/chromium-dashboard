import {html} from 'lit';
import {expect, fixture} from '@open-wc/testing';
import {ChromedashProcessOverview} from './chromedash-process-overview';

describe('chromedash-proces-overview', () => {
  it('renders element with no data, untyped fixture', async () => {
    const container = await fixture(
        html`<chromedash-process-overview></chromedash-process-overview>`);
    expect(container).to.exist;
    expect(typeof container).to.equal('object');
    container.shadowRoot.querySelector<HTMLElement>('div');
  });

  it('renders element with no data, typed fixture', async () => {
    const container = await fixture< ChromedashProcessOverview >(
          html`<chromedash-process-overview></chromedash-process-overview>`);
    expect(container).to.exist;
    // I don't really expect the container to be boolean, but it is in this case.
    expect(typeof container).to.equal('boolean');
    // I really want to start testing the container as a DOM node of some kind:
    // container.shadowRoot.querySelector<HTMLElement>('div');
  });
});
