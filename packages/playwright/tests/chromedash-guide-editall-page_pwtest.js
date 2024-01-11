// @ts-check
import { test, expect } from '@playwright/test';
import { captureConsoleMessages, delay, login, logout, createNewFeature } from './test_utils';


test.beforeEach(async ({ page }) => {
    captureConsoleMessages(page);
    test.setTimeout(90000);

    // Login before running each test.
    await login(page);
});

test.afterEach(async ({ page }) => {
    // Logout after running each test.
    await logout(page);
});


test('editall page', async ({ page }) => {
    await createNewFeature(page);
    await delay(500);

    // Edit all fields.
    const editButton = page.getByText('Edit all fields');
    await editButton.click();
    await delay(500);

    await expect(page).toHaveScreenshot('edit-all-fields.png');
});

test('test semantic checks', async ({ page }) => {
    await createNewFeature(page);

    const devTrialDesktopInput = page.locator('input[name="dt_milestone_desktop_start"]');
    await devTrialDesktopInput.fill('100');
    await devTrialDesktopInput.blur(); // Must blur to trigger change event.
    await delay(500);

    // test screenshot of OK dev trial milestone
    await expect(page).toHaveScreenshot('dev-trial-desktop-ok.png');

    // Enter shipped desktop milestone of same number
    const shippedDesktopInput = page.locator('input[name="shipped_milestone"]');
    await shippedDesktopInput.fill('100');
    await shippedDesktopInput.blur(); // Must blur to trigger change event.
    await delay(500);
    // Test that the error message is shown for invalid shipped date
    await expect(page).toHaveScreenshot('shipped-desktop-error.png');
});
