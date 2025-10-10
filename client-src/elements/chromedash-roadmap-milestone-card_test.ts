import {assert, fixture} from '@open-wc/testing';
import {html} from 'lit';
import {ReleaseInfo, Feature} from '../js-src/cs-client';
import {
  ChromedashRoadmapMilestoneCard,
  TemplateContent,
} from './chromedash-roadmap-milestone-card';
import { FEATURE_TYPES } from './form-field-enums';

describe('chromedash-roadmap-milestone-card', () => {
  const mockFeature = {
    id: 134,
    name: 'vmvvv',
    summary: 'd',
    unlisted: false,
    enterprise_impact: 1,
    breaking_change: false,
    first_enterprise_notification_milestone: null,
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
      spec: null,
      maturity: {
        text: null,
        short_text: 'Unknown status',
        val: 0,
      },
    },
    browsers: {
      chrome: {
        bug: null,
        blink_components: ['Blink>CaptureFromElement'],
        devrel: ['devrel-chromestatus-all@google.com'],
        owners: ['example@chromium.org'],
        origintrial: false,
        intervention: false,
        prefixed: null,
        flag: false,
        status: {
          text: 'No active development',
          val: 1,
        },
      },
      ff: {
        view: {
          url: null,
          notes: null,
          text: 'No signal',
          val: 5,
        },
      },
      safari: {
        view: {
          url: null,
          notes: null,
          text: 'No signal',
          val: 5,
        },
      },
      webdev: {
        view: {
          text: 'No signals',
          val: 4,
          url: null,
          notes: null,
        },
      },
      other: {
        view: {
          notes: null,
        },
      },
    },
    is_released: false,
    milestone: null,
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
    features: {} as Feature,
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

  it('not renders the oudated icon when accurate_as_of is null', async () => {
    channel.features['Origin trial'][0]['accurate_as_of'] = null;
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
      const features = [
        deprecationFeature,
        anotherDeprecationFeature,
      ];
      const resultTemplates = el.renderOTFeatures(features);

      assert.lengthOf(resultTemplates, 1);

      const container = await fixture(html`<div>${resultTemplates}</div>`);
      const header = container.querySelector('h3.feature_shipping_type');
      assert.exists(header);
      assert.include(header!.textContent, 'Deprecation trial');

      const featureItems = container.querySelectorAll('li');
      assert.lengthOf(featureItems, 2);
      assert.include(
        featureItems[0].textContent,
        'Deprecation Trial Feature'
      );
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
