// @ts-check
import { expect, test } from '@playwright/test';
import { captureConsoleMessages } from './test_utils';
import external_reviews_api_result from './external_reviews_api_result.json';

const API_PREFIX = ")]}'\n";

test.beforeEach(async ({ page }) => {
  captureConsoleMessages(page);
});

/**
 * Locates a section by its heading text.
 * @param {import('@playwright/test').Page} page
 * @param {string} headingText
 */
function getSection(page, headingText) {
  // Finds a <section> that contains a heading with the specific name
  return page.locator('chromedash-report-external-reviews-page section').filter({
    has: page.getByRole('heading', { name: headingText })
  });
}

test('external reviewers report renders', async ({ page }) => {
  await test.step('Setup: Mock API and Navigate', async () => {
    await page.route('/api/v0/external_reviews/gecko', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: API_PREFIX + JSON.stringify(external_reviews_api_result),
      });
    });
    await page.goto('/reports/external_reviews/gecko');
  });

  await test.step('Verify Headers', async () => {
    await expect(page.getByRole('heading', { level: 2 })).toContainText('Mozilla');
    await expect(page.getByRole('heading', { level: 3 })).toHaveText([
      'In Origin Trial',
      'Prototyping',
      'Already shipped'
    ]);
  });

  await test.step('Verify "In Origin Trial" section', async () => {
    const section = getSection(page, 'In Origin Trial');
    const rows = section.getByRole('row');

    // Expect 2 rows: 1 header + 1 data row
    await expect(rows).toHaveCount(2);

    // Verify Data Row Content
    // We match the whole row text once, rather than individual cells, for speed
    const dataRow = rows.nth(1);
    await expect(dataRow).toContainText('Feature 7 shares a review with Feature 5');
    await expect(dataRow).toContainText('#5 A Title');
    await expect(dataRow).toContainText('M100–M104');

    // Verify Links
    await expect(dataRow.getByRole('link', { name: 'Feature 7 shares a review with Feature 5' }))
      .toHaveAttribute('href', '/feature/1001');

    await expect(dataRow.getByRole('link', { name: /#5 A Title/i }))
      .toHaveAttribute('href', 'https://github.com/mozilla/standards-positions/issues/5');
  });

  await test.step('Verify "Prototyping" section', async () => {
    const section = getSection(page, 'Prototyping');
    const rows = section.getByRole('row');

    // 1 header + 3 data rows = 4
    await expect(rows).toHaveCount(4);

    // Verify Row Order & Content
    // Checking the array ensures the order is correct in one assertion
    await expect(rows).toHaveText([
      /Feature/,
      /Feature 3/,
      /Feature 5/,
      /Feature 4/
    ]);

    // Specific check for Feature 3 details
    await expect(rows.filter({ hasText: 'Feature 3' }))
      .toContainText('M101–M103');
  });

  await test.step('Verify "Already shipped" section', async () => {
    const section = getSection(page, 'Already shipped');
    await expect(section.getByRole('row')).toHaveCount(2);
    await expect(section).toContainText('Feature 2');
  });
});

test('sorts features by target milestone', async ({ page }) => {
  // Factory for cleaner mock data generation
  const createFeature = (id, start, end) => ({
    current_stage: 'incubating',
    estimated_start_milestone: start,
    estimated_end_milestone: end,
    feature: { id, name: `Feature ${id}` },
    review_link: `https://github.com/w3ctag/design-reviews/issues/${id}`,
  });

  await test.step('Setup: Mock API with unsorted data', async () => {
    const mockData = {
      reviews: [
        createFeature(1, null, null),
        createFeature(0, null, null),
        createFeature(2, 100, null),
        createFeature(3, 101, null),
        createFeature(4, null, 109),
        createFeature(5, null, 102),
        createFeature(6, 104, 107),
        createFeature(7, 103, 108),
        createFeature(8, 105, 106),
      ],
      link_previews: []
    };

    await page.route('/api/v0/external_reviews/tag', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: API_PREFIX + JSON.stringify(mockData),
      });
    });

    await page.goto('/reports/external_reviews/tag');
  });

  await test.step('Verify Sort Order', async () => {
    const section = getSection(page, 'Incubating');

    // Validate exact order of rows:
    // 1. By End Milestone (asc)
    // 2. By Start Milestone (asc)
    // 3. No milestone (by ID/Review Link)
    await expect(section.getByRole('row')).toHaveText([
      /Feature/,   // Header
      /Feature 5/, // End: 102
      /Feature 8/, // End: 106
      /Feature 6/, // End: 107
      /Feature 7/, // End: 108
      /Feature 4/, // End: 109
      /Feature 2/, // Start: 100 (No End)
      /Feature 3/, // Start: 101 (No End)
      /Feature 0/, // No milestones (ID 0)
      /Feature 1/, // No milestones (ID 1)
    ]);
  });
});
