import {assert, fixture} from '@open-wc/testing';
import {html} from 'lit';
import sinon from 'sinon';
import '../js-src/cs-client';
import {ChromedashActivityPage} from './chromedash-activity-page';

declare const ChromeStatusClient: typeof window.csClient;

describe('chromedash-settings-page', () => {
  let getCommentsStub: sinon.SinonStub;
  /* window.csClient is initialized in spa.html
   * which is not available here, so we initialize it before each test.
   * We also stub out the API calls here so that they return test data. */
  beforeEach(async () => {
    window.csClient = new ChromeStatusClient('fake_token', 1);
    getCommentsStub = sinon.stub(window.csClient, 'getComments');
  });

  afterEach(() => {
    getCommentsStub.restore();
  });

  it('can be added to the page before being opened', async () => {
    const component = await fixture(
      html`<chromedash-activity-page></chromedash-activity-page>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashActivityPage);
  });
});
