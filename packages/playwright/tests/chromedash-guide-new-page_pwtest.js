// @ts-check
import { test, expect } from '@playwright/test';
import {
  captureConsoleMessages, login, logout, gotoNewFeaturePage, createNewFeature
} from './test_utils';

test.beforeEach(async ({ page }, testInfo) => {
  captureConsoleMessages(page);
  testInfo.setTimeout(90000);

  // Login is required for all tests in this file
  await login(page);
});

test.afterEach(async ({ page }) => {
    // Logout after running each test.
    await logout(page);
});

test('navigate to create feature page', async ({ page }) => {
  await gotoNewFeaturePage(page);
  await expect(page).toHaveScreenshot('new-feature-page.png');
});

test('enter feature name', async ({ page }) => {
  await gotoNewFeaturePage(page);

  const featureNameInput = page.locator('input[name="name"]');
  await expect(featureNameInput).toBeVisible();

  // Expand the extra help
  // We use the CSS attribute selector to find the specific field wrapper
  const extraHelpButton = page.locator('chromedash-form-field[name="name"] sl-icon-button');
  await extraHelpButton.click();

  await featureNameInput.fill('Test feature name');

  // expect(screenshot) waits for the frame to stabilize
  await expect(page).toHaveScreenshot('feature-name.png');
});

test('test semantic checks', async ({ page }) => {
  await gotoNewFeaturePage(page);

  await test.step('Trigger Validation Error', async () => {
    // Fill feature name
    await page.locator('input[name="name"]').fill('Test deprecated feature name');

    // Fill short summary to trigger length validation
    const summaryInput = page.locator('textarea[name="summary"]');
    await summaryInput.fill('Test summary description');
    await summaryInput.blur();

    // Check for warning
    const summaryField = page.locator('chromedash-form-field[name="summary"]');
    // Auto-wait for text to appear.
    await expect(summaryField).toContainText('Feature summary should be');

    await expect(page).toHaveScreenshot('warning-feature-name-and-summary-length.png', {
      mask: [page.locator('#history')]
    });
  });

  await test.step('Fix Validation Error', async () => {
    const summaryInput = page.locator('textarea[name="summary"]');
    // Fill with valid length (> 100 chars)
    await summaryInput.fill('0123456789 '.repeat(10));
    await summaryInput.blur();

    // Check error is gone
    const summaryField = page.locator('chromedash-form-field[name="summary"]');
    await expect(summaryField).not.toContainText('Feature summary should be');
  });
});

test('enter blink component', async ({ page }) => {
  await gotoNewFeaturePage(page);

  // Use testId for robustness (matches update in test_utils.js)
  const blinkField = page.getByTestId('blink_components_wrapper');
  await blinkField.scrollIntoViewIfNeeded();

  // Click wrapper -> Find Input -> Fill -> Enter
  await blinkField.click();
  const input = blinkField.locator('input');
  await input.fill('blink');
  await input.press('Enter');

  await expect(page).toHaveScreenshot('blink-components.png');
});

test('enter web feature id', async ({ page }) => {
  await gotoNewFeaturePage(page);

  const webFeatureField = page.getByTestId('web_feature_wrapper');
  await webFeatureField.scrollIntoViewIfNeeded();

  //Click wrapper -> Find Input -> Fill -> Enter
  await webFeatureField.click();
  const input = webFeatureField.locator('input');
  await input.fill('hwb');
  await input.press('Enter');

  await expect(page).toHaveScreenshot('feature-id.png');
});

test('create new feature', async ({ page }) => {
  // Uses the robust helper from test_utils
  await createNewFeature(page);

  // Screenshot of this new feature.
  await expect(page).toHaveScreenshot('new-feature-created.png', {
    mask: [page.locator('#history')]
  });
});
