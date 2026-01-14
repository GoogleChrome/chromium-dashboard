// @ts-check
import { test, expect } from '@playwright/test';
import {
  captureConsoleMessages, login, createNewFeature
} from './test_utils';

test.beforeEach(async ({ page }, testInfo) => {
  captureConsoleMessages(page);
  testInfo.setTimeout(90000);

  // Login is required to create and edit features
  await login(page);
});

test('edit origin trial stage', async ({ page }) => {
  await test.step('Setup: Create Feature and Origin Trial Stage', async () => {
    await createNewFeature(page);

    // Expand "Start incubating"
    const incubatingPanel = page.locator('sl-details', { hasText: 'Start incubating' });
    await incubatingPanel.click();

    // Open "Add Stage" dialog
    await page.getByRole('button', { name: 'Add stage' }).click();

    // Select "Origin trial" from the dropdown
    const stageSelect = page.locator('sl-select#stage_create_select');
    await stageSelect.click();

    const originTrialOption = page.locator('sl-option', { hasText: 'Origin trial' }).first();
    await expect(originTrialOption).toBeVisible();
    await originTrialOption.click();

    // Create
    await page.getByRole('button', { name: 'Create stage' }).click();

    // Wait for the page to settle (Feature page reload)
    await page.waitForURL('**/feature/*');
  });

  await test.step('Step 1: Trigger Semantic Check Error (Start == End)', async () => {
    // Open the first Origin Trial panel
    const otPanel = page.locator('sl-details', { hasText: 'Origin Trial' }).first();
    await otPanel.click();

    // Click "Edit fields"
    await otPanel.getByRole('button', { name: 'Edit fields' }).click();
    await page.waitForURL('**/guide/stage/*/*/*');

    // Locate inputs
    const startInput = page.locator('input[name="ot_milestone_desktop_start"]');
    const endInput = page.locator('input[name="ot_milestone_desktop_end"]');

    // Enter conflicting values (Start 100, End 100)
    await startInput.fill('100');
    await startInput.blur();
    await endInput.fill('100');
    await endInput.blur(); // Trigger validation

    // Verify Error Messages appear
    // Use standard CSS attribute selectors
    const startField = page.locator('chromedash-form-field[name="ot_milestone_desktop_start"]');
    const endField = page.locator('chromedash-form-field[name="ot_milestone_desktop_end"]');

    await expect(startField.locator('.check-error')).toBeVisible();
    await expect(endField.locator('.check-error')).toBeVisible();

    // Screenshot (Visual Regression)
    await page.locator('input[name="ot_milestone_android_start"]').scrollIntoViewIfNeeded();
    await expect(page).toHaveScreenshot('semantic-check-origin-trial.png');

    // Fix the error (Clear End date)
    await endInput.fill('');
    await endInput.blur();

    // Verify Errors disappear
    await expect(startField.locator('.check-error')).toBeHidden();
    await expect(endField.locator('.check-error')).toBeHidden();

    // Submit and return to Feature page
    await page.locator('input[type="submit"]').click();
    await page.waitForURL('**/feature/*');
  });

  await test.step('Step 2: Verify Origin Trial 2 (No conflicts)', async () => {
    const otPanel2 = page.locator('sl-details', { hasText: 'Origin Trial 2' });
    await otPanel2.click();

    // Navigate to Edit
    await otPanel2.getByRole('button', { name: 'Edit fields' }).click();
    await page.waitForURL('**/guide/stage/*/*/*');

    // Set End Milestone only
    const endInput = page.locator('input[name="ot_milestone_desktop_end"]');
    await endInput.fill('100');
    await endInput.blur();

    // Assert NO error exists
    const endField = page.locator('chromedash-form-field[name="ot_milestone_desktop_end"]');
    await expect(endField.locator('.check-error')).toBeHidden();

    // Submit
    await page.locator('input[type="submit"]').click();
    await page.waitForURL('**/feature/*');
  });

  await test.step('Step 3: Verify "Prepare to Ship" Warning', async () => {
    const shipPanel = page.locator('sl-details', { hasText: 'Prepare to ship' });
    await shipPanel.click();

    // Navigate to Edit
    await shipPanel.getByRole('button', { name: 'Edit fields' }).click();
    await page.waitForURL('**/guide/stage/*/*/*');

    // Enter Shipped Milestone = 100 (Same as OT Start, which should trigger warning)
    const shippedInput = page.locator('input[name="shipped_milestone"]');
    await shippedInput.fill('100');
    await shippedInput.blur();

    // Verify Warning Text
    const fieldWrapper = page.locator('chromedash-form-field[name="shipped_milestone"]');
    await expect(fieldWrapper).toContainText('All origin trials starting milestones should be before feature shipping milestone');

    // Warnings are non-blocking; Submit should succeed.
    await page.locator('input[type="submit"]').click();
    await page.waitForURL('**/feature/*');
  });
});
