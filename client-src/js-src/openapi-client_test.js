import {assert, expect} from '@open-wc/testing';
import sinon from 'sinon';
import {ChromeStatusClient} from './cs-client';
import {
  ChromeStatusMiddlewares,
  ChromeStatusOpenApiClient,
} from './openapi-client';

describe('openapi-client', () => {
  beforeEach(async () => {
    window.csClient = new ChromeStatusClient('fake_token', 1);
    sinon.stub(window.csClient, 'getPermissions');
    window.csClient.getPermissions.returns(Promise.resolve(null));
  });
  afterEach(() => {
    window.csClient.getPermissions.restore();
  });
  describe('ChromeStatusOpenApiClient', () => {
    describe('constructor', () => {
      beforeEach(async () => {
        window.csOpenApiClient = new ChromeStatusOpenApiClient();
      });
      it('should have same-origin in the config', async () => {
        assert.equal(
          window.csOpenApiClient.configuration.credentials,
          'same-origin'
        );
      });
      it('should have the middlewares loaded', async () => {
        assert.equal(
          window.csOpenApiClient.middleware[0].pre,
          ChromeStatusMiddlewares.xsrfMiddleware
        );
        assert.equal(
          window.csOpenApiClient.middleware[1].post,
          ChromeStatusMiddlewares.xssiMiddleware
        );
      });
    });
  });
  describe('Middlewares', () => {
    describe('xsrfMiddleware', () => {
      it('should update the XSRF token to the request with existing headers', async () => {
        const tokenValidStub = sinon
          .stub(window.csClient, 'ensureTokenIsValid')
          .resolves();
        /** @type {import('chromestatus-openapi').RequestContext} */
        const req = {
          init: {
            headers: {
              'content-type': ['application/json'],
              'X-Xsrf-Token': 'Wrong-value',
            },
          },
        };
        /** @type {import('chromestatus-openapi').FetchParams} */
        const params = await ChromeStatusMiddlewares.xsrfMiddleware(req);
        assert.equal(
          params.init.headers['content-type'][0],
          'application/json'
        );
        assert.equal(params.init.headers['X-Xsrf-Token'], 'fake_token');
        tokenValidStub.restore();
      });
      it('should not add the XSRF token to the request with no existing header', async () => {
        const tokenValidStub = sinon
          .stub(window.csClient, 'ensureTokenIsValid')
          .resolves();
        /** @type {import('chromestatus-openapi').RequestContext} */
        const req = {
          init: {
            headers: {'content-type': ['application/json']},
          },
        };
        /** @type {import('chromestatus-openapi').FetchParams} */
        const params = await ChromeStatusMiddlewares.xsrfMiddleware(req);
        assert.notExists(params.init.headers['X-Xsrf-Token']);
        tokenValidStub.restore();
      });
    });
    describe('xssiMiddleware', () => {
      it('should remove the prefix and create a new response', async () => {
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
        const newResponse =
          await ChromeStatusMiddlewares.xssiMiddleware(context);
        assert.equal(
          newResponse.headers.get('content-type'),
          'application/json'
        );
        const jsonBody = await newResponse.json();
        expect(jsonBody).to.eql({status: true});
        assert.equal(newResponse.status, 200);
        assert.equal(newResponse.statusText, 'OK');
      });
    });
  });
});
