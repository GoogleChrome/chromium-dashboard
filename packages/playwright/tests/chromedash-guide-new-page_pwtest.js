// @ts-check
import { test, expect } from '@playwright/test';
import {
  captureConsoleMessages, delay, login, logout,
  gotoNewFeaturePage, enterBlinkComponent, createNewFeature
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


test('navigate to create feature page', async ({page}) => {
  await gotoNewFeaturePage(page);

  // Take a screenshot of the content area.
  await expect(page).toHaveScreenshot('new-feature-page.png');
});


test('enter feature name', async ({page}) => {
  await gotoNewFeaturePage(page);

  test.setTimeout(90000);
  const featureNameInput = page.locator('input[name="name"]');
  await expect(featureNameInput).toBeVisible({timeout: 60000});

  // Expand the extra help.
  const extraHelpButton = page.locator('chromedash-form-field[name="name"] sl-icon-button');
  await expect(extraHelpButton).toBeVisible();
  await extraHelpButton.click();

  // Enter a feature name.
  await featureNameInput.fill('Test feature name');
  await delay(500);

  await expect(page).toHaveScreenshot('feature-name.png');

});


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

  // Check that the warning shows up.
  const summaryLocator = page.locator('chromedash-form-field[name="summary"]');
  await expect(summaryLocator).toContainText('Feature summary should be');

  // Screenshot of warnings about feature name summary length
  await expect(page).toHaveScreenshot('warning-feature-name-and-summary-length.png', {
    mask: [page.locator('section[id="history"]')]
  });
  await delay(500);

  // Fix cause of the error
  await summaryInput.fill('0123456789 0123456789 0123456789 0123456789 0123456789 0123456789 0123456789 0123456789 0123456789 0123456789');
  await summaryInput.blur(); // Must blur to trigger change event.

  // Check that there is no error now for the summary field
  await expect(summaryLocator).not.toContainText('Feature summary should be');

  // // Save changes
  // const submitButton = page.locator('input[type="submit"]');
  // await expect(submitButton).toBeVisible();
  // await submitButton.click();
  // await delay(500);
});


test('enter blink component', async ({ page }) => {
  await gotoNewFeaturePage(page);

  // Scroll to blink components field.
  const blinkComponentsField = page.locator('chromedash-form-field[name=blink_components]');
  await blinkComponentsField.scrollIntoViewIfNeeded();
  await expect(blinkComponentsField).toBeVisible();

  await enterBlinkComponent(page);

  await expect(page).toHaveScreenshot('blink-components.png');
});


test('create new feature', async ({ page }) => {
  await createNewFeature(page);

  // Screenshot of this new feature.
  await expect(page).toHaveScreenshot('new-feature-created.png', {
    mask: [page.locator('section[id="history"]')]
  });
  await delay(500);
});
