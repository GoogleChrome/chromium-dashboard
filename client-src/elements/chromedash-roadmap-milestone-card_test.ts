import {assert, fixture} from '@open-wc/testing';
import {html} from 'lit';
import {ReleaseInfo, Feature} from '../js-src/cs-client';
import {
  ChromedashRoadmapMilestoneCard,
  TemplateContent,
} from './chromedash-roadmap-milestone-card';
import {FEATURE_TYPES} from './form-field-enums';

describe('chromedash-roadmap-milestone-card', () => {
  const baseFeature = {
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
    screenshot_links: [
      'https://example.com/screenshot1.png',
      'https://example.com/screenshot2.png',
    ],
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

    ergonomics_risks:
      'Potential ergonomics risk for developers if API is misused.',
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
      },
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
        intervention: false,
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

  const mockFeature = {
    ...baseFeature,
    id: 134,
    name: 'vmvvv',
    summary: 'd',
    unlisted: false,
    enterprise_impact: 1,
    breaking_change: false,
    first_enterprise_notification_milestone: undefined,
    blink_components: ['Blink>CaptureFromElement'],
    resources: {
      samples: [],
      docs: [],
    },
    created: {
      by: 'example@chromium.org',
      when: '2024-08-28 21:51:34.223994',
    },
    updated: {
      by: 'example@chromium.org',
      when: '2024-10-21 23:17:53.647165',
    },
    accurate_as_of: '2024-08-28 21:51:34.223867',
    standards: {
      spec: undefined,
      maturity: {
        text: undefined,
        short_text: 'Unknown status',
        val: 0,
      },
    },
    browsers: {
      chrome: {
        bug: undefined,
        blink_components: ['Blink>CaptureFromElement'],
        devrel: ['devrel-chromestatus-all@google.com'],
        owners: ['example@chromium.org'],
        origintrial: false,
        intervention: false,
        prefixed: false,
        flag: false,
        status: {
          text: 'No active development',
          val: 1,
        },
      },
      ff: {
        view: {
          url: undefined,
          notes: undefined,
          text: 'No signal',
          val: 5,
        },
      },
      safari: {
        view: {
          url: undefined,
          notes: undefined,
          text: 'No signal',
          val: 5,
        },
      },
      webdev: {
        view: {
          text: 'No signals',
          val: 4,
          url: undefined,
          notes: undefined,
        },
      },
      other: {
        view: {
          notes: undefined,
        },
      },
    },
    is_released: false,
    milestone: undefined,
  };
  const stableMilestone: number = 107;

  const templateContent: TemplateContent = {
    channelLabel: 'Stable',
    h1Class: '',
    dateText: 'was',
    featureHeader: 'Features in this release',
  };

  const channel: ReleaseInfo = {
    version: 108,
    early_stable: '2020-02 - 13T00:00:00',
    features: {},
  };
  channel.features['Origin trial'] = [mockFeature];

  const testDate: number = new Date('2024-10-23').getTime();

  it('can be added to the page', async () => {
    const el: ChromedashRoadmapMilestoneCard =
      await fixture<ChromedashRoadmapMilestoneCard>(
        html`<chromedash-roadmap-milestone-card
          .templateContent=${templateContent}
          .channel=${channel}
          .stableMilestone=${stableMilestone}
        ></chromedash-roadmap-milestone-card>`
      );
    await el.updateComplete;

    assert.exists(el);
    assert.instanceOf(el, ChromedashRoadmapMilestoneCard);
  });

  it('_isFeatureOutdated tests', async () => {
    const el: ChromedashRoadmapMilestoneCard =
      await fixture<ChromedashRoadmapMilestoneCard>(
        html`<chromedash-roadmap-milestone-card
          .templateContent=${templateContent}
          .channel=${channel}
          .stableMilestone=${stableMilestone}
        ></chromedash-roadmap-milestone-card>`
      );
    el.currentDate = testDate;
    el.stableMilestone = 10;

    assert.isFalse(el._isFeatureOutdated(undefined, 20));
    // False when a feature is not shipped within two milestones.
    assert.isFalse(el._isFeatureOutdated('2023-10-23 07:07:05.264715', 20));
    // False when a feature is accurate within four weeks.
    assert.isFalse(el._isFeatureOutdated('2024-10-23 07:07:05.264715', 11));
    assert.isFalse(el._isFeatureOutdated('2024-09-28 07:07:05.264715', 11));

    assert.isTrue(el._isFeatureOutdated('2024-08-23 07:07:05.264715', 11));
    assert.isTrue(el._isFeatureOutdated('2023-10-23 07:07:05.264715', 11));
    assert.isTrue(el._isFeatureOutdated('2023-10-23 07:07:05.264715', 12));
  });

  it('renders the feature oudated warning icon', async () => {
    channel.features['Origin trial'][0]['accurate_as_of'] =
      '2024-08-28 21:51:34.223867';
    channel.version = stableMilestone + 1;
    const el: ChromedashRoadmapMilestoneCard =
      await fixture<ChromedashRoadmapMilestoneCard>(
        html`<chromedash-roadmap-milestone-card
          .templateContent=${templateContent}
          .channel=${channel}
          .stableMilestone=${stableMilestone}
        ></chromedash-roadmap-milestone-card>`
      );
    el.currentDate = testDate;

    const oudated = el.shadowRoot!.querySelector('#outdated-icon');
    assert.exists(oudated);
  });

  it('not renders the oudated icon when shipped in 3 milestones', async () => {
    channel.features['Origin trial'][0]['accurate_as_of'] =
      '2024-08-28 21:51:34.223867';
    channel.version = stableMilestone + 3;
    const el: ChromedashRoadmapMilestoneCard =
      await fixture<ChromedashRoadmapMilestoneCard>(
        html`<chromedash-roadmap-milestone-card
          .templateContent=${templateContent}
          .channel=${channel}
          .stableMilestone=${stableMilestone}
        ></chromedash-roadmap-milestone-card>`
      );
    el.currentDate = testDate;

    const oudated = el.shadowRoot!.querySelector('#outdated-icon');
    assert.isNull(oudated);
  });

  it('not renders the oudated icon when accurate_as_of is undefined', async () => {
    channel.features['Origin trial'][0]['accurate_as_of'] = undefined;
    channel.version = stableMilestone + 3;
    const el: ChromedashRoadmapMilestoneCard =
      await fixture<ChromedashRoadmapMilestoneCard>(
        html`<chromedash-roadmap-milestone-card
          .templateContent=${templateContent}
          .channel=${channel}
          .stableMilestone=${stableMilestone}
        ></chromedash-roadmap-milestone-card>`
      );
    el.currentDate = testDate;

    const oudated = el.shadowRoot!.querySelector('#outdated-icon');
    assert.isNull(oudated);
  });

  it('not renders the oudated icon when accurate_as_of is recent', async () => {
    channel.features['Origin trial'][0]['accurate_as_of'] =
      '2024-09-28 21:51:34.223867';
    channel.version = stableMilestone + 3;
    const el: ChromedashRoadmapMilestoneCard =
      await fixture<ChromedashRoadmapMilestoneCard>(
        html`<chromedash-roadmap-milestone-card
          .templateContent=${templateContent}
          .channel=${channel}
          .stableMilestone=${stableMilestone}
        ></chromedash-roadmap-milestone-card>`
      );
    el.currentDate = testDate;

    const oudated = el.shadowRoot!.querySelector('#outdated-icon');
    assert.isNull(oudated);
  });
  describe('renderOTFeatures', () => {
    const otFeature = {
      ...mockFeature,
      id: 101,
      name: 'Origin Trial Feature',
      feature_type_int: 1,
    };
    const deprecationFeature = {
      ...mockFeature,
      id: 102,
      name: 'Deprecation Trial Feature',
      feature_type_int: FEATURE_TYPES.FEATURE_TYPE_DEPRECATION_ID[0],
    };
    const anotherDeprecationFeature = {
      ...mockFeature,
      id: 103,
      name: 'Another Deprecation Trial Feature',
      feature_type_int: FEATURE_TYPES.FEATURE_TYPE_DEPRECATION_ID[0],
    };

    it('returns an empty array for undefined or empty input', async () => {
      const el: ChromedashRoadmapMilestoneCard =
        await fixture<ChromedashRoadmapMilestoneCard>(
          html`<chromedash-roadmap-milestone-card
            .templateContent=${templateContent}
            .channel=${channel}
            .stableMilestone=${stableMilestone}
          ></chromedash-roadmap-milestone-card>`
        );
      assert.deepEqual(el.renderOTFeatures(undefined), []);
      assert.deepEqual(el.renderOTFeatures([]), []);
    });

    it('renders only origin trial features', async () => {
      const el: ChromedashRoadmapMilestoneCard =
        await fixture<ChromedashRoadmapMilestoneCard>(
          html`<chromedash-roadmap-milestone-card
            .templateContent=${templateContent}
            .channel=${channel}
            .stableMilestone=${stableMilestone}
          ></chromedash-roadmap-milestone-card>`
        );
      const features = [otFeature];
      const resultTemplates = el.renderOTFeatures(features);

      assert.lengthOf(resultTemplates, 1);

      const container = await fixture(html`<div>${resultTemplates}</div>`);
      const header = container.querySelector('h3.feature_shipping_type');
      assert.exists(header);
      assert.include(header!.textContent, 'Origin trial');

      const featureItems = container.querySelectorAll('li');
      assert.lengthOf(featureItems, 1);
      assert.include(featureItems[0].textContent, 'Origin Trial Feature');

      // Ensure no deprecation trial header is rendered.
      const allHeaders = container.querySelectorAll('h3.feature_shipping_type');
      assert.lengthOf(allHeaders, 1);
    });

    it('renders only deprecation trial features', async () => {
      const el: ChromedashRoadmapMilestoneCard =
        await fixture<ChromedashRoadmapMilestoneCard>(
          html`<chromedash-roadmap-milestone-card
            .templateContent=${templateContent}
            .channel=${channel}
            .stableMilestone=${stableMilestone}
          ></chromedash-roadmap-milestone-card>`
        );
      const features = [deprecationFeature, anotherDeprecationFeature];
      const resultTemplates = el.renderOTFeatures(features);

      assert.lengthOf(resultTemplates, 1);

      const container = await fixture(html`<div>${resultTemplates}</div>`);
      const header = container.querySelector('h3.feature_shipping_type');
      assert.exists(header);
      assert.include(header!.textContent, 'Deprecation trial');

      const featureItems = container.querySelectorAll('li');
      assert.lengthOf(featureItems, 2);
      assert.include(featureItems[0].textContent, 'Deprecation Trial Feature');
      assert.include(
        featureItems[1].textContent,
        'Another Deprecation Trial Feature'
      );
    });

    it('renders a mix of origin trial and deprecation trial features', async () => {
      const el: ChromedashRoadmapMilestoneCard =
        await fixture<ChromedashRoadmapMilestoneCard>(
          html`<chromedash-roadmap-milestone-card
            .templateContent=${templateContent}
            .channel=${channel}
            .stableMilestone=${stableMilestone}
          ></chromedash-roadmap-milestone-card>`
        );
      const features = [otFeature, deprecationFeature];
      const resultTemplates = el.renderOTFeatures(features);

      assert.lengthOf(resultTemplates, 2);

      const container = await fixture(html`<div>${resultTemplates}</div>`);
      const headers = container.querySelectorAll('h3.feature_shipping_type');
      assert.lengthOf(headers, 2);
      assert.include(headers[0].textContent, 'Origin trial');
      assert.include(headers[1].textContent, 'Deprecation trial');

      const lists = container.querySelectorAll('ul');
      assert.lengthOf(lists, 2);

      const otItems = lists[0].querySelectorAll('li');
      assert.lengthOf(otItems, 1);
      assert.include(otItems[0].textContent, 'Origin Trial Feature');

      const deprecationItems = lists[1].querySelectorAll('li');
      assert.lengthOf(deprecationItems, 1);
      assert.include(
        deprecationItems[0].textContent,
        'Deprecation Trial Feature'
      );
    });
  });
});
