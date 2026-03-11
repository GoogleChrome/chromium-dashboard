// @ts-check
import {test, expect} from '@playwright/test';
import {
  captureConsoleMessages,
  login,
  logout,
  gotoNewFeaturePage,
  enterBlinkComponent,
  createNewFeature,
  enterWebFeatureId,
  expectScreenshot,
} from './test_utils';

test.beforeEach(async ({page}, testInfo) => {
  captureConsoleMessages(page);
  testInfo.setTimeout(30000);

  // Login before running each test.
  await login(page);
});

test.afterEach(async ({page}) => {
  // Logout after running each test.
  await logout(page);
});

test('navigate to create feature page', async ({page}) => {
  await gotoNewFeaturePage(page);
  const menuButton = page.getByTestId('menu');

  // 1. Wait for the button container
  await expect(menuButton).toBeVisible();

  // 2. Wait for the internal icon to paint
  await expect(menuButton.locator('sl-icon svg')).toBeVisible({timeout: 20000});

  // Take a screenshot of the content area.
  await expectScreenshot(page, 'new-feature-page');
});

test('enter feature name', async ({page}) => {
  await gotoNewFeaturePage(page);

  const featureNameInput = page.locator('input[name="name"]');
  await expect(featureNameInput).toBeVisible();

  // Expand the extra help.
  const extraHelpButton = page.locator(
    'chromedash-form-field[name="name"] sl-icon-button'
  );
  // Wait for the SVG inside the Shadow DOM to be present.
  // This ensures the icon graphic has actually rendered.
  await expect(extraHelpButton.locator('sl-icon svg')).toBeVisible({
    timeout: 20000,
  });
  await expect(extraHelpButton).toBeVisible();
  await extraHelpButton.click();

  // Enter a feature name.
  await featureNameInput.fill('Test feature name');

  // Verify the input has the value before screenshotting (implicitly waits for fill to complete)
  await expect(featureNameInput).toHaveValue('Test feature name');

  await expectScreenshot(page, 'feature-name');
});

test('test semantic checks', async ({page}) => {
  await gotoNewFeaturePage(page);

  // Enter feature name
  const featureNameInput = page.locator('input[name="name"]');
  await featureNameInput.fill('Test deprecated feature name');

  // Enter summary description
  const summaryInput = page.locator('textarea[name="summary"]');
  await summaryInput.fill('Test summary description');
  await summaryInput.blur(); // Must blur to trigger change event logic.

  // Check that the warning shows up.
  // Playwright automatically retries this assertion until it passes or times out.
  const summaryLocator = page.locator('chromedash-form-field[name="summary"]');
  await expect(summaryLocator).toContainText('Feature summary should be');

  const helpIcon = page.locator(
    'chromedash-form-field[name="name"] sl-icon-button'
  );
  await expect(helpIcon).toBeVisible();
  // Wait for the SVG inside the Shadow DOM to be present.
  // This ensures the icon graphic has actually rendered.
  await expect(helpIcon.locator('sl-icon svg')).toBeVisible({timeout: 20000});

  // Screenshot of warnings about feature name summary length
  await expectScreenshot(page, 'warning-feature-name-and-summary-length', {
    mask: [page.locator('section[id="history"]')],
  });

  // Fix cause of the error
  await summaryInput.fill(
    '0123456789 0123456789 0123456789 0123456789 0123456789 0123456789 0123456789 0123456789 0123456789 0123456789'
  );
  await summaryInput.blur(); // Must blur to trigger change event.

  // Check that there is no error now for the summary field
  await expect(summaryLocator).not.toContainText('Feature summary should be');
});

test('enter blink component', async ({page}) => {
  await gotoNewFeaturePage(page);

  // Scroll to blink components field.
  const blinkComponentsField = page.locator(
    'chromedash-form-field[name=blink_components]'
  );
  await blinkComponentsField.scrollIntoViewIfNeeded();
  await expect(blinkComponentsField).toBeVisible();

  const datalistOptions = blinkComponentsField.locator(
    'datalist#blink_components_list option'
  );
  await expect(datalistOptions.first()).toBeAttached({timeout: 20000});

  await enterBlinkComponent(page);
  await blinkComponentsField.click();

  await expectScreenshot(page, 'blink-components');
});

test('enter web feature id', async ({page}) => {
  await gotoNewFeaturePage(page);

  // Scroll to web feature id field.
  const webFeatureIdField = page.locator(
    'chromedash-form-field[name=web_feature]'
  );
  await webFeatureIdField.scrollIntoViewIfNeeded();
  await expect(webFeatureIdField).toBeVisible();

  // Explicitly wait for the datalist to populate with options.
  // The browser will not paint the arrow until these exist.
  const datalistOptions = webFeatureIdField.locator(
    'datalist#web_feature_list option'
  );
  await expect(datalistOptions.first()).toBeAttached({timeout: 20000});

  await enterWebFeatureId(page);
  await webFeatureIdField.click();

  await expectScreenshot(page, 'feature-id');
});

test('create new feature', async ({page}) => {
  await createNewFeature(page);

  // Screenshot of this new feature.
  // The mask handles the dynamic history section.
  await expectScreenshot(page, 'new-feature-created', {
    mask: [page.locator('section[id="history"]')],
  });
});
