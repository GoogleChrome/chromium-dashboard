import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashFeaturePage} from './chromedash-feature-page';
import './chromedash-toast';
import '../js-src/cs-client';
import sinon from 'sinon';

describe('chromedash-feature-page', () => {
  const user = {
    can_approve: false,
    can_create_feature: true,
    can_edit_all: true,
    is_admin: false,
    email: 'example@google.com',
  };
  const editor = {
    can_approve: false,
    can_create_feature: false,
    can_edit_all: false,
    editable_features: [123456],
    is_admin: false,
    email: 'editor@example.com',
  };
  const visitor = {
    can_approve: false,
    can_create_feature: false,
    can_edit_all: false,
    editable_features: [],
    is_admin: false,
    email: 'example@example.com',
  };
  const anon = null;
  const commentsPromise = Promise.resolve([]);
  const processPromise = Promise.resolve({
    stages: [{
      name: 'stage one',
      description: 'a description',
      progress_items: [],
      outgoing_stage: 1,
      actions: [],
    }],
  });
  const dismissedCuesPromise = Promise.resolve(['progress-checkmarks']);
  const starsPromise = Promise.resolve([123456]);
  const channelsPromise = Promise.resolve({
    'canary_asan': {
      'version': 81,
      'earliest_beta': '2020-02-13T00:00:00',
      'mstone': 'fake milestone number',
    },
    'canary': {
      'version': 81,
      'earliest_beta': '2020-02-13T00:00:00',
      'mstone': 'fake milestone number',
    },
    'dev': {
      'version': 81,
      'earliest_beta': '2020-02-13T00:00:00',
      'mstone': 'fake milestone number',
    },
    'beta': {
      'version': 80,
      'earliest_beta': '2020-02-13T00:00:00',
      'mstone': 'fake milestone number',
    },
    'stable': {
      'version': 79,
      'earliest_beta': '2020-02-13T00:00:00',
      'mstone': 'fake milestone number',
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
      ff: {view: {text: 'fake ff view text'}},
      safari: {view: {text: 'fake safari view text'}},
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
  });

  /* window.csClient and <chromedash-toast> are initialized at spa.html
   * which are not available here, so we initialize them before each test.
   * We also stub out the API calls here so that they return test data. */
  beforeEach(async () => {
    await fixture(html`<chromedash-toast></chromedash-toast>`);
    window.csClient = new ChromeStatusClient('fake_token', 1);
    sinon.stub(window.csClient, 'getFeature');
    sinon.stub(window.csClient, 'getComments');
    sinon.stub(window.csClient, 'getFeatureProcess');
    sinon.stub(window.csClient, 'getDismissedCues');
    sinon.stub(window.csClient, 'getStars');
    window.csClient.getComments.returns(commentsPromise);
    window.csClient.getFeatureProcess.returns(processPromise);
    window.csClient.getDismissedCues.returns(dismissedCuesPromise);
    window.csClient.getStars.returns(starsPromise);

    // For the child component - chromedash-gantt
    sinon.stub(window.csClient, 'getChannels');
    window.csClient.getChannels.returns(channelsPromise);
  });

  afterEach(() => {
    window.csClient.getFeature.restore();
    window.csClient.getFeatureProcess.restore();
    window.csClient.getDismissedCues.restore();
    window.csClient.getStars.restore();
    window.csClient.getChannels.restore();
  });

  it('renders with no data', async () => {
    const invalidFeaturePromise = Promise.reject(new Error('Got error response from server'));
    window.csClient.getFeature.withArgs(0).returns(invalidFeaturePromise);

    const component = await fixture(
      html`<chromedash-feature-page></chromedash-feature-page>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashFeaturePage);

    // invalid feature requests would trigger the toast to show message
    const toastEl = document.querySelector('chromedash-toast');
    const toastMsgSpan = toastEl.shadowRoot.querySelector('span#msg');
    assert.include(toastMsgSpan.innerHTML,
      'Some errors occurred. Please refresh the page or try again later.');
  });

  it('renders with fake data', async () => {
    const featureId = 123456;
    const contextLink = '/features';
    window.csClient.getFeature.withArgs(featureId).returns(validFeaturePromise);

    const component = await fixture(
      html`<chromedash-feature-page
            .user=${user}
            .featureId=${featureId}
            .contextLink=${contextLink}>
           </chromedash-feature-page>`);
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

    const summarySection = component.shadowRoot.querySelector('section#summary');
    assert.exists(summarySection);
    // feature summary is rendered
    assert.include(summarySection.innerHTML, 'detailed sum');

    const sampleSection = component.shadowRoot.querySelector('section#demo');
    assert.exists(sampleSection);
    // sample links are clickable
    assert.include(sampleSection.innerHTML, 'href="fake sample link one"');
    assert.include(sampleSection.innerHTML, 'href="fake sample link two"');

    const docSection = component.shadowRoot.querySelector('section#documentation');
    assert.exists(docSection);
    // doc links are clickable
    assert.include(docSection.innerHTML, 'href="fake doc link one"');
    assert.include(docSection.innerHTML, 'href="fake doc link two"');

    const specSection = component.shadowRoot.querySelector('section#specification');
    assert.exists(specSection);
    // spec link is clickable
    assert.include(specSection.innerHTML, 'href="fake spec link"');

    const tagSection = component.shadowRoot.querySelector('section#tags');
    assert.exists(tagSection);
    // feature tag link is clickable
    assert.include(tagSection.innerHTML, 'href="/features#tags:tag_one"');
  });

  it('does offer editing to a listed editor', async () => {
    const featureId = 123456;
    const contextLink = '/features';
    window.csClient.getFeature.withArgs(featureId).returns(validFeaturePromise);

    const component = await fixture(
      html`<chromedash-feature-page
            .user=${editor}
            .featureId=${featureId}
            .contextLink=${contextLink}>
           </chromedash-feature-page>`);
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
            .contextLink=${contextLink}>
           </chromedash-feature-page>`);
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
            .contextLink=${contextLink}>
           </chromedash-feature-page>`);
    const subheaderDiv = component.shadowRoot.querySelector('div#subheader');
    // Edit icon is not offered because the visitor cannot edit.
    assert.notInclude(subheaderDiv.innerHTML, 'icon="chromestatus:create"');
  });
});
