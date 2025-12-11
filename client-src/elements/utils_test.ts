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
import {Channels, Feature} from '../js-src/cs-client';

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
    const mockChannels: Channels = {
      stable: {
        version: 100,
        earliest_beta: '2025-09-20T00:00:00Z',
        mstone: '125',
        stable_date: '2025-10-20T00:00:00Z',
        latest_beta: '2025-10-10T00:00:00Z',
        final_beta: '2025-01-01T00:00:00Z',
        early_stable: '2025-10-19T00:00:00Z',
        features: {},
      },
      beta: {
        version: 101,
        earliest_beta: '2025-10-20T00:00:00Z',
        mstone: '126',
        stable_date: '2025-11-20T00:00:00Z',
        latest_beta: '2025-11-10T00:00:00Z',
        final_beta: '2025-02-01T00:00:00Z',
        early_stable: '2025-11-19T00:00:00Z',
        features: {},
      },
      dev: {
        version: 102,
        earliest_beta: '2Next-release-TBD',
        mstone: '127',
        stable_date: null,
        latest_beta: null,
        final_beta: '2025-03-01T00:00:00Z',
        early_stable: null,
        features: {},
      },
      canary: {
        version: 103,
        mstone: '128',
        stable_date: null,
        latest_beta: null,
        final_beta: '2025-04-01T00:00:00Z',
        early_stable: null,
        features: {},
      }
    };
    const baseStage = {
      id: 201,
      created: '2025-02-01T00:00:00Z',
      feature_id: 1001,
      stage_type: 160,
      display_name: 'Shipping Stage',
      intent_stage: 2,
      intent_thread_url: 'https://example.com/intent-to-prototype',
      announcement_url: 'https://example.com/prototype-announced',
      origin_trial_id: 'OT_TestFeature_123',
      experiment_goals: 'Gather feedback on API shape and usability.',
      experiment_risks: 'Low risk, API is behind a flag.',
      extensions: [],
      origin_trial_feedback_url: 'https://example.com/ot-feedback',
      ot_action_requested: true,
      ot_activation_date: '2025-11-01T00:00:00Z',
      ot_approval_buganizer_component: 12345,
      ot_approval_buganizer_custom_field_id: 67890,
      ot_approval_criteria_url: 'https://example.com/ot-criteria',
      ot_approval_group_email: 'ot-approvers@example.com',
      ot_chromium_trial_name: 'TestFeatureOriginTrial',
      ot_description: 'An Origin Trial for the Test Feature.',
      ot_display_name: 'Test Feature OT',
      ot_documentation_url: 'https://example.com/ot-docs',
      ot_emails: ['ot-admin@example.com', 'owner1@example.com'],
      ot_feedback_submission_url: 'https://example.com/ot-submit',
      ot_has_third_party_support: false,
      ot_is_critical_trial: false,
      ot_is_deprecation_trial: false,
      ot_owner_email: 'ot-owner@example.com',
      ot_require_approvals: true,
      ot_setup_status: 1,
      ot_request_note: 'Please approve this OT for M124.',
      ot_stage_id: 201,
      ot_use_counter_bucket_number: 5001,
      experiment_extension_reason: 'Need more time for feedback.',
      finch_url: 'https://example.com/finch-rollout',
      rollout_details: 'Rolling out to 1% of users.',
      rollout_milestone: 124,
      rollout_platforms: ['Desktop', 'Android'],
      rollout_stage_plan: 1,
      enterprise_policies: ['TestFeatureEnabled', 'LegacyFeatureDisabled'],
      pm_emails: ['pm@example.com'],
      tl_emails: ['tl@example.com'],
      ux_emails: ['ux@example.com'],
      te_emails: ['te@example.com'],
      desktop_first: 124,
      android_first: 124,
      ios_first: 125,
      webview_first: 124,
      desktop_last: 126,
      android_last: 126,
      ios_last: 127,
      webview_last: 126,
    };
    const shippingStageType = 160;
    const otStageType = 150;
    const entRolloutStageType = 1061;

    it('should identify an upcoming feature (M+1)', async () => {
      const stages = [{...baseStage, stage_type: shippingStageType, desktop_first: 101}];
      const result = await findClosestShippingDate(mockChannels, stages);
      assert.deepEqual(result, {
        closestShippingDate: '2025-02-01T00:00:00Z',
        isUpcoming: true,
        hasShipped: false,
      });
    });

    it('should identify an upcoming feature (M+2)', async () => {
      const stages = [{...baseStage, stage_type: shippingStageType, android_first: 102}];
      const result = await findClosestShippingDate(mockChannels, stages);
      assert.deepEqual(result, {
        closestShippingDate: '2025-03-01T00:00:00Z',
        isUpcoming: true,
        hasShipped: false,
      });
    });

    it('should NOT identify an upcoming feature based solely on OT', async () => {
      const stages = [{...baseStage, stage_type: otStageType, desktop_first: 101}];
      const result = await findClosestShippingDate(mockChannels, stages);
      assert.deepEqual(result, {
        closestShippingDate: '',
        isUpcoming: false,
        hasShipped: true,
      });
    });

    it('should identify an upcoming feature based on Enterprise Rollout', async () => {
      const stages = [{...baseStage, stage_type: entRolloutStageType, desktop_first: 101}];
      const result = await findClosestShippingDate(mockChannels, stages);
      assert.deepEqual(result, {
        closestShippingDate: '2025-02-01T00:00:00Z',
        isUpcoming: true,
        hasShipped: false,
      });
    });

    it('should identify a shipped feature (current stable)', async () => {
      const stages = [{...baseStage, stage_type: shippingStageType, desktop_first: 100}];
      const result = await findClosestShippingDate(mockChannels, stages);
      assert.deepEqual(result, {
        closestShippingDate: '2025-01-01T00:00:00Z',
        isUpcoming: false,
        hasShipped: true,
      });
    });

    it('should identify a shipped feature based on Enterprise Rollout', async () => {
      const stages = [{...baseStage, stage_type: entRolloutStageType, desktop_first: 100}];
      const result = await findClosestShippingDate(mockChannels, stages);
      assert.deepEqual(result, {
        closestShippingDate: '2025-01-01T00:00:00Z',
        isUpcoming: false,
        hasShipped: true,
      });
    });

    it('should not a shipped feature for a past milestone', async () => {
      const stages = [{...baseStage, stage_type: shippingStageType, webview_first: 98}];
      const result = await findClosestShippingDate(mockChannels, stages);
      assert.deepEqual(result, {
        closestShippingDate: '',
        isUpcoming: false,
        hasShipped: true,
      });
    });

    it('should find latest shipped milestone among many', async () => {
      const stages = [
        {...baseStage, stage_type: shippingStageType, desktop_first: 95},
        {...baseStage, stage_type: shippingStageType, android_first: 98},
        {...baseStage, stage_type: otStageType, ios_first: 99}, // Ignored, not a shipping type
        {...baseStage, stage_type: shippingStageType, webview_first: 101},
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

    const baseFeature: Feature = {
      id: 1001,
      created: {
        by: 'creator@example.com',
        when: '2025-01-01T00:00:00Z',
      },
      updated: {
        by: 'updater@example.com',
        when: '2025-10-20T12:00:00Z',
      },
      accurate_as_of: '2025-10-20T12:00:00Z',
      creator_email: 'creator@example.com',
      updater_email: 'updater@example.com',

      owner_emails: ['owner1@example.com', 'owner2@example.com'],
      editor_emails: ['editor1@example.com'],
      cc_emails: ['cc1@example.com', 'cc2@example.com'],
      spec_mentor_emails: ['mentor1@example.com'],
      unlisted: false,
      confidential: false,
      deleted: false,

      editors: ['editor1@example.com'],
      cc_recipients: ['cc1@example.com', 'cc2@example.com'],
      spec_mentors: ['mentor1@example.com'],
      creator: 'creator@example.com',

      name: 'Test Feature',
      summary: 'This is a complete summary for the test feature.',
      markdown_fields: ['summary', 'motivation', 'feature_notes'],
      category: 'Web Components',
      category_int: 1,
      web_feature: 'New Custom Element Lifecycle',
      blink_components: ['Blink>WebComponents'],
      star_count: 42,
      search_tags: ['web-components', 'custom-elements', 'test'],
      feature_notes: 'Some internal notes about this feature.',
      enterprise_feature_categories: ['security', 'productivity'],
      enterprise_product_category: 2,

      feature_type: 'Incubation',
      feature_type_int: 0,
      intent_stage: 'Prototype',
      intent_stage_int: 2,
      active_stage_id: 201,
      bug_url: 'https://bugs.example.com/12345',
      launch_bug_url: 'https://bugs.example.com/launch/67890',
      screenshot_links: ['https://example.com/screenshot1.png', 'https://example.com/screenshot2.png'],
      first_enterprise_notification_milestone: 120,
      breaking_change: false,
      enterprise_impact: 2,

      flag_name: 'EnableTestFeature',
      finch_name: 'TestFeatureFinchRollout',
      non_finch_justification: 'Not applicable, will use Finch.',
      ongoing_constraints: 'Requires specific hardware for full functionality.',

      motivation: 'To provide developers with more control over custom elements.',
      devtrial_instructions: 'Enable the #EnableTestFeature flag in about:flags.',
      activation_risks: 'Low risk of activation issues.',
      measurement: 'Usage will be monitored via UMA counters.',
      availability_expectation: 'Expected to be available in M125.',
      adoption_expectation: 'High adoption expected from framework authors.',
      adoption_plan: 'Blog post on web.dev and tutorials.',

      initial_public_proposal_url: 'https://discourse.example.com/t/123',
      explainer_links: ['https://example.com/explainer.md'],
      requires_embedder_support: false,
      spec_link: 'https://example.com/spec.html',
      api_spec: 'Yes',
      prefixed: false,
      interop_compat_risks: 'Some minor interop risks identified with Safari.',
      all_platforms: true,
      all_platforms_descr: 'Basic description.',
      tag_review: 'TAG review requested, see link: https://example.com/tag/1',
      non_oss_deps: 'No non-OSS dependencies.',
      anticipated_spec_changes: 'Minor spec changes expected after TAG review.',

      security_risks: 'No major security risks identified.',
      tags: ['security', 'privacy'],
      tag_review_status: 'Pending',
      tag_review_status_int: 1,
      security_review_status: 'Pending',
      security_review_status_int: 1,
      privacy_review_status: 'Pending',
      privacy_review_status_int: 1,
      security_continuity_id: 9001,
      security_launch_issue_id: 9002,

      ergonomics_risks: 'Potential ergonomics risk for developers if API is misused.',
      wpt: true,
      wpt_descr: 'WPTs are being written in parallel.',
      webview_risks: 'Low risk for WebView.',

      devrel_emails: ['devrel1@example.com', 'devrel2@example.com'],
      debuggability: 'Feature is debuggable via DevTools.',
      doc_links: ['https://example.com/docs/test-feature'],
      sample_links: ['https://example.com/samples/test-feature'],

      stages: [
        {
          id: 201,
          created: '2025-02-01T00:00:00Z',
          feature_id: 1001,
          stage_type: 150,
          display_name: 'Prototype Stage',
          intent_stage: 2,
          intent_thread_url: 'https://example.com/intent-to-prototype',
          announcement_url: 'https://example.com/prototype-announced',
          origin_trial_id: 'OT_TestFeature_123',
          experiment_goals: 'Gather feedback on API shape and usability.',
          experiment_risks: 'Low risk, API is behind a flag.',
          extensions: [],
          origin_trial_feedback_url: 'https://example.com/ot-feedback',
          ot_action_requested: true,
          ot_activation_date: '2025-11-01T00:00:00Z',
          ot_approval_buganizer_component: 12345,
          ot_approval_buganizer_custom_field_id: 67890,
          ot_approval_criteria_url: 'https://example.com/ot-criteria',
          ot_approval_group_email: 'ot-approvers@example.com',
          ot_chromium_trial_name: 'TestFeatureOriginTrial',
          ot_description: 'An Origin Trial for the Test Feature.',
          ot_display_name: 'Test Feature OT',
          ot_documentation_url: 'https://example.com/ot-docs',
          ot_emails: ['ot-admin@example.com', 'owner1@example.com'],
          ot_feedback_submission_url: 'https://example.com/ot-submit',
          ot_has_third_party_support: false,
          ot_is_critical_trial: false,
          ot_is_deprecation_trial: false,
          ot_owner_email: 'ot-owner@example.com',
          ot_require_approvals: true,
          ot_setup_status: 1,
          ot_request_note: 'Please approve this OT for M124.',
          ot_stage_id: 201,
          ot_use_counter_bucket_number: 5001,
          experiment_extension_reason: 'Need more time for feedback.',
          finch_url: 'https://example.com/finch-rollout',
          rollout_details: 'Rolling out to 1% of users.',
          rollout_milestone: 124,
          rollout_platforms: ['Desktop', 'Android'],
          rollout_stage_plan: 1,
          enterprise_policies: ['TestFeatureEnabled', 'LegacyFeatureDisabled'],
          pm_emails: ['pm@example.com'],
          tl_emails: ['tl@example.com'],
          ux_emails: ['ux@example.com'],
          te_emails: ['te@example.com'],
          desktop_first: 124,
          android_first: 124,
          ios_first: 125,
          webview_first: 124,
          desktop_last: 126,
          android_last: 126,
          ios_last: 127,
          webview_last: 126,
        }
      ],

      resources: {
        samples: ['https://example.com/sample1', 'https://example.com/sample2'],
        docs: ['https://example.com/doc1', 'https://example.com/doc2'],
      },
      comments: 'This is a test feature with all fields filled.',

      ff_views: 1,
      safari_views: 2,
      web_dev_views: 1,

      browsers: {
        chrome: {
          bug: 'https://bugs.example.com/chrome/123',
          blink_components: ['Blink>WebComponents'],
          devrel: ['devrel1@example.com'],
          owners: ['owner1@example.com'],
          origintrial: true,
          prefixed: false,
          flag: true,
          status: {
            text: 'In development',
            val: 1,
            milestone_str: '124',
          },
          desktop: 124,
          android: 124,
          webview: 124,
          ios: 125,
        },
        ff: {
          view: {
            text: 'Positive',
            val: 1,
            url: 'https://example.com/ff-position',
            notes: 'Firefox is supportive of the goals.',
          },
        },
        safari: {
          view: {
            text: 'Neutral',
            val: 2,
            url: 'https://example.com/safari-position',
            notes: 'Safari is waiting for more feedback.',
          },
        },
        webdev: {
          view: {
            text: 'Positive',
            val: 1,
            url: 'https://example.com/webdev-position',
            notes: 'Web developers are excited.',
          },
        },
        other: {
          view: {
            text: 'No signal',
            val: 0,
            url: '',
            notes: 'No signals from other engines.',
          },
        },
      },

      standards: {
        spec: 'https://example.com/spec.html',
        maturity: {
          text: 'Early Draft',
          short_text: 'Draft',
          val: 1,
        },
      },

      is_released: false,
      is_enterprise_feature: true,
      updated_display: 'Oct 20, 2025',
      new_crbug_url: 'https://crbug.com/new/component=Blink>WebComponents',
    };
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
      closestShippingDate: '',
      isUpcoming: false,
      hasShipped: false,
    };

    it('should return null if feature is upcoming but verified', () => {
      const feature: Feature = {...baseFeature, accurate_as_of: VERIFIED_DATE};
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

    it('should return upcoming banner if accurate_as_of is missing', () => {
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
        closestShippingDate: '',
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
