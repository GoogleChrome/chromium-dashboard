import {html} from 'lit';
import {assert, fixture, nextFrame} from '@open-wc/testing';
import {ChromedashEnterpriseReleaseNotesPage} from './chromedash-enterprise-release-notes-page';
import {parseRawQuery, clearURLParams} from './utils.js';
import './chromedash-toast';
import '../js-src/cs-client';
import sinon from 'sinon';

describe('chromedash-feature-page', () => {
  const featuresPromise = Promise.resolve(
    {
      features: [
        {
          id: 1,
          name: 'feature with no stages',
          summary: 'feature 1 summary',
          enterprise_feature_categories: ['1', '2'],
          new_crbug_url: 'fake crbug link',
          stages: [],
        },
        {
          id: 2,
          name: 'feature with no rollout stages',
          summary: 'feature 2 summary',
          enterprise_feature_categories: ['1', '3'],
          new_crbug_url: 'fake crbug link',
          stages: [
            {
              id: 1,
              stage_type: 110,
            },
            {
              id: 2,
              stage_type: 120,
            },
          ],
        },
        {
          id: 3,
          name: 'feature with one rollout stages',
          summary: 'feature 3 summary',
          new_crbug_url: 'fake crbug link',
          enterprise_feature_categories: ['1', '2', '3'],
          stages: [
            {
              id: 3,
              stage_type: 1061,
              rollout_milestone: 100,
              rollout_details: 'fake rollout details 100',
              rollout_impact: 1,
              rollout_platforms: [],
            },
            {
              id: 4,
              stage_type: 120,
            },
          ],
        },
        {
          id: 4,
          name: 'feature with two consecutive rollout stages',
          summary: 'feature 4 summary',
          new_crbug_url: 'fake crbug link',
          enterprise_feature_categories: ['3'],
          stages: [
            {
              id: 5,
              stage_type: 1061,
              rollout_milestone: 100,
              rollout_details: 'fake rollout details 100',
              rollout_impact: 2,
              rollout_platforms: [],
            },
            {
              id: 6,
              stage_type: 1061,
              rollout_milestone: 101,
              rollout_details: 'fake rollout details 101',
              rollout_impact: 2,
              rollout_platforms: [],
            },
          ],
        },
        {
          id: 5,
          name: 'feature with past and future rollout stages',
          summary: 'feature 5 summary',
          new_crbug_url: 'fake crbug link',
          enterprise_feature_categories: ['2'],
          stages: [
            {
              id: 7,
              stage_type: 1061,
              rollout_milestone: 1,
              rollout_details: 'fake rollout details 1',
              rollout_impact: 3,
              rollout_platforms: [],
            },
            {
              id: 8,
              stage_type: 1061,
              rollout_milestone: 1000,
              rollout_details: 'fake rollout details 1000',
              rollout_impact: 2,
              rollout_platforms: [],
            },
          ],
        },
        {
          id: 6,
          name: 'feature with upcoming rollout stages',
          summary: 'feature 6 summary',
          new_crbug_url: 'fake crbug link',
          enterprise_feature_categories: ['2'],
          stages: [
            {
              id: 8,
              stage_type: 1061,
              rollout_milestone: 999,
              rollout_details: 'fake rollout details 999',
              rollout_impact: 2,
              rollout_platforms: [],
            },
          ],
        },
      ],
    });

  const channelsPromise = Promise.resolve({
    'stable': {
      'version': 100,
    },
  });

  beforeEach(async () => {
    await fixture(html`<chromedash-toast></chromedash-toast>`);
    window.csClient = new ChromeStatusClient('fake_token', 1);
    sinon.stub(window.csClient, 'searchFeatures');
    sinon.stub(window.csClient, 'getChannels');
    window.csClient.searchFeatures.returns(featuresPromise);
    window.csClient.getChannels.returns(channelsPromise);
  });

  afterEach(() => {
    window.csClient.searchFeatures.restore();
    window.csClient.getChannels.restore();
    clearURLParams('milestone');
  });

  it('reflects the milestone in the query params', async () => {
    const component = await fixture(html`
      <chromedash-enterprise-release-notes-page></chromedash-enterprise-release-notes-page>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashEnterpriseReleaseNotesPage);
    assert.equal(parseRawQuery(window.location.search).milestone, 100);

    // Select a future milestone
    component.selectedMilestone = 110;
    await nextFrame();
    assert.equal(parseRawQuery(window.location.search).milestone, 110);

    // Select a previous milestone
    component.selectedMilestone = 90;
    await nextFrame();
    assert.equal(parseRawQuery(window.location.search).milestone, 90);
  });

  it('renders with no data', async () => {
    const invalidFeaturePromise = Promise.reject(new Error('Got error response from server'));
    window.csClient.searchFeatures.returns(invalidFeaturePromise);

    const component = await fixture(html`
      <chromedash-enterprise-release-notes-page></chromedash-enterprise-release-notes-page>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashEnterpriseReleaseNotesPage);

    // invalid feature requests would trigger the toast to show message
    const toastEl = document.querySelector('chromedash-toast');
    const toastMsgSpan = toastEl.shadowRoot.querySelector('span#msg');
    assert.include(toastMsgSpan.innerHTML,
      'Some errors occurred. Please refresh the page or try again later.');
  });

  it('renders summary table with features in the right sections', async () => {
    const component = await fixture(html`
      <chromedash-enterprise-release-notes-page></chromedash-enterprise-release-notes-page>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashEnterpriseReleaseNotesPage);

    const releaseNotesSummary = component.shadowRoot.querySelector('#release-notes-summary');
    const children = [...releaseNotesSummary.querySelectorAll('tr > *')];

    // Validate first headers
    assert.equal(children[0].textContent, 'Chrome browser updates');
    assert.equal(children[1].textContent, 'Security / Privacy');
    assert.equal(children[2].textContent, 'User productivity / Apps');
    assert.equal(children[3].textContent, 'Management');

    // Validate first feature row
    assert.equal(children[4].textContent, 'feature with two consecutive rollout stages');
    assert.notInclude(children[5].textContent, '✓');
    assert.notInclude(children[6].textContent, '✓');
    assert.include(children[7].textContent, '✓');

    // Validate second feature row
    assert.equal(children[8].textContent, 'feature with one rollout stages');
    assert.include(children[9].textContent, '✓');
    assert.include(children[10].textContent, '✓');
    assert.include(children[11].textContent, '✓');

    // Validate second headers
    assert.equal(children[12].textContent, 'Upcoming Chrome browser updates');
    assert.equal(children[13].textContent, 'Security / Privacy');
    assert.equal(children[14].textContent, 'User productivity / Apps');
    assert.equal(children[15].textContent, 'Management');

    // Validate first upcoming feature row
    assert.equal(children[16].textContent, 'feature with upcoming rollout stages');
    assert.notInclude(children[17].textContent, '✓');
    assert.include(children[18].textContent, '✓');
    assert.notInclude(children[19].textContent, '✓');

    // Validate first upcoming feature row
    assert.equal(children[20].textContent, 'feature with past and future rollout stages');
    assert.notInclude(children[21].textContent, '✓');
    assert.include(children[22].textContent, '✓');
    assert.notInclude(children[23].textContent, '✓');
  });

  it('renders detailed release with features in the right sections', async () => {
    const component = await fixture(html`
      <chromedash-enterprise-release-notes-page></chromedash-enterprise-release-notes-page>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashEnterpriseReleaseNotesPage);

    const releaseNotes = [...component.shadowRoot.querySelectorAll('.note-section')];
    assert.equal(2, releaseNotes.length);

    // Test Chrome browser updates
    {
      assert.equal('Chrome browser updates', releaseNotes[0].querySelector('h2').textContent);
      const features = [...releaseNotes[0].querySelectorAll('.note-details > li')];

      // Test feature 1
      {
        assert.equal(
          'feature with two consecutive rollout stages',
          features[0].querySelector('strong').textContent);
        assert.equal(
          'feature 4 summary',
          features[0].querySelector('p').textContent);
        const stages = [...features[0].querySelectorAll('li')];
        assert.equal(2, stages.length);
        assert.include(stages[0].textContent, 'Chrome 100: ');
        assert.include(stages[0].textContent, 'fake rollout details 100');
        assert.include(stages[1].textContent, 'Chrome 101: ');
        assert.include(stages[1].textContent, 'fake rollout details 101');
      }

      // Test feature 2
      {
        assert.equal(
          'feature with one rollout stages',
          features[1].querySelector('strong').textContent);
        assert.equal(
          'feature 3 summary',
          features[1].querySelector('p').textContent);
        const stages = [...features[1].querySelectorAll('li')];
        assert.equal(1, stages.length);
        assert.include(stages[0].textContent, 'Chrome 100: ');
        assert.include(stages[0].textContent, 'fake rollout details 100');
      }
    }

    // Test Upcoming Chrome browser updates
    {
      assert.equal(
        'Upcoming Chrome browser updates',
        releaseNotes[1].querySelector('h2').textContent);
      const features = [...releaseNotes[1].querySelectorAll('.note-details > li')];

      // Test feature 1
      {
        assert.equal(
          'feature with upcoming rollout stages',
          features[0].querySelector('strong').textContent);
        assert.equal(
          'feature 6 summary',
          features[0].querySelector('p').textContent);
        const stages = [...features[0].querySelectorAll('li')];
        assert.equal(1, stages.length);
        assert.include(stages[0].textContent, 'Chrome 999: ');
        assert.include(stages[0].textContent, 'fake rollout details 999');
      }

      // Test feature 2
      {
        assert.equal(
          'feature with past and future rollout stages',
          features[1].querySelector('strong').textContent);
        assert.equal(
          'feature 5 summary',
          features[1].querySelector('p').textContent);
        const stages = [...features[1].querySelectorAll('li')];
        assert.equal(2, stages.length);
        assert.include(stages[0].textContent, 'Chrome 1: ');
        assert.include(stages[0].textContent, 'fake rollout details 1');
        assert.include(stages[1].textContent, 'Chrome 1000: ');
        assert.include(stages[1].textContent, 'fake rollout details 1000');
      }
    }
  });

  it('renders nothing if all rollouts are older', async () => {
    const component = await fixture(html`
      <chromedash-enterprise-release-notes-page></chromedash-enterprise-release-notes-page>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashEnterpriseReleaseNotesPage);

    // Select a future milestone
    component.selectedMilestone = 2000;
    await nextFrame();

    // Tests summary
    const releaseNotesSummary = component.shadowRoot.querySelector('#release-notes-summary');
    const children = [...releaseNotesSummary.querySelectorAll('tr > *')];

    // Validate first headers
    assert.equal(children[0].textContent, 'Chrome browser updates');
    assert.equal(children[1].textContent, 'Security / Privacy');
    assert.equal(children[2].textContent, 'User productivity / Apps');
    assert.equal(children[3].textContent, 'Management');

    // Validate first feature row
    assert.equal(children[4].textContent, 'Nothing');

    // Validate second headers
    assert.equal(children[5].textContent, 'Upcoming Chrome browser updates');
    assert.equal(children[6].textContent, 'Security / Privacy');
    assert.equal(children[7].textContent, 'User productivity / Apps');
    assert.equal(children[8].textContent, 'Management');

    // Validate first upcoming feature row
    assert.equal(children[9].textContent, 'Nothing');

    // Tests release notes
    const releaseNotes = [...component.shadowRoot.querySelectorAll('.note-section')];
    assert.equal(2, releaseNotes.length);

    // Test Chrome browser updates
    {
      assert.equal('Chrome browser updates', releaseNotes[0].querySelector('h2').textContent);
      const features = [...releaseNotes[0].querySelectorAll('.note-details > li')];
      assert.equal(0, features.length);
    }

    // Test Upcoming Chrome browser updates
    {
      assert.equal(
        'Upcoming Chrome browser updates',
        releaseNotes[1].querySelector('h2').textContent);
      const features = [...releaseNotes[1].querySelectorAll('.note-details > li')];
      assert.equal(0, features.length);
    }
  });
});
