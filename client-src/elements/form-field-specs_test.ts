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
import sinon from 'sinon';
import {ChromeStatusClient} from '../js-src/cs-client.js';
import {STAGE_SPECIFIC_FIELDS} from './form-field-enums.js';
import {
  ALL_FIELDS,
  checkExtensionMilestoneIsValid,
  checkFirstEnterpriseNotice,
  checkWptDescriptionLink,
  FieldValueGetter,
  makeDisplaySpec,
} from './form-field-specs.js';

function makeGetFieldValue(values: Record<string, unknown>): FieldValueGetter {
  const getFieldValue = (fieldName: string) => values[fieldName];
  return getFieldValue as unknown as FieldValueGetter;
}

describe('form-field-specs and enums', () => {
  it('includes intent_to_deprecate_url in STAGE_SPECIFIC_FIELDS', () => {
    assert.isTrue(STAGE_SPECIFIC_FIELDS.has('intent_to_deprecate_url'));
  });

  it('replaces all underscores in makeDisplaySpec fallback label', () => {
    const spec = makeDisplaySpec('some_custom_field_name');
    assert.equal(spec[1], 'Some custom field name');
  });

  it('validates ot_creation milestone ranges using ot_creation field names', () => {
    const getFieldValue = makeGetFieldValue({
      ot_creation__milestone_desktop_first: 130,
      ot_creation__milestone_desktop_last: 125,
    });
    const checkFn = ALL_FIELDS.ot_creation__milestone_desktop_first
      .check as Function;
    const result = checkFn('130', getFieldValue, '');
    assert.isDefined(result?.error);
  });
});

describe('checkFirstEnterpriseNotice', () => {
  let getSpecifiedChannelsStub: sinon.SinonStub;

  beforeEach(() => {
    window.csClient = new ChromeStatusClient('fake_token', 1);
    getSpecifiedChannelsStub = sinon.stub(
      window.csClient,
      'getSpecifiedChannels'
    );
  });

  afterEach(() => {
    getSpecifiedChannelsStub.restore();
  });

  it('warns when initialValue milestone was already released and value is changed', async () => {
    getSpecifiedChannelsStub.withArgs('140', '140').resolves({
      '140': {stable_date: '2099-01-01T00:00:00'},
    });
    getSpecifiedChannelsStub.withArgs('120', '120').resolves({
      '120': {stable_date: '2024-01-01T00:00:00'},
    });

    const result = await checkFirstEnterpriseNotice('140', '120');
    assert.include(
      result?.warning,
      'Feature was already shown in milestone 120'
    );
  });
});

describe('checkExtensionMilestoneIsValid', () => {
  it('returns undefined immediately when value is empty without fetching', async () => {
    const fetchSpy = sinon.spy(window, 'fetch');
    try {
      const result = await checkExtensionMilestoneIsValid('');
      assert.isUndefined(result);
      assert.isFalse(fetchSpy.called);
    } finally {
      fetchSpy.restore();
    }
  });
});

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
