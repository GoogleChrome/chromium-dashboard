// @ts-check
import { test, expect } from '@playwright/test';
import {
  captureConsoleMessages, delay, login, logout,
  gotoNewFeaturePage, createNewFeature
} from './test_utils';


test.beforeEach(async ({page}) => {
  captureConsoleMessages(page);
  test.setTimeout(90000);

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

  // Screenshot of warnings about feature name summary length
  await expect(page).toHaveScreenshot('warning-feature-name-and-summary-length.png', {
    mask: [page.locator('section[id="history"]')]
  });
  await delay(500);
});


test('enter blink component', async ({ page }) => {
  await gotoNewFeaturePage(page);

  // Scroll to blink components field.
  const blinkComponentsField = page.locator('chromedash-form-field[name=blink_components]');
  await blinkComponentsField.scrollIntoViewIfNeeded();
  await expect(blinkComponentsField).toBeVisible();

  const blinkComponentsInputWrapper = page.locator('div.datalist-input-wrapper');
  await expect(blinkComponentsInputWrapper).toBeVisible();

  // Trying to show options, doesn't work yet.
  await blinkComponentsInputWrapper.focus();
  await delay(500);

  const blinkComponentsInput = blinkComponentsInputWrapper.locator('input');
  await blinkComponentsInput.fill('blink');
  await delay(500);

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
