// @ts-check
import { test, expect } from '@playwright/test';
import {
  captureConsoleMessages, login, createNewFeature
} from './test_utils';

test.beforeEach(async ({ page }, testInfo) => {
  captureConsoleMessages(page);
  testInfo.setTimeout(30000);

  await login(page);
});

test('add an origin trial stage', async ({ page }) => {
  // Use test.step to organize the report and make debugging easier.
  await test.step('Setup: Create a new feature', async () => {
    await createNewFeature(page);
  });

  await test.step('Open the Add Stage dialog', async () => {
    // Locate by accessible text/role where possible
    const incubatingPanel = page.locator('sl-details', { hasText: 'Start incubating' });

    // Ensure the panel is actually usable before clicking
    await expect(incubatingPanel).toBeVisible();
    await incubatingPanel.click();

    await page.getByRole('button', { name: 'Add stage' }).click();

    // Assertion acts as a wait: Wait for the dialog/select to appear
    await expect(page.locator('sl-select#stage_create_select')).toBeVisible();
  });

  await test.step('Select Origin Trial stage and verify dialog', async () => {
    const stageSelect = page.locator('sl-select#stage_create_select');
    await stageSelect.click();

    // Avoid magic numbers (value="150"). Use text to be readable and resilient to ID changes.
    // We locate the option visible in the dropdown.
    const originTrialOption = page.locator('sl-option', { hasText: 'Origin trial' }).first();

    // Wait for the dropdown animation to settle
    await expect(originTrialOption).toBeVisible();
    await originTrialOption.hover();

    // Visual Regression: Ensure the mask selector is specific enough
    await expect(page).toHaveScreenshot('create-origin-trial-stage-dialog.png', {
      mask: [page.locator('#history')],
      // Increase threshold slightly if font rendering causes flakes
      maxDiffPixelRatio: 0.01
    });

    await originTrialOption.click();

    // Verify the selection took hold before moving on.
    await expect(stageSelect).toContainText('Origin trial');
  });

  await test.step('Create the stage', async () => {
    await page.getByRole('button', { name: 'Create stage' }).click();

    // Wait for navigation and verify URL pattern
    await page.waitForURL(/\/feature\//);
  });

  await test.step('Verify Origin Trial panels', async () => {
    // Define panels
    const otPanel1 = page.locator('sl-details', { hasText: 'Origin Trial' }).first();
    const otPanel2 = page.locator('sl-details', { hasText: 'Origin Trial 2' }).first();

    // Click and wait for state change (attribute verification acts as a wait)
    await otPanel1.click();
    await expect(otPanel1).toHaveAttribute('open', '');

    await otPanel2.click();
    await expect(otPanel2).toHaveAttribute('open', '');

    // Scroll to "Prepare to ship" to position the screen
    const prepareToShip = page.locator('sl-details', { hasText: 'Prepare to ship' });
    await prepareToShip.scrollIntoViewIfNeeded();

    // Final Screenshot
    await expect(page).toHaveScreenshot('origin-trial-panels.png', {
      mask: [page.locator('#history')]
    });
  });
});
