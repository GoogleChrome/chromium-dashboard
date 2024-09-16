import {html} from 'lit';
import {
  autolink,
  clamp,
  formatFeatureChanges,
  getDisabledHelpText,
} from './utils';
import {assert} from '@open-wc/testing';
import {OT_SETUP_STATUS_OPTIONS} from './form-field-enums';

const compareAutolinkResult = (result, expected) => {
  assert.equal(result.length, expected.length);
  for (let i = 0; i < result.length; i++) {
    if (typeof result[i] === 'string') {
      assert.equal(result[i].replaceAll(/\s{2,}/g, ' '), expected[i]);
    } else {
      assert.deepEqual(result[i], expected[i]);
    }
  }
};

// prettier-ignore
describe('utils', () => {
  describe('autolink', () => {
    it('creates anchor tags for links', () => {
      const before = `This is a test & result of the autolinking.
go/this-is-a-test.
A bug cr/1234 exists and also cl/1234. Info at issue 1234 comment 3.
AKA issue 1234 #c3. https://example.com/ --- testing. bug 1234 also.
https://example.com#testing https://example.com/test?querystring=here&q=1234 ??.
send requests to user@example.com or just check out request.net`;
      const expected = [
        'This is a test & result of the autolinking.',
        '\n',
        html`<chromedash-link href=${'http://go/this-is-a-test'} .featureLinks=${[]} .ignoreHttpErrorCodes=${[404]}>${'go/this-is-a-test'}</chromedash-link>`,
        '.',
        '\nA bug',
        ' ',
        html`<chromedash-link href=${'http://cr/1234'} .featureLinks=${[]} .ignoreHttpErrorCodes=${[404]}>${'cr/1234'}</chromedash-link>`,
        ' exists and also',
        ' ',
        html`<chromedash-link href=${'http://cl/1234'} .featureLinks=${[]} .ignoreHttpErrorCodes=${[404]}>${'cl/1234'}</chromedash-link>`,
        '. Info at ',
        html`<chromedash-link href=${'https://bugs.chromium.org/p/chromium/issues/detail?id=1234#c3'} .featureLinks=${[]} .ignoreHttpErrorCodes=${[404]}>${'issue 1234 comment 3'}</chromedash-link>`,
        '.\nAKA ',
        html`<chromedash-link href=${'https://bugs.chromium.org/p/chromium/issues/detail?id=1234#c3'} .featureLinks=${[]} .ignoreHttpErrorCodes=${[404]}>${'issue 1234 #c3'}</chromedash-link>`,
        '. ',
        html`<chromedash-link href=${'https://example.com/'} .featureLinks=${[]} .ignoreHttpErrorCodes=${[404]}>${'https://example.com/'}</chromedash-link>`,
        ' --- testing. ',
        html`<chromedash-link href=${'https://bugs.chromium.org/p/chromium/issues/detail?id=1234'} .featureLinks=${[]} .ignoreHttpErrorCodes=${[404]}>${'bug 1234'}</chromedash-link>`,
        ' ',
        'also.\n',
        html`<chromedash-link href=${'https://example.com#testing'} .featureLinks=${[]} .ignoreHttpErrorCodes=${[404]}>${'https://example.com#testing'}</chromedash-link>`,
        ' ',
        html`<chromedash-link href=${'https://example.com/test?querystring=here&q=1234'} .featureLinks=${[]} .ignoreHttpErrorCodes=${[404]}>${'https://example.com/test?querystring=here&q=1234'}</chromedash-link>`,
        ' ??.\nsend requests to user@example.com or just check out',
        ' ',
        html`<chromedash-link href=${'https://request.net'} .featureLinks=${[]} .ignoreHttpErrorCodes=${[404]}>${'request.net'}</chromedash-link>`,
      ];

      const result = autolink(before);
      compareAutolinkResult(result, expected);
    });

    it('does not change text with no links', () => {
      const before = `This is a test of the autolinking.
go this-is-a-test.
A bug cr /1234 exists and also /1234. This is an example sentence.
AKA issue here 1234. example com --- testing.`;
      const expected = [
        'This is a test of the autolinking.\n' +
          'go this-is-a-test.\n' +
          'A bug cr /1234 exists and also /1234. This is an example sentence.\n' +
          'AKA issue here 1234. example com --- testing.',
      ];

      const result = autolink(before);
      compareAutolinkResult(result, expected);
    });

    it('does not convert any other tags to html', () => {
      const before = `<b>Test</b>
go/this-is-a-test
<p>Do not convert this</p>
<script>Dangerous stuff</script>`;
      const expected = [
        '<b>Test</b>',
        '\n',
        html`<chromedash-link href=${'http://go/this-is-a-test'} .featureLinks=${[]} .ignoreHttpErrorCodes=${[404]}>${'go/this-is-a-test'}</chromedash-link>`,
        '\n<p>Do not convert this</p>\n<script>Dangerous stuff</script>',
      ];

      const result = autolink(before);
      compareAutolinkResult(result, expected);
    });
  });

  describe('clamp', () => {
    it('returns val when in bounds', () => {
      assert.equal(10, clamp(10, 1, 100));
    });
    it('returns lowerBound when val is equal or below lowerBound', () => {
      assert.equal(1, clamp(1, 1, 100));
      assert.equal(1, clamp(0, 1, 100));
    });
    it('returns upperBound when val is equal or above upperBound', () => {
      assert.equal(100, clamp(100, 1, 100));
      assert.equal(100, clamp(101, 1, 100));
    });
  });

  describe('formatFeatureChanges', () => {
    const featureId = 1;
    it('ignores untouched fields', () => {
      // No field should be marked as 'touched'.
      const testFieldValues = [
        {
          name: 'example_field',
          value: '123',
          touched: false,
          stageId: undefined,
          implicitValue: undefined,
        },
      ];
      const expected = {
        feature_changes: {id: 1},
        stages: [],
        has_changes: false,
      };
      assert.deepEqual(formatFeatureChanges(testFieldValues, featureId), expected);
    });
    it('detects feature changes', () => {
      const testFieldValues = [
        {
          name: 'example_field',
          value: '123',
          touched: true,
          stageId: undefined,
          implicitValue: undefined,
        },
      ];
      const expected = {
        feature_changes: {
          id: 1,
          example_field: '123',
        },
        stages: [],
        has_changes: true,
      };
      assert.deepEqual(formatFeatureChanges(testFieldValues, featureId), expected);
    });
    it('detects stage changes', () => {
      const testFieldValues = [
        {
          name: 'example_field',
          value: '123',
          touched: true,
          stageId: 1, // Field is now associated with a stage.
          implicitValue: undefined,
        },
      ];
      const expected = {
        feature_changes: {id: 1},
        stages: [
          {
            id: 1,
            example_field: {
              form_field_name: 'example_field',
              value: '123',
            },
          },
        ],
        has_changes: true,
      };
      assert.deepEqual(formatFeatureChanges(testFieldValues, featureId), expected);
    });
    it('handles implicit values', () => {
      const testFieldValues = [
        {
          name: 'implicit_value_field',
          value: true,
          touched: true,
          stageId: undefined,
          implicitValue: 123,
        },
      ];
      const expected = {
        feature_changes: {
          id: 1,
          implicit_value_field: 123,
        },
        stages: [],
        has_changes: true,
      };
      assert.deepEqual(formatFeatureChanges(testFieldValues, featureId), expected);
    });
    it('differentiates field database names vs field display names', () => {
      const testFieldValues = [
        {
          name: 'intent_to_ship_url',
          value: 123,
          touched: true,
          stageId: 1,
        },
      ];
      const expected = {
        feature_changes: {
          id: 1,
        },
        stages: [
          {
            id: 1,
            intent_thread_url: {
              form_field_name: 'intent_to_ship_url',
              value: 123,
            },
          },
        ],
        has_changes: true,
      };
      assert.deepEqual(formatFeatureChanges(testFieldValues, featureId), expected);
    });
    it('ignores implicit values when falsey value', () => {
      const testFieldValues = [
        {
          name: 'implicit_value_field',
          value: false, // Value is false, so change should be ignored even if touched.
          touched: true,
          stageId: undefined,
          implicitValue: 123,
        },
      ];
      const expected = {
        feature_changes: {id: 1},
        stages: [],
        has_changes: false,
      };
      assert.deepEqual(formatFeatureChanges(testFieldValues, featureId), expected);
    });
    it('detects changes to multiple entities', () => {
      const testFieldValues = [
        {
          name: 'example_field1',
          value: '123',
          touched: true,
          stageId: undefined,
          implicitValue: undefined,
        },
        {
          name: 'example_field2',
          value: '456',
          touched: true,
          stageId: 1,
          implicitValue: undefined,
        },
        {
          name: 'example_field3',
          value: '789',
          touched: true,
          stageId: 2,
          implicitValue: undefined,
        },
        {
          name: 'example_field4',
          value: 'A value',
          touched: false, // Field should be ignored.
          stageId: 2,
          implicitValue: undefined,
        },
      ];
      const expected = {
        feature_changes: {id: 1, example_field1: '123'},
        stages: [
          {
            id: 1,
            example_field2: {
              form_field_name: 'example_field2',
              value: '456',
            },
          },
          {
            id: 2,
            example_field3: {
              form_field_name: 'example_field3',
              value: '789',
            },
          },
        ],
        has_changes: true,
      };
      assert.deepEqual(formatFeatureChanges(testFieldValues, featureId), expected);
    });
  });

  describe('getDisabledHelpText', () => {
    it('returns disabled help text for OT milestones while automated creation in progress', () => {
      const otStartResult = getDisabledHelpText('ot_milestone_desktop_start',
        {ot_setup_status: OT_SETUP_STATUS_OPTIONS.OT_READY_FOR_CREATION})
      assert.notEqual(otStartResult, '');
      const otEndResult = getDisabledHelpText('ot_milestone_desktop_end',
        {ot_setup_status: OT_SETUP_STATUS_OPTIONS.OT_READY_FOR_CREATION})
      assert.notEqual(otEndResult, '');
    });
      it('returns no disabled help text for OT milestone fields when automated creation not in progress', () => {
        const otStartResult = getDisabledHelpText('ot_milestone_desktop_start', {})
        assert.equal(otStartResult, '');
        const otEndResult = getDisabledHelpText('ot_milestone_desktop_start', {})
        assert.equal(otEndResult, '');
      });
    it('returns an empty string for fields with no conditional disabling', () => {
      const result = getDisabledHelpText('name', {});
      assert.equal(result, '');
    });
  });
});
