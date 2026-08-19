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
 * Polls or streams status updates until task completion, timeout, or abort.
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
   * Runs the progress monitor until completion or abort signal.
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

        if (Date.now() - startTime > this._maxDurationMs) {
          throw new Error('Task execution timed out. Please retry.');
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
            this._consecutive404Count++;
            if (this._consecutive404Count >= this._maxInitial404Retries) {
              throw new Error('Task did not start or expired. Please retry.');
            }
          } else {
            throw err instanceof Error ? err : new Error(String(err));
          }
        }

        await this._delay(this._pollIntervalMs, signal);
      }

      throw new DOMException('Task monitoring stopped', 'AbortError');
    } finally {
      this._isRunning = false;
    }
  }

  stop(): void {
    this._isRunning = false;
  }

  private _delay(ms: number, signal?: AbortSignal): Promise<void> {
    return new Promise((resolve, reject) => {
      if (signal?.aborted) {
        return reject(
          new DOMException('Task monitoring was aborted', 'AbortError')
        );
      }

      const timer = window.setTimeout(() => {
        if (signal) {
          signal.removeEventListener('abort', onAbort);
        }
        resolve();
      }, ms);

      const onAbort = () => {
        window.clearTimeout(timer);
        reject(new DOMException('Task monitoring was aborted', 'AbortError'));
      };

      if (signal) {
        signal.addEventListener('abort', onAbort, {once: true});
      }
    });
  }
}
