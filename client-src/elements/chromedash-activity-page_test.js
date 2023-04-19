import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashActivityPage} from './chromedash-activity-page';
import '../js-src/cs-client';
import sinon from 'sinon';

describe('chromedash-settings-page', () => {
  /* window.csClient is initialized in spa.html
   * which is not available here, so we initialize it before each test.
   * We also stub out the API calls here so that they return test data. */
  beforeEach(async () => {
    window.csClient = new ChromeStatusClient('fake_token', 1);
    sinon.stub(window.csClient, 'getComments');
  });

  afterEach(() => {
    window.csClient.getComments.restore();
  });

  it('can be added to the page before being opened', async () => {
    const component = await fixture(
      html`<chromedash-activity-page></chromedash-activity-page>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashActivityPage);
  });
});
