// @ts-check
import {expect, test} from '@playwright/test';
import {captureConsoleMessages} from './test_utils';

import spec_mentor_api_result from './spec_mentor_api_result.json';

test.beforeEach(async ({page}, testInfo) => {
  captureConsoleMessages(page);
});

test('spec mentors report renders', async ({page}) => {
  await page.route('/api/v0/spec_mentors?after=*', route => route.fulfill({
    status: 200,
    body: `)]}'\n${JSON.stringify(spec_mentor_api_result)}`,
  }));

  await page.goto('/reports/spec_mentors');

  // <details> elements have the 'group' role:
  await expect.soft(page.getByRole('group').filter({hasText: /has mentored:/}))
    .toHaveText([/expert@example.com/, /mentor@example.org/]);

  const expertLink = page.locator('sl-details', {hasText: 'expert@example.com has mentored'})
    .getByRole('link');
  await expect.soft(expertLink).toHaveText("First feature");
  await expect.soft(expertLink).toHaveAttribute("href", /\/feature\/9009/);

  const mentorLinks = page.locator('sl-details', {hasText: "mentor@example.org has mentored"})
    .getByRole('link');
  await expect.soft(mentorLinks.nth(0)).toHaveText("Second feature");
  await expect.soft(mentorLinks.nth(0)).toHaveAttribute("href", /\/feature\/9010/);
  await expect.soft(mentorLinks.nth(1)).toHaveText("First feature");
  await expect.soft(mentorLinks.nth(1)).toHaveAttribute("href", /\/feature\/9009/);
});
