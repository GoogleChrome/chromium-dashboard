// @ts-check
import {expect, test} from '@playwright/test';
import {captureConsoleMessages} from './test_utils';

import external_reviews_api_result from './external_reviews_api_result.json';

test.beforeEach(async ({page}, testInfo) => {
  captureConsoleMessages(page);
});

/**
 * @param {import('@playwright/test').Page} page
 * @param {string} heading
 * @returns {import('@playwright/test').Locator}
 */
function section(page, heading) {
  return page
    .locator('chromedash-report-external-reviews-page section')
    .filter({has: page.getByRole('heading', {name: heading})});
}

test('external reviewers report renders', async ({page}) => {
  await page.route('/api/v0/external_reviews/gecko', route =>
    route.fulfill({
      status: 200,
      body: `)]}'\n${JSON.stringify(external_reviews_api_result)}`,
    })
  );

  await page.goto('/reports/external_reviews/gecko');

  // Check that the page identifies the reviewer.
  await expect
    .soft(page.getByRole('heading', {level: 2}))
    .toContainText('Mozilla');

  // Check that the right subset of sections is present, in the right order.
  await expect
    .soft(page.getByRole('heading', {level: 3}))
    .toHaveText(['In Origin Trial', 'Prototyping', 'Already shipped']);

  // Features in origin trial.
  await expect(
    section(page, 'In Origin Trial').getByRole('row'),
    '1 feature'
  ).toHaveCount(2);
  await expect
    .soft(
      section(page, 'In Origin Trial').getByRole('row').nth(1).getByRole('cell')
    )
    .toHaveText([
      /Feature 7 shares a review with Feature 5/,
      /#5 A Title/,
      /M100–M104/,
    ]);
  await expect
    .soft(
      section(page, 'In Origin Trial')
        .getByRole('row')
        .nth(1)
        .getByRole('link', {name: 'Feature 7 shares a review with Feature 5'})
    )
    .toHaveAttribute('href', '/feature/1001');
  await expect
    .soft(
      section(page, 'In Origin Trial')
        .getByRole('row')
        .nth(1)
        .getByRole('link', {name: /#5 A Title/i})
    )
    .toHaveAttribute(
      'href',
      'https://github.com/mozilla/standards-positions/issues/5'
    );

  // Features in prototyping.
  await expect(
    section(page, 'Prototyping').getByRole('row'),
    '3 features'
  ).toHaveCount(4);
  await expect
    .soft(section(page, 'Prototyping').getByRole('row'))
    .toHaveText([/Feature/, /Feature 3/, /Feature 5/, /Feature 4/]); // In this order.
  await expect
    .soft(
      section(page, 'Prototyping')
        .getByRole('row')
        .filter({hasText: 'Feature 3'})
    )
    .toContainText('M101–M103');

  // Features that already shipped.
  await expect(
    section(page, 'Already shipped').getByRole('row'),
    '1 feature'
  ).toHaveCount(2);
  await expect
    .soft(section(page, 'Already shipped').getByRole('row').nth(1))
    .toContainText('Feature 2');
});

test('sorts features by target milestone', async ({page}) => {
  function feature(id, start, end) {
    return {
      current_stage: 'incubating',
      estimated_start_milestone: start,
      estimated_end_milestone: end,
      feature: {
        id,
        name: `Feature ${id}`,
      },
      review_link: `https://github.com/w3ctag/design-reviews/issues/${id}`,
    };
  }
  await page.route('/api/v0/external_reviews/tag', route =>
    route.fulfill({
      status: 200,
      body: `)]}'\n${JSON.stringify({
        reviews: [
          feature(1, null, null),
          feature(0, null, null),
          feature(2, 100, null),
          feature(3, 101, null),
          feature(4, null, 109),
          feature(5, null, 102),
          feature(6, 104, 107),
          feature(7, 103, 108),
          feature(8, 105, 106),
        ],
        link_previews: [1, 2, 3, 4, 5].map(id => ({
          information: {
            created_at: '2024-04-15T08:30:42',
            labels: [],
            number: id,
            state: 'open',
            title: 'A Title',
            updated_at: '2024-04-15T10:30:43',
            url: `https://api.github.com/mozilla/standards-positions/issues/${id}`,
          },
          type: 'github_issue',
          url: `https://github.com/mozilla/standards-positions/issues/${id}`,
        })),
      })}`,
    })
  );

  await page.goto('/reports/external_reviews/tag');

  await expect.soft(section(page, 'Incubating').getByRole('row')).toHaveText([
    // Header row
    /Feature/,
    // Sort first by end milestone.
    /Feature 5/,
    /Feature 8/,
    /Feature 6/,
    /Feature 7/,
    /Feature 4/,
    // Then by start milestone.
    /Feature 2/,
    /Feature 3/,
    // Then list features without any milestones, in order of review link.
    /Feature 0/,
    /Feature 1/,
  ]);
});
