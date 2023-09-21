// @ts-check
import { test, expect } from '@playwright/test';
import { captureConsoleMessages, isMobile, delay, login, logout } from './test_utils';


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
