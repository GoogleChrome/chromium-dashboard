// @ts-check
import { test, expect } from '@playwright/test';
import { captureConsoleMessages, login, logout, createNewFeature } from './test_utils';

/**
 * Starting from the feature page, goto 'Edit all fields'.
 * @param {import('@playwright/test').Page} page
 */
async function gotoEditAllPage(page) {
    const editButton = page.getByRole('link', { name: 'Edit all fields' });
    await editButton.click();

    await page.waitForURL('**/guide/editall/**');
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

    await expect(page).toHaveScreenshot('edit-all-fields.png');
});


test('test semantic checks', async ({ page }) => {
    await createNewFeature(page);
    await gotoEditAllPage(page);

    const devTrialDesktopInput = page.locator('input[name="dt_milestone_desktop_start"]');
    await devTrialDesktopInput.fill('100');
    await devTrialDesktopInput.blur(); // Must blur to trigger change event.

    const devTrialDesktopMilestoneLocator = page.locator('chromedash-form-field[name="dt_milestone_desktop_start"]');
    await expect(devTrialDesktopMilestoneLocator.locator('.check-warning')).toHaveCount(0);

    // Enter shipped desktop milestone of same number
    const shippedDesktopInput = page.locator('input[name="shipped_milestone"]');
    await shippedDesktopInput.fill('100');
    await shippedDesktopInput.blur(); // Must blur to trigger change event.

    // Scroll next field into view, so we can see the error.
    const shippedAndroidInput = page.locator('input[name="shipped_android_milestone"]');
    await shippedAndroidInput.scrollIntoViewIfNeeded();

    // Test that the error message is shown for invalid shipped date
    const shippedDesktopMilestoneLocator = page.locator('chromedash-form-field[name="shipped_milestone"]');
    const errorLocator = shippedDesktopMilestoneLocator.locator('.check-warning');

    // 1. Functional check: Assert the error is visible and has correct text
    await expect(errorLocator).toBeVisible();
    await expect(errorLocator).toHaveText('Shipped milestone should be later than dev trial.');

    // 2. Visual check: Now snapshot the element
    await expect(shippedDesktopMilestoneLocator).toHaveScreenshot('shipped-desktop-error.png');

    // Remove the cause of the error.
    await shippedDesktopInput.fill('');
    await shippedDesktopInput.blur(); // Must blur to trigger change event.

    // Check that there is no error. `expect` will auto-wait for the element to disappear.
    await expect(errorLocator).toHaveCount(0);
});
