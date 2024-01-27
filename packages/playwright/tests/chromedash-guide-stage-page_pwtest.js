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


test('edit origin trial stage', async ({ page }) => {
    // Safest way to work with a unique feature is to create it.
    await createNewFeature(page);

    // Add an origin trial stage.
    const addStageButton = page.getByText('Add stage');
    await addStageButton.click();
    await delay(500);

    // Select stage to create
    const stageSelect = page.locator('sl-select#stage_create_select');
    await stageSelect.click();
    await delay(500);

    // Click the origin trial stage option to prepare to create stage.
    const originTrialStageOption = page.locator('sl-select sl-option[value="150"]');
    originTrialStageOption.click();
    await delay(500);

    // Click the Create stage button to finally create the stage.
    const createStageButton = page.getByText('Create stage');
    await createStageButton.click();
    await delay(500);

    // Edit the Origin Trial (1) stage
    const originTrialPanel = page.locator('sl-details[summary="Origin Trial"]');
    await originTrialPanel.click();
    const editFieldsButton = originTrialPanel.locator('sl-button[href^="/guide/stage"]');
    await editFieldsButton.click();
    await delay(500);

    await page.waitForURL('**/guide/stage/*/*/*');

    // Find the desktop start milestone field
    const originTrialDesktopInput = page.locator('input[name="ot_milestone_desktop_start"]');
    await originTrialDesktopInput.fill('100');
    await originTrialDesktopInput.blur(); // Must blur to trigger change event.
    await delay(500);

    // Enter the same value for the _end field
    const originTrialDesktopEndInput = page.locator('input[name="ot_milestone_desktop_end"]');
    await originTrialDesktopEndInput.fill('100');
    await originTrialDesktopEndInput.blur(); // Must blur to trigger change event.
    await delay(500);

    // Check that there is an error now for the origin trail milestone fields
    const originTrailDesktopMilestoneStartLocator = page.locator('chromedash-form-field[name="ot_milestone_desktop_start"]');
    await expect(originTrailDesktopMilestoneStartLocator.locator('.check-error')).toHaveCount(1);

    const originTrailDesktopMilestoneEndLocator = page.locator('chromedash-form-field[name="ot_milestone_desktop_end"]');
    await expect(originTrailDesktopMilestoneEndLocator.locator('.check-error')).toHaveCount(1);

    // Scroll to a later field to center the OT milestone fields.
    const originTrialAndroidMilestoneStart =
        page.locator('chromedash-form-field[name="ot_milestone_android_start"]');
    await originTrialAndroidMilestoneStart.scrollIntoViewIfNeeded();
    await delay(500);

    // Screenshot
    await expect(page).toHaveScreenshot('semantic-check-origin-trial.png');

    // Remove the end value
    await originTrialDesktopEndInput.fill('');
    await originTrialDesktopEndInput.blur(); // Must blur to trigger change event.
    await delay(500);

    // Check that there is no error now.
    await expect(originTrailDesktopMilestoneStartLocator.locator('.check-error')).toHaveCount(0);
    await expect(originTrailDesktopMilestoneEndLocator.locator('.check-error')).toHaveCount(0);

    // Get the Submit button, to submit the change of OT start milestone.
    const submitButton = page.locator('input[type="submit"]');
    await submitButton.click();
    await delay(500);

    // Check that we are back on the Feature page
    await page.waitForURL('**/feature/*');

    // Edit the Origin Trial (2) stage
    const originTrial2Panel = page.locator('sl-details[summary="Origin Trial 2"]');
    await originTrial2Panel.click();
    const editFieldsButton2 = originTrial2Panel.locator('sl-button[href^="/guide/stage"]');
    await editFieldsButton2.click();
    await delay(500);
    await page.waitForURL('**/guide/stage/*/*/*');

    // Find the desktop end milestone field
    const originTrial2DesktopInput = page.locator('input[name="ot_milestone_desktop_end"]');
    await originTrial2DesktopInput.fill('100');
    await originTrial2DesktopInput.blur();  // To trigger change event.

    // Check that there is no error.
    const originTrail2DesktopMilestoneEndLocator = page.locator('chromedash-form-field[name="ot_milestone_desktop_end"]');
    await expect(originTrail2DesktopMilestoneEndLocator.locator('.check-error')).toHaveCount(0);

    // Submit this change
    const submitButton2 = page.locator('input[type="submit"]');
    await submitButton2.click();
    await delay(500);

    // Wait until we are back on the feature page
    await page.waitForURL('**/feature/*');

    // Open the Prepare to ship section.
    const prepareToShipPanel = page.locator('sl-details[summary="Prepare to ship"]');
    await prepareToShipPanel.click();
    await delay(500);

    // click 'Edit fields' button to go to the stage page.
    const editFieldsButton3 = prepareToShipPanel.locator('sl-button[href^="/guide/stage"]');
    await editFieldsButton3.click();
    await delay(500);

    // Find the shipped_milestone field
    const shippedMilestoneInput = page.locator('input[name="shipped_milestone"]');
    // Enter the same milestone as the OT 1 start.
    await shippedMilestoneInput.fill('100');
    await shippedMilestoneInput.blur();  // To trigger change event.
    await delay(500);

    // Check that there is a warning message.
    const shippedMilestoneLocator = page.locator('chromedash-form-field[name="shipped_milestone"]');
    await expect(shippedMilestoneLocator).toContainText('All origin trials starting milestones should be before feature shipping milestone.');

    // Warning should allow submit
    const submitButton3 = page.locator('input[type="submit"]');
    await submitButton3.click();
    await delay(500);

    // We should be back on the feature page.
    await page.waitForURL('**/feature/*');
});
