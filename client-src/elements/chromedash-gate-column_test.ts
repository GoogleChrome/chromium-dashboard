import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashGateColumn} from './chromedash-gate-column';
import {ChromeStatusClient} from '../js-src/cs-client';
import sinon from 'sinon';

describe('chromedash-settings-page', () => {
  /* window.csClient is initialized in spa.html
   * which is not available here, so we initialize it before each test.
   * We also stub out the API calls here so that they return test data. */
  beforeEach(async () => {
    window.csClient = new ChromeStatusClient('fake_token', 1);
    sinon.stub(window.csClient, 'getFeatureProcess');
    sinon.stub(window.csClient, 'getVotes');
    sinon.stub(window.csClient, 'getComments');
  });

  afterEach(() => {
    window.csClient.getFeatureProcess.restore();
    window.csClient.getVotes.restore();
    window.csClient.getComments.restore();
  });

  it('can be added to the page before being opened', async () => {
    const component = await fixture(
      html`<chromedash-gate-column></chromedash-gate-column>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashGateColumn);
  });
});
