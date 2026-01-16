// @ts-check
import {test, expect} from '@playwright/test';
import {
  captureConsoleMessages,
  login,
  logout,
  createNewFeature,
} from './test_utils';

test.beforeEach(async ({page}, testInfo) => {
  captureConsoleMessages(page);
  testInfo.setTimeout(90000);

  // Login before running each test.
  await login(page);
});

test.afterEach(async ({page}) => {
  // Logout after running each test.
  await logout(page);
});

test('edit origin trial stage', async ({page}) => {
  // Safest way to work with a unique feature is to create it.
  await createNewFeature(page);

  // Add an origin trial stage.
  await page.getByText('Add stage').click();

  // Select stage to create.
  // We wait for the select element to be ready before interacting.
  const stageSelect = page.locator('sl-select#stage_create_select');
  await stageSelect.click();

  // Click the origin trial stage option.
  const originTrialStageOption = page.locator(
    'sl-select sl-option[value="150"]'
  );
  await expect(originTrialStageOption).toBeVisible();
  await originTrialStageOption.click();

  // Click the Create stage button to finally create the stage.
  await page.getByRole('button', {name: 'Create stage'}).click();

  // Edit the Origin Trial (1) stage
  const originTrialPanel = page.locator('sl-details[summary="Origin Trial"]');
  await originTrialPanel.click();

  const editFieldsButton = originTrialPanel.locator(
    'sl-button[href^="/guide/stage"]'
  );
  // Ensure the panel animation is done and button is visible
  await expect(editFieldsButton).toBeVisible();
  await editFieldsButton.click();

  await page.waitForURL('**/guide/stage/*/*/*');

  // Find the desktop start milestone field
  const originTrialDesktopInput = page.locator(
    'input[name="ot_milestone_desktop_start"]'
  );
  await originTrialDesktopInput.fill('100');
  await originTrialDesktopInput.blur(); // Triggers change event logic in the app

  // Enter the same value for the _end field
  const originTrialDesktopEndInput = page.locator(
    'input[name="ot_milestone_desktop_end"]'
  );
  await originTrialDesktopEndInput.fill('100');
  await originTrialDesktopEndInput.blur(); // Triggers change event logic in the app

  // Check that there is an error now for the origin trial milestone fields.
  // Playwright will retry this assertion automatically until the UI renders the error.
  const originTrialDesktopStartError = page.locator(
    'chromedash-form-field[name="ot_milestone_desktop_start"] .check-error'
  );
  await expect(originTrialDesktopStartError).toBeVisible();

  const originTrialDesktopEndError = page.locator(
    'chromedash-form-field[name="ot_milestone_desktop_end"] .check-error'
  );
  await expect(originTrialDesktopEndError).toBeVisible();

  // Scroll to a later field to center the OT milestone fields for the screenshot.
  const originTrialAndroidMilestoneStart = page.locator(
    'chromedash-form-field[name="ot_milestone_android_start"]'
  );
  await originTrialAndroidMilestoneStart.scrollIntoViewIfNeeded();

  await expect(page).toHaveScreenshot('semantic-check-origin-trial.png');

  // Remove the end value
  await originTrialDesktopEndInput.fill('');
  await originTrialDesktopEndInput.blur();

  // Check that there is no error now.
  await expect(originTrialDesktopStartError).not.toBeVisible();
  await expect(originTrialDesktopEndError).not.toBeVisible();

  // Submit the change of OT start milestone.
  const submitButton = page.locator('input[type="submit"]');
  await submitButton.click();

  // Check that we are back on the Feature page
  await page.waitForURL('**/feature/*');

  // Edit the Origin Trial (2) stage
  const originTrial2Panel = page.locator(
    'sl-details[summary="Origin Trial 2"]'
  );
  await originTrial2Panel.click();

  const editFieldsButton2 = originTrial2Panel.locator(
    'sl-button[href^="/guide/stage"]'
  );
  await expect(editFieldsButton2).toBeVisible();
  await editFieldsButton2.click();

  await page.waitForURL('**/guide/stage/*/*/*');

  // Find the desktop end milestone field
  const originTrial2DesktopInput = page.locator(
    'input[name="ot_milestone_desktop_end"]'
  );
  await originTrial2DesktopInput.fill('100');
  await originTrial2DesktopInput.blur();

  // Check that there is no error.
  const originTrial2DesktopEndError = page.locator(
    'chromedash-form-field[name="ot_milestone_desktop_end"] .check-error'
  );
  await expect(originTrial2DesktopEndError).not.toBeVisible();

  await submitButton.click();

  // Wait until we are back on the feature page
  await page.waitForURL('**/feature/*');

  // Open the Prepare to ship section.
  const prepareToShipPanel = page.locator(
    'sl-details[summary="Prepare to ship"]'
  );
  await prepareToShipPanel.click();

  // click 'Edit fields' button to go to the stage page.
  const editFieldsButton3 = prepareToShipPanel.locator(
    'sl-button[href^="/guide/stage"]'
  );
  await expect(editFieldsButton3).toBeVisible();
  await editFieldsButton3.click();

  // Find the shipped_milestone field
  const shippedMilestoneInput = page.locator('input[name="shipped_milestone"]');

  // Enter the same milestone as the OT 1 start.
  await shippedMilestoneInput.fill('100');
  await shippedMilestoneInput.blur();

  // Check that there is a warning message.
  const shippedMilestoneField = page.locator(
    'chromedash-form-field[name="shipped_milestone"]'
  );
  await expect(shippedMilestoneField).toContainText(
    'All origin trials starting milestones should be before feature shipping milestone.'
  );

  // Warning should allow submit
  await submitButton.click();

  // We should be back on the feature page.
  await page.waitForURL('**/feature/*');
});
