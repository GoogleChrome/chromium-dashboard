import {ChromedashAdminBlinkComponentListing} from './chromedash-admin-blink-component-listing';
import {html} from 'lit';
import {assert, expect, fixture, oneEvent} from '@open-wc/testing';
import sinon from 'sinon';
import {DefaultApi} from 'chromestatus-openapi';

/** @type {Map<number, import('chromestatus-openapi').ComponentsUser>} */
const testUsersMap = new Map([
  [0, {id: 0, email: 'a@b.c', name: '0'}],
  [1, {id: 1, email: 'a@b.c', name: '1'}],
  [2, {id: 2, email: 'a@b.c', name: '2'}],
  [3, {id: 3, email: 'a@b.c', name: '3'}],
  [4, {id: 4, email: 'a@b.c', name: '4'}],
  [5, {id: 5, email: 'a@b.c', name: '5'}],
]);

describe('chromedash-admin-blink-component-listing', () => {
  it('renders with data', async () => {
    const element = await fixture(
      html`<chromedash-admin-blink-component-listing
      .id=${1}
      .name=${'foo'}
      .subscriberIds=${[0, 1]}
      .ownerIds=${[0]}
      .index=${0}
      .usersMap=${testUsersMap}
      ?editing=${false}
    ></chromedash-admin-blink-component-listing>`,
    );
    assert.exists(element);
    assert.instanceOf(element, ChromedashAdminBlinkComponentListing);
  });
  describe('interactions on the element call certain functions', async () => {
    let element;
    beforeEach(async () => {
      element = await fixture(
        html`<chromedash-admin-blink-component-listing
        .id=${1}
        .name=${'foo'}
        .subscriberIds=${[0, 1]}
        .ownerIds=${[0]}
        .index=${0}
        .usersMap=${testUsersMap}
        ?editing=${true}
      ></chromedash-admin-blink-component-listing>`,
      );
    });
    it('calls addUser when Add button is clicked', async () => {
      // Stub the function and re-render
      // https://open-wc.org/guides/knowledge/testing/stubs/
      const addUserFn = sinon.stub(element, '_addUser');
      element.requestUpdate();
      await element.updateComplete;

      expect(addUserFn).to.have.callCount(0);
      const addBtn = element.shadowRoot.querySelector('.add_owner_button');
      addBtn.click();
      expect(addUserFn).to.have.callCount(1);
    });
    it('calls removeUser when Remove button is clicked', async () => {
      // Stub the function and re-render
      // https://open-wc.org/guides/knowledge/testing/stubs/
      const removeUserFn = sinon.stub(element, '_removeUser');
      element.requestUpdate();
      await element.updateComplete;

      expect(removeUserFn).to.have.callCount(0);
      const removeBtn = element.shadowRoot.querySelector('.remove_owner_button');
      removeBtn.click();
      expect(removeUserFn).to.have.callCount(1);
    });
  });
  describe('_addUser', async () => {
    const eventListeners = {add: function() {}, remove: function() {}};
    let sandbox;
    let element;
    /** @type {import('sinon').SinonStubbedInstance<DefaultApi>} */
    let client;

    beforeEach(async () => {
      sandbox = sinon.createSandbox();
      /** @type {import('sinon').SinonStubbedInstance<DefaultApi>} */
      client = sandbox.createStubInstance(DefaultApi);
      sandbox.stub(eventListeners, 'add');
      sandbox.stub(eventListeners, 'remove');
      window.csOpenApiClient = client;

      element = await fixture(
        html`<chromedash-admin-blink-component-listing
        .id=${1}
        .name=${'foo'}
        .subscriberIds=${[0, 1]}
        .ownerIds=${[0]}
        .index=${0}
        .usersMap=${testUsersMap}
        ?editing=${true}
        @adminRemoveComponentUser=${eventListeners.remove}
        @adminAddComponentUser=${eventListeners.add}
      ></chromedash-admin-blink-component-listing>`,
      );
    });
    afterEach(async () => {
      sandbox.restore();
    });
    it('should generate an alert if nothing is selected', async () => {
      const alertStub = sandbox.stub(window, 'alert');
      const el = element._findSelectedOptionElement();
      // The placeholder is selected.
      expect(el.dataset.placeholder).to.equal('true');
      expect(alertStub).to.have.callCount(0);
      element._addUser();
      expect(alertStub).to.have.callCount(1);
    });
    it('should do nothing for a user already subscribed', async () => {
      const alertStub = sandbox.stub(window, 'alert');
      // Must select user currently a subscriber.
      element._getOptionsElement().options[1].selected = true;
      client.addUserToComponent.resolves({});
      element._addUser();
      // Should timeout
      expect(oneEvent(element, 'adminAddComponentUser')).to.throw;
      expect(alertStub).to.have.callCount(0);
      sandbox.assert.callCount(eventListeners.add, 0);
      sandbox.assert.callCount(eventListeners.remove, 0);
    });
    it('should make successful adminAddComponentUser event if addUserToComponent OK', async () => {
      const alertStub = sandbox.stub(window, 'alert');
      // Must select user not currently a subscriber.
      element._getOptionsElement().options[5].selected = true;
      client.addUserToComponent.resolves({});
      element._addUser();
      const ev = await oneEvent(element, 'adminAddComponentUser');
      expect(ev).to.exist;
      expect(alertStub).to.have.callCount(0);
      sandbox.assert.callCount(eventListeners.add, 1);
      sandbox.assert.callCount(eventListeners.remove, 0);
    });
  });
  describe('_removeUser', async () => {
    const eventListeners = {add: function() {}, remove: function() {}};
    let sandbox;
    let element;
    /** @type {import('sinon').SinonStubbedInstance<DefaultApi>} */
    let client;

    beforeEach(async () => {
      sandbox = sinon.createSandbox();
      client = sandbox.createStubInstance(DefaultApi);
      sandbox.stub(eventListeners, 'add');
      sandbox.stub(eventListeners, 'remove');
      window.csOpenApiClient = client;

      element = await fixture(
        html`<chromedash-admin-blink-component-listing
        .id=${1}
        .name=${'foo'}
        .subscriberIds=${[0, 1]}
        .ownerIds=${[0]}
        .index=${0}
        .usersMap=${testUsersMap}
        ?editing=${true}
        @adminRemoveComponentUser=${eventListeners.remove}
        @adminAddComponentUser=${eventListeners.add}
      ></chromedash-admin-blink-component-listing>`,
      );
    });
    afterEach(async () => {
      sandbox.restore();
    });
    it('should generate an alert if nothing is selected', async () => {
      const alertStub = sandbox.stub(window, 'alert');
      const el = element._findSelectedOptionElement();
      // The placeholder is selected.
      expect(el.dataset.placeholder).to.equal('true');
      expect(alertStub).to.have.callCount(0);
      element._removeUser();
      expect(alertStub).to.have.callCount(1);
    });
    it('should do nothing for a user not already subscribed', async () => {
      const alertStub = sandbox.stub(window, 'alert');
      // Must select user currently a subscriber.
      element._getOptionsElement().options[5].selected = true;
      client.removeUserFromComponent.resolves({});
      element._removeUser();
      // Should timeout
      expect(oneEvent(element, 'adminRemoveComponentUser')).to.throw;
      expect(alertStub).to.have.callCount(0);
      sandbox.assert.callCount(eventListeners.add, 0);
      sandbox.assert.callCount(eventListeners.remove, 0);
    });
    // eslint-disable-next-line max-len
    it('should make successful adminRemoveComponentUser event if removeUserFromComponent OK', async () => {
      const alertStub = sandbox.stub(window, 'alert');
      // Must select user is currently a subscriber.
      element._getOptionsElement().options[1].selected = true;
      client.removeUserFromComponent.resolves({});
      element._removeUser();
      const ev = await oneEvent(element, 'adminRemoveComponentUser');
      expect(ev).to.exist;
      expect(alertStub).to.have.callCount(0);
      sandbox.assert.callCount(eventListeners.add, 0);
      sandbox.assert.callCount(eventListeners.remove, 1);
    });
  });
});
