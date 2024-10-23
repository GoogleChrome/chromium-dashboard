import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashStackRankPage} from './chromedash-stack-rank-page';
import './chromedash-toast';
import sinon from 'sinon';

describe('chromedash-stack-rank-page', () => {
  /* <chromedash-toast> are initialized at spa.html
   * which are not available here, so we initialize them before each test.
   * We also stub out the API calls here so that they return test data. */
  let fetchStub;
  beforeEach(async () => {
    await fixture(html`<chromedash-toast></chromedash-toast>`);
    fetchStub = sinon.stub(window, 'fetch');
  });

  afterEach(() => {
    fetchStub.restore();
  });

  it('invalid stack-rank fetch response', async () => {
    fetchStub.returns(Promise.reject(new Error('No results')));
    const component = await fixture(
      html`<chromedash-stack-rank-page></chromedash-stack-rank-page>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashStackRankPage);

    // error response would trigger the toast to show message
    const toastEl = document.querySelector('chromedash-toast');
    const toastMsgSpan = toastEl?.shadowRoot?.querySelector('span#msg');
    assert.include(
      toastMsgSpan?.innerHTML,
      'Some errors occurred. Please refresh the page or try again later.'
    );
  });

  it('valid stack-rank fetch response', async () => {
    const type = 'feature';
    const view = 'popularity';
    fetchStub.returns(Promise.resolve({}));
    const component = await fixture(
      html`<chromedash-stack-rank-page .type="${type}" .view="${view}">
      </chromedash-stack-rank-page>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashStackRankPage);

    // header exists and with the correct link and title
    const subheaderDiv = component.renderRoot.querySelector('div#subheader');
    assert.exists(subheaderDiv);
    assert.include(
      subheaderDiv.innerHTML,
      'HTML &amp; JavaScript usage metrics &gt; all features &gt; stack rank'
    );

    // datalist and its input exist
    const datalistInputEl = component.renderRoot.querySelector(
      'input#datalist-input'
    );
    const datalistEl = component.renderRoot.querySelector('datalist#features');
    assert.exists(datalistInputEl);
    assert.exists(datalistEl);

    // chromedash-stack-rank exists
    const stackrankEl = component.renderRoot.querySelector(
      'chromedash-stack-rank'
    );
    assert.exists(stackrankEl);
  });
});
