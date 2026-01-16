// @ts-check
import {test, expect} from '@playwright/test';
import {
  captureConsoleMessages,
  login,
  logout,
  createNewFeature,
} from './test_utils';

/**
 * Starting from the feature page, goto 'Edit all fields'.
 * @param {import('@playwright/test').Page} page
 */
async function gotoEditAllPage(page) {
  // Use a precise locator for the edit button
  const editButton = page.locator('a[href^="/guide/editall/"]');
  await expect(editButton).toBeVisible();
  await editButton.click();

  // Wait for the form table to render
  await expect(page.locator('chromedash-form-table')).toBeVisible({
    timeout: 30000,
  });
}

test.beforeEach(async ({page}, testInfo) => {
  captureConsoleMessages(page);
  testInfo.setTimeout(30000);

  await login(page);
});

test.afterEach(async ({page}) => {
  // Logout after running each test.
  await logout(page);
});

test('editall page', async ({page}) => {
  await createNewFeature(page);
  await gotoEditAllPage(page);

  await expect(page).toHaveScreenshot('edit-all-fields.png');
});

test('test semantic checks', async ({page}) => {
  await test.step('Setup: Create Feature and Go to Edit All', async () => {
    await createNewFeature(page);
    await gotoEditAllPage(page);
  });

  await test.step('Verify Dev Trial Milestone (Valid)', async () => {
    const devTrialInput = page.locator(
      'input[name="dt_milestone_desktop_start"]'
    );
    await devTrialInput.fill('100');
    await devTrialInput.blur();

    // Ensure no warning appears
    const devTrialField = page.locator(
      'chromedash-form-field[name="dt_milestone_desktop_start"]'
    );
    await expect(devTrialField.locator('.check-warning')).toHaveCount(0);
  });

  await test.step('Trigger Shipped Milestone Conflict', async () => {
    const shippedInput = page.locator('input[name="shipped_milestone"]');
    // Enter same milestone '100' to trigger semantic check
    await shippedInput.fill('100');
    await shippedInput.blur();

    // Verify warning appears
    // We check for visibility before screenshotting to ensure the UI has updated
    const shippedField = page.locator(
      'chromedash-form-field[name="shipped_milestone"]'
    );
    await expect(shippedField.locator('.check-warning')).toBeVisible();

    // Scroll to next field to center the error for the screenshot
    const nextField = page.locator('input[name="shipped_android_milestone"]');
    await nextField.scrollIntoViewIfNeeded();

    await expect(page).toHaveScreenshot('shipped-desktop-error.png');
  });

  await test.step('Resolve Conflict', async () => {
    const shippedInput = page.locator('input[name="shipped_milestone"]');
    await shippedInput.fill('');
    await shippedInput.blur();

    // Verify warning disappears
    const shippedField = page.locator(
      'chromedash-form-field[name="shipped_milestone"]'
    );
    await expect(shippedField.locator('.check-warning')).toHaveCount(0);
  });
});
