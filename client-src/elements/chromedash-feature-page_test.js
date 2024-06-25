import {assert, fixture} from '@open-wc/testing';
import {html} from 'lit';
import sinon from 'sinon';
import {ChromeStatusClient, FeatureNotFoundError} from '../js-src/cs-client';
import {ChromedashFeaturePage} from './chromedash-feature-page';
import './chromedash-toast';

describe('chromedash-feature-page', () => {
  const user = {
    can_create_feature: true,
    can_edit_all: true,
    is_admin: false,
    email: 'example@google.com',
    approvable_gate_types: [],
  };
  const editor = {
    can_create_feature: false,
    can_edit_all: false,
    editable_features: [123456],
    is_admin: false,
    email: 'editor@example.com',
    approvable_gate_types: [],
  };
  const visitor = {
    can_create_feature: false,
    can_edit_all: false,
    editable_features: [],
    is_admin: false,
    email: 'example@example.com',
    approvable_gate_types: [],
  };
  const anon = null;
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
  const channelsPromise = Promise.resolve({
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
    },
    stable: {
      version: 79,
      earliest_beta: '2020-02-13T00:00:00',
      mstone: 'fake milestone number',
    },
  });
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
    ],
  });

  /**
   * @param {HTMLElement} parentEl
   * @param {object} options
   * @param {string} options.href
   * @param {string} options.text
   * @returns {Promise<void>}
   */
  async function assertClickableVendorLink(parentEl, {href, text}) {
    // Select chromedash-vendor-views element
    const vendorViewsEl = parentEl.querySelector(
      `chromedash-vendor-views[href="${href}"]`
    );
    assert.exists(vendorViewsEl);
    // Verify that the link's text content matches the expected display text
    assert.equal(vendorViewsEl.textContent, text);

    // Select the chromedash-link
    await vendorViewsEl.updateComplete;
    const link = vendorViewsEl.shadowRoot.querySelector('chromedash-link');
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
    window.csClient.getGates.returns(gatesPromise);
    window.csClient.getComments.returns(commentsPromise);
    window.csClient.getFeatureProcess.returns(processPromise);
    window.csClient.getStars.returns(starsPromise);
    window.csClient.getFeatureProgress.returns(progressPromise);

    // For the child component - chromedash-gantt
    sinon.stub(window.csClient, 'getChannels');
    window.csClient.getChannels.returns(channelsPromise);
  });

  afterEach(() => {
    window.csClient.getFeature.restore();
    window.csClient.getFeatureProcess.restore();
    window.csClient.getStars.restore();
    window.csClient.getChannels.restore();
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
    const toastMsgSpan = toastEl.shadowRoot.querySelector('span#msg');
    assert.include(
      toastMsgSpan.innerHTML,
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
    assert.include(component.shadowRoot.innerHTML, expectedMsg);
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

    const subheaderDiv = component.shadowRoot.querySelector('div#subheader');
    assert.exists(subheaderDiv);
    // crbug link is clickable
    assert.include(subheaderDiv.innerHTML, 'href="fake crbug link"');
    // star icon is rendered and the feature is starred
    assert.include(subheaderDiv.innerHTML, 'icon="chromestatus:star"');
    // edit icon is rendered (the test user can edit)
    assert.include(subheaderDiv.innerHTML, 'icon="chromestatus:create"');
    // approval icon is not rendered (the test user cannot approve)
    assert.notInclude(subheaderDiv.innerHTML, 'icon="chromestatus:approval"');

    const breadcrumbsH2 = component.shadowRoot.querySelector('h2#breadcrumbs');
    assert.exists(breadcrumbsH2);
    // feature name is rendered
    assert.include(breadcrumbsH2.innerHTML, 'feature one');
    // context link is clickable
    assert.include(breadcrumbsH2.innerHTML, 'href="/features"');
    // feature link is clickable
    assert.include(breadcrumbsH2.innerHTML, 'href="/feature/123456');

    const highlightsElement = component.shadowRoot.querySelector(
      'chromedash-feature-highlights'
    );
    assert.exists(highlightsElement);
    const summarySection =
      highlightsElement.shadowRoot.querySelector('section#summary');
    assert.exists(summarySection);
    // feature summary is rendered
    assert.include(summarySection.innerHTML, 'detailed sum');

    const sampleSection =
      highlightsElement.shadowRoot.querySelector('section#demo');
    assert.exists(sampleSection);
    // sample links are clickable
    assert.include(sampleSection.innerHTML, 'href="fake sample link one"');
    assert.include(sampleSection.innerHTML, 'href="fake sample link two"');

    const docSection = highlightsElement.shadowRoot.querySelector(
      'section#documentation'
    );
    assert.exists(docSection);
    // doc links are clickable
    assert.include(docSection.innerHTML, 'href="fake doc link one"');
    assert.include(docSection.innerHTML, 'href="fake doc link two"');

    const specSection = highlightsElement.shadowRoot.querySelector(
      'section#specification'
    );
    assert.exists(specSection);
    // spec link is clickable
    assert.include(specSection.innerHTML, 'href="fake spec link"');

    const consensusSection =
      highlightsElement.shadowRoot.querySelector('section#consensus');
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
      highlightsElement.shadowRoot.querySelector('section#tags');
    assert.exists(tagSection);
    // feature tag link is clickable
    assert.include(tagSection.innerHTML, 'href="/features#tags:tag_one"');
  });

  it('omits absent vendor views', async () => {
    const featureId = 123456;
    const contextLink = '/features';
    const features = structuredClone(await validFeaturePromise);
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

    const highlightsElement = component.shadowRoot.querySelector(
      'chromedash-feature-highlights'
    );
    assert.exists(highlightsElement);
    const consensusSection =
      highlightsElement.shadowRoot.querySelector('section#consensus');
    assert.exists(consensusSection);
    // Views are omitted based on an empty 'val' field.
    assert.notInclude(consensusSection.innerHTML, '<chromedash-vendor-views');
    // But it does still include webdev views.
    assert.include(consensusSection.innerHTML, 'fake webdev view text');
  });

  it('does offer editing to a listed editor', async () => {
    const featureId = 123456;
    const contextLink = '/features';
    window.csClient.getFeature.withArgs(featureId).returns(validFeaturePromise);

    const component = await fixture(
      html`<chromedash-feature-page
        .user=${editor}
        .featureId=${featureId}
        .contextLink=${contextLink}
      >
      </chromedash-feature-page>`
    );
    const subheaderDiv = component.shadowRoot.querySelector('div#subheader');
    // Edit icon is offered because user's editable_features has this one.
    assert.include(subheaderDiv.innerHTML, 'icon="chromestatus:create"');
  });

  it('does not offer editing to anon users', async () => {
    const featureId = 123456;
    const contextLink = '/features';
    window.csClient.getFeature.withArgs(featureId).returns(validFeaturePromise);

    const component = await fixture(
      html`<chromedash-feature-page
        .user=${anon}
        .featureId=${featureId}
        .contextLink=${contextLink}
      >
      </chromedash-feature-page>`
    );
    const subheaderDiv = component.shadowRoot.querySelector('div#subheader');
    // Edit icon is not offered because anon cannot edit.
    assert.notInclude(subheaderDiv.innerHTML, 'icon="chromestatus:create"');
  });

  it('does not offer editing to signed in visitors', async () => {
    const featureId = 123456;
    const contextLink = '/features';
    window.csClient.getFeature.withArgs(featureId).returns(validFeaturePromise);

    const component = await fixture(
      html`<chromedash-feature-page
        .user=${visitor}
        .featureId=${featureId}
        .contextLink=${contextLink}
      >
      </chromedash-feature-page>`
    );
    const subheaderDiv = component.shadowRoot.querySelector('div#subheader');
    // Edit icon is not offered because the visitor cannot edit.
    assert.notInclude(subheaderDiv.innerHTML, 'icon="chromestatus:create"');
  });
});
