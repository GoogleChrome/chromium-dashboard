// @ts-check
import { test, expect } from '@playwright/test';
import { captureConsoleMessages, delay, login, logout, createNewFeature } from './test_utils';


/**
 * Starting from the feature page, goto 'Edit all fields'.
 * @param {import('@playwright/test').Page} page
 */
async function gotoEditAllPage(page) {
    const editButton = page.locator('a[href^="/guide/editall/"]');
    await editButton.click();
  await expect(page.locator('chromedash-form-table')).toBeVisible(
      {timeout: 30000});
}


test.beforeEach(async ({ page }, testInfo) => {
    captureConsoleMessages(page);
    testInfo.setTimeout(30000);

    // Login before running each test.
    await login(page);
});

test.afterEach(async ({ page }) => {
    // Logout after running each test.
    await logout(page);
});


test('editall page', async ({ page }) => {
    await createNewFeature(page);
    await gotoEditAllPage(page);

  await expect(page).toHaveScreenshot('edit-all-fields.png', {timeout: 30000});
});


test('test semantic checks', async ({ page }) => {
    await createNewFeature(page);
    await gotoEditAllPage(page);

    const devTrialDesktopInput = page.locator('input[name="dt_milestone_desktop_start"]');
    await devTrialDesktopInput.fill('100');
    await devTrialDesktopInput.blur(); // Must blur to trigger change event.
    await delay(500);

    // Check that there is no error now for the dev trail milestone field
    const devTrailDesktopMilestoneLocator = page.locator('chromedash-form-field[name="dt_milestone_desktop_start"]');
    await expect(devTrailDesktopMilestoneLocator.locator('.check-warning')).toHaveCount(0);

    // Enter shipped desktop milestone of same number
    const shippedDesktopInput = page.locator('input[name="shipped_milestone"]');
    await shippedDesktopInput.fill('100');
    await shippedDesktopInput.blur(); // Must blur to trigger change event.
    await delay(500);

    // Scroll next field into view, so we can see the error.
    const shippedAndroidInput = page.locator('input[name="shipped_android_milestone"]');
    await shippedAndroidInput.scrollIntoViewIfNeeded();
    await delay(500);

    // Test that the error message is shown for invalid shipped date
    await expect(page).toHaveScreenshot('shipped-desktop-error.png');

    // Remove the cause of the error.
    await shippedDesktopInput.fill('');
    await shippedDesktopInput.blur(); // Must blur to trigger change event.
    await delay(500);

    // Check that there is no error now for the dev trail milestone field
    const shippedDesktopMilestoneLocator = page.locator('chromedash-form-field[name="shipped_milestone"]');
    await expect(shippedDesktopMilestoneLocator.locator('.check-warning')).toHaveCount(0);
});
