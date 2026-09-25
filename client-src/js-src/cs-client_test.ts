/**
 * Copyright 2026 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import {assert} from '@open-wc/testing';
import sinon from 'sinon';
import {ChromeStatusClient} from './cs-client.js';
import {
  SummarySuggestionPatchRequest,
  SummarySuggestionPatchRequestStatusEnum,
  SummarySuggestionResponse,
} from 'chromestatus-openapi';

describe('ChromeStatusClient - Summary Suggestions API', () => {
  let sandbox: sinon.SinonSandbox;
  let client: ChromeStatusClient;

  beforeEach(() => {
    sandbox = sinon.createSandbox();
    client = new ChromeStatusClient('test_token', 9999999999);
  });

  afterEach(() => {
    sandbox.restore();
  });

  describe('getSummarySuggestion', () => {
    it('calls doGet with the expected path', async () => {
      const mockResponse: SummarySuggestionResponse = {
        suggestion: {
          feature_id: 123,
          status: 'PENDING',
          suggested_summary: 'Test summary',
          suggested_doc_links: [],
          version_token: 1,
          created: new Date(),
          updated: new Date(),
        },
        progress_steps: [],
      };
      const doGetStub = sandbox.stub(client, 'doGet').resolves(mockResponse);

      const result = await client.getSummarySuggestion(123);

      assert.deepEqual(result, mockResponse);
      assert.isTrue(doGetStub.calledOnceWith('/summary-suggestions/123'));
    });

    it('rejects on invalid featureId with descriptive error context', async () => {
      const invalidIds = [0, -1, -100, 1.5, NaN];
      for (const id of invalidIds) {
        try {
          await client.getSummarySuggestion(id);
          assert.fail(`Should have thrown for featureId: ${id}`);
        } catch (err) {
          const error = err as Error;
          assert.include(error.message, 'Invalid featureId');
          assert.include(error.message, String(id));
        }
      }
    });
  });

  describe('triggerSummaryGeneration', () => {
    it('calls doPost with expected path and payload', async () => {
      const mockResponse = {message: 'Task enqueued'};
      const doPostStub = sandbox.stub(client, 'doPost').resolves(mockResponse);

      const result = await client.triggerSummaryGeneration(456, true);

      assert.deepEqual(result, mockResponse);
      assert.isTrue(
        doPostStub.calledOnceWith('/summary-suggestions/456', {force: true})
      );
    });

    it('defaults force parameter to false', async () => {
      const mockResponse = {message: 'Task enqueued'};
      const doPostStub = sandbox.stub(client, 'doPost').resolves(mockResponse);

      await client.triggerSummaryGeneration(456);

      assert.isTrue(
        doPostStub.calledOnceWith('/summary-suggestions/456', {force: false})
      );
    });

    it('rejects on invalid featureId with descriptive error context', async () => {
      try {
        await client.triggerSummaryGeneration(0);
        assert.fail('Should have thrown for featureId 0');
      } catch (err) {
        const error = err as Error;
        assert.include(error.message, 'Invalid featureId');
        assert.include(error.message, '0');
      }
    });
  });

  describe('updateSummarySuggestion', () => {
    it('calls doPatch with expected path and patch request payload', async () => {
      const patchPayload: SummarySuggestionPatchRequest = {
        status: SummarySuggestionPatchRequestStatusEnum.APPLIED,
        suggested_summary: 'Edited summary text',
        version_token: 42,
      };
      const mockResponse: SummarySuggestionResponse = {
        suggestion: {
          feature_id: 789,
          status: 'APPLIED',
          suggested_summary: 'Edited summary text',
          suggested_doc_links: [],
          version_token: 43,
          created: new Date(),
          updated: new Date(),
        },
        progress_steps: [],
      };
      const doPatchStub = sandbox
        .stub(client, 'doPatch')
        .resolves(mockResponse);

      const result = await client.updateSummarySuggestion(789, patchPayload);

      assert.deepEqual(result, mockResponse);
      assert.isTrue(
        doPatchStub.calledOnceWith('/summary-suggestions/789', patchPayload)
      );
    });

    it('rejects on invalid featureId with descriptive error context', async () => {
      try {
        await client.updateSummarySuggestion(-5, {
          status: SummarySuggestionPatchRequestStatusEnum.REJECTED,
          version_token: 1,
        });
        assert.fail('Should have thrown for featureId -5');
      } catch (err) {
        const error = err as Error;
        assert.include(error.message, 'Invalid featureId');
        assert.include(error.message, '-5');
      }
    });
  });
});
