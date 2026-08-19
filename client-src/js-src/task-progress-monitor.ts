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

import {ChromeStatusHttpError} from './cs-client.js';

export interface TaskProgressMonitorOptions<TData> {
  fetcher: (signal?: AbortSignal) => Promise<TData>;
  shouldContinue: (data: TData) => boolean;
  onProgress?: (data: TData) => void;
  pollIntervalMs?: number;
  maxDurationMs?: number;
  maxInitial404Retries?: number;
}

const DEFAULT_POLL_INTERVAL_MS = 2000;
const DEFAULT_MAX_DURATION_MS = 5 * 60 * 1000; // 5 minutes
const DEFAULT_MAX_INITIAL_404_RETRIES = 5;

/**
 * Transport-agnostic asynchronous task progress monitor.
 * Polls status updates until task completion, timeout, abort, or manual stop.
 *
 * @example
 * ```typescript
 * const monitor = new TaskProgressMonitor<MyTaskResponse>({
 *   fetcher: (signal) => apiClient.fetchTaskStatus(taskId, {signal}),
 *   shouldContinue: (resp) => resp.status === 'RUNNING',
 *   onProgress: (resp) => {
 *     console.log('Task progress:', resp.percent);
 *   },
 * });
 * const finalResult = await monitor.run(abortController.signal);
 * ```
 */
export class TaskProgressMonitor<TData> {
  private readonly _fetcher: (signal?: AbortSignal) => Promise<TData>;
  private readonly _shouldContinue: (data: TData) => boolean;
  private readonly _onProgress?: (data: TData) => void;
  private readonly _pollIntervalMs: number;
  private readonly _maxDurationMs: number;
  private readonly _maxInitial404Retries: number;

  private _consecutive404Count = 0;
  private _isRunning = false;
  private _activeTimer: ReturnType<typeof setTimeout> | null = null;
  private _activeReject: ((reason?: unknown) => void) | null = null;

  constructor(options: TaskProgressMonitorOptions<TData>) {
    this._fetcher = options.fetcher;
    this._shouldContinue = options.shouldContinue;
    this._onProgress = options.onProgress;
    this._pollIntervalMs = options.pollIntervalMs ?? DEFAULT_POLL_INTERVAL_MS;
    this._maxDurationMs = options.maxDurationMs ?? DEFAULT_MAX_DURATION_MS;
    this._maxInitial404Retries =
      options.maxInitial404Retries ?? DEFAULT_MAX_INITIAL_404_RETRIES;
  }

  get isRunning(): boolean {
    return this._isRunning;
  }

  /**
   * Runs the progress monitor until completion, timeout, abort signal, or stop.
   */
  async run(signal?: AbortSignal): Promise<TData> {
    if (signal?.aborted) {
      throw new DOMException('Task monitoring was aborted', 'AbortError');
    }

    this._isRunning = true;
    this._consecutive404Count = 0;
    const startTime = Date.now();

    try {
      while (this._isRunning) {
        if (signal?.aborted) {
          throw new DOMException('Task monitoring was aborted', 'AbortError');
        }

        // Hard timeout ceiling to prevent runaway polling if backend workers stall.
        if (Date.now() - startTime > this._maxDurationMs) {
          const timeoutSec = Math.round(this._maxDurationMs / 1000);
          throw new Error(
            `Task execution timed out after ${timeoutSec}s. Please retry.`
          );
        }

        try {
          const data = await this._fetcher(signal);
          this._consecutive404Count = 0;

          if (this._onProgress) {
            this._onProgress(data);
          }

          if (!this._shouldContinue(data)) {
            return data;
          }
        } catch (err) {
          const is404 =
            err instanceof ChromeStatusHttpError && err.status === 404;

          if (is404) {
            // Tolerates up to 5 consecutive 404s (10s window) to accommodate Cloud Task
            // dispatch latency before the worker creates the initial Datastore entity.
            this._consecutive404Count++;
            if (this._consecutive404Count >= this._maxInitial404Retries) {
              throw new Error('Task did not start or expired. Please retry.');
            }
          } else {
            // Non-404 errors (e.g. 403, 500) fail fast immediately.
            throw err instanceof Error ? err : new Error(String(err));
          }
        }

        await this._delay(this._pollIntervalMs, signal);
      }

      throw new DOMException('Task monitoring stopped', 'AbortError');
    } finally {
      this._isRunning = false;
      if (this._activeTimer !== null) {
        globalThis.clearTimeout(this._activeTimer);
        this._activeTimer = null;
      }
      this._activeReject = null;
    }
  }

  stop(): void {
    this._isRunning = false;
    if (this._activeTimer !== null) {
      globalThis.clearTimeout(this._activeTimer);
      this._activeTimer = null;
    }
    if (this._activeReject) {
      this._activeReject(
        new DOMException('Task monitoring stopped', 'AbortError')
      );
      this._activeReject = null;
    }
  }

  private _delay(ms: number, signal?: AbortSignal): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this._isRunning || signal?.aborted) {
        return reject(
          new DOMException('Task monitoring was aborted', 'AbortError')
        );
      }

      this._activeReject = reject;
      const timer = globalThis.setTimeout(() => {
        this._activeTimer = null;
        this._activeReject = null;
        if (signal) {
          signal.removeEventListener('abort', onAbort);
        }
        resolve();
      }, ms);
      this._activeTimer = timer;

      const onAbort = () => {
        if (this._activeTimer !== null) {
          globalThis.clearTimeout(this._activeTimer);
          this._activeTimer = null;
        }
        this._activeReject = null;
        reject(new DOMException('Task monitoring was aborted', 'AbortError'));
      };

      if (signal) {
        signal.addEventListener('abort', onAbort, {once: true});
      }
    });
  }
}
