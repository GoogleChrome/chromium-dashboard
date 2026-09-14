/**
 * Copyright 2025 Google LLC
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
import {checkWptDescriptionLink, FieldValueGetter} from './form-field-specs.js';

function makeGetFieldValue(values: Record<string, unknown>): FieldValueGetter {
  const getFieldValue = (fieldName: string) => values[fieldName];
  return getFieldValue as unknown as FieldValueGetter;
}

describe('checkWptDescriptionLink', () => {
  it('returns nothing when wpt is not checked', () => {
    const getFieldValue = makeGetFieldValue({wpt: false, wpt_descr: ''});
    assert.isUndefined(checkWptDescriptionLink(getFieldValue));
  });

  it('returns an error when wpt is checked and there is no link', () => {
    const getFieldValue = makeGetFieldValue({wpt: true, wpt_descr: ''});
    const result = checkWptDescriptionLink(getFieldValue);
    assert.isDefined(result?.error);
  });

  it('returns an error when the description has text but no link', () => {
    const getFieldValue = makeGetFieldValue({
      wpt: true,
      wpt_descr: 'Fully covered by existing tests.',
    });
    const result = checkWptDescriptionLink(getFieldValue);
    assert.isDefined(result?.error);
  });

  it('returns a warning when there is a link, but not to wpt.fyi', () => {
    const getFieldValue = makeGetFieldValue({
      wpt: true,
      wpt_descr:
        'Tests at https://github.com/web-platform-tests/wpt/tree/master/foo',
    });
    const result = checkWptDescriptionLink(getFieldValue);
    assert.isUndefined(result?.error);
    assert.isDefined(result?.warning);
  });

  it('returns nothing when there is a wpt.fyi link', () => {
    const getFieldValue = makeGetFieldValue({
      wpt: true,
      wpt_descr: 'See https://wpt.fyi/results/css/css-foo',
    });
    assert.isUndefined(checkWptDescriptionLink(getFieldValue));
  });

  it('handles a null description', () => {
    const getFieldValue = makeGetFieldValue({wpt: true, wpt_descr: null});
    const result = checkWptDescriptionLink(getFieldValue);
    assert.isDefined(result?.error);
  });
});
