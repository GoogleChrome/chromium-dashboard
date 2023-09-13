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


test('navigate to create feature page', async ({page}) => {
  // console.log('navigate to create feature page');
  const mobile = await isMobile(page);

  const menuButton = page.locator('[data-testid=menu]');
  await expect(menuButton).toBeVisible();
  if (mobile) {
    await menuButton.click();  // To show menu.
  }

  // Expect create feature button to be present.
  const createFeatureButton = page.getByTestId('create-feature-button');
  await expect(createFeatureButton).toBeVisible({timeout: 30000});
  // Take a screenshot of the "Create feature" button.
  await expect(createFeatureButton).toHaveScreenshot('create-feature-button.png');

  // Navigate to the new feature page.
  await createFeatureButton.click();
  if (mobile) {
    await menuButton.click();  // To hide menu
    delay(500);
  }

  // Expect "Add a feature" header to be present.
  const addAFeatureHeader = page.getByTestId('add-a-feature');
  await expect(addAFeatureHeader).toBeVisible({timeout:10000});

  // Take a screenshot of the content area.
  await expect(page).toHaveScreenshot('new-feature-page.png');
  // console.log('navigate to create feature page done');
});


test('enter feature name', async ({page}) => {
  // console.log('enter feature name');
  test.setTimeout(90000);
  const mobile = await isMobile(page);

  const menuButton = page.locator('[data-testid=menu]');
  await expect(menuButton).toBeVisible();
  if (mobile) {
    await menuButton.click();
  }

  const createFeatureButton = page.getByTestId('create-feature-button');
  await expect(createFeatureButton).toBeVisible({ timeout: 30000 });

  // Navigate to the new feature page.
  await createFeatureButton.click();
  if (mobile) {
    await menuButton.click();  // To hide menu
    delay(2500);
  }

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
