// @ts-check
import { test, expect } from '@playwright/test';
import { captureConsoleMessages, acceptBeforeUnloadDialogs, delay, login, logout, createNewFeature, deleteFeature } from './test_utils';


/**
 * Starting from the feature page, goto 'Edit all fields'.
 * @param {import('@playwright/test').Page} page
 */
async function gotoEditAllPage(page) {
    const editButton = page.getByText('Edit all fields');
    await editButton.click();
    await delay(500);
}


test.beforeEach(async ({ page }) => {
    captureConsoleMessages(page);
    test.setTimeout(90000);

    // Login before running each test.
    await login(page);
    await acceptBeforeUnloadDialogs(page);
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
    await delay(500);

    // Check that there is no error now for the dev trail milestone field
    const devTrailDesktopMilestoneLocator = page.locator('chromedash-form-field[name="dt_milestone_desktop_start"]');
    await expect(devTrailDesktopMilestoneLocator.locator('.check-warning')).toHaveCount(0);

    // Enter shipped desktop milestone of same number
    const shippedDesktopInput = page.locator('input[name="shipped_milestone"]');
    await shippedDesktopInput.fill('100');
    await shippedDesktopInput.blur(); // Must blur to trigger change event.
    await shippedDesktopInput.scrollIntoViewIfNeeded();
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

    // // Submit the change.
    // const saveButton = page.getByText('Save');
    // await saveButton.click();
    // await delay(500);

    // await deleteFeature(page);
});
