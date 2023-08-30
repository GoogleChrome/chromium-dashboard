// @ts-check
import { test, expect } from '@playwright/test';
import { captureConsoleMessages, delay, login, logout } from './test_utils';

test.beforeEach(async ({page}) => {
  captureConsoleMessages(page);
  test.setTimeout(90000);

  // Attempt to login before running each test.
  await login(page);
});

test.afterEach(async ({page}) => {
  await logout(page);
});


test('navigate to create feature page', async ({page}) => {
  // console.log('navigate to create feature page');

  // Expect create feature button to be present.
  const createFeatureButton = page.locator('[data-testid=create-feature-button]');
  await expect(createFeatureButton).toBeVisible({timeout: 30000});

  // Take a screenshot of header with "Create feature" button.
  await expect(page.locator('[data-testid=header]')).toHaveScreenshot('create-feature-button.png');

  // Navigate to the new feature page by clicking.
  createFeatureButton.click();

  // Expect "Add a feature" header to be present.
  const addAFeatureHeader = page.locator('[data-testid=add-a-feature]');
  await expect(addAFeatureHeader).toBeVisible();

  // Take a screenshot of the content area.
  await expect(page).toHaveScreenshot('new-feature-page.png');
  // console.log('navigate to create feature page done');
});


test('enter feature name', async ({page}) => {
  // console.log('enter feature name');
  test.setTimeout(90000);

  // Navigate to the new feature page.
  const createFeatureButton = page.locator('[data-testid=create-feature-button]');
  createFeatureButton.click({timeout: 10000});

  const featureNameInput = page.locator('input[name="name"]');
  await expect(featureNameInput).toBeVisible({timeout: 60000});

  // Expand the extra help.
  const extraHelpButton = page.locator('chromedash-form-field[name="name"] sl-icon-button');
  await expect(extraHelpButton).toBeVisible();
  extraHelpButton.click();

  // Enter a feature name.
  featureNameInput.fill('Test feature name');

  await expect(page).toHaveScreenshot('feature-name.png');
  // console.log('enter feature name done');
});
