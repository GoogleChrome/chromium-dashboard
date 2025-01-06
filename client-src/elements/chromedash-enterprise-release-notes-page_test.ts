import {html} from 'lit';
import {assert, fixture, nextFrame} from '@open-wc/testing';
import {ChromedashEnterpriseReleaseNotesPage} from './chromedash-enterprise-release-notes-page';
import {parseRawQuery, clearURLParams} from './utils.js';
import './chromedash-toast';
import {ChromeStatusClient} from '../js-src/cs-client';
import sinon from 'sinon';

function normalizedTextContent(element) {
  return element.textContent
    .replace(/^\s+/, '')
    .replace(/\s+$/, '')
    .replaceAll(/\s+/g, ' ');
}

// prettier-ignore
describe('chromedash-enterprise-release-notes-page', () => {
  const featuresPromise = Promise.resolve(
    {
      features: [
        {
          id: 1,
          name: 'feature with no stages',
          summary: 'feature 1 summary',
          editors: ['editor1', 'editor2'],
          enterprise_feature_categories: ['1', '2'],
          new_crbug_url: 'fake crbug link',
          stages: [],
          browsers: {
            chrome: {
              owners: ['owner'],
            },
          },
          updated: {
            when: 'feature1 updated',
          },
          screenshot_links: [],
        },
        {
          id: 2,
          name: 'feature with no rollout stages',
          summary: 'feature 2 summary',
          editors: ['editor1', 'editor2'],
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
          browsers: {
            chrome: {
              owners: ['owner'],
            },
          },
          updated: {
            when: 'updated when',
          },
          screenshot_links: [],
        },
        {
          id: 3,
          name: 'feature with one rollout stages',
          summary: 'feature 3 summary',
          new_crbug_url: 'fake crbug link',
          editors: ['editor1', 'editor2'],
          enterprise_feature_categories: ['1', '2', '3'],
          enterprise_product_category: 0,
          first_enterprise_notification_milestone: 'n_milestone_feat_3',
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
          browsers: {
            chrome: {
              owners: ['owner'],
            },
          },
          updated: {
            when: 'updated when',
          },
          screenshot_links: ['https://example.com/screenshot1'],
        },
        {
          id: 4,
          name: 'feature with two consecutive rollout stages',
          summary: 'feature 4 summary',
          new_crbug_url: 'fake crbug link',
          editors: ['editor1'],
          enterprise_feature_categories: ['3'],
          enterprise_product_category: 1,
          first_enterprise_notification_milestone: 'n_milestone_feat_4',
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
          browsers: {
            chrome: {
              owners: ['owner1'],
            },
          },
          updated: {
            when: 'feature 4 updated',
          },
          screenshot_links: ['https://example.com/screenshot1', 'https://example.com/screenshot2'],
        },
        {
          id: 5,
          name: 'feature with past and future rollout stages',
          summary: 'feature 5 summary',
          new_crbug_url: 'fake crbug link',
          editors: ['editor1', 'editor2'],
          enterprise_feature_categories: ['2'],
          enterprise_product_category: 3,
          first_enterprise_notification_milestone: 'n_milestone_feat_5',
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
          browsers: {
            chrome: {
              owners: ['owner'],
            },
          },
          updated: {
            when: 'updated when',
          },
          screenshot_links: ['https://example.com/screenshot1'],
        },
        {
          id: 6,
          name: 'feature with upcoming rollout stages',
          summary: 'feature 6 summary',
          new_crbug_url: 'fake crbug link',
          editors: ['editor1', 'editor2'],
          enterprise_feature_categories: ['2'],
          enterprise_product_category: 0,
          first_enterprise_notification_milestone: 'n_milestone_feat_6',
          stages: [
            {
              id: 9,
              stage_type: 1061,
              rollout_milestone: 999,
              rollout_details: 'fake rollout details 999',
              rollout_impact: 2,
              rollout_platforms: [],
            },
          ],
          browsers: {
            chrome: {
              owners: ['owner'],
            },
          },
          updated: {
            when: 'updated when',
          },
          screenshot_links: [],
        },
        {
          id: 7,
          name: 'normal feature with shipping stage',
          summary: 'normal feature summary',
          new_crbug_url: 'fake crbug link',
          editors: ['editor1', 'editor2'],
          enterprise_feature_categories: [],
          enterprise_product_category: 1,
          first_enterprise_notification_milestone: 'n_milestone_feat_7',
          stages: [
            {
              id: 10,
              stage_type: 460,
              desktop_first: 100,
              desktop_last: 101,
              android_first: 100,
              android_last: 101,
              ios_first: 102,
              ios_last: 103,
              webview_first: 100,
              webview_last: 102,
            },
          ],
          browsers: {
            chrome: {
              owners: ['owner'],
            },
          },
          updated: {
            when: 'updated when',
          },
          screenshot_links: [],
        },
        {
          id: 8,
          name: 'future premium feature',
          summary: 'future premium feature summary',
          new_crbug_url: 'fake crbug link',
          editors: ['editor1', 'editor2'],
          enterprise_feature_categories: [],
          enterprise_product_category: 2,
          first_enterprise_notification_milestone: 'n_milestone_feat_8',
          stages: [
            {
              id: 11,
              stage_type: 1061,
              rollout_milestone: 1000,
              rollout_details: 'fake rollout details 1000',
              rollout_impact: 2,
              rollout_platforms: [],
            },
          ],
          browsers: {
            chrome: {
              owners: ['owner'],
            },
          },
          updated: {
            when: 'updated when',
          },
          screenshot_links: [],
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
    sinon.stub(window.csClient, 'getFeaturesForEnterpriseReleaseNotes');
    sinon.stub(window.csClient, 'getChannels');
    window.csClient.getFeaturesForEnterpriseReleaseNotes.returns(featuresPromise);
    window.csClient.getChannels.returns(channelsPromise);
  });

  afterEach(() => {
    window.csClient.getFeaturesForEnterpriseReleaseNotes.restore();
    window.csClient.getChannels.restore();
    clearURLParams('milestone');
  });

  it('reflects the milestone in the query params', async () => {
    const component = await fixture(html`
      <chromedash-enterprise-release-notes-page></chromedash-enterprise-release-notes-page>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashEnterpriseReleaseNotesPage);
    assert.equal((parseRawQuery(window.location.search)).milestone, '100');

    // Select a future milestone
    component.selectedMilestone = 110;
    await nextFrame();
    assert.equal((parseRawQuery(window.location.search)).milestone, '110');

    // Select a previous milestone
    component.selectedMilestone = 90;
    await nextFrame();
    assert.equal((parseRawQuery(window.location.search)).milestone, '90');
  });

  it('renders with no data', async () => {
    const invalidFeaturePromise = Promise.reject(new Error('Got error response from server'));
    window.csClient.getFeaturesForEnterpriseReleaseNotes.returns(invalidFeaturePromise);

    const component = await fixture(html`
      <chromedash-enterprise-release-notes-page></chromedash-enterprise-release-notes-page>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashEnterpriseReleaseNotesPage);

    // invalid feature requests would trigger the toast to show message
    const toastEl = document.querySelector('chromedash-toast');
    const toastMsgSpan = toastEl?.shadowRoot?.querySelector('span#msg');
    assert.include(toastMsgSpan?.innerHTML,
      'Some errors occurred. Please refresh the page or try again later.');
  });

  it('renders summary table with features in the right sections', async () => {
    const component = await fixture(html`
      <chromedash-enterprise-release-notes-page></chromedash-enterprise-release-notes-page>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashEnterpriseReleaseNotesPage);

    const releaseNotesSummary = component.renderRoot.querySelector('#release-notes-summary');
    const children = Array.from(releaseNotesSummary!.querySelectorAll('tr > *'));

    // Validate chrome browser updates
    assert.equal(children[0].textContent, 'Chrome Browser updates');
    assert.equal(children[1].textContent, 'Security / Privacy');
    assert.equal(children[2].textContent, 'User productivity / Apps');
    assert.equal(children[3].textContent, 'Management');
    assert.equal(children[4].textContent, 'feature with one rollout stages');
    assert.include(children[5].textContent, '✓');
    assert.include(children[6].textContent, '✓');
    assert.include(children[7].textContent, '✓');

    // Validate chrome enterprise core
    assert.equal(children[8].textContent, 'Chrome Enterprise Core (CEC)');
    assert.equal(children[9].textContent, 'Security / Privacy');
    assert.equal(children[10].textContent, 'User productivity / Apps');
    assert.equal(children[11].textContent, 'Management');

    assert.equal(children[12].textContent, 'feature with two consecutive rollout stages');
    assert.notInclude(children[13].textContent, '✓');
    assert.notInclude(children[14].textContent, '✓');
    assert.include(children[15].textContent, '✓');
  
    assert.equal(children[16].textContent, 'normal feature with shipping stage');
    assert.notInclude(children[17].textContent, '✓');
    assert.notInclude(children[18].textContent, '✓');
    assert.notInclude(children[19].textContent, '✓');

    // Validate chrome enterprise premium
    assert.equal(children[20].textContent, 'Chrome Enterprise Premium (CEP, paid SKU)');
    assert.equal(children[21].textContent, 'Security / Privacy');
    assert.equal(children[22].textContent, 'User productivity / Apps');
    assert.equal(children[23].textContent, 'Management');

    assert.equal(children[24].textContent, 'Nothing');
  
    // Validate upcoming chrome browser updates
    assert.equal(children[25].textContent, 'Upcoming Chrome Browser updates');
    assert.equal(children[26].textContent, 'Security / Privacy');
    assert.equal(children[27].textContent, 'User productivity / Apps');
    assert.equal(children[28].textContent, 'Management');

    assert.equal(children[29].textContent, 'feature with upcoming rollout stages');
    assert.notInclude(children[30].textContent, '✓');
    assert.include(children[31].textContent, '✓');
    assert.notInclude(children[32].textContent, '✓');

    // Validate upcoming chrome enterprise core
    assert.equal(children[33].textContent, 'Upcoming Chrome Enterprise Core (CEC)');
    assert.equal(children[34].textContent, 'Security / Privacy');
    assert.equal(children[35].textContent, 'User productivity / Apps');
    assert.equal(children[36].textContent, 'Management');

    assert.equal(children[37].textContent, 'Nothing');

    // Validate upcoming chrome enterprise premium
    assert.equal(children[38].textContent, 'Upcoming Chrome Enterprise Premium (CEP, paid SKU)');
    assert.equal(children[39].textContent, 'Security / Privacy');
    assert.equal(children[40].textContent, 'User productivity / Apps');
    assert.equal(children[41].textContent, 'Management');

    assert.equal(children[42].textContent, 'future premium feature');
    assert.notInclude(children[43].textContent, '✓');
    assert.notInclude(children[44].textContent, '✓');
    assert.notInclude(children[45].textContent, '✓');
  });

  it('renders detailed release with features in the right sections', async () => {
    const component = await fixture(html`
      <chromedash-enterprise-release-notes-page></chromedash-enterprise-release-notes-page>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashEnterpriseReleaseNotesPage);

    const releaseNotes = Array.from(component.shadowRoot!.querySelectorAll('.note-section'));
    assert.lengthOf(releaseNotes, 6);

    // // Test Chrome Browser updates
    // {
    //   assert.equal('Chrome Browser updates', releaseNotes[0].querySelector('h2')!.textContent);
    //   const features = Array.from(releaseNotes[0].querySelectorAll('.feature'));

    //   // Test feature 1
    //   {
    //     assert.equal(
    //       'feature with one rollout stages',
    //       features[0].querySelector('strong')!.textContent);
    //     assert.equal(
    //       '< To remove - Feature details - ' +
    //       'Owners: owner - Editors: editor1, editor2 - First Notice: n_milestone_feat_3 - ' +
    //       'Last Updated: updated when >',
    //       normalizedTextContent(features[0].querySelector('.toremove')));
    //     assert.equal(
    //       'feature 3 summary',
    //       features[0].querySelector('.summary')!.textContent);
    //     const stages = Array.from(features[0].querySelectorAll('li'));
    //     assert.equal(1, stages.length);
    //     assert.include(stages[0].textContent, 'Chrome 100');
    //     assert.include(stages[0].textContent, 'fake rollout details 100');

    //     const screenshots: HTMLImageElement[] = Array.from(features[0].querySelectorAll('.screenshots img'));
    //     assert.lengthOf(screenshots, 1);
    //     assert.equal(screenshots[0].src, 'https://example.com/screenshot1');
    //     assert.equal(screenshots[0].alt, 'Feature screenshot 1');
    //   }
    // }

    // // Test Chrome Enterprise Core
    // {
    //   assert.equal(
    //     'Chrome Enterprise Core (CEC)',
    //     releaseNotes[1].querySelector('h2')!.textContent);
    //   const features = Array.from(releaseNotes[1].querySelectorAll('.feature'));

    //   // Test feature 1
    //   {
    //     assert.equal(
    //       'feature with two consecutive rollout stages',
    //       features[0].querySelector('strong')!.textContent);
    //     assert.equal(
    //       '< To remove - Feature details - ' +
    //       'Owners: owner1 - Editors: editor1 - First Notice: n_milestone_feat_4 - ' +
    //       'Last Updated: feature 4 updated >',
    //       normalizedTextContent(features[0].querySelector('.toremove')));
    //     assert.equal(
    //       'feature 4 summary',
    //       features[0].querySelector('.summary')!.textContent);
    //     const stages = Array.from(features[0].querySelectorAll('li'));
    //     assert.equal(2, stages.length);
    //     assert.include(stages[0].textContent, 'Chrome 100');
    //     assert.include(stages[0].textContent, 'fake rollout details 100');
    //     assert.include(stages[1].textContent, 'Chrome 101');
    //     assert.include(stages[1].textContent, 'fake rollout details 101');

    //     const screenshots: HTMLImageElement[] = Array.from(features[0].querySelectorAll('.screenshots img'));
    //     assert.lengthOf(screenshots, 2);
    //     assert.equal(screenshots[0].src, 'https://example.com/screenshot1');
    //     assert.equal(screenshots[0].alt, 'Feature screenshot 1');
    //     assert.equal(screenshots[1].src, 'https://example.com/screenshot2');
    //     assert.equal(screenshots[1].alt, 'Feature screenshot 2');
    //   }
    
    //   // Feature 2
    //   {
    //     assert.equal(
    //       'normal feature with shipping stage',
    //       features[1].querySelector('strong')!.textContent);
    //     assert.equal(
    //       '< To remove - Feature details - ' +
    //       'Owners: owner - Editors: editor1, editor2 - First Notice: n_milestone_feat_7 - ' +
    //       'Last Updated: updated when >',
    //       normalizedTextContent(features[1].querySelector('.toremove')));
    //     assert.equal(
    //       'normal feature summary',
    //       features[1].querySelector('.summary')!.textContent);
    //     const stages = Array.from(features[1].querySelectorAll('li'));
    //     assert.equal(4, stages.length);
    //     assert.include(stages[0].textContent, 'Chrome 100 on Windows, MacOS, Linux, Android');
    //     assert.include(stages[1].textContent, 'Chrome 101 on Windows, MacOS, Linux, Android');
    //     assert.include(stages[2].textContent, 'Chrome 102 on iOS, Android');
    //     assert.include(stages[3].textContent, 'Chrome 103 on iOS');

    //     const screenshots: HTMLImageElement[] = Array.from(features[1].querySelectorAll('.screenshots img'));
    //     assert.isEmpty(screenshots);
    //   }
    // }

    // Test Chrome Enterprise Premium
    {
      assert.equal(
        'Chrome Enterprise Premium (CEP, paid SKU)',
        releaseNotes[2].querySelector('h2')!.textContent);
      const features = Array.from(releaseNotes[2].querySelectorAll('.feature'));
      assert.isEmpty(features);
    }
  
    // Test Upcoming Chrome Browser updates
    {
      assert.equal(
        'Upcoming Chrome Browser updates',
        releaseNotes[3].querySelector('h2')!.textContent);
      const features = Array.from(releaseNotes[3].querySelectorAll('.feature'));
      {
        assert.equal(
          'feature with upcoming rollout stages',
          features[0].querySelector('strong')!.textContent);
        assert.equal(
          '< To remove - Feature details - ' +
          'Owners: owner - Editors: editor1, editor2 - First Notice: n_milestone_feat_6 - ' +
          'Last Updated: updated when >',
          normalizedTextContent(features[0].querySelector('.toremove')));
        assert.equal(
          'feature 6 summary',
          features[0].querySelector('.summary')!.textContent);
        const stages = Array.from(features[0].querySelectorAll('li'));
        assert.equal(1, stages.length);
        assert.include(stages[0].textContent, 'Chrome 999');
        assert.include(stages[0].textContent, 'fake rollout details 999');

        const screenshots = Array.from(features[0].querySelectorAll('.screenshots img'));
        assert.isEmpty(screenshots);
      }
    }
    
    // Test Upcoming Chrome Enterprise Core
    {
      assert.equal(
        'Upcoming Chrome Enterprise Core (CEC)',
        releaseNotes[4].querySelector('h2')!.textContent);
      const features = Array.from(releaseNotes[4].querySelectorAll('.feature'));
      assert.isEmpty(features);
    }

    // Test Upcoming Chrome Enterprise Premium
    {
      assert.equal(
        'Upcoming Chrome Enterprise Premium (CEP, paid SKU)',
        releaseNotes[5].querySelector('h2')!.textContent);
      const features = Array.from(releaseNotes[5].querySelectorAll('.feature'));
      // Test feature 1
      {
        assert.equal(
          'future premium feature',
          features[0].querySelector('strong')!.textContent);
        assert.equal(
          '< To remove - Feature details - ' +
          'Owners: owner - Editors: editor1, editor2 - First Notice: n_milestone_feat_8 - ' +
          'Last Updated: updated when >',
          normalizedTextContent(features[0].querySelector('.toremove')));
        assert.equal(
          'future premium feature summary',
          features[0].querySelector('.summary')!.textContent);
        const stages = Array.from(features[0].querySelectorAll('li'));
        assert.equal(1, stages.length);
        assert.include(stages[0].textContent, 'Chrome 1000');
        assert.include(stages[0].textContent, 'fake rollout details 1000');

        const screenshots = Array.from(features[0].querySelectorAll('.screenshots img'));
        assert.isEmpty(screenshots);
      }
    }
  });
});
