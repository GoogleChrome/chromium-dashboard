// @ts-check
import { test, expect } from '@playwright/test';
import {
    captureConsoleMessages, delay, login, logout,
    gotoNewFeatureList
} from './test_utils';


test.beforeEach(async ({ page }, testInfo) => {
    captureConsoleMessages(page);
    testInfo.setTimeout(90000);

    // Login before running each test.
    await login(page);
});

test.afterEach(async ({ page }) => {
    // Logout after running each test.
    await logout(page);
});

test('Typing slash focuses on searchbox', async ({page}) => {
  await gotoNewFeatureList(page, 'http://localhost:5555/');
  const searchbox = page.locator('#inputfield');
  await expect(searchbox).toBeVisible();
  await expect(searchbox).toHaveAttribute('value', '');
  await page.keyboard.type('abc/def/ghi');
  // Characters before the first slash go to the page.
  // The slash focuses on the searchbox.
  // Later characters, including slashes, go in the searchbox.
  await expect(searchbox).toHaveAttribute('value', 'def/ghixx');
});
