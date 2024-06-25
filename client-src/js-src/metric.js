/**
 * Copyright 2016 Google Inc. All rights reserved.
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

export class Metric {
  static get supportsPerfNow() {
    return performance && performance.now;
  }

  static get supportsPerfMark() {
    return performance && performance.mark;
  }

  /**
   * Returns the duration of the timing metric or -1 if there hasn't been a
   * measurement made.
   * @readonly
   */
  get duration() {
    let duration = this._end - this._start;

    // Use User Timing API results if available, otherwise return
    // performance.now() fallback.
    if (Metric.supportsPerfMark) {
      // Note: this assumes the user has made only one measurement for the given
      // name. Return the first one found.
      const entry = performance.getEntriesByName(this.name)[0];
      if (entry && entry.entryType !== 'measure') {
        duration = entry.duration;
      }
    }

    return duration || -1;
  }

  constructor(name) {
    if (!name) {
      throw Error('Please provide a metric name');
    }

    if (!Metric.supportsPerfMark) {
      console.warn(`Timeline won't be marked for "${name}".`);

      if (!Metric.supportsPerfNow) {
        throw Error('This library cannot be used in this browser.');
      }
    }

    this.name = name;
  }

  /**
   * Prints the metric's duration to the console.
   * @return {Metric} instance of this object.
   */
  log() {
    console.info(this.name, this.duration, 'ms');
    return this;
  }

  /**
   * Prints all the metrics for a given name to the console.
   *
   * @param {string=} name If provided, prints the stats of another metric.
   * @return {Metric} instance of this object.
   */
  logAll(name = this.name) {
    // Use User Timing API results if available, otherwise return
    // performance.now() fallback.
    if (Metric.supportsPerfNow) {
      const items = window.performance.getEntriesByName(name);
      for (let i = 0; i < items.length; ++i) {
        const item = items[i];
        console.info(name, item.duration, 'ms');
      }
    }
    return this;
  }

  /**
   * Call to begin a measurement.
   * @return {Metric} instance of this object.
   */
  start() {
    if (this._start) {
      console.warn('Recording already started.');
      return this;
    }

    this._start = performance.now();

    // Support: developer.mozilla.org/en-US/docs/Web/API/Performance/mark
    if (Metric.supportsPerfMark) {
      performance.mark(`mark_${this.name}_start`);
    }

    return this;
  }

  /**
   * Call to end a measurement.
   * @return {Metric} instance of this object.
   */
  end() {
    if (this._end) {
      console.warn('Recording already stopped.');
      return this;
    }

    this._end = performance.now();

    // Support: developer.mozilla.org/en-US/docs/Web/API/Performance/mark
    if (Metric.supportsPerfMark) {
      const startMark = `mark_${this.name}_start`;
      const endMark = `mark_${this.name}_end`;
      performance.mark(endMark);
      performance.measure(this.name, startMark, endMark);
    }

    return this;
  }

  /**
   * Sends the metric to Google Analytics as a user timing metric.
   *
   * @param {string} category The category of the metric.
   * @param {string} metric Optional name of the metric to record in Analytics.
   *     By default, the metric `name` is used.
   * @param {Number} duration How long the measurement took. The user can
   *     optionally specify another value.
   * @return {Metric} instance of this object.
   */
  sendToAnalytics(category, metric = this.name, duration = this.duration) {
    if (!window.ga) {
      console.warn('Google Analytics has not been loaded');
    } else if (duration >= 0) {
      ga('send', 'timing', category, metric, duration);
    }
    return this;
  }
}
