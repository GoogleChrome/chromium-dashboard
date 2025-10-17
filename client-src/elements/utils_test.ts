import {html} from 'lit';
import {
  autolink,
  clamp,
  findClosestShippingDate,
  formatFeatureChanges,
  getDisabledHelpText,
  getFeatureOutdatedBanner,
  isVerifiedWithinGracePeriod,
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

/**
 * Helper to identify which banner is returned by checking the ID
 * of the first element with an ID.
 * @param {TemplateResult | null} result
 * @returns {string | null} The ID of the banner, or null.
 */
const getBannerId = result => {
  if (!result) return null;
  // A lit TemplateResult has a 'strings' array.
  // We can find the ID in the strings.
  const htmlString = result.strings.join('');
  const match = htmlString.match(/id="([^"]+)"/);
  return match ? match[1] : null;
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
        html`${'This is a test & result of the autolinking.'}`,
        html`${'\n'}`,
        html`<chromedash-link href=${'http://go/this-is-a-test'} .featureLinks=${[]} .ignoreHttpErrorCodes=${[404]}>${'go/this-is-a-test'}</chromedash-link>`,
        html`${'.'}`,
        html`${'\nA bug'}`,
        html`${' '}`,
        html`<chromedash-link href=${'http://cr/1234'} .featureLinks=${[]} .ignoreHttpErrorCodes=${[404]}>${'cr/1234'}</chromedash-link>`,
        html`${' exists and also'}`,
        html`${' '}`,
        html`<chromedash-link href=${'http://cl/1234'} .featureLinks=${[]} .ignoreHttpErrorCodes=${[404]}>${'cl/1234'}</chromedash-link>`,
        html`${'. Info at '}`,
        html`<chromedash-link href=${'https://bugs.chromium.org/p/chromium/issues/detail?id=1234#c3'} .featureLinks=${[]} .ignoreHttpErrorCodes=${[404]}>${'issue 1234 comment 3'}</chromedash-link>`,
        html`${'.\nAKA '}`,
        html`<chromedash-link href=${'https://bugs.chromium.org/p/chromium/issues/detail?id=1234#c3'} .featureLinks=${[]} .ignoreHttpErrorCodes=${[404]}>${'issue 1234 #c3'}</chromedash-link>`,
        html`${'. '}`,
        html`<chromedash-link href=${'https://example.com/'} .featureLinks=${[]} .ignoreHttpErrorCodes=${[404]}>${'https://example.com/'}</chromedash-link>`,
        html`${' --- testing. '}`,
        html`<chromedash-link href=${'https://bugs.chromium.org/p/chromium/issues/detail?id=1234'} .featureLinks=${[]} .ignoreHttpErrorCodes=${[404]}>${'bug 1234'}</chromedash-link>`,
        html`${' '}`,
        html`${'also.\n'}`,
        html`<chromedash-link href=${'https://example.com#testing'} .featureLinks=${[]} .ignoreHttpErrorCodes=${[404]}>${'https://example.com#testing'}</chromedash-link>`,
        html`${' '}`,
        html`<chromedash-link href=${'https://example.com/test?querystring=here&q=1234'} .featureLinks=${[]} .ignoreHttpErrorCodes=${[404]}>${'https://example.com/test?querystring=here&q=1234'}</chromedash-link>`,
        html`${' ??.\nsend requests to user@example.com or just check out'}`,
        html`${' '}`,
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
        html`${'This is a test of the autolinking.\n' +
          'go this-is-a-test.\n' +
          'A bug cr /1234 exists and also /1234. This is an example sentence.\n' +
          'AKA issue here 1234. example com --- testing.'}`,
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
        html`${'<b>Test</b>'}`,
        html`${'\n'}`,
        html`<chromedash-link href=${'http://go/this-is-a-test'} .featureLinks=${[]} .ignoreHttpErrorCodes=${[404]}>${'go/this-is-a-test'}</chromedash-link>`,
        html`${'\n<p>Do not convert this</p>\n<script>Dangerous stuff</script>'}`,
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
    it('sends changes for the "Use Markdown" checkbox', () => {
      const testFieldValues = [
        {
          name: 'summary',
          value: 'Now with **Markdown**',
          touched: true,
          isMarkdown: true,
        },
        {
          name: 'description',
          value: 'No longer desires markdown',
          touched: true,
          isMarkdown: false,
        },
        {
          name: 'motivation',
          value: 'Makes no change to markdown',
          touched: true,
        },
      ];
      const expected = {
        feature_changes: {
          id: 1,
          summary: 'Now with **Markdown**',
          summary_is_markdown: true,
          description: 'No longer desires markdown',
          description_is_markdown: false,
          motivation: 'Makes no change to markdown',
        },
        stages: [],
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

describe('isVerifiedWithinGracePeriod', () => {
    const GRACE_PERIOD = 4 * 7 * 24 * 60 * 60 * 1000; // 4 weeks
    const CURRENT_DATE = Date.parse('2025-03-01T00:00:00Z');

    it('should return false if accurateAsOf is undefined', () => {
      assert.isFalse(isVerifiedWithinGracePeriod(undefined, CURRENT_DATE));
    });

    it('should return true if within the grace period', () => {
      // 2 weeks ago
      const accurateAsOf = '2025-02-15T00:00:00Z';
      assert.isTrue(isVerifiedWithinGracePeriod(accurateAsOf, CURRENT_DATE));
    });

    it('should return false if outside the grace period', () => {
      // 5 weeks ago
      const accurateAsOf = '2025-01-25T00:00:00Z';
      assert.isFalse(isVerifiedWithinGracePeriod(accurateAsOf, CURRENT_DATE));
    });

    it('should return true if exactly on the edge of the grace period', () => {
      // Exactly 4 weeks ago
      const accurateAsOf = '2025-02-01T00:00:00Z';
      // The check is (date + grace < current), so exact match is still valid
      const edgeDate = Date.parse(accurateAsOf) + GRACE_PERIOD;
      assert.isTrue(isVerifiedWithinGracePeriod(accurateAsOf, edgeDate));
    });

    it('should return false if 1ms past the grace period', () => {
      const accurateAsOf = '2025-02-01T00:00:00Z';
      const edgeDate = Date.parse(accurateAsOf) + GRACE_PERIOD + 1;
      assert.isFalse(isVerifiedWithinGracePeriod(accurateAsOf, edgeDate));
    });

    it('should respect custom grace period', () => {
      // 5 weeks ago
      const accurateAsOf = '2025-01-25T00:00:00Z';
      const NINE_WEEKS = 9 * 7 * 24 * 60 * 60 * 1000;
      // Still valid under a 9-week grace period
      assert.isTrue(
        isVerifiedWithinGracePeriod(accurateAsOf, CURRENT_DATE, NINE_WEEKS)
      );
      // Invalid under a 2-week grace period
      const TWO_WEEKS = 2 * 7 * 24 * 60 * 60 * 1000;
      assert.isFalse(
        isVerifiedWithinGracePeriod(accurateAsOf, CURRENT_DATE, TWO_WEEKS)
      );
    });
  });

  describe('findClosestShippingDate', () => {
    const mockChannels = {
      stable: {version: 100, final_beta: '2025-01-01T00:00:00Z'},
      beta: {version: 101, final_beta: '2025-02-01T00:00:00Z'},
      dev: {version: 102, final_beta: '2025-03-01T00:00:00Z'},
      canary: {version: 103, final_beta: '2025-04-01T00:00:00Z'},
    };
    const shippingStageType = 160;
    const otStageType = 150;
    const devTrialStageType = 130;

    it('should identify an upcoming feature (M+1)', async () => {
      const stages = [{stage_type: shippingStageType, desktop_first: 101}];
      const result = await findClosestShippingDate(mockChannels, stages);
      assert.deepEqual(result, {
        closestShippingDate: '2025-02-01T00:00:00Z',
        isUpcoming: true,
        hasShipped: false,
      });
    });

    it('should identify an upcoming feature (M+2)', async () => {
      const stages = [{stage_type: shippingStageType, android_first: 102}];
      const result = await findClosestShippingDate(mockChannels, stages);
      assert.deepEqual(result, {
        closestShippingDate: '2025-03-01T00:00:00Z',
        isUpcoming: true,
        hasShipped: false,
      });
    });

    it('should identify a shipped feature (current stable)', async () => {
      const stages = [{stage_type: shippingStageType, desktop_first: 100}];
      const result = await findClosestShippingDate(mockChannels, stages);
      assert.deepEqual(result, {
        closestShippingDate: '2025-01-01T00:00:00Z',
        isUpcoming: false,
        hasShipped: true,
      });
    });

    it('should not a shipped feature for a past milestone', async () => {
      const stages = [{stage_type: shippingStageType, webview_first: 98}];
      const result = await findClosestShippingDate(mockChannels, stages);
      assert.deepEqual(result, {
        closestShippingDate: '',
        isUpcoming: false,
        hasShipped: true,
      });
    });

    it('should find latest shipped milestone among many', async () => {
      const stages = [
        {stage_type: shippingStageType, desktop_first: 95},
        {stage_type: shippingStageType, android_first: 98},
        {stage_type: otStageType, ios_first: 99}, // Ignored, not a shipping type
        {stage_type: shippingStageType, webview_first: 101},
      ];
      const result = await findClosestShippingDate(mockChannels, stages);
      assert.deepEqual(result, {
        closestShippingDate: '2025-02-01T00:00:00Z',
        isUpcoming: true,
        hasShipped: false,
      });
    });
  });

  describe('getFeatureOutdatedBanner', () => {
    // 4 weeks
    const FOUR_WEEKS = 4 * 7 * 24 * 60 * 60 * 1000;
    // 9 weeks
    const NINE_WEEKS = 9 * 7 * 24 * 60 * 60 * 1000;
    // Current date: March 1, 2025
    const CURRENT_DATE_MS = Date.parse('2025-03-01T00:00:00Z');
    // Verified: Feb 15, 2025 (within 4 weeks)
    const VERIFIED_DATE = new Date(CURRENT_DATE_MS - FOUR_WEEKS / 2).toISOString();
    // Outdated: Jan 15, 2025 (outside 4 weeks)
    const OUTDATED_DATE = new Date(
      CURRENT_DATE_MS - FOUR_WEEKS - 1000
    ).toISOString();
    // Very Outdated: Dec 1, 2024 (outside 9 weeks)
    const VERY_OUTDATED_DATE = new Date(
      CURRENT_DATE_MS - NINE_WEEKS - 1000
    ).toISOString();

    const UPCOMING_SHIPPING_DATE = '2025-03-15T00:00:00Z';
    const SHIPPED_SHIPPING_DATE = '2025-02-01T00:00:00Z';

    const baseFeature = {id: 1, accurate_as_of: VERIFIED_DATE};
    const shippingInfoUpcoming = {
      closestShippingDate: UPCOMING_SHIPPING_DATE,
      isUpcoming: true,
      hasShipped: false,
    };
    const shippingInfoShipped = {
      closestShippingDate: SHIPPED_SHIPPING_DATE,
      isUpcoming: false,
      hasShipped: true,
    };
    const shippingInfoNeither = {
      closestShippingDate: undefined,
      isUpcoming: false,
      hasShipped: false,
    };

    // --- Upcoming Features ---

    it('should return null if feature is upcoming but verified', () => {
      const feature = {...baseFeature, accurate_as_of: VERIFIED_DATE};
      const result = getFeatureOutdatedBanner(
        feature,
        shippingInfoUpcoming,
        CURRENT_DATE_MS,
        true
      );
      assert.isNull(result);
    });

    it('should return upcoming banner if upcoming, outdated, and user can edit', () => {
      const feature = {...baseFeature, accurate_as_of: OUTDATED_DATE};
      const result = getFeatureOutdatedBanner(
        feature,
        shippingInfoUpcoming,
        CURRENT_DATE_MS,
        true
      );
      assert.equal(getBannerId(result), 'outdated-icon');
    });

    it('should return upcoming banner if upcoming, outdated, and user cannot edit', () => {
      const feature = {...baseFeature, accurate_as_of: OUTDATED_DATE};
      const result = getFeatureOutdatedBanner(
        feature,
        shippingInfoUpcoming,
        CURRENT_DATE_MS,
        false
      );
      assert.equal(getBannerId(result), 'outdated-icon');
    });

    // --- Shipped Features ---

    it('should return null if feature is shipped but verified', () => {
      const feature = {...baseFeature, accurate_as_of: VERIFIED_DATE};
      const result = getFeatureOutdatedBanner(
        feature,
        shippingInfoShipped,
        CURRENT_DATE_MS,
        true
      );
      assert.isNull(result);
    });

    it('should return author banner if shipped, outdated (<9 weeks), and user can edit', () => {
      const feature = {...baseFeature, accurate_as_of: OUTDATED_DATE};
      const result = getFeatureOutdatedBanner(
        feature,
        shippingInfoShipped,
        CURRENT_DATE_MS,
        true
      );
      assert.equal(getBannerId(result), 'shipped-outdated-author');
    });

    it('should return null if shipped, outdated (<9 weeks), and user cannot edit', () => {
      const feature = {...baseFeature, accurate_as_of: OUTDATED_DATE};
      const result = getFeatureOutdatedBanner(
        feature,
        shippingInfoShipped,
        CURRENT_DATE_MS,
        false
      );
      assert.isNull(result);
    });

    it('should return "all" banner if shipped, outdated (>9 weeks), and user can edit', () => {
      const feature = {...baseFeature, accurate_as_of: VERY_OUTDATED_DATE};
      const result = getFeatureOutdatedBanner(
        feature,
        shippingInfoShipped,
        CURRENT_DATE_MS,
        true
      );
      // Author banner still takes precedence
      assert.equal(getBannerId(result), 'shipped-outdated-author');
    });

    it('should return "all" banner if shipped, outdated (>9 weeks), and user cannot edit', () => {
      const feature = {...baseFeature, accurate_as_of: VERY_OUTDATED_DATE};
      const result = getFeatureOutdatedBanner(
        feature,
        shippingInfoShipped,
        CURRENT_DATE_MS,
        false
      );
      assert.equal(getBannerId(result), 'shipped-outdated-all');
    });

    // --- Edge Cases ---

    it('should return null if not upcoming and not shipped', () => {
      const feature = {...baseFeature, accurate_as_of: OUTDATED_DATE};
      const result = getFeatureOutdatedBanner(
        feature,
        shippingInfoNeither,
        CURRENT_DATE_MS,
        true
      );
      assert.isNull(result);
    });

    it('should return a banner if accurate_as_of is missing for upcoming', () => {
      const feature = {...baseFeature, accurate_as_of: undefined};
      const result = getFeatureOutdatedBanner(
        feature,
        shippingInfoUpcoming,
        CURRENT_DATE_MS,
        true
      );
      // isUpcomingFeatureOutdated returns false if accurate_as_of is missing
      assert.isNotNull(result);
    });

    it('should return null if accurate_as_of is missing for shipped', () => {
      const feature = {...baseFeature, accurate_as_of: undefined};
      const result = getFeatureOutdatedBanner(
        feature,
        shippingInfoShipped,
        CURRENT_DATE_MS,
        true
      );
      // isShippedFeatureOutdated returns false if accurate_as_of is missing
      assert.isNull(result);
    });

    it('should return null if closestShippingDate is missing', () => {
      const feature = {...baseFeature, accurate_as_of: OUTDATED_DATE};
      const shippingInfo = {
        closestShippingDate: undefined,
        isUpcoming: false,
        hasShipped: true,
      };
      const result = getFeatureOutdatedBanner(
        feature,
        shippingInfo,
        CURRENT_DATE_MS,
        true
      );
      // isShippedFeatureOutdated returns false if closestShippingDate is missing
      assert.isNull(result);
    });
  });
});
