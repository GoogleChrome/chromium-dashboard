// @ts-check
import { test, expect } from '@playwright/test';
import {
  captureConsoleMessages, login, logout, gotoNewFeatureList
} from './test_utils';

test.beforeEach(async ({ page }) => {
  captureConsoleMessages(page);

  // Login is required to access the feature list features fully
  await login(page);
});

test.afterEach(async ({ page }) => {
    // Logout after running each test.
    await logout(page);
});

test('Typing slash focuses on searchbox', async ({ page }) => {
  // Use the utility to navigate (removes hardcoded localhost URL)
  await gotoNewFeatureList(page);

  const searchbox = page.locator('#inputfield input');

  // Verify initial state
  await expect(searchbox).toBeVisible();
  await expect(searchbox).toHaveValue('');

  await test.step('Verify keyboard shortcut', async () => {
    // Explanation of expected behavior:
    // 1. "abc" -> Typed on <body> (ignored)
    // 2. "/"   -> Hotkey detected by app, moves focus to searchbox
    // 3. "def" -> Typed into searchbox
    // 4. "/"   -> Typed into searchbox (literal character now that it has focus)
    // 5. "ghi" -> Typed into searchbox
    await page.keyboard.type('abc/def/ghi');

    // Assertion:
    // We use toHaveValue() because user input changes the DOM property,
    // not necessarily the HTML attribute.
    await expect(searchbox).toHaveValue('def/ghi');
  });
});
