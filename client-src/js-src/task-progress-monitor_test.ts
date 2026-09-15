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
import {TaskProgressMonitor} from './task-progress-monitor.js';
import {ChromeStatusHttpError} from './cs-client.js';

interface TestProgressData {
  status: string;
  step?: number;
}

describe('TaskProgressMonitor', () => {
  let sandbox: sinon.SinonSandbox;

  beforeEach(() => {
    sandbox = sinon.createSandbox();
  });

  afterEach(() => {
    sandbox.restore();
  });

  it('resolves when shouldContinue returns false', async () => {
    const fetcherStub = sandbox
      .stub()
      .onFirstCall()
      .resolves({status: 'IN_PROGRESS', step: 1})
      .onSecondCall()
      .resolves({status: 'COMPLETED', step: 2});

    const progressUpdates: TestProgressData[] = [];

    const monitor = new TaskProgressMonitor<TestProgressData>({
      fetcher: fetcherStub,
      shouldContinue: data => data.status === 'IN_PROGRESS',
      onProgress: data => progressUpdates.push(data),
      pollIntervalMs: 10,
    });

    const result = await monitor.run();
    assert.deepEqual(result, {status: 'COMPLETED', step: 2});
    assert.equal(progressUpdates.length, 2);
    assert.equal(progressUpdates[0].step, 1);
    assert.equal(progressUpdates[1].step, 2);
    assert.isTrue(fetcherStub.calledTwice);
  });

  it('tolerates initial 404s and continues polling once available', async () => {
    const fetcherStub = sandbox
      .stub()
      .onFirstCall()
      .rejects(new ChromeStatusHttpError('Not Found', '/test', 'GET', 404))
      .onSecondCall()
      .resolves({status: 'COMPLETED'});

    const monitor = new TaskProgressMonitor<TestProgressData>({
      fetcher: fetcherStub,
      shouldContinue: data => data.status === 'IN_PROGRESS',
      pollIntervalMs: 10,
      maxInitial404Retries: 3,
    });

    const result = await monitor.run();
    assert.deepEqual(result, {status: 'COMPLETED'});
    assert.isTrue(fetcherStub.calledTwice);
  });

  it('throws error when max initial 404 retries are exhausted', async () => {
    const fetcherStub = sandbox
      .stub()
      .rejects(new ChromeStatusHttpError('Not Found', '/test', 'GET', 404));

    const monitor = new TaskProgressMonitor<TestProgressData>({
      fetcher: fetcherStub,
      shouldContinue: () => true,
      pollIntervalMs: 10,
      maxInitial404Retries: 3,
    });

    try {
      await monitor.run();
      assert.fail('Should have thrown error');
    } catch (err) {
      const error = err as Error;
      assert.include(error.message, 'did not start or expired');
      assert.equal(fetcherStub.callCount, 3);
    }
  });

  it('stops monitoring immediately when stop() is called during poll interval', async () => {
    const fetcherStub = sandbox
      .stub()
      .resolves({status: 'IN_PROGRESS', step: 1});

    const monitor = new TaskProgressMonitor<TestProgressData>({
      fetcher: fetcherStub,
      shouldContinue: () => true,
      pollIntervalMs: 5000,
    });

    const runPromise = monitor.run();
    assert.isTrue(monitor.isRunning);

    // Wait for the first fetch to complete and enter the delay
    await new Promise(r => setTimeout(r, 20));
    assert.equal(fetcherStub.callCount, 1);

    // Call stop() while delay is active
    monitor.stop();
    assert.isFalse(monitor.isRunning);

    try {
      await runPromise;
      assert.fail('Should have rejected with AbortError on stop()');
    } catch (err) {
      const error = err as DOMException;
      assert.equal(error.name, 'AbortError');
      assert.include(error.message, 'Task monitoring stopped');
    }

    // Advance real time slightly to ensure no second fetch occurred
    await new Promise(r => setTimeout(r, 50));
    assert.equal(fetcherStub.callCount, 1);
  });

  it('aborts immediately when AbortSignal is triggered', async () => {
    const abortController = new AbortController();
    const fetcherStub = sandbox.stub().resolves({status: 'IN_PROGRESS'});

    const monitor = new TaskProgressMonitor<TestProgressData>({
      fetcher: fetcherStub,
      shouldContinue: () => true,
      pollIntervalMs: 50,
    });

    const runPromise = monitor.run(abortController.signal);
    abortController.abort();

    try {
      await runPromise;
      assert.fail('Should have thrown AbortError');
    } catch (err) {
      const error = err as DOMException;
      assert.equal(error.name, 'AbortError');
    }
  });

  it('throws error when maxDurationMs is exceeded', async () => {
    const clock = sandbox.useFakeTimers();
    try {
      const fetcherStub = sandbox.stub().resolves({status: 'IN_PROGRESS'});

      const monitor = new TaskProgressMonitor<TestProgressData>({
        fetcher: fetcherStub,
        shouldContinue: () => true,
        pollIntervalMs: 1000,
        maxDurationMs: 5000,
      });

      let errorThrown: Error | null = null;
      const runPromise = monitor.run().catch((err: Error) => {
        errorThrown = err;
      });

      // Advance clock past max duration
      await clock.tickAsync(6000);
      await runPromise;

      assert.isNotNull(errorThrown);
      assert.include((errorThrown as unknown as Error).message, 'timed out');
    } finally {
      clock.restore();
    }
  });

  it('propagates non-404 errors immediately', async () => {
    const fetcherStub = sandbox
      .stub()
      .rejects(new Error('Internal Server Error 500'));

    const monitor = new TaskProgressMonitor<TestProgressData>({
      fetcher: fetcherStub,
      shouldContinue: () => true,
      pollIntervalMs: 10,
    });

    try {
      await monitor.run();
      assert.fail('Should have thrown 500 error');
    } catch (err) {
      const error = err as Error;
      assert.equal(error.message, 'Internal Server Error 500');
      assert.isTrue(fetcherStub.calledOnce);
    }
  });
});
