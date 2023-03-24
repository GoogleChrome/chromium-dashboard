import './chromedash-toast';
import {html} from 'lit';
import {ChromedashAdminBlinkPage} from './chromedash-admin-blink-page';
import {assert, fixture} from '@open-wc/testing';
import sinon from 'sinon';
import {DefaultApi} from 'chromestatus-openapi';
describe('chromedash-admin-blink-page', () => {
  beforeEach(async () => {
    await fixture(html`<chromedash-toast></chromedash-toast>`);
  });
  it('render with no data', async () => {
    window.csOpenApiClient = sinon.createStubInstance(DefaultApi, {
      listComponentUsers: sinon.stub().rejects(
        new Error('Got error response from server')),
    });

    const component = await fixture(
      html`<chromedash-admin-blink-page></chromedash-admin-blink-page>`,
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashAdminBlinkPage);

    // error response would trigger the toast to show message
    const toastEl = document.querySelector('chromedash-toast');
    const toastMsgSpan = toastEl.shadowRoot.querySelector('span#msg');
    assert.include(toastMsgSpan.innerHTML,
      'Some errors occurred. Please refresh the page or try again later.');
  });

  it('render with fake data', async () => {
    /** @type {import('chromestatus-openapi').ComponentsUsersResponse} */
    const response = {
      users: [
        {id: 0, name: 'user0', email: 'user0@example.com'},
      ],
      components: [
        {id: 0, name: 'component0', subscriberIds: [0], ownerIds: [0]},
      ],
    };
    window.csOpenApiClient = sinon.createStubInstance(DefaultApi, {
      listComponentUsers: sinon.stub().resolves(response),
    });

    const component = await fixture(
      html`<chromedash-admin-blink-page></chromedash-admin-blink-page>`,
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashAdminBlinkPage);

    // subheader exists
    const subheaderCountEl = component.shadowRoot.querySelector('#component-count');
    assert.exists(subheaderCountEl);
  });
});
