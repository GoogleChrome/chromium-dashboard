import {fixture, html, assert, elementUpdated} from '@open-wc/testing';
import sinon from 'sinon';
import {ChromedashStaleFeaturesPage} from './chromedash-stale-features-page';
import './chromedash-stale-features-page';

const csClient = {
  getStaleFeatures: sinon.stub(),
};
window.csClient = csClient;

const MOCK_STALE_FEATURES = [
  {
    id: 1,
    name: 'Feature C',
    owner_emails: ['owner1@example.com'],
    milestone: 102,
    milestone_field: 'shipped_milestone',
    outstanding_notifications: 3,
    accurate_as_of: '2023-01-15T00:00:00Z',
  },
  {
    id: 2,
    name: 'Feature A',
    owner_emails: ['owner2@example.com'],
    milestone: 100,
    milestone_field: 'shipped_milestone',
    outstanding_notifications: 5,
    accurate_as_of: '2023-03-10T00:00:00Z',
  },
  {
    id: 3,
    name: 'Feature B',
    owner_emails: ['owner3@example.com'],
    milestone: 101,
    milestone_field: 'shipped_milestone',
    outstanding_notifications: 1,
    accurate_as_of: '2023-02-20T00:00:00Z',
  },
];

describe('ChromedashStaleFeaturesPage', () => {
  let element: ChromedashStaleFeaturesPage;

  beforeEach(() => {
    csClient.getStaleFeatures.reset();
  });

  describe('rendering and loading', () => {
    it('renders loading skeletons initially', async () => {
      csClient.getStaleFeatures.returns(new Promise(() => {})); // Prevent promise from resolving
      element = await fixture(
        html`<chromedash-stale-features-page></chromedash-stale-features-page>`
      );
      await elementUpdated(element);

      const skeleton = element.shadowRoot?.querySelector('sl-skeleton');
      assert.isNotNull(skeleton, 'Skeleton should be rendered while loading');

      const table = element.shadowRoot?.querySelector('table');
      assert.isNull(table, 'Table should not be rendered while loading');
    });

    it('renders the subheader', async () => {
      csClient.getStaleFeatures.resolves({stale_features: []});
      element = await fixture(
        html`<chromedash-stale-features-page></chromedash-stale-features-page>`
      );
      await element.updateComplete;

      const subheader = element.shadowRoot?.querySelector('#subheader');
      assert.isNotNull(subheader);
      const breadcrumbs = subheader?.querySelector('#breadcrumbs');
      assert.strictEqual(breadcrumbs?.textContent?.trim(), 'Stale Features');
    });

    it('fetches and renders stale features on connection', async () => {
      csClient.getStaleFeatures.resolves({
        stale_features: MOCK_STALE_FEATURES,
      });
      element = await fixture(
        html`<chromedash-stale-features-page></chromedash-stale-features-page>`
      );
      await element.updateComplete;

      const rows = element.shadowRoot?.querySelectorAll('tbody tr');
      assert.isNotNull(rows);
      assert.lengthOf(
        rows || [],
        MOCK_STALE_FEATURES.length,
        'Should render a row for each feature'
      );

      // Check content of the first row (after default sorting by name)
      const firstRowCells = rows?.[0].querySelectorAll('td');
      assert.isNotNull(firstRowCells);
      assert.include(
        firstRowCells?.[0].textContent,
        'Feature A',
        'First row should contain Feature A'
      );
      assert.include(
        firstRowCells?.[1].textContent,
        'owner2@example.com',
        'Email should be correct'
      );
    });

    it('displays a message when no stale features are found', async () => {
      csClient.getStaleFeatures.resolves({stale_features: []});
      element = await fixture(
        html`<chromedash-stale-features-page></chromedash-stale-features-page>`
      );
      await element.updateComplete;

      const noFeaturesDiv = element.shadowRoot?.querySelector('.no-features');
      assert.isNotNull(
        noFeaturesDiv,
        'Message for no features should be displayed'
      );
      assert.include(
        noFeaturesDiv?.textContent,
        'No stale features found. Great job!'
      );
    });
  });

  describe('sorting', () => {
    beforeEach(async () => {
      csClient.getStaleFeatures.resolves({
        stale_features: MOCK_STALE_FEATURES,
      });
      element = await fixture(
        html`<chromedash-stale-features-page></chromedash-stale-features-page>`
      );
      await element.updateComplete;
    });

    const getRenderedFeatureNames = (
      el: ChromedashStaleFeaturesPage
    ): string[] => {
      const rows = el.shadowRoot?.querySelectorAll('tbody tr');
      if (!rows) return [];
      return Array.from(rows).map(
        row => row.querySelector('td:first-child a')?.textContent?.trim() || ''
      );
    };

    it('sorts by name ascending by default', () => {
      const featureNames = getRenderedFeatureNames(element);
      assert.deepEqual(featureNames, ['Feature A', 'Feature B', 'Feature C']);
    });

    it('reverses sort direction when clicking the same column header', async () => {
      const nameHeader = Array.from(
        element.shadowRoot?.querySelectorAll('th.sortable') || []
      ).find(th => th.textContent?.includes('Name')) as HTMLElement;
      nameHeader.click();
      await element.updateComplete;

      const featureNames = getRenderedFeatureNames(element);
      assert.deepEqual(
        featureNames,
        ['Feature C', 'Feature B', 'Feature A'],
        'Should be sorted descending'
      );

      const sortIndicator = nameHeader.querySelector('.sort-indicator');
      assert.strictEqual(sortIndicator?.textContent?.trim(), '▼');
    });

    it('sorts by milestone when clicking the milestone header', async () => {
      const milestoneHeader = Array.from(
        element.shadowRoot?.querySelectorAll('th.sortable') || []
      ).find(
        th =>
          th.textContent?.includes('Milestone') &&
          !th.textContent?.includes('Field')
      ) as HTMLElement;
      milestoneHeader.click();
      await element.updateComplete;

      const featureNames = getRenderedFeatureNames(element);
      assert.deepEqual(
        featureNames,
        ['Feature A', 'Feature B', 'Feature C'],
        'Sorted by milestone ascending'
      );

      const sortIndicator = milestoneHeader.querySelector('.sort-indicator');
      assert.strictEqual(sortIndicator?.textContent?.trim(), '▲');
    });

    it('sorts by notifications when clicking the notifications header', async () => {
      const notificationsHeader = Array.from(
        element.shadowRoot?.querySelectorAll('th.sortable') || []
      ).find(th => th.textContent?.includes('Notifications')) as HTMLElement;
      notificationsHeader.click();
      await element.updateComplete;

      const featureNames = getRenderedFeatureNames(element);
      assert.deepEqual(
        featureNames,
        ['Feature B', 'Feature C', 'Feature A'],
        'Sorted by notifications ascending'
      );
    });

    it('sorts by last updated date when clicking the date header', async () => {
      const dateHeader = Array.from(
        element.shadowRoot?.querySelectorAll('th.sortable') || []
      ).find(th => th.textContent?.includes('Last Updated')) as HTMLElement;
      dateHeader.click();
      await element.updateComplete;

      const featureNames = getRenderedFeatureNames(element);
      assert.deepEqual(
        featureNames,
        ['Feature C', 'Feature B', 'Feature A'],
        'Sorted by date ascending'
      );
    });
  });
});
