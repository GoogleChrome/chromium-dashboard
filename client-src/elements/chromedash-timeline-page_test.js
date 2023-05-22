import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashTimelinePage} from './chromedash-timeline-page';
import './chromedash-toast';
import sinon from 'sinon';

describe('chromedash-timeline-page', () => {
  /* <chromedash-toast> are initialized at spa.html
   * which are not available here, so we initialize them before each test.
   * We also stub out the API calls here so that they return test data. */
  beforeEach(async () => {
    await fixture(html`<chromedash-toast></chromedash-toast>`);
    sinon.stub(window, 'fetch');
    // hacky way to stub out google chart load method
    window.google = {charts: {
      load: () => {},
      setOnLoadCallback: (f) => f(),
    }};
  });

  afterEach(() => {
    window.fetch.restore();
  });

  it('invalid timeline fetch response', async () => {
    window.fetch.returns(Promise.reject(new Error('No results')));
    const component = await fixture(
      html`<chromedash-timeline-page></chromedash-timeline-page>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashTimelinePage);

    // error response would trigger the toast to show message
    const toastEl = document.querySelector('chromedash-toast');
    const toastMsgSpan = toastEl.shadowRoot.querySelector('span#msg');
    assert.include(toastMsgSpan.innerHTML,
      'Some errors occurred. Please refresh the page or try again later.');
  });

  it('valid timeline fetch response', async () => {
    const type = 'feature';
    const view = 'popularity';
    window.fetch.returns(Promise.resolve({}));
    const component = await fixture(
      html`<chromedash-timeline-page
            .type="${type}"
            .view="${view}">
           </chromedash-timeline-page>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashTimelinePage);

    // header exists and with the correct link and title
    const subheaderDiv = component.shadowRoot.querySelector('div#subheader');
    assert.exists(subheaderDiv);
    assert.include(subheaderDiv.innerHTML, `href="/metrics/${type}/${view}"`);
    assert.include(subheaderDiv.innerHTML,
      'HTML &amp; JavaScript usage metrics &gt; all features &gt; timeline');

    // chromedash-timeline exists
    const timelineEl = component.shadowRoot.querySelector('chromedash-timeline');
    assert.exists(timelineEl);
  });
});
