// @ts-check
import { test, expect } from '@playwright/test';
import { captureConsoleMessages, isMobile, delay, login, logout } from './test_utils';


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


/**
 * @param {import('@playwright/test').Page} page
 */
async function gotoNewFeaturePage(page) {
    // console.log('navigate to create feature page');
    const mobile = await isMobile(page);
    const createFeatureButton = page.getByTestId('create-feature-button');
    const menuButton = page.locator('[data-testid=menu]');

    // Navigate to the new feature page.
    await expect(menuButton).toBeVisible();
    if (mobile) {
        await menuButton.click();  // To show menu.
    }
    await createFeatureButton.click();
    if (mobile) {
        await menuButton.click();  // To hide menu
        await delay(500);
    }

    // Expect "Add a feature" header to be present.
    const addAFeatureHeader = page.getByTestId('add-a-feature');
    await expect(addAFeatureHeader).toBeVisible({ timeout: 10000 });
    // console.log('navigate to create feature page done');
}

test('test semantic checks', async ({ page }) => {
    await gotoNewFeaturePage(page);

    // Enter feature name
    const featureNameInput = page.locator('input[name="name"]');
    await featureNameInput.fill('Test deprecated feature name');
    await delay(500);

    // Enter summary description
    const summaryInput = page.locator('textarea[name="summary"]');
    await summaryInput.fill('Test summary description');
    await summaryInput.blur(); // Must blur to trigger change event.

    await delay(500);

    // Screenshot of this warning about summary length
    await expect(page).toHaveScreenshot('warning-feature-name-and-summary-length.png', {
        mask: [page.locator('section[id="history"]')]
    });
    await delay(500);
});
