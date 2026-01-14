// @ts-check
import { expect, test } from '@playwright/test';
import { captureConsoleMessages } from './test_utils';
import spec_mentor_api_result from './spec_mentor_api_result.json';

// Define common mock data constants
// The prefix ")]}'\n" is a standard Chromium XSSI defense.
const API_PREFIX = ")]}'\n";
const MOCK_BODY = API_PREFIX + JSON.stringify(spec_mentor_api_result);

test.beforeEach(async ({ page }) => {
  captureConsoleMessages(page);

  // Setup the route once for all tests.
  // This ensures consistent behavior and reduces code duplication.
  await page.route('/api/v0/spec_mentors?after=*', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: MOCK_BODY,
    });
  });
});

test('spec mentors report renders', async ({ page }) => {
  await page.goto('/reports/spec_mentors');

  await test.step('Verify Mentor groupings', async () => {
    // Assert on the entire list of headers at once.
    // This is cleaner than checking them individually.
    await expect(page.getByRole('group').filter({ hasText: /has mentored:/ }))
      .toHaveText([
        /expert@example.com/,
        /mentor@example.org/
      ]);
  });

  await test.step('Verify "Expert" mentor details', async () => {
    // Scope locators to the specific panel to avoid accidental cross-talk
    const expertPanel = page.locator('sl-details', { hasText: 'expert@example.com' });
    const links = expertPanel.getByRole('link');

    // Verify text and href link correctness
    await expect(links).toHaveText(['First feature']);
    await expect(links).toHaveAttribute('href', /\/feature\/9009/);
  });

  await test.step('Verify "Mentor" mentor details', async () => {
    const mentorPanel = page.locator('sl-details', { hasText: 'mentor@example.org' });
    const links = mentorPanel.getByRole('link');

    // Verify order and content of multiple links simultaneously
    // This replaces the brittle .nth(0) and .nth(1) calls
    await expect(links).toHaveText(['Second feature', 'First feature']);

    // Note: for attributes, we still check individually or use specific matchers,
    // but scoping strictly to 'links' ensures we don't grab other elements.
    await expect(links.first()).toHaveAttribute('href', /\/feature\/9010/);
    await expect(links.last()).toHaveAttribute('href', /\/feature\/9009/);
  });
});

test('after query param affects api request', async ({ page }) => {
  const apiRequestPromise = page.waitForRequest(req =>
    req.url().includes('/api/v0/spec_mentors') &&
    req.url().endsWith('after=2023-04-05')
  );

  await page.goto('/reports/spec_mentors?after=2023-04-05');

  // Wait for the specific request to fire
  await apiRequestPromise;

  // Verify UI reflection
  await expect(page.getByLabel('updated after')).toHaveValue('2023-04-05');
});

test('after form field affects api request and page url', async ({ page }) => {
  await page.goto('/reports/spec_mentors');

  const apiRequestPromise = page.waitForRequest(req =>
    req.url().includes('/api/v0/spec_mentors') &&
    req.url().includes('after=2023-05-06')
  );

  // Interaction
  await page.getByLabel('updated after').fill('2023-05-06');

  // Wait for the network effect
  await apiRequestPromise;

  // Verify URL update
  await expect(page).toHaveURL(/after=2023-05-06/);
});
