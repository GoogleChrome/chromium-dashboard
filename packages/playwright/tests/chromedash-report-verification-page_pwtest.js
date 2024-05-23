// @ts-check
import {expect, test} from '@playwright/test';
import {captureConsoleMessages} from './test_utils';

import verifications_api_result from './verification_api_result.json';

test.beforeEach(({page}) => {
  captureConsoleMessages(page);
});

test('feature verification report renders', async ({page}) => {
  await page.route('/api/v0/verification', route =>
    route.fulfill({
      status: 200,
      body: `)]}'\n${JSON.stringify(verifications_api_result)}`,
    })
  );

  await page.goto('/reports/verification');

  await expect
    .soft(page.getByRole('heading', {level: 2}))
    .toHaveText('Features whose accuracy needs to be verified');

  // The table should have two columns.
  await expect
    .soft(page.getByRole('rowgroup').nth(0).getByRole('cell'))
    .toHaveText(['Feature', 'Last Verified']);

  // Features should show names and accurate-as-of dates (but not times).
  await expect
    .soft(page.getByRole('cell'))
    .toHaveText([
      'Feature',
      'Last Verified',
      'Feature one',
      'Nov 3, 2023',
      'Feature three',
      'May 7, 2024',
      'Feature two',
      'Nov 9, 2024',
    ]);

  // Features should link to their verification pages.
  await page.route('/api/v0/features/1001', route =>
    route.fulfill({
      status: 200,
      body: `)]}'\n${JSON.stringify({
        id: 1001,
        name: 'Feature one',
        stages: [],
        browsers: {
          chrome: {
            blink_components: ['Blink'],
            status: {},
          },
          ff: {view: {}},
          safari: {view: {}},
          webdev: {view: {}},
          other: {view: {}},
        },
        resources: {
          samples: [],
        },
        standards: {
          maturity: {},
          status: {},
        },
      })}`,
    })
  );
  await page.getByRole('table').getByRole('link').first().click();

  await expect(page.getByRole('heading', {level: 2})).toHaveText(
    'Verify feature data for Feature one'
  );
});
