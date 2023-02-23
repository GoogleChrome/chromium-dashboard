import {ContextConsumer} from '@lit-labs/context';
import {html, LitElement} from 'lit';
import {chromestatusOpenApiContext} from '../contexts/openapi-context';
import {assert, expect, fixture} from '@open-wc/testing';
import './chromedash-app';
import '../js-src/cs-client';
import sinon from 'sinon';

describe('chromedash-app', () => {
  beforeEach(async () => {
    window.csClient = new ChromeStatusClient('fake_token', 1);
    sinon.stub(window.csClient, 'getPermissions');
    window.csClient.getPermissions.returns(Promise.resolve(null));
  });
  afterEach(() => {
    window.csClient.getPermissions.restore();
  });
  describe('openapi client', () => {
    it('should be provided to child elements', async () => {
      customElements.define(`fake-chromedash-element-child`, class extends LitElement {
        constructor() {
          super();
          this.consumer = new ContextConsumer(this, chromestatusOpenApiContext, undefined);
        }
      });
      const app = await fixture(html`<chromedash-app></chromedash-app>`);
      app.pageComponent = document.createElement('fake-chromedash-element-child');
      assert.isUndefined(app.pageComponent.consumer.value);
      app.requestUpdate();
      await app.updateComplete;
      // Should no longer be undefined.
      assert.isObject(app.pageComponent.consumer.value);
    });
    describe('xsrfMiddleware', () => {
      it('should add the XSRF token to the request with existing headers', async () => {
        const tokenValidStub = sinon.stub(window.csClient, 'ensureTokenIsValid').resolves();
        const app = await fixture(html`<chromedash-app></chromedash-app>`);
        /** @type {import('chromestatus-openapi').RequestContext} */
        const req = {
          init: {
            headers: {'content-type': ['application/json']},
          },
        };
        /** @type {import('chromestatus-openapi').FetchParams} */
        const params = await app.xsrfMiddleware(req);
        assert.equal(params.init.headers['content-type'][0], 'application/json');
        assert.equal(params.init.headers['X-Xsrf-Token'][0], 'fake_token');
        tokenValidStub.restore();
      });
      it('should add the XSRF token to the request with no existing headers', async () => {
        const tokenValidStub = sinon.stub(window.csClient, 'ensureTokenIsValid').resolves();
        const app = await fixture(html`<chromedash-app></chromedash-app>`);
        /** @type {import('chromestatus-openapi').RequestContext} */
        const req = {
          init: {},
        };
        /** @type {import('chromestatus-openapi').FetchParams} */
        const params = await app.xsrfMiddleware(req);
        assert.equal(params.init.headers['X-Xsrf-Token'][0], 'fake_token');
        tokenValidStub.restore();
      });
    });
    describe('xssiMiddleware', () => {
      it('should remove the prefix and create a new response', async () => {
        const app = await fixture(html`<chromedash-app></chromedash-app>`);
        const textPromise = sinon.promise();
        textPromise.resolve(')]}\'\n{"status": true}');
        /** @type {import('chromestatus-openapi').ResponseContext} */
        const context = {
          response: {
            status: 200,
            statusText: 'OK',
            headers: {'content-type': ['application/json']},
            text: () => textPromise,
          },
        };
        await context.response.text();
        /** @type {Response} */
        const newResponse = await app.xssiMiddleware(context);
        assert.equal(newResponse.headers.get('content-type'), 'application/json');
        const jsonBody = await newResponse.json();
        expect(jsonBody).to.eql({status: true});
        assert.equal(newResponse.status, 200);
        assert.equal(newResponse.statusText, 'OK');
      });
    });
  });
});
