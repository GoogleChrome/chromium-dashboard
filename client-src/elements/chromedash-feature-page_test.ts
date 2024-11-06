import {assert, fixture} from '@open-wc/testing';
import {html} from 'lit';
import sinon from 'sinon';
import {ChromeStatusClient, FeatureNotFoundError} from '../js-src/cs-client';
import {ChromedashFeaturePage} from './chromedash-feature-page';
import {ChromedashLink} from './chromedash-link';
import './chromedash-toast';
import {ChromedashVendorViews} from './chromedash-vendor-views';

describe('chromedash-feature-page', () => {
  const user = {
    can_create_feature: true,
    can_edit_all: true,
    is_admin: false,
    email: 'example@google.com',
    approvable_gate_types: [],
  };
  const gatesPromise = Promise.resolve([]);
  const commentsPromise = Promise.resolve([]);
  const processPromise = Promise.resolve({
    stages: [
      {
        name: 'stage one',
        description: 'a description',
        progress_items: [],
        outgoing_stage: 1,
        actions: [],
      },
    ],
  });
  const starsPromise = Promise.resolve([123456]);
  const progressPromise = Promise.resolve({
    'Code in Chromium': 'True',
    'Draft API spec': 'fake spec link',
    'Estimated target milestone': 'True',
    'Final target milestone': 'True',
    'Intent to Experiment email': 'fake intent to experiment url',
    'Ready for Developer Testing email': 'fake ready for dev test url',
    'Spec link': 'fake spec link',
    'Web developer signals': 'True',
  });
  const channels = {
    canary_asan: {
      version: 81,
      earliest_beta: '2020-02-13T00:00:00',
      mstone: 'fake milestone number',
    },
    canary: {
      version: 81,
      earliest_beta: '2020-02-13T00:00:00',
      mstone: 'fake milestone number',
    },
    dev: {
      version: 81,
      earliest_beta: '2020-02-13T00:00:00',
      mstone: 'fake milestone number',
    },
    beta: {
      version: 80,
      earliest_beta: '2020-02-13T00:00:00',
      mstone: 'fake milestone number',
      final_beta: '2020-03-13T00:00:00',
    },
    stable: {
      version: 79,
      earliest_beta: '2020-02-13T00:00:00',
      mstone: 'fake milestone number',
      final_beta: '2020-03-13T00:00:00',
    },
    20: {
      version: 20,
      final_beta: '2018-02-13T00:00:00',
      mstone: 'fake milestone number',
    },
  };
  const channelsPromise = Promise.resolve(channels);
  const validFeaturePromise = Promise.resolve({
    id: 123456,
    name: 'feature one',
    summary: 'detailed sum',
    new_crbug_url: 'fake crbug link',
    browsers: {
      chrome: {
        blink_components: ['Blink'],
        owners: ['fake chrome owner one', 'fake chrome owner two'],
        status: {text: 'fake chrome status text'},
      },
      ff: {view: {val: 1, text: 'fake ff view text', url: 'fake ff url'}},
      safari: {
        view: {val: 1, text: 'fake safari view text', url: 'fake safari url'},
      },
      webdev: {view: {text: 'fake webdev view text'}},
    },
    resources: {
      samples: ['fake sample link one', 'fake sample link two'],
      docs: ['fake doc link one', 'fake doc link two'],
    },
    standards: {
      spec: 'fake spec link',
      maturity: {text: 'Unknown standards status - check spec link for status'},
    },
    tags: ['tag_one'],
    stages: [
      {
        id: 1,
        stage_type: 110,
        intent_stage: 1,
      },
      {
        id: 2,
        stage_type: 120,
        intent_stage: 2,
      },
      {
        id: 3,
        stage_type: 160,
        intent_stage: 3,
        desktop_first: 80,
      },
    ],
  });

  async function assertClickableVendorLink(
    parentEl: HTMLElement,
    {href, text}: {href: string; text: string}
  ): Promise<void> {
    // Select chromedash-vendor-views element
    const vendorViewsEl: ChromedashVendorViews | null = parentEl.querySelector(
      `chromedash-vendor-views[href="${href}"]`
    );
    assert.exists(vendorViewsEl);
    // Verify that the link's text content matches the expected display text
    assert.equal(vendorViewsEl.textContent, text);

    // Select the chromedash-link
    await vendorViewsEl.updateComplete;
    const link: ChromedashLink | null =
      vendorViewsEl.renderRoot.querySelector('chromedash-link');
    assert.exists(link);

    // Check if the link's 'href' attribute matches the expected URL
    assert.equal(link.href, href);
  }

  /* window.csClient and <chromedash-toast> are initialized at spa.html
   * which are not available here, so we initialize them before each test.
   * We also stub out the API calls here so that they return test data. */
  beforeEach(async () => {
    await fixture(html`<chromedash-toast></chromedash-toast>`);
    window.csClient = new ChromeStatusClient('fake_token', 1);
    sinon.stub(window.csClient, 'getFeature');
    sinon.stub(window.csClient, 'getGates');
    sinon.stub(window.csClient, 'getComments');
    sinon.stub(window.csClient, 'getFeatureProcess');
    sinon.stub(window.csClient, 'getStars');
    sinon.stub(window.csClient, 'getFeatureProgress');
    sinon.stub(window.csClient, 'getSpecifiedChannels');
    window.csClient.getGates.returns(gatesPromise);
    window.csClient.getComments.returns(commentsPromise);
    window.csClient.getFeatureProcess.returns(processPromise);
    window.csClient.getStars.returns(starsPromise);
    window.csClient.getFeatureProgress.returns(progressPromise);
    window.csClient.getSpecifiedChannels.returns(channelsPromise);

    // For the child component - chromedash-gantt
    sinon.stub(window.csClient, 'getChannels');
    window.csClient.getChannels.returns(channelsPromise);
  });

  afterEach(() => {
    window.csClient.getFeature.restore();
    window.csClient.getFeatureProcess.restore();
    window.csClient.getStars.restore();
    window.csClient.getChannels.restore();
    window.csClient.getSpecifiedChannels.restore();
  });

  it('renders with no data', async () => {
    const invalidFeaturePromise = Promise.reject(
      new Error('Got error response from server')
    );
    window.csClient.getFeature.withArgs(0).returns(invalidFeaturePromise);

    const component = await fixture(
      html`<chromedash-feature-page></chromedash-feature-page>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashFeaturePage);

    // invalid feature requests would trigger the toast to show message
    const toastEl = document.querySelector('chromedash-toast');
    const toastMsgSpan = toastEl?.shadowRoot?.querySelector('span#msg');
    assert.include(
      toastMsgSpan?.innerHTML,
      'Some errors occurred. Please refresh the page or try again later.'
    );
  });

  it('renders with "Feature not found." when feature not found', async () => {
    const featureNotFoundPromise = Promise.reject(
      new FeatureNotFoundError(12345)
    );
    window.csClient.getFeature.withArgs(0).returns(featureNotFoundPromise);

    const component = await fixture(
      html`<chromedash-feature-page></chromedash-feature-page>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashFeaturePage);

    // If a request for a feature returns stating that it is not found, it
    // should show a simple message about that.
    const expectedMsg = 'Feature not found.';
    assert.include(component.shadowRoot?.innerHTML, expectedMsg);
  });

  it('renders with fake data', async () => {
    const featureId = 123456;
    const contextLink = '/features';
    window.csClient.getFeature.withArgs(featureId).returns(validFeaturePromise);

    const component = await fixture(
      html`<chromedash-feature-page
        .user=${user}
        .featureId=${featureId}
        .contextLink=${contextLink}
      >
      </chromedash-feature-page>`
    );
    assert.exists(component);

    const subheaderDiv = component.shadowRoot?.querySelector('div#subheader');
    assert.exists(subheaderDiv);
    // crbug link is clickable
    assert.include(subheaderDiv.innerHTML, 'href="fake crbug link"');
    // star icon is rendered and the feature is starred
    assert.include(subheaderDiv.innerHTML, 'icon="chromestatus:star"');

    const breadcrumbsH2 = component.shadowRoot?.querySelector('h2#breadcrumbs');
    assert.exists(breadcrumbsH2);
    // feature name is rendered
    assert.include(breadcrumbsH2.innerHTML, 'feature one');
    // context link is clickable
    assert.include(breadcrumbsH2.innerHTML, 'href="/features"');
    // feature link is clickable
    assert.include(breadcrumbsH2.innerHTML, 'href="/feature/123456');

    const highlightsElement = component.shadowRoot?.querySelector(
      'chromedash-feature-highlights'
    );
    assert.exists(highlightsElement);
    const summarySection =
      highlightsElement.shadowRoot?.querySelector('section#summary');
    assert.exists(summarySection);
    // feature summary is rendered
    assert.include(summarySection.innerHTML, 'detailed sum');

    const sampleSection =
      highlightsElement.shadowRoot?.querySelector('section#demo');
    assert.exists(sampleSection);
    // sample links are clickable
    assert.include(sampleSection.innerHTML, 'href="fake sample link one"');
    assert.include(sampleSection.innerHTML, 'href="fake sample link two"');

    const docSection = highlightsElement.shadowRoot?.querySelector(
      'section#documentation'
    );
    assert.exists(docSection);
    // doc links are clickable
    assert.include(docSection.innerHTML, 'href="fake doc link one"');
    assert.include(docSection.innerHTML, 'href="fake doc link two"');

    const specSection = highlightsElement.shadowRoot?.querySelector(
      'section#specification'
    );
    assert.exists(specSection);
    // spec link is clickable
    assert.include(specSection.innerHTML, 'href="fake spec link"');

    const consensusSection = highlightsElement.shadowRoot?.querySelector(
      'section#consensus'
    ) as HTMLElement;
    assert.exists(consensusSection);
    // FF and Safari views are present and clickable.
    await assertClickableVendorLink(consensusSection, {
      href: 'fake ff url',
      text: 'fake ff view text',
    });
    await assertClickableVendorLink(consensusSection, {
      href: 'fake safari url',
      text: 'fake safari view text',
    });
    assert.include(consensusSection.innerHTML, 'fake webdev view text');

    const tagSection =
      highlightsElement.shadowRoot?.querySelector('section#tags');
    assert.exists(tagSection);
    // feature tag link is clickable
    assert.include(tagSection.innerHTML, 'href="/features#tags:tag_one"');
  });

  it('omits absent vendor views', async () => {
    const featureId = 123456;
    const contextLink = '/features';
    const features: any = structuredClone(await validFeaturePromise);
    delete features.browsers.ff.view.val;
    delete features.browsers.safari.view.val;
    window.csClient.getFeature
      .withArgs(featureId)
      .returns(Promise.resolve(features));

    const component = await fixture(
      html`<chromedash-feature-page
        .user=${user}
        .featureId=${featureId}
        .contextLink=${contextLink}
      >
      </chromedash-feature-page>`
    );
    assert.exists(component);

    const highlightsElement = component.shadowRoot?.querySelector(
      'chromedash-feature-highlights'
    );
    assert.exists(highlightsElement);
    const consensusSection =
      highlightsElement.shadowRoot?.querySelector('section#consensus');
    assert.exists(consensusSection);
    // Views are omitted based on an empty 'val' field.
    assert.notInclude(consensusSection.innerHTML, '<chromedash-vendor-views');
    // But it does still include webdev views.
    assert.include(consensusSection.innerHTML, 'fake webdev view text');
  });

  it('findClosestShippingDate() tests for isUpcoming state', async () => {
    const featureId = 123456;
    const contextLink = '/features';
    const feature: any = structuredClone(await validFeaturePromise);
    const component: ChromedashFeaturePage =
      await fixture<ChromedashFeaturePage>(
        html`<chromedash-feature-page
          .user=${user}
          .featureId=${featureId}
          .contextLink=${contextLink}
        >
        </chromedash-feature-page>`
      );
    assert.exists(component);

    component.findClosestShippingDate({}, feature.stages);
    assert.isFalse(component.isUpcoming);
    assert.equal(component.closestShippingDate, '');

    component.findClosestShippingDate(channels, []);
    assert.isFalse(component.isUpcoming);
    assert.equal(component.closestShippingDate, '');

    // No shipping milestones.
    let stages: any = structuredClone(feature.stages);
    stages[2].stage_type = 130;
    component.findClosestShippingDate(channels, stages);
    assert.isFalse(component.isUpcoming);
    assert.equal(component.closestShippingDate, '');

    // No upcoming shipping milestones.
    stages = structuredClone(feature.stages);
    stages[2].desktop_first = 20;
    component.findClosestShippingDate(channels, stages);
    assert.isFalse(component.isUpcoming);
    assert.isFalse(component.hasShipped);
    assert.equal(component.closestShippingDate, '');

    component.findClosestShippingDate(channels, feature.stages);
    assert.isTrue(component.isUpcoming);
    assert.isFalse(component.hasShipped);
    assert.equal(component.closestShippingDate, '2020-03-13T00:00:00');

    component.closestShippingDate = '';
    component.isUpcoming = false;
    stages = structuredClone(feature.stages);
    // Test with STAGE_BLINK_ORIGIN_TRIAL type.
    stages[2].stage_type = 150;
    component.findClosestShippingDate(channels, stages);
    assert.isTrue(component.isUpcoming);
    assert.isFalse(component.hasShipped);
    assert.equal(component.closestShippingDate, '2020-03-13T00:00:00');
  });

  it('findClosestShippingDate() tests for hasShipped state', async () => {
    const featureId = 123456;
    const contextLink = '/features';
    const feature: any = structuredClone(await validFeaturePromise);
    const component: ChromedashFeaturePage =
      await fixture<ChromedashFeaturePage>(
        html`<chromedash-feature-page
          .user=${user}
          .featureId=${featureId}
          .contextLink=${contextLink}
        >
        </chromedash-feature-page>`
      );
    assert.exists(component);

    component.findClosestShippingDate({}, feature.stages);
    assert.isFalse(component.hasShipped);
    assert.equal(component.closestShippingDate, '');

    component.findClosestShippingDate(channels, []);
    assert.isFalse(component.hasShipped);
    assert.equal(component.closestShippingDate, '');

    // No shipping milestones.
    let stages: any = structuredClone(feature.stages);
    stages[2].stage_type = 130;
    component.findClosestShippingDate(channels, stages);
    assert.isFalse(component.hasShipped);
    assert.equal(component.closestShippingDate, '');

    // No shipped milestones in the past.
    const testChannels: any = structuredClone(channels);
    testChannels['stable'].version = 10;
    component.findClosestShippingDate(testChannels, stages);
    assert.isFalse(component.hasShipped);
    assert.equal(component.closestShippingDate, '');

    // Shipped on the stable milestone.
    stages = structuredClone(feature.stages);
    stages[2].desktop_first = 79;
    component.findClosestShippingDate(channels, stages);
    assert.isFalse(component.isUpcoming);
    assert.isTrue(component.hasShipped);
    assert.equal(component.closestShippingDate, '2020-03-13T00:00:00');

    component.isUpcoming = false;
    component.hasShipped = false;
    component.closestShippingDate = '';
    // Ignore OT milestones in the past.
    stages = structuredClone(feature.stages);
    stages[2].desktop_first = 79;
    // The type for STAGE_BLINK_ORIGIN_TRIAL.
    stages[2].stage_type = 150;
    component.findClosestShippingDate(channels, stages);
    assert.isFalse(component.isUpcoming);
    assert.isFalse(component.hasShipped);
    assert.equal(component.closestShippingDate, '');
  });

  it('findClosestShippingDate() tests when fetch specific channels', async () => {
    const featureId = 123456;
    const contextLink = '/features';
    const feature: any = structuredClone(await validFeaturePromise);
    feature.stages[2].desktop_first = 20;
    window.csClient.getFeature
      .withArgs(featureId)
      .returns(Promise.resolve(feature));

    const component: ChromedashFeaturePage =
      await fixture<ChromedashFeaturePage>(
        html`<chromedash-feature-page
          .user=${user}
          .featureId=${featureId}
          .contextLink=${contextLink}
        >
        </chromedash-feature-page>`
      );

    assert.exists(component);
    assert.isFalse(component.isUpcoming);
    assert.isTrue(component.hasShipped);
    assert.equal(component.closestShippingDate, '2018-02-13T00:00:00');
  });

  it('isUpcomingFeatureOutdated() tests', async () => {
    const featureId = 123456;
    const contextLink = '/features';
    const feature: any = structuredClone(await validFeaturePromise);
    feature.accurate_as_of = '2024-08-28 21:51:34.22386';
    window.csClient.getFeature
      .withArgs(featureId)
      .returns(Promise.resolve(feature));
    const component: ChromedashFeaturePage =
      await fixture<ChromedashFeaturePage>(
        html`<chromedash-feature-page
          .user=${user}
          .featureId=${featureId}
          .contextLink=${contextLink}
        >
        </chromedash-feature-page>`
      );
    component.currentDate = new Date('2024-10-23').getTime();
    assert.exists(component);

    component.findClosestShippingDate(channels, feature.stages);
    assert.isTrue(component.isUpcoming);
    assert.equal(component.closestShippingDate, '2020-03-13T00:00:00');
    assert.isTrue(component.isUpcomingFeatureOutdated());

    // accurate_as_of is not outdated and within the 4-week grace period.
    component.currentDate = new Date('2024-09-18').getTime();
    assert.isFalse(component.isUpcomingFeatureOutdated());
  });

  it('render the oudated warning when outdated', async () => {
    const featureId = 123456;
    const contextLink = '/features';
    const feature: any = structuredClone(await validFeaturePromise);
    feature.accurate_as_of = '2024-08-28 21:51:34.22386';
    window.csClient.getFeature
      .withArgs(featureId)
      .returns(Promise.resolve(feature));
    const component: ChromedashFeaturePage =
      await fixture<ChromedashFeaturePage>(
        html`<chromedash-feature-page
          .user=${user}
          .featureId=${featureId}
          .contextLink=${contextLink}
        >
        </chromedash-feature-page>`
      );
    component.currentDate = new Date('2024-10-23').getTime();
    assert.exists(component);

    component.findClosestShippingDate(channels, feature.stages);
    const oudated = component.shadowRoot!.querySelector('#outdated-icon');
    assert.exists(oudated);
  });

  it('render shipped feature outdated warnings for authors', async () => {
    const featureId = 123456;
    const contextLink = '/features';
    const feature: any = structuredClone(await validFeaturePromise);
    feature.accurate_as_of = '2017-10-28 21:51:34.22386';
    feature.stages[2].desktop_first = 20;
    window.csClient.getFeature
      .withArgs(featureId)
      .returns(Promise.resolve(feature));

    const component: ChromedashFeaturePage =
      await fixture<ChromedashFeaturePage>(
        html`<chromedash-feature-page
          .user=${user}
          .featureId=${featureId}
          .contextLink=${contextLink}
        >
        </chromedash-feature-page>`
      );

    component.currentDate = new Date('2017-10-29').getTime();
    await component.updateComplete;
    assert.exists(component);

    assert.isTrue(component.isShippedFeatureOutdated());
    assert.isTrue(component.isShippedFeatureOutdatedForAuthor());
    assert.isFalse(component.isShippedFeatureOutdatedForAll());
    const oudated = component.shadowRoot!.querySelector(
      '#shipped-outdated-author'
    );
    assert.exists(oudated);
  });

  it('render shipped feature outdated warnings for all', async () => {
    const featureId = 123456;
    const contextLink = '/features';
    const feature: any = structuredClone(await validFeaturePromise);
    feature.accurate_as_of = '2017-10-28 21:51:34.22386';
    feature.stages[2].desktop_first = 20;
    window.csClient.getFeature
      .withArgs(featureId)
      .returns(Promise.resolve(feature));

    const component: ChromedashFeaturePage =
      await fixture<ChromedashFeaturePage>(
        html`<chromedash-feature-page
          .featureId=${featureId}
          .contextLink=${contextLink}
        >
        </chromedash-feature-page>`
      );

    component.currentDate = new Date('2020-10-29').getTime();
    await component.updateComplete;
    assert.exists(component);

    assert.isTrue(component.isShippedFeatureOutdated());
    // undefined because this.user is undefined.
    assert.isUndefined(component.isShippedFeatureOutdatedForAuthor());
    assert.isTrue(component.isShippedFeatureOutdatedForAll());
    const oudated = component.shadowRoot!.querySelector(
      '#shipped-outdated-all'
    );
    assert.exists(oudated);
  });
});
