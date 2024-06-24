import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashRoadmapPage} from './chromedash-roadmap-page';
import {ChromeStatusClient} from '../js-src/cs-client';
import sinon from 'sinon';

describe('chromedash-roadmap-page', () => {
  const starsPromise = Promise.resolve([123456]);
  const channelsPromise = Promise.resolve({
    108: {
      version: 108,
      earliest_beta: '2020-02-13T00:00:00',
      mstone: 'fake milestone number',
    },
    107: {
      version: 107,
      earliest_beta: '2020-02-13T00:00:00',
      mstone: 'fake milestone number',
    },
    106: {
      version: 106,
      earliest_beta: '2020-02-13T00:00:00',
      mstone: 'fake milestone number',
    },
    canary_asan: {
      version: 105,
      earliest_beta: '2020-02-13T00:00:00',
      mstone: 'fake milestone number',
    },
    canary: {
      version: 105,
      earliest_beta: '2020-02-13T00:00:00',
      mstone: 'fake milestone number',
    },
    dev: {
      version: 105,
      earliest_beta: '2020-02-13T00:00:00',
      mstone: 'fake milestone number',
    },
    beta: {
      version: 104,
      earliest_beta: '2020-02-13T00:00:00',
      mstone: 'fake milestone number',
    },
    stable: {
      version: 103,
      earliest_beta: '2020-02-13T00:00:00',
      mstone: 'fake milestone number',
    },
    102: {
      version: 102,
      earliest_beta: '2020-02-13T00:00:00',
      mstone: 'fake milestone number',
    },
  });
  const featuresInMilestonePromise = Promise.resolve({
    'Brower Intervention': [{name: 'fake feature one'}],
    Deprecated: [{name: 'fake feature two'}],
    'Enabled by default': [{name: 'fake feature three'}],
    'Original Trial': [{name: 'fake feature four'}],
    Removed: [{name: 'fake feature five'}],
  });

  /* window.csClient and <chromedash-toast> are initialized at spa.html
   * which are not available here, so we initialize them before each test.
   * We also stub out the API calls here so that they return test data. */
  beforeEach(async () => {
    await fixture(html`<chromedash-toast></chromedash-toast>`);
    window.csClient = new ChromeStatusClient('fake_token', 1);

    // For the child component - chromedash-roadmap
    sinon.stub(window.csClient, 'getChannels');
    sinon.stub(window.csClient, 'getStars');
    sinon.stub(window.csClient, 'getFeaturesInMilestone');
    sinon.stub(window.csClient, 'getSpecifiedChannels');
    window.csClient.getStars.returns(starsPromise);
    window.csClient.getChannels.returns(channelsPromise);
    window.csClient.getFeaturesInMilestone.returns(featuresInMilestonePromise);
    window.csClient.getSpecifiedChannels.returns(channelsPromise);
  });

  afterEach(() => {
    window.csClient.getChannels.restore();
    window.csClient.getStars.restore();
    window.csClient.getFeaturesInMilestone.restore();
    window.csClient.getSpecifiedChannels.restore();
  });

  it('renders with fake data', async () => {
    const user = {
      can_create_feature: true,
      can_edit: true,
      is_admin: false,
      email: 'example@google.com',
    };
    const component = await fixture(
      html`<chromedash-roadmap-page .user=${user}> </chromedash-roadmap-page>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashRoadmapPage);

    // subheader exists
    const subheaderDiv = component.shadowRoot.querySelector('div#subheader');
    assert.exists(subheaderDiv);

    // releases-section exists and contains the previous and next buttons
    const releasesSec = component.shadowRoot.querySelector(
      'section#releases-section'
    );
    assert.exists(releasesSec);
    assert.include(releasesSec.innerHTML, 'button id="previous-button"');
    assert.include(releasesSec.innerHTML, 'button id="next-button"');

    // chromedash-roadmap component exists
    const roadmap = component.shadowRoot.querySelector('chromedash-roadmap');
    assert.exists(roadmap);
  });
});
