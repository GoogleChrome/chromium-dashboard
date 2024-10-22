import {assert, fixture} from '@open-wc/testing';
import {html} from 'lit';
import sinon from 'sinon';
import {
  ChromedashRoadmapMilestoneCard,
  TemplateContent,
} from './chromedash-roadmap-milestone-card';

describe('chromedash-roadmap-milestone-card', () => {
  let el: ChromedashRoadmapMilestoneCard;

  beforeEach(async () => {
    const templateContent: TemplateContent = {
      channelLabel: 'Stable',
      h1Class: '',
      dateText: 'was',
      featureHeader: 'Features in this release',
    };
    el = await fixture<ChromedashRoadmapMilestoneCard>(
      html`<chromedash-roadmap-milestone-card
        .templateContent=${templateContent}
      ></chromedash-roadmap-milestone-card>`
    );
    // Represents 2024-10-23.
    el.currentDate = 1729666830595;
    el.stableMilestone = 10;
    await el.updateComplete;
  });

  it('can be added to the page', async () => {
    assert.exists(el);
    assert.instanceOf(el, ChromedashRoadmapMilestoneCard);
  });

  it('_isFeatureOutdated tests', async () => {
    assert.isFalse(el._isFeatureOutdated(null, 20));
    // False when a feature is not shipped within two milestones.
    assert.isFalse(el._isFeatureOutdated('2023-10-23 07:07:05.264715', 20));
    // False when a feature is accurate within four weeks.
    assert.isFalse(el._isFeatureOutdated('2024-10-23 07:07:05.264715', 11));
    assert.isFalse(el._isFeatureOutdated('2024-09-28 07:07:05.264715', 11));

    assert.isTrue(el._isFeatureOutdated('2024-08-23 07:07:05.264715', 11));
    assert.isTrue(el._isFeatureOutdated('2023-10-23 07:07:05.264715', 11));
    assert.isTrue(el._isFeatureOutdated('2023-10-23 07:07:05.264715', 12));
  });
});
