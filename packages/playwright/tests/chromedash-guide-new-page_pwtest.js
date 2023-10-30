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


test('create new feature', async ({ page }) => {
  await gotoNewFeaturePage(page);

  // Enter feature name
  const featureNameInput = page.locator('input[name="name"]');
  await featureNameInput.fill('Test feature name');
  await delay(500);

  // Enter summary description
  const summaryInput = page.locator('textarea[name="summary"]');
  await summaryInput.fill('Test summary description');
  await delay(500);

  // Select blink component.
  const blinkComponentsInputWrapper = page.locator('div.datalist-input-wrapper');
  await blinkComponentsInputWrapper.focus();
  await delay(500);
  const blinkComponentsInput = blinkComponentsInputWrapper.locator('input');
  await blinkComponentsInput.fill('blink');
  await delay(500);

  // Select feature type.
  const featureTypeRadioNew = page.locator('input[name="feature_type"][value="0"]');
  await featureTypeRadioNew.click();
  await delay(500);

  // Submit the form.
  const submitButton = page.locator('input[type="submit"]');
  await submitButton.click();
  await delay(500);

  // Check if we have a screenshot for this new feature.
  await expect(page).toHaveScreenshot('new-feature-created.png', {
    mask: [page.locator('section[id="history"]')]
  });
  await delay(500);

  // Edit the feature.
  const editButton = page.locator('a[class="editfeature"]');
  await editButton.click();
  await delay(500);

  // Screenshot this editor page
  await expect(page).toHaveScreenshot('new-feature-edit.png');

  // Register to accept the confirm dialog before clicking to delete.
  page.once('dialog', dialog => dialog.accept());

    // Delete the new feature.
  const deleteButton = page.locator('a[id$="delete-feature"]');
  await deleteButton.click();
  await delay(500);

  // Screenshot the feature list after deletion.
  // Not yet, since deletion only marks the feature as deleted,
  // and the resulting page is always different.
  // await expect(page).toHaveScreenshot('new-feature-deleted.png');
  // await delay(500);
});
